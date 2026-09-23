"""Emit the product SystemVerilog for vibe_pcs_tx_pack (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_params.vh"``,
four ``vibe_pcs_tx_amctl`` instances, combo ``beat_ready`` /
``lane_vld`` / ``am_word`` / lane mux, and the timer / pack / emit
always-block (5×512 → 4×640, inverse G2). pycc netlists are a
prototype only; this file is what lands in
``rtl/pcs/vibe_pcs_tx_pack.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_pcs_tx_pack.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip ee5e8f4 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_tx_pack
//
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_tx_pack
"""

BODY = """\
// AS-0.1 §5 T5 G2: 512b beats + AMCTL (outside FEC) → 640b = 4×160. almost_full backpresses.
module vibe_pcs_tx_pack (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         sdf_period,
  input  logic         afifo_afull,
  input  logic [511:0] beat_data,
  input  logic         beat_vld,
  output logic         beat_ready,
  output logic [159:0] lane0,
  output logic [159:0] lane1,
  output logic [159:0] lane2,
  output logic [159:0] lane3,
  output logic         lane_vld,
  input  logic         lane_ready,
  output logic         am_word
);
  `include "vibe_ub_params.vh"

  logic [9:0]   sym_cnt; // symbols since last AMCTL on a lane (20 sym/beat-word)
  logic [1:0]   am_phase; // 0=data, 1=am0, 2=am1
  logic [319:0] am0, am1, am2, am3;
  logic         am_ack0;
  logic [639:0] acc;
  logic [2:0]   acc_n; // 0..4  : 512-bit beats gathered toward 2560 = 4×640
  logic [2559:0] pack;
  logic          pack_vld;
  logic [1:0]    emit_idx;

  vibe_pcs_tx_amctl u_am0 (.clk(clk), .rst_n(rst_n), .link_up(1'b1), .sdf_period(sdf_period),
    .lane_id(2'd0), .req(am_phase!=2'd0), .ack(am_ack0), .amctl_40B(am0));
  vibe_pcs_tx_amctl u_am1 (.clk(clk), .rst_n(rst_n), .link_up(1'b1), .sdf_period(sdf_period),
    .lane_id(2'd1), .req(1'b1), .ack(), .amctl_40B(am1));
  vibe_pcs_tx_amctl u_am2 (.clk(clk), .rst_n(rst_n), .link_up(1'b1), .sdf_period(sdf_period),
    .lane_id(2'd2), .req(1'b1), .ack(), .amctl_40B(am2));
  vibe_pcs_tx_amctl u_am3 (.clk(clk), .rst_n(rst_n), .link_up(1'b1), .sdf_period(sdf_period),
    .lane_id(2'd3), .req(1'b1), .ack(), .amctl_40B(am3));

  wire [9:0] period = sdf_period ? 10'd640 : 10'd512;
  wire insert_am = (sym_cnt >= period);

  assign beat_ready = !afifo_afull && lane_ready && (am_phase == 2'd0) && !pack_vld;
  // Emit the current 4×640 first, then AMCTL. Holding AM *before* P0 put the
  // post-AM 512 stream on an odd beat (group of 5 starting at beat 35, 75, …)
  // so RX 1024b pairs were permanently off-by-one. Idle zeros still passed.
  assign lane_vld   = (am_phase != 2'd0) || pack_vld;
  assign am_word    = (am_phase != 2'd0);
  wire completing   = beat_vld && beat_ready && (acc_n == 3'd4);
  assign lane0 = (am_phase == 2'd1) ? am0[319:160] :
                 (am_phase == 2'd2) ? am0[159:0]   :
                 pack[640*emit_idx + 159 -: 160];
  assign lane1 = (am_phase == 2'd1) ? am1[319:160] :
                 (am_phase == 2'd2) ? am1[159:0]   :
                 pack[640*emit_idx + 319 -: 160];
  assign lane2 = (am_phase == 2'd1) ? am2[319:160] :
                 (am_phase == 2'd2) ? am2[159:0]   :
                 pack[640*emit_idx + 479 -: 160];
  assign lane3 = (am_phase == 2'd1) ? am3[319:160] :
                 (am_phase == 2'd2) ? am3[159:0]   :
                 pack[640*emit_idx + 639 -: 160];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sym_cnt  <= 10'd0;
      am_phase <= 2'd0;
      acc      <= 640'd0;
      acc_n    <= 3'd0;
      pack     <= 2560'd0;
      pack_vld <= 1'b0;
      emit_idx <= 2'd0;
    end else begin
      // AMCTL on the 640 (SDF) / 512 (other) symbol timer even if beat_vld.
      // G1 idle-fills Null Blocks while link_up, so beat_vld stays 1; requiring
      // !beat_vld meant AMCTL never went on the wire and PMA held stale txdata.
      // am_phase!=0 already drops beat_ready: pause data, emit 2×160b/lane, resume.
      if (insert_am && am_phase == 2'd0 && !pack_vld && !completing) begin
        am_phase <= 2'd1;
      end else if (am_phase == 2'd1 && lane_ready && !afifo_afull) begin
        am_phase <= 2'd2;
      end else if (am_phase == 2'd2 && lane_ready && !afifo_afull) begin
        am_phase <= 2'd0;
        sym_cnt  <= 10'd0;
      end

      if (beat_vld && beat_ready) begin
        pack[512*acc_n +: 512] <= beat_data;
        if (acc_n == 3'd4) begin
          acc_n    <= 3'd0;
          pack_vld <= 1'b1;
          emit_idx <= 2'd0;
        end else begin
          acc_n <= acc_n + 3'd1;
        end
        if (!insert_am)
          sym_cnt <= sym_cnt + 10'd16; // 512b / 4 lanes / 8b = 16 symbols/lane
      end

      if (pack_vld && lane_ready && am_phase == 2'd0 && !afifo_afull) begin
        if (emit_idx == 2'd3) begin
          pack_vld <= 1'b0;
          emit_idx <= 2'd0;
        end else begin
          emit_idx <= emit_idx + 2'd1;
        end
      end
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY + FOOTER


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "pcs" / "vibe_pcs_tx_pack.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
