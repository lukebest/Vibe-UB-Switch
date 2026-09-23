"""Emit the product SystemVerilog for vibe_dll_credit (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_params.vh"``
for ``VIBE_CREDIT_THRESH`` / ``VIBE_US_CYC``, ``ceil_div``, consume
CFG0 skip, credit return in cells, thresh 1024 → ``bp_nw`` + force
Crd_Ack, 1µs timeout → ``proto_err``, and 17-bit cells-sum
``fc_ovf``. No credit underflow code. pycc netlists are a prototype
only; this file is what lands in ``rtl/dll/vibe_dll_credit.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_dll_credit.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip ad36bf66 / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_dll_credit
"""

BODY = """\
// AS-0.1 §12 / FS-0.2.6: credit consume ceil(DLLDP_flits/n), n default 8.
// Pending-to-return is a cell count. Pending >= 1024 cell → backpressure NW
// and force Crd_Ack (VIBE_CREDIT_THRESH stays 1024; not 1024×n flits).
// Timeout 1us → DL Protocol Error. CFG0 DLLCB does not consume credit.
// No credit underflow code.
module vibe_dll_credit (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        port_rst,
  input  logic        link_up,
  input  logic [7:0]  grain_n,     // 1,2,4,...,128 default 8
  input  logic        consume_vld,
  input  logic [9:0]  consume_flits,
  input  logic        is_cfg0,
  input  logic        credit_ret,
  input  logic [15:0] credit_ret_n,
  output logic [15:0] pending,
  output logic        credit_low,
  output logic        force_crd_ack,
  output logic        bp_nw,
  output logic        proto_err,
  output logic        fc_ovf
);
  `include "vibe_ub_params.vh"

  logic [15:0] cells;
  logic [15:0] pend;
  logic [10:0] to;

  // flits → cells. n=0 → 0. Same grain for consume and pending-to-return.
  function automatic [15:0] ceil_div;
    input [15:0] flits;
    input [7:0]  n;
    begin
      if (n == 8'd0) ceil_div = 16'd0;
      else ceil_div = ({1'b0, flits} + {9'd0, n} - 17'd1) / {9'd0, n};
    end
  endfunction

  assign pending       = pend;
  assign force_crd_ack = (pend >= VIBE_CREDIT_THRESH[15:0]) || (!consume_vld && pend != 0);
  assign bp_nw         = (pend >= VIBE_CREDIT_THRESH[15:0]);
  assign credit_low    = (cells == 16'd0);

  // 17-bit sum so Flow Control Overflow is reachable (16-bit CMPCONST never fired).
  wire [15:0] consume_cells = ceil_div({6'd0, consume_flits}, grain_n);
  wire [16:0] cells_sum     = {1'b0, cells} + {1'b0, consume_cells};
  // pend is cells. Sent/received flits use the same ceil(flits/n) as consume.
  // Crd_Ack grain (credit_ret_n) is already cells — do not treat it as raw flits.
  wire [16:0] pend_sum = {1'b0, pend}
                       + (credit_ret ? {1'b0, credit_ret_n} : 17'd0)
                       + ((consume_vld && !is_cfg0) ? {1'b0, consume_cells} : 17'd0);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cells     <= 16'd0;
      pend      <= 16'd0;
      to        <= 11'd0;
      proto_err <= 1'b0;
      fc_ovf    <= 1'b0;
    end else if (port_rst || !link_up) begin
      cells     <= 16'd0;
      pend      <= 16'd0;
      to        <= 11'd0;
    end else begin
      if (consume_vld && !is_cfg0) begin
        if (cells_sum > 17'd65535) begin
          fc_ovf <= 1'b1;
          cells  <= 16'd65535;
        end else
          cells  <= cells_sum[15:0];
      end
      pend <= pend_sum[15:0];
      if (credit_ret || (consume_vld && !is_cfg0 && consume_cells != 16'd0))
        to <= VIBE_US_CYC[10:0];
      else if (pend != 0) begin
        if (to == 0) proto_err <= 1'b1;
        else         to <= to - 11'd1;
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
    dest = repo / "rtl" / "dll" / "vibe_dll_credit.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
