"""Emit the product SystemVerilog for vibe_dll_sm (hand-finished).

Keeps tip ports, async-low ``rst_n``, Disabled when
``LinkUp==0``, entity reset not a pin (must not force
Disabled via rst alone beyond async ``rst_n`` /
``port_rst``), states Disabled → Param → Credit → Normal,
``dll_error`` → Disabled, and ``status_up`` when Normal.
pycc netlists are a prototype only; this file is what
lands in ``rtl/dll/vibe_dll_sm.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_dll_sm.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 39d3aa1d / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_dll_sm
"""

BODY = """\
// AS-0.1 §12: DLL SM. Disabled when LinkUp==0. Entity reset must not force Disabled.
module vibe_dll_sm (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       link_up,
  input  logic       param_ok,
  input  logic       credit_ok,
  input  logic       dll_error,
  output logic [1:0] state,
  output logic       status_up,
  output logic       disabled
);
  localparam logic [1:0] ST_DIS  = 2'd0;
  localparam logic [1:0] ST_PARM = 2'd1;
  localparam logic [1:0] ST_CRD  = 2'd2;
  localparam logic [1:0] ST_NRM  = 2'd3;

  logic [1:0] st;

  assign state     = st;
  assign disabled  = (st == ST_DIS);
  assign status_up = (st == ST_NRM);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st <= ST_DIS;
    end else if (port_rst) begin
      st <= ST_DIS;
    end else if (!link_up) begin
      st <= ST_DIS;
    end else if (dll_error) begin
      st <= ST_DIS;
    end else begin
      case (st)
        ST_DIS:  st <= ST_PARM;
        ST_PARM: if (param_ok) st <= ST_CRD;
        ST_CRD:  if (credit_ok) st <= ST_NRM;
        default: st <= ST_NRM;
      endcase
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
    dest = repo / "rtl" / "dll" / "vibe_dll_sm.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
