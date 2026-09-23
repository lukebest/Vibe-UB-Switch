"""Emit the product SystemVerilog for vibe_vl_rr (hand-finished).

Keeps tip ports, async-low ``rst_n``, and RR among non-empty
VOQs (AS-0.1 §8: first nonempty from ``rr``, wrap 16; on
``grant && valid`` advance ``rr`` to ``vl_sel+1``; no SL).
pycc netlists are a prototype only; this file is what lands in
``rtl/fabric/vibe_vl_rr.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/fabric/vibe_vl_rr.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 450ed1c2 / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_vl_rr
"""

BODY = """\
// AS-0.1 §8: VL scheduling RR among non-empty VOQs of an egress; FCFS within VL. No SL.
module vibe_vl_rr (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [15:0] nonempty,
  input  logic        grant,
  output logic [3:0]  vl_sel,
  output logic        valid
);
  logic [3:0] rr;
  logic [3:0] pick;
  integer     n;
  logic [3:0] p;

  always @* begin
    valid = |nonempty;
    pick  = rr;
    p     = rr;
    for (n = 0; n < 16; n = n + 1) begin
      if (nonempty[p]) begin
        pick = p;
        n = 16;
      end else
        p = p + 4'd1;
    end
    vl_sel = pick;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) rr <= 4'd0;
    else if (grant && valid) rr <= vl_sel + 4'd1;
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
    dest = repo / "rtl" / "fabric" / "vibe_vl_rr.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
