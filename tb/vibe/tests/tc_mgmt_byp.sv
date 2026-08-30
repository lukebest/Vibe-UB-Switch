// Mgmt bypass FIFO does not enter xbar (unit: 16x640, ready/valid).
`timescale 1ns/1ps
module tc_mgmt_byp;
  logic clk, rst_n, in_vld, in_ready, out_vld, out_ready;
  logic [639:0] in_data, out_data;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_mgmt_byp u_b (
    .clk(clk), .rst_n(rst_n),
    .in_data(in_data), .in_vld(in_vld), .in_ready(in_ready),
    .out_data(out_data), .out_vld(out_vld), .out_ready(out_ready)
  );
  initial begin
    fail = 0;
    rst_n = 0; in_vld = 0; out_ready = 0; in_data = 640'hA5;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    in_vld = 1;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    @(posedge clk);
    if (!out_vld || out_data !== 640'hA5) begin
      $display("FAIL tc_mgmt_byp");
      $display("  stimulus : one 640b write, out_ready=0");
      $display("  expected : out_vld=1 data=A5 (held, not xbar)");
      $display("  actual   : vld=%0b data=%h", out_vld, out_data);
      fail = 1;
    end
    if (!fail) $display("PASS tc_mgmt_byp");
    $finish;
  end
endmodule
