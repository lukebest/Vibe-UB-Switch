// Deskew on AMCTL. Factory physical=logical; no lane swap (U24).
`timescale 1ns/1ps
module tc_pcs_rx_deskew;
  logic clk, rst_n, in_vld, am0, am1, am2, am3, out_vld, aligned;
  logic [159:0] in0, in1, in2, in3, out0, out1, out2, out3;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_rx_deskew u_d (
    .clk(clk), .rst_n(rst_n),
    .in0(in0), .in1(in1), .in2(in2), .in3(in3), .in_vld(in_vld),
    .am0(am0), .am1(am1), .am2(am2), .am3(am3),
    .out0(out0), .out1(out1), .out2(out2), .out3(out3),
    .out_vld(out_vld), .aligned(aligned)
  );
  initial begin
    fail = 0;
    rst_n = 0; in_vld = 0; am0 = 0; am1 = 0; am2 = 0; am3 = 0;
    in0 = 0; in1 = 0; in2 = 0; in3 = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // staggered AM
    @(negedge clk);
    in_vld = 1; am0 = 1; in0 = 160'hA;
    @(posedge clk);
    @(negedge clk);
    am0 = 0; am1 = 1; in1 = 160'hB;
    @(posedge clk);
    @(negedge clk);
    am1 = 0; am2 = 1; in2 = 160'hC;
    @(posedge clk);
    @(negedge clk);
    am2 = 0; am3 = 1; in3 = 160'hD;
    @(posedge clk);
    @(negedge clk);
    am3 = 0;
    @(posedge clk);
    if (!aligned) begin
      $display("FAIL tc_pcs_rx_deskew");
      $display("  stimulus : AM on each lane staggered");
      $display("  expected : aligned");
      $display("  actual   : 0");
      fail = 1;
    end
    // data (no AM) → out_vld
    @(negedge clk);
    in0 = 160'h1; in1 = 160'h2; in2 = 160'h3; in3 = 160'h4;
    in_vld = 1;
    #1;
    if (!out_vld) begin
      $display("FAIL tc_pcs_rx_deskew");
      $display("  stimulus : aligned + data no AM");
      $display("  expected : out_vld");
      $display("  actual   : 0");
      fail = 1;
    end
    @(posedge clk);
    in_vld = 0;
    if (!fail) $display("PASS tc_pcs_rx_deskew");
    $finish;
  end
endmodule
