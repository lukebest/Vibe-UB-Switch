"""Emit the product SystemVerilog for vibe_pcs_tx_cw2beat (hand-finished).

Keeps tip ports, async-low ``rst_n``, combo ``cw_ready`` /
``beat_vld`` / ``beat_data``, and the ready/valid 1024b→two-512b
split. pycc netlists are a prototype only; this file is what lands
in ``rtl/pcs/vibe_pcs_tx_cw2beat.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_pcs_tx_cw2beat.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip c8804c0 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_tx_cw2beat
//
"""

BODY = """\
// AS-0.1 §5 T4: 1024b codeword as two 512b beats.
module vibe_pcs_tx_cw2beat (
  input  logic          clk,
  input  logic          rst_n,
  input  logic [1023:0] cw_data,
  input  logic          cw_vld,
  output logic          cw_ready,
  output logic [511:0]  beat_data,
  output logic          beat_vld,
  input  logic          beat_ready
);
  logic [511:0] hi, lo;
  logic         have_hi, have_lo;

  assign cw_ready  = !have_hi && !have_lo;
  assign beat_vld  = have_hi || have_lo;
  assign beat_data = have_hi ? hi : lo;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hi      <= 512'd0;
      lo      <= 512'd0;
      have_hi <= 1'b0;
      have_lo <= 1'b0;
    end else begin
      if (cw_vld && cw_ready) begin
        hi      <= cw_data[1023:512];
        lo      <= cw_data[511:0];
        have_hi <= 1'b1;
        have_lo <= 1'b1;
      end
      if (beat_vld && beat_ready) begin
        if (have_hi) have_hi <= 1'b0;
        else         have_lo <= 1'b0;
      end
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
    dest = repo / "rtl" / "pcs" / "vibe_pcs_tx_cw2beat.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
