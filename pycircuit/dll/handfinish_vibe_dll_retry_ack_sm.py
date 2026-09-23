"""Emit the product SystemVerilog for vibe_dll_retry_ack_sm (hand-finished).

Keeps tip ports, async-low ``rst_n``, NORMAL / ACK (1 Idle + 32
Ack then replay ``RdPtr=RcvPtr`` until ``WrPtr``). pycc netlists
are a prototype only; this file is what lands in
``rtl/dll/vibe_dll_retry_ack_sm.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_dll_retry_ack_sm.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 0b0a82db / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_dll_retry_ack_sm
"""

BODY = """\
// AS-0.1 §12 RETRY_ACK_SM: NORMAL, ACK (1 Idle + 32 Ack then replay RdPtr=RcvPtr until WrPtr).
module vibe_dll_retry_ack_sm (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       start_ack,
  input  logic [7:0] wr_ptr,
  input  logic [7:0] rcv_ptr,
  output logic [2:0] state,
  output logic       send_idle,
  output logic       send_ack,
  output logic       replay,
  output logic [7:0] rd_ptr
);
  localparam logic [2:0] ST_N = 3'd0;
  localparam logic [2:0] ST_A = 3'd1;
  localparam logic [2:0] ST_P = 3'd2;

  logic [2:0] st;
  logic [5:0] burst;
  logic [7:0] rp;

  assign state     = st;
  assign send_idle = (st == ST_A) && (burst == 6'd0);
  assign send_ack  = (st == ST_A) && (burst != 6'd0);
  assign replay    = (st == ST_P);
  assign rd_ptr    = rp;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st    <= ST_N;
      burst <= 6'd0;
      rp    <= 8'd0;
    end else if (port_rst) begin
      st    <= ST_N;
      burst <= 6'd0;
      rp    <= 8'd0;
    end else begin
      case (st)
        ST_N: if (start_ack) begin
          st    <= ST_A;
          burst <= 6'd0;
        end
        ST_A: begin
          if (burst == 6'd32) begin
            st <= ST_P;
            rp <= rcv_ptr;
          end else
            burst <= burst + 6'd1;
        end
        ST_P: begin
          if (rp == wr_ptr)
            st <= ST_N;
          else
            rp <= rp + 8'd1;
        end
        default: st <= ST_N;
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
    dest = repo / "rtl" / "dll" / "vibe_dll_retry_ack_sm.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
