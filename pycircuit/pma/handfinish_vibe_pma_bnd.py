"""Emit the product SystemVerilog for vibe_pma_bnd (hand-finished).

Keeps tip ports, async-low ``txrst_n`` / ``rxrst_n``, ITU-T O.150
PRBS31 pin-idle (SPEC §4.4 / CR-PMA-IDLE-PRBS31), and rxclk-only idle
check (no txclk→rxclk sample). No ``PMA_IDLE_MARK``. pycc netlists are
a prototype only; this file is what lands in ``rtl/pma/vibe_pma_bnd.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pma/vibe_pma_bnd.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports match tip afcc2162. Decision I UNFROZEN. Path B hold.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Idle: ITU-T O.150 PRBS31 (SPEC §4.4 / CR-PMA-IDLE-PRBS31). No PMA_IDLE_MARK.
// Regenerate: make -C pycircuit vibe_pma_bnd
//
"""

BODY = """\
// AS-0.1 §3 / SPEC §4.4: product PMA boundary. No extra handshake. No PMA ready.
// Slice: [127:0]=lane0, [255:128]=lane1, [383:256]=lane2, [511:384]=lane3.
// No DLL/PCS beat: every txclk emits ITU-T O.150 PRBS31 so the pin changes
// every clock (SPEC §4.4 / CR-PMA-IDLE-PRBS31).
//   Poly: x^31 + x^28 + 1. LFSR step: {s[30:0], s[30] ^ s[27]} (31-bit state).
//   Per-lane seed: {27'd1, lid[1:0], 2'b01} for lid=0..3. Non-zero only.
//   Word: 128b, bit i = LFSR[0] after i steps (LSB first); advance 128/beat.
// No PMA_IDLE_MARK XOR — PRBS31 != PCS scramble(0) PRBS23. Historical #115
// PRBS23 + mark is no longer the SPEC idle rule.
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
  // 31-bit result of {s[30:0], s[30] ^ s[27]} is {s[29:0], s[30] ^ s[27]}.
  function automatic [30:0] prbs31_step;
    input [30:0] s;
    begin
      prbs31_step = {s[29:0], s[30] ^ s[27]};
    end
  endfunction

  function automatic [30:0] prbs31_seed;
    input [1:0] lid;
    begin
      prbs31_seed = {27'd1, lid, 2'b01};
    end
  endfunction

  function automatic [127:0] prbs31_word;
    input [30:0] s;
    logic [30:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1) begin
        prbs31_word[i] = t[0];
        t = prbs31_step(t);
      end
    end
  endfunction

  function automatic [30:0] prbs31_adv128;
    input [30:0] s;
    logic [30:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1)
        t = prbs31_step(t);
      prbs31_adv128 = t;
    end
  endfunction

  // Pin-idle is raw PRBS31. Fan-in stays pma_pcs_rxdata / rxclk —
  // do not sample txclk tx_pcs_d or compare pcs_pma_txdata
  // (was unsanctioned txclk→rxclk).
  logic [30:0] lfsr0 = {27'd1, 2'd0, 2'b01};
  logic [30:0] lfsr1 = {27'd1, 2'd1, 2'b01};
  logic [30:0] lfsr2 = {27'd1, 2'd2, 2'b01};
  logic [30:0] lfsr3 = {27'd1, 2'd3, 2'b01};
  wire  [127:0] idle0 = prbs31_word(lfsr0);
  wire  [127:0] idle1 = prbs31_word(lfsr1);
  wire  [127:0] idle2 = prbs31_word(lfsr2);
  wire  [127:0] idle3 = prbs31_word(lfsr3);

  always @(posedge txclk or negedge txrst_n) begin
    if (!txrst_n) begin
      lfsr0 <= prbs31_seed(2'd0);
      lfsr1 <= prbs31_seed(2'd1);
      lfsr2 <= prbs31_seed(2'd2);
      lfsr3 <= prbs31_seed(2'd3);
      pcs_pma_txdata <= {prbs31_word(prbs31_seed(2'd3)),
                         prbs31_word(prbs31_seed(2'd2)),
                         prbs31_word(prbs31_seed(2'd1)),
                         prbs31_word(prbs31_seed(2'd0))};
    end else if (afifo_pma_lane_vld) begin
      pcs_pma_txdata <= {afifo_pma_lane3, afifo_pma_lane2,
                         afifo_pma_lane1, afifo_pma_lane0};
    end else begin
      pcs_pma_txdata <= {idle3, idle2, idle1, idle0};
      lfsr0 <= prbs31_adv128(lfsr0);
      lfsr1 <= prbs31_adv128(lfsr1);
      lfsr2 <= prbs31_adv128(lfsr2);
      lfsr3 <= prbs31_adv128(lfsr3);
    end
  end

  function automatic prbs31_word_ok;
    input [127:0] w;
    integer       i;
    begin
      prbs31_word_ok = 1'b1;
      for (i = 31; i < 128; i = i + 1)
        if (w[i] != (w[i-31] ^ w[i-28]))
          prbs31_word_ok = 1'b0;
    end
  endfunction

  // Drop PRBS31 pin-idle only. Non-PRBS31 128b (incl. scramble(0)) keeps vld.
  wire idle_prbs = prbs31_word_ok(pma_pcs_rxdata[127:0]) &&
                   prbs31_word_ok(pma_pcs_rxdata[255:128]) &&
                   prbs31_word_ok(pma_pcs_rxdata[383:256]) &&
                   prbs31_word_ok(pma_pcs_rxdata[511:384]);

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
