// CDC rst_sync: async assert, sync deassert.
`timescale 1ns/1ps
module tc_rst_sync;
  logic clk, rst_n_in, rst_n_out;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_rst_sync u_s (.clk(clk), .rst_n_in(rst_n_in), .rst_n_out(rst_n_out));
  initial begin
    fail = 0;
    rst_n_in = 0;
    repeat (3) @(posedge clk);
    if (rst_n_out !== 1'b0) begin
      $display("FAIL tc_rst_sync");
      $display("  stimulus : rst_n_in=0");
      $display("  expected : rst_n_out=0 async assert");
      $display("  actual   : %0b", rst_n_out);
      fail = 1;
    end
    rst_n_in = 1;
    @(posedge clk);
    if (rst_n_out !== 1'b0) begin
      $display("FAIL tc_rst_sync");
      $display("  stimulus : deassert, first dest clock");
      $display("  expected : still 0 (2-FF)");
      $display("  actual   : %0b", rst_n_out);
      fail = 1;
    end
    @(posedge clk);
    @(posedge clk);
    if (rst_n_out !== 1'b1) begin
      $display("FAIL tc_rst_sync");
      $display("  stimulus : two dest clocks after deassert");
      $display("  expected : rst_n_out=1");
      $display("  actual   : %0b", rst_n_out);
      fail = 1;
    end
    if (!fail) $display("PASS tc_rst_sync");
    $finish;
  end
endmodule
