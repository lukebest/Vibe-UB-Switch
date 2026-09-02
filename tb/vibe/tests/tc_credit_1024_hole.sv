// G7 closed: 1024 is cell. Same 1023→1024 cell bp_nw score as tc_credit_1024_flit_bp.
`timescale 1ns/1ps
module tc_credit_1024_hole;
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
    .grain_n(grain_n),
    .consume_vld(consume_vld), .consume_flits(consume_flits), .is_cfg0(is_cfg0),
    .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1;
    grain_n = 8'd8; consume_vld = 0; consume_flits = 10'd0; is_cfg0 = 0;
    credit_ret = 0; credit_ret_n = 16'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd1023;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    @(posedge clk);
    if (pending !== 16'd1023 || bp_nw) begin
      $display("FAIL tc_credit_1024_hole");
      $display("  stimulus : credit_ret_n=1023 cell (no ×n / no /n)");
      $display("  expected : pending=1023 cell bp_nw=0");
      $display("  actual   : pending=%0d bp_nw=%0b", pending, bp_nw);
      $display("  hier     : u_crd.pend / bp_nw");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd1;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    @(posedge clk);
    if (pending !== 16'd1024 || !bp_nw || !force_crd_ack) begin
      $display("FAIL tc_credit_1024_hole");
      $display("  stimulus : pending reaches 1024 cell via credit_ret_n");
      $display("  expected : pending=1024 cell bp_nw=1 force_crd_ack=1");
      $display("  actual   : pending=%0d bp=%0b ack=%0b", pending, bp_nw, force_crd_ack);
      $display("  hier     : u_crd.pend / bp_nw / force_crd_ack");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_credit_1024_hole");
    $finish;
  end
endmodule
