"""Emit the product SystemVerilog for vibe_pma_bnd (hand-finished).

Keeps tip ports, async-low ``txrst_n`` / ``rxrst_n``, PRBS23 pin-idle,
``PMA_IDLE_MARK`` decorate/undecorate (issue #115), and rxclk-only idle
check (no txclk→rxclk sample). pycc netlists are a prototype only; this
file is what lands in ``rtl/pma/vibe_pma_bnd.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pma/vibe_pma_bnd.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip ef3f121 / freeze 302ac943 (PR116 idle-mark).
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pma_bnd
//
"""

BODY = """\
// AS-0.1 §3: product PMA boundary. No extra handshake. No PMA ready.
// Slice: [127:0]=lane0, [255:128]=lane1, [383:256]=lane2, [511:384]=lane3.
// No DLL/PCS beat: every txclk emits PRBS23 XOR PMA_IDLE_MARK so the
// SerDes pin is never held at 0 (UB 3.2.6) and pin-idle is not the same
// stream as PCS scramble(0) (same poly+seed; issue #115).
module vibe_pma_bnd (
  input  logic         txclk,
  input  logic         rxclk,
  input  logic         txrst_n,
  input  logic         rxrst_n,
  input  logic [127:0] afifo_pma_lane0,
  input  logic [127:0] afifo_pma_lane1,
  input  logic [127:0] afifo_pma_lane2,
  input  logic [127:0] afifo_pma_lane3,
  input  logic         afifo_pma_lane_vld,
  output logic [511:0] pcs_pma_txdata,
  input  logic [511:0] pma_pcs_rxdata,
  output logic [127:0] pma_afifo_lane0,
  output logic [127:0] pma_afifo_lane1,
  output logic [127:0] pma_afifo_lane2,
  output logic [127:0] pma_afifo_lane3,
  output logic         pma_afifo_lane_vld
);
  function automatic [22:0] prbs23_step;
    input [22:0] s;
    begin
      prbs23_step = {s[21:0], s[22] ^ s[17]};
    end
  endfunction

  function automatic [22:0] prbs23_seed;
    input [1:0] lid;
    begin
      prbs23_seed = {19'd1, lid, 2'b01};
    end
  endfunction

  function automatic [127:0] prbs23_word;
    input [22:0] s;
    logic [22:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1) begin
        prbs23_word[i] = t[0];
        t = prbs23_step(t);
      end
    end
  endfunction

  function automatic [22:0] prbs23_adv128;
    input [22:0] s;
    logic [22:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1)
        t = prbs23_step(t);
      prbs23_adv128 = t;
    end
  endfunction

  // Pin-idle must not be raw PRBS23. vibe_pcs_scramble uses the same
  // poly and seed {19'd1, lid, 2'b01}. G1 Null Blocks scramble to that
  // stream; after 160→128 those 128b windows satisfy the undecorated
  // recurrence, so a658d141's idle_prbs drop ate packed beats (issue
  // #115). XOR a mark that is not itself a PRBS word. RX undoes the
  // mark before the recurrence test. Fan-in stays pma_pcs_rxdata /
  // rxclk — do not sample txclk tx_pcs_d or compare pcs_pma_txdata
  // (was unsanctioned txclk→rxclk).
  localparam [127:0] PMA_IDLE_MARK = 128'h8000_0000_0000_0000_0000_0000_0000_0000;

  logic [22:0] lfsr0 = {19'd1, 2'd0, 2'b01};
  logic [22:0] lfsr1 = {19'd1, 2'd1, 2'b01};
  logic [22:0] lfsr2 = {19'd1, 2'd2, 2'b01};
  logic [22:0] lfsr3 = {19'd1, 2'd3, 2'b01};
  wire  [127:0] prbs0 = prbs23_word(lfsr0);
  wire  [127:0] prbs1 = prbs23_word(lfsr1);
  wire  [127:0] prbs2 = prbs23_word(lfsr2);
  wire  [127:0] prbs3 = prbs23_word(lfsr3);
  wire  [127:0] idle0 = prbs0 ^ PMA_IDLE_MARK;
  wire  [127:0] idle1 = prbs1 ^ PMA_IDLE_MARK;
  wire  [127:0] idle2 = prbs2 ^ PMA_IDLE_MARK;
  wire  [127:0] idle3 = prbs3 ^ PMA_IDLE_MARK;

  always @(posedge txclk or negedge txrst_n) begin
    if (!txrst_n) begin
      lfsr0 <= prbs23_seed(2'd0);
      lfsr1 <= prbs23_seed(2'd1);
      lfsr2 <= prbs23_seed(2'd2);
      lfsr3 <= prbs23_seed(2'd3);
      pcs_pma_txdata <= {prbs23_word(prbs23_seed(2'd3)) ^ PMA_IDLE_MARK,
                         prbs23_word(prbs23_seed(2'd2)) ^ PMA_IDLE_MARK,
                         prbs23_word(prbs23_seed(2'd1)) ^ PMA_IDLE_MARK,
                         prbs23_word(prbs23_seed(2'd0)) ^ PMA_IDLE_MARK};
    end else if (afifo_pma_lane_vld) begin
      pcs_pma_txdata <= {afifo_pma_lane3, afifo_pma_lane2,
                         afifo_pma_lane1, afifo_pma_lane0};
    end else begin
      pcs_pma_txdata <= {idle3, idle2, idle1, idle0};
      lfsr0 <= prbs23_adv128(lfsr0);
      lfsr1 <= prbs23_adv128(lfsr1);
      lfsr2 <= prbs23_adv128(lfsr2);
      lfsr3 <= prbs23_adv128(lfsr3);
    end
  end

  function automatic prbs23_word_ok;
    input [127:0] w;
    integer       i;
    begin
      prbs23_word_ok = 1'b1;
      for (i = 23; i < 128; i = i + 1)
        if (w[i] != (w[i-23] ^ w[i-18]))
          prbs23_word_ok = 1'b0;
    end
  endfunction

  // Drop decorated pin-idle only. Raw PRBS / scramble(0) 128b keeps vld.
  wire idle_prbs = prbs23_word_ok(pma_pcs_rxdata[127:0]    ^ PMA_IDLE_MARK) &&
                   prbs23_word_ok(pma_pcs_rxdata[255:128]  ^ PMA_IDLE_MARK) &&
                   prbs23_word_ok(pma_pcs_rxdata[383:256]  ^ PMA_IDLE_MARK) &&
                   prbs23_word_ok(pma_pcs_rxdata[511:384]  ^ PMA_IDLE_MARK);

  always @(posedge rxclk or negedge rxrst_n) begin
    if (!rxrst_n) begin
      pma_afifo_lane0    <= 128'd0;
      pma_afifo_lane1    <= 128'd0;
      pma_afifo_lane2    <= 128'd0;
      pma_afifo_lane3    <= 128'd0;
      pma_afifo_lane_vld <= 1'b0;
    end else begin
      pma_afifo_lane0    <= pma_pcs_rxdata[127:0];
      pma_afifo_lane1    <= pma_pcs_rxdata[255:128];
      pma_afifo_lane2    <= pma_pcs_rxdata[383:256];
      pma_afifo_lane3    <= pma_pcs_rxdata[511:384];
      pma_afifo_lane_vld <= !idle_prbs;
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "pma" / "vibe_pma_bnd.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
