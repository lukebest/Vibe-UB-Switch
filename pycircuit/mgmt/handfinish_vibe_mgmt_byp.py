"""Emit the product SystemVerilog for vibe_mgmt_byp (hand-finished).

Keeps tip ports, async-low ``rst_n``, DEPTH=16, and the
5-bit pointer FIFO body (AS-0.1 §14: mgmt bypass 16×512b;
does not enter xbar). pycc netlists are a prototype only;
this file is what lands in ``rtl/mgmt/vibe_mgmt_byp.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/mgmt/vibe_mgmt_byp.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 23718d19. Decision I UNFROZEN. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_mgmt_byp
"""

BODY = """\
// AS-0.1 §14: mgmt bypass FIFO 16×512b. Does not enter xbar.
module vibe_mgmt_byp #(
  parameter int DEPTH = 16
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [511:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [511:0] out_data,
  output logic         out_vld,
  input  logic         out_ready
);
  logic [511:0] mem [0:DEPTH-1];
  logic [4:0]   wptr, rptr;
  assign in_ready = ((wptr + 5'd1) != rptr);
  assign out_vld  = (wptr != rptr);
  assign out_data = mem[rptr[3:0]];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 5'd0;
      rptr <= 5'd0;
    end else begin
      if (in_vld && in_ready) begin
        mem[wptr[3:0]] <= in_data;
        wptr <= wptr + 5'd1;
      end
      if (out_vld && out_ready)
        rptr <= rptr + 5'd1;
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
    dest = repo / "rtl" / "mgmt" / "vibe_mgmt_byp.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
