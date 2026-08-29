// Credit threshold 1024 is FS-must; the UNIT (cell vs flit) is a HOLE.
// Do not guess. This TC only checks the named comparator vs VIBE_CREDIT_THRESH.
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

    if (VIBE_CREDIT_THRESH != 1024) begin
      $display("FAIL tc_credit_1024_hole");
      $display("  stimulus : parameter probe");
      $display("  expected : VIBE_CREDIT_THRESH==1024 (FS-must)");
      $display("  actual   : %0d", VIBE_CREDIT_THRESH);
      $display("  hier     : vibe_ub_params.vh");
      fail = 1;
    end

    // Drive pending to 1024 via credit_ret_n without interpreting unit.
    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd1024;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    @(posedge clk);
    if (!bp_nw || !force_crd_ack) begin
      $display("FAIL tc_credit_1024_hole");
      $display("  stimulus : credit_ret_n=1024 (unit unspecified — HOLE)");
      $display("  expected : bp_nw=1 and force_crd_ack=1 at pending>=1024");
      $display("  actual   : bp_nw=%0b force=%0b pending=%0d", bp_nw, force_crd_ack, pending);
      $display("  hier     : u_crd.pend / VIBE_CREDIT_THRESH");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    $display("HOLE credit-1024-unit: AS/FS do not lock cell vs flit; TB does not guess");
    if (!fail) $display("PASS tc_credit_1024_hole");
    $finish;
  end
endmodule
