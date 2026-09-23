"""Emit the product SystemVerilog for vibe_icrc (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_params.vh"``
for ``VIBE_ICRC_POLY``, ``include "vibe_ub_fn.vh"`` for ``vibe_rev8``
/ ``vibe_rev32``, ``step8``, CRC32 init all-1s, per-byte bit reverse
then reverse+invert, and ``~vibe_rev32(step8(crc, in_byte))`` on
``last``. pycc netlists are a prototype only; this file is what
lands in ``rtl/nw/vibe_icrc.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/nw/vibe_icrc.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 186dde4e / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_icrc
"""

BODY = """\
// AS-0.1 §13: CRC32 0x04C11DB7 init 0xFFFFFFFF, per-byte bit reverse then reverse+invert.
// Used only by cna_ep (sender/receiver). Transit has NO ICRC unit.
module vibe_icrc (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_byte,
  input  logic         last,
  output logic [31:0]  crc_out,
  output logic         done
);
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  logic [31:0] crc;
  integer i;

  function automatic [31:0] step8;
    input [31:0] c;
    input [7:0]  b;
    logic [31:0] t;
    logic [7:0]  br;
    integer k;
    begin
      br = vibe_rev8(b);
      t = c;
      for (k = 0; k < 8; k = k + 1) begin
        if (t[31] ^ br[7-k])
          t = {t[30:0], 1'b0} ^ VIBE_ICRC_POLY;
        else
          t = {t[30:0], 1'b0};
      end
      step8 = t;
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      crc     <= 32'hFFFF_FFFF;
      crc_out <= 32'd0;
      done    <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start)
        crc <= 32'hFFFF_FFFF;
      else if (in_vld) begin
        crc <= step8(crc, in_byte);
        if (last) begin
          crc_out <= ~vibe_rev32(step8(crc, in_byte));
          done    <= 1'b1;
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
    dest = repo / "rtl" / "nw" / "vibe_icrc.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
