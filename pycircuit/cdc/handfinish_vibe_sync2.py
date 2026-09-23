"""Emit the product SystemVerilog for vibe_sync2 (hand-finished).

Keeps tip ports/params, async-low ``rst_n``, and the 2-FF body
(``q1 <= d; q <= q1``). pycc netlists are a prototype only; this file
is what lands in ``rtl/cdc/vibe_sync2.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_sync2.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 7cf680f / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_sync2
//
"""

BODY = """\
// AS-0.1 §7: 2-FF synchronizer for gray pointers.
module vibe_sync2 #(
  parameter int W = 5
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [W-1:0] d,
  output logic [W-1:0] q
);
  logic [W-1:0] q1;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      q1 <= '0;
      q  <= '0;
    end else begin
      q1 <= d;
      q  <= q1;
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
    dest = repo / "rtl" / "cdc" / "vibe_sync2.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
