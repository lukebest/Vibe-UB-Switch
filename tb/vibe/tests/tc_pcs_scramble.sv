// Scramble LTB when en=1; pass-through when en=0 (AMCTL/EEIB).
`timescale 1ns/1ps
module tc_pcs_scramble;
  logic clk, rst_n, seed_load, en, in_vld, out_vld;
  logic [1:0] lane_id;
  logic [159:0] in_data, out_data;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_scramble u_s (
    .clk(clk), .rst_n(rst_n), .lane_id(lane_id), .seed_load(seed_load),
    .en(en), .in_vld(in_vld), .in_data(in_data), .out_vld(out_vld), .out_data(out_data)
  );
  initial begin
    fail = 0;
    rst_n = 0; lane_id = 0; seed_load = 0; en = 0; in_vld = 0; in_data = 160'h55;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    in_vld = 1; en = 0;
    @(posedge clk);
    @(posedge clk);
    if (out_data !== 160'h55) begin
      $display("FAIL tc_pcs_scramble");
      $display("  stimulus : en=0 in=55");
      $display("  expected : pass-through (AMCTL/EEIB)");
      $display("  actual   : %h", out_data);
      fail = 1;
    end
    seed_load = 1;
    @(posedge clk);
    seed_load = 0; en = 1; in_data = 160'h0;
    @(posedge clk);
    @(posedge clk);
    if (out_data === 160'h0) begin
      $display("FAIL tc_pcs_scramble");
      $display("  stimulus : en=1 in=0 after seed");
      $display("  expected : scrambled nonzero mask");
      $display("  actual   : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_scramble");
    $finish;
  end
endmodule
