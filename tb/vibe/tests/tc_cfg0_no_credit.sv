// TP-CFG-001 / TP-CRD-007 — CFG0 does not consume data credit (is_cfg0).
`timescale 1ns/1ps
module tc_cfg0_no_credit;
  `include "vibe_ub_params.vh"
  logic        clk, rst_n, port_rst, link_up;
  logic        consume_vld, is_cfg0, credit_ret;
  logic [7:0]  grain_n;
  logic [9:0]  consume_flits;
  logic [15:0] credit_ret_n, pending;
  logic        credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf;
  integer      fail;
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
    consume_vld = 0; consume_flits = 10'd32; is_cfg0 = 0;
    credit_ret = 0; credit_ret_n = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // CFG0 consume pulse must not add cells / raise fc_ovf
    @(negedge clk);
    is_cfg0 = 1; consume_vld = 1; consume_flits = 10'd32;
    @(posedge clk);
    @(negedge clk);
    consume_vld = 0; is_cfg0 = 0;
    @(posedge clk);
    if (fc_ovf || u_crd.cells !== 16'd0) begin
      $display("FAIL tc_cfg0_no_credit");
      $display("  stimulus : consume_vld=1 is_cfg0=1 consume_flits=32");
      $display("  expected : cells stay 0 (CFG0 does not consume)");
      $display("  actual   : cells=%0d fc_ovf=%0b", u_crd.cells, fc_ovf);
      $display("  hier     : u_crd.cells / is_cfg0");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    // control: data consume does increment cells
    @(negedge clk);
    is_cfg0 = 0; consume_vld = 1; consume_flits = 10'd8;
    @(posedge clk);
    @(negedge clk);
    consume_vld = 0;
    @(posedge clk);
    if (u_crd.cells === 16'd0) begin
      $display("FAIL tc_cfg0_no_credit");
      $display("  stimulus : consume_vld=1 is_cfg0=0 flits=8 grain=8");
      $display("  expected : cells += ceil(8/8)=1");
      $display("  actual   : cells=%0d", u_crd.cells);
      fail = 1;
    end
    if (!fail) $display("PASS tc_cfg0_no_credit");
    $finish;
  end
endmodule
