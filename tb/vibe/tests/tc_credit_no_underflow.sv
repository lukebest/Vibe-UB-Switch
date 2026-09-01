// TP-CRD-008: no invented credit underflow code (scan + port exercise).
`timescale 1ns/1ps
module tc_credit_no_underflow;
  `include "vibe_ub_params.vh"
  `include "und_scan.inc"
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
    if (UND_CODE_HIT) begin
      $display("FAIL tc_credit_no_underflow");
      $display("  stimulus : scan vibe_dll_credit.sv code (// comments ignored)");
      $display("  expected : no underflow / und_err token in ports or logic");
      $display("  actual   : token present in code");
      $display("  hier     : rtl/dll/vibe_dll_credit.sv");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    rst_n = 0; port_rst = 0; link_up = 1;
    grain_n = 8'd8; consume_vld = 0; consume_flits = 0; is_cfg0 = 0;
    credit_ret = 0; credit_ret_n = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd4;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    @(posedge clk);
    if (fc_ovf) begin
      $display("FAIL tc_credit_no_underflow");
      $display("  stimulus : credit_ret_n=4 with no consume");
      $display("  expected : fc_ovf=0 (return is not underflow)");
      $display("  actual   : fc_ovf=1");
      $display("  hier     : u_crd.fc_ovf / proto_err");
      fail = 1;
    end
    if (!fail) $display("PASS tc_credit_no_underflow");
    $finish;
  end
endmodule
