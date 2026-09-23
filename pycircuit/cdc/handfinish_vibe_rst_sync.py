"""Emit the product SystemVerilog for vibe_rst_sync (hand-finished).

Keeps tip ports, async-low ``rst_n_in``, and the 2-FF body
(``r1 <= 1'b1; rst_n_out <= r1``). pycc netlists are a prototype
only; this file is what lands in ``rtl/cdc/vibe_rst_sync.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_rst_sync.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 49421f9 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_rst_sync
//
"""

BODY = """\
// AS-0.1 §3: async assert, sync deassert into a destination clock.
module vibe_rst_sync (
  input  logic clk,
  input  logic rst_n_in,
  output logic rst_n_out
);
  logic r1;
  always @(posedge clk or negedge rst_n_in) begin
    if (!rst_n_in) begin
      r1        <= 1'b0;
      rst_n_out <= 1'b0;
    end else begin
      r1        <= 1'b1;
      rst_n_out <= r1;
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
    dest = repo / "rtl" / "cdc" / "vibe_rst_sync.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
