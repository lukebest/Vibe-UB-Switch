// Credit return timeout 1 us = 1250 clk_fab → DL Protocol Error. Separate from deadlock.
`timescale 1ns/1ps
module tc_credit_timeout_1us;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, port_rst, link_up, consume_vld, is_cfg0, credit_ret;
  logic [7:0] grain_n;
  logic [9:0] consume_flits;
  logic [15:0] credit_ret_n, pending;
  logic credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf;
  integer fail, i;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(grain_n), .consume_vld(consume_vld), .consume_flits(consume_flits),
    .is_cfg0(is_cfg0), .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; grain_n = 8'd8;
    consume_vld = 0; consume_flits = 0; is_cfg0 = 0; credit_ret = 0; credit_ret_n = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd1;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    // wait just under 1us
    for (i = 0; i < (VIBE_US_CYC - 2); i = i + 1) @(posedge clk);
    if (proto_err) begin
      $display("FAIL tc_credit_timeout_1us");
      $display("  stimulus : pending=1, wait <1250 cycles");
      $display("  expected : proto_err still 0");
      $display("  actual   : 1");
      fail = 1;
    end
    for (i = 0; i < 8; i = i + 1) @(posedge clk);
    if (!proto_err) begin
      $display("FAIL tc_credit_timeout_1us");
      $display("  stimulus : pending held without return for >=1us");
      $display("  expected : proto_err=1 (credit timeout, not deadlock)");
      $display("  actual   : 0 pending=%0d", pending);
      $display("  hier     : u_crd.to / proto_err");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_credit_timeout_1us");
    $finish;
  end
endmodule
