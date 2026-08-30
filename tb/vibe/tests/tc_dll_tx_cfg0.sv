// DLL TX + credit: CFG0 accept may pulse consume_vld, but is_cfg0 gates cells.
`timescale 1ns/1ps
module tc_dll_tx_cfg0;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, link_up, status_up, credit_low, bp_pending, drop_data, can_send;
  logic replay, send_idle, send_req, send_ack;
  logic [159:0] replay_flit;
  logic [639:0] nw_data, pcs_data;
  logic nw_vld, nw_ready, pcs_vld, pcs_ready;
  logic wr_en, is_null, is_retry, consume_vld, consume_cfg0;
  logic [159:0] wr_flit;
  logic [9:0] consume_flits;
  logic port_rst, credit_ret, proto_err, fc_ovf, bp_nw, force_crd_ack, credit_low_o;
  logic [15:0] credit_ret_n, pending;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .status_up(status_up),
    .credit_low(credit_low), .bp_pending(bp_pending), .drop_data(drop_data),
    .can_send(can_send), .replay(replay), .replay_flit(replay_flit),
    .send_idle(send_idle), .send_req(send_req), .send_ack(send_ack),
    .nw_data(nw_data), .nw_vld(nw_vld), .nw_ready(nw_ready),
    .pcs_data(pcs_data), .pcs_vld(pcs_vld), .pcs_ready(pcs_ready),
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
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; status_up = 1; credit_low = 0;
    bp_pending = 0; drop_data = 0; can_send = 1; replay = 0; replay_flit = 0;
    send_idle = 0; send_req = 0; send_ack = 0; pcs_ready = 1; nw_vld = 0;
    credit_ret = 0; credit_ret_n = 0;
    nw_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd0, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    nw_vld = 1;
    @(posedge clk);
    @(negedge clk);
    nw_vld = 0;
    repeat (8) @(posedge clk);
    if (u_crd.cells !== 16'd0) begin
      $display("FAIL tc_dll_tx_cfg0");
      $display("  stimulus : CFG0 on dll_tx.nw_* wired to credit is_cfg0=consume_cfg0");
      $display("  expected : cells=0 (CFG0 does not consume)");
      $display("  actual   : cells=%0d consume_cfg0=%0b", u_crd.cells, consume_cfg0);
      $display("  hier     : u_tx.consume_cfg0 / u_crd.cells");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    // send_idle / send_req / send_ack / replay / !link_up
    send_idle = 1;
    @(posedge clk);
    send_idle = 0;
    send_req = 1;
    @(posedge clk);
    send_req = 0;
    send_ack = 1;
    @(posedge clk);
    send_ack = 0;
    replay = 1; replay_flit = 160'hA5;
    @(posedge clk);
    replay = 0;
    // non-CFG0 consume
    nw_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    @(negedge clk);
    nw_vld = 1;
    @(posedge clk);
    @(negedge clk);
    nw_vld = 0;
    repeat (8) @(posedge clk);
    link_up = 0;
    @(posedge clk);
    link_up = 1;
    if (!fail) $display("PASS tc_dll_tx_cfg0");
    $finish;
  end
endmodule
