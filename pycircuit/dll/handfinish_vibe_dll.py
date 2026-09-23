"""Emit the product SystemVerilog for vibe_dll (hand-finished).

Keeps tip ports, ``RETRY_WAIT_CYC`` default 12500, the seven
already-migrated children (``u_sm`` / ``u_crd`` / ``u_rbuf`` /
``u_req`` / ``u_ack`` / ``u_tx`` / ``u_rx``), interconnect
nets, and wrap-local ``proto_err`` / ``fc_ovf`` assigns
(AS-0.1 §12). pycc netlists are a prototype only; this file
is what lands in ``rtl/dll/vibe_dll.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_dll.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 5b071097 / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_dll
"""

BODY = """\
// AS-0.1 §12: DLL wrapper — sm, tx, rx, credit, retry_buf, retry_req_sm, retry_ack_sm.
module vibe_dll #(
  parameter int RETRY_WAIT_CYC = 12500
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         device_rst,
  input  logic         link_up,
  input  logic         fec_fail,
  input  logic [511:0] nw_dll_data,
  input  logic         nw_dll_vld,
  output logic         nw_dll_ready,
  output logic [511:0] dll_nw_data,
  output logic         dll_nw_vld,
  input  logic         dll_nw_ready,
  output logic [639:0] dll_pcs_data,
  output logic         dll_pcs_vld,
  input  logic         dll_pcs_ready,
  input  logic [639:0] pcs_dll_data,
  input  logic         pcs_dll_vld,
  output logic         pcs_dll_ready,
  output logic         status_up,
  output logic         disabled,
  output logic         retrain_req,
  output logic         retry_error,
  output logic         proto_err,
  output logic         fc_ovf,
  output logic         rx_ovf,
  output logic         cfg0_hit,
  output logic [639:0] cfg0_data
);
  logic [1:0]  sm_st;
  logic        credit_low, force_ack, bp_nw, crd_proto, crd_ovf;
  logic [15:0] pending;
  logic        drop_data, send_idle, send_req, send_ack, replay;
  logic [7:0]  rd_ptr, wr_ptr, tail_ptr, rcv_ptr;
  logic [8:0]  nfree;
  logic        can_send, buf_proto;
  logic [159:0] wr_flit, rd_flit;
  logic        wr_en, is_null, is_retry;
  logic [9:0]  cons_flits;
  logic        cons_vld, cons_cfg0;
  logic        bcrc_fail, start_retry, start_ack;
  logic [2:0]  req_st, ack_st;

  vibe_dll_sm u_sm (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst),
    .link_up(link_up), .param_ok(1'b1), .credit_ok(1'b1),
    .dll_error(retry_error || proto_err),
    .state(sm_st), .status_up(status_up), .disabled(disabled)
  );

  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(8'd8),
    .consume_vld(cons_vld), .consume_flits(cons_flits), .is_cfg0(cons_cfg0),
    .credit_ret(force_ack), .credit_ret_n(16'd1),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_ack),
    .bp_nw(bp_nw), .proto_err(crd_proto), .fc_ovf(crd_ovf)
  );

  vibe_dll_retry_buf u_rbuf (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .wr_en(wr_en), .is_null(is_null), .is_retry(is_retry), .wr_flit(wr_flit),
    .send_size(8'd4), .ack_rel(1'b0), .rel_size(8'd0), .rd_ptr_i(rd_ptr),
    .rd_flit(rd_flit), .wr_ptr(wr_ptr), .tail_ptr(tail_ptr), .rcv_ptr(rcv_ptr),
    .num_free(nfree), .proto_err(buf_proto), .can_send(can_send)
  );

  vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(RETRY_WAIT_CYC)) u_req (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .start_retry(start_retry), .phy_retrain(1'b0), .wait_done_ack(1'b0),
    .state(req_st), .drop_data(drop_data), .retrain_req(retrain_req),
    .retry_error(retry_error), .send_idle(send_idle), .send_req(send_req),
    .send_cnt()
  );

  vibe_dll_retry_ack_sm u_ack (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst),
    .start_ack(start_ack), .wr_ptr(wr_ptr), .rcv_ptr(rcv_ptr),
    .state(ack_st), .send_idle(), .send_ack(send_ack),
    .replay(replay), .rd_ptr(rd_ptr)
  );

  vibe_dll_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .status_up(status_up),
    .credit_low(credit_low), .bp_pending(bp_nw), .drop_data(drop_data),
    .can_send(can_send), .replay(replay), .replay_flit(rd_flit),
    .send_idle(send_idle), .send_req(send_req), .send_ack(send_ack),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .wr_en(wr_en), .wr_flit(wr_flit), .is_null(is_null), .is_retry(is_retry),
    .consume_flits(cons_flits), .consume_vld(cons_vld), .consume_cfg0(cons_cfg0)
  );

  vibe_dll_rx u_rx (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .fec_fail(fec_fail),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data),
    .bcrc_fail(bcrc_fail), .start_retry(start_retry),
    .rx_ovf(rx_ovf), .start_ack(start_ack)
  );

  assign proto_err = crd_proto | buf_proto;
  assign fc_ovf    = crd_ovf;
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
    dest = repo / "rtl" / "dll" / "vibe_dll.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
