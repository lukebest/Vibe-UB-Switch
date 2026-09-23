"""Emit the product SystemVerilog for vibe_bcrc (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_params.vh"``
for ``VIBE_BCRC_POLY``, ``crc30_step``, the 160-bit eat loop, CRC30
init all-1s / no invert, and ``{1'b0, error_flag, crc[29:0]}`` on
``last`` (bit31 reserved, bit30 ERROR_FLAG). pycc netlists are a
prototype only; this file is what lands in ``rtl/dll/vibe_bcrc.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_bcrc.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 1e57f2a5 / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_bcrc
"""

BODY = """\
// AS-0.1 §12: BCRC CRC30, init all-1, no invert. bit31 reserved, bit30 ERROR_FLAG.
module vibe_bcrc (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [159:0] in_flit,
  input  logic         last,
  input  logic         error_flag,
  output logic [31:0]  crc_word,
  output logic         done
);
  `include "vibe_ub_params.vh"

  logic [29:0] crc;
  integer i;

  function automatic [29:0] crc30_step;
    input [29:0] c;
    input        b;
    logic        fb;
    begin
      fb = c[29] ^ b;
      crc30_step = {c[28:0], 1'b0} ^ ({30{fb}} & VIBE_BCRC_POLY);
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      crc      <= {30{1'b1}};
      crc_word <= 32'd0;
      done     <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start)
        crc <= {30{1'b1}};
      else if (in_vld) begin
        begin : eat
          logic [29:0] t;
          t = crc;
          for (i = 0; i < 160; i = i + 1)
            t = crc30_step(t, in_flit[i]);
          crc <= t;
          if (last) begin
            crc_word <= {1'b0, error_flag, t};
            done     <= 1'b1;
          end
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
    dest = repo / "rtl" / "dll" / "vibe_bcrc.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
