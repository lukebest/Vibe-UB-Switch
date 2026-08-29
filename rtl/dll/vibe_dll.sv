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
  input  logic [639:0] nw_tx_data,
  input  logic         nw_tx_vld,
  output logic         nw_tx_ready,
  output logic [639:0] nw_rx_data,
  output logic         nw_rx_vld,
  input  logic         nw_rx_ready,
  output logic [639:0] pcs_tx_data,
  output logic         pcs_tx_vld,
  input  logic         pcs_tx_ready,
  input  logic [639:0] pcs_rx_data,
  input  logic         pcs_rx_vld,
  output logic         pcs_rx_ready,
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
    .nw_data(nw_tx_data), .nw_vld(nw_tx_vld), .nw_ready(nw_tx_ready),
    .pcs_data(pcs_tx_data), .pcs_vld(pcs_tx_vld), .pcs_ready(pcs_tx_ready),
    .wr_en(wr_en), .wr_flit(wr_flit), .is_null(is_null), .is_retry(is_retry),
    .consume_flits(cons_flits), .consume_vld(cons_vld), .consume_cfg0(cons_cfg0)
  );

  vibe_dll_rx u_rx (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .fec_fail(fec_fail),
    .pcs_data(pcs_rx_data), .pcs_vld(pcs_rx_vld), .pcs_ready(pcs_rx_ready),
    .nw_data(nw_rx_data), .nw_vld(nw_rx_vld), .nw_ready(nw_rx_ready),
    .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data),
    .bcrc_fail(bcrc_fail), .start_retry(start_retry),
    .rx_ovf(rx_ovf), .start_ack(start_ack)
  );

  assign proto_err = crd_proto | buf_proto;
  assign fc_ovf    = crd_ovf;
endmodule
