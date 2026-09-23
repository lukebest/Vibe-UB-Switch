"""Emit the product SystemVerilog for vibe_pcs_tx_g1 (hand-finished).

Keeps tip ports, async-low ``rst_n``, combo ``in_ready`` /
``win_data`` / ``win_vld``, ``NULL_FLIT = 160'd0``, rem / rem_vld /
nflit / acc / have, and the collect / rem leftover / idle-Null
always-block (6 flits / 960b FEC window). pycc netlists are a
prototype only; this file is what lands in
``rtl/pcs/vibe_pcs_tx_g1.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_pcs_tx_g1.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 24f7239a / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_tx_g1
"""

BODY = """\
module vibe_pcs_tx_g1 (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic [639:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [959:0] win_data,
  output logic         win_vld,
  input  logic         win_ready
);
  logic [319:0] rem;
  logic         rem_vld;
  logic [2:0]   nflit; // 0,2,4,6 collected in current window (pairs of 2 from rem)
  logic [959:0] acc;
  logic         have;

  // Null Block flit: CFG=0, CLENGTH=0 (AS-0.1 §5 T2 / UB 2.0 Null Block)
  localparam logic [159:0] NULL_FLIT = 160'd0;

  assign in_ready = link_up && (!have || win_ready) && !((nflit >= 3'd4) && rem_vld);
  assign win_data = acc;
  assign win_vld  = have;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rem     <= 320'd0;
      rem_vld <= 1'b0;
      nflit   <= 3'd0;
      acc     <= 960'd0;
      have    <= 1'b0;
    end else begin
      if (have && win_ready)
        have <= 1'b0;

      if (have && win_ready) begin
        nflit <= 3'd0;
      end

      if (in_vld && in_ready) begin
        if (!rem_vld) begin
          // Take 4 flits; keep 2 if we already have 4, else store 4 and wait.
          // have&&win_ready is a fresh window (nflit cleared NBA this cycle).
          if (nflit == 3'd0 || (have && win_ready)) begin
            acc[959:320] <= in_data; // 4 flits, need 2 more
            rem          <= 320'd0;
            rem_vld      <= 1'b0;
            nflit        <= 3'd4;
          end else if (nflit == 3'd4) begin
            acc[319:0] <= in_data[639:320];
            rem        <= in_data[319:0];
            rem_vld    <= 1'b1;
            nflit      <= 3'd6;
            have       <= 1'b1;
          end
        end
      end else if (rem_vld && !have) begin
        acc[959:640] <= rem;
        acc[639:0]   <= {NULL_FLIT, NULL_FLIT, NULL_FLIT, NULL_FLIT};
        rem_vld      <= 1'b0;
        nflit        <= 3'd6;
        have         <= 1'b1;
      end else if (!have && !in_vld && link_up && win_ready && nflit == 3'd4) begin
        // Complete a 4-flit packet with 2 Nulls; do not overwrite it.
        acc[319:0] <= {NULL_FLIT, NULL_FLIT};
        nflit      <= 3'd6;
        have       <= 1'b1;
      end else if (!have && !in_vld && link_up && win_ready && nflit == 3'd0 && !rem_vld) begin
        // Idle fill: 6 Null Blocks
        acc   <= {NULL_FLIT, NULL_FLIT, NULL_FLIT, NULL_FLIT, NULL_FLIT, NULL_FLIT};
        nflit <= 3'd6;
        have  <= 1'b1;
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
    dest = repo / "rtl" / "pcs" / "vibe_pcs_tx_g1.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
