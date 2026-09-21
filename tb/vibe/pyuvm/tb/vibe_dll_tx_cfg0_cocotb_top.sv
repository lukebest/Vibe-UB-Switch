// Thin parameter / array wrapper. DUT RTL never edited.
`timescale 1ns/1ps

module vibe_dll_tx_cfg0_cocotb_top (
  input  logic         clk, rst_n, link_up, status_up, credit_low, bp_pending,
  input  logic         drop_data, can_send, replay, send_idle, send_req, send_ack,
  input  logic [159:0] replay_flit,
  input  logic [511:0] nw_dll_data,
  input  logic         nw_dll_vld, dll_pcs_ready, port_rst, credit_ret,
  input  logic [15:0]  credit_ret_n,
  output logic         nw_dll_ready, dll_pcs_vld, wr_en, is_null, is_retry,
  output logic         consume_vld, consume_cfg0, proto_err, fc_ovf, bp_nw,
  output logic [639:0] dll_pcs_data,
  output logic [159:0] wr_flit,
  output logic [9:0]   consume_flits,
  output logic [15:0]  pending, cells
);
  logic credit_low_o, force_crd_ack;
  vibe_dll_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .status_up(status_up),
    .credit_low(credit_low), .bp_pending(bp_pending), .drop_data(drop_data),
    .can_send(can_send), .replay(replay), .replay_flit(replay_flit),
    .send_idle(send_idle), .send_req(send_req), .send_ack(send_ack),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .wr_en(wr_en), .wr_flit(wr_flit), .is_null(is_null), .is_retry(is_retry),
    .consume_flits(consume_flits), .consume_vld(consume_vld), .consume_cfg0(consume_cfg0)
  );
  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(8'd8), .consume_vld(consume_vld), .consume_flits(consume_flits),
    .is_cfg0(consume_cfg0), .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low_o), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );
  assign cells = u_crd.cells;
endmodule
