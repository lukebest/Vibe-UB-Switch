// FEC bypass 3'b000: skip encoder, still 6-flit (two-window) align. Dual encoders unused.
`timescale 1ns/1ps
module tc_pcs_fec_bypass;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, win_vld, win_ready, cw_vld, cw_ready;
  logic [2:0] fec_mode;
  logic [959:0] win_data;
  logic [1023:0] cw_data;
  integer fail, ncw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_fec u_f (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .cw_data(cw_data), .cw_vld(cw_vld), .cw_ready(cw_ready)
  );
  initial begin
    fail = 0; ncw = 0;
    rst_n = 0; fec_mode = VIBE_FEC_BYPASS; win_vld = 0; cw_ready = 1; win_data = 960'h1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    win_vld = 1; win_data = {960{1'b1}};
    @(posedge clk);
    @(negedge clk);
    win_data = 960'hA;
    @(posedge clk);
    @(negedge clk);
    win_vld = 0;
    repeat (16) begin
      @(posedge clk);
      if (cw_vld) ncw = ncw + 1;
    end
    if (ncw < 2) begin
      $display("FAIL tc_pcs_fec_bypass");
      $display("  stimulus : fec_mode=bypass two 960b windows");
      $display("  expected : two 1024b cw beats (align, no RS)");
      $display("  actual   : %0d cw_vld", ncw);
      $display("  hier     : u_f.bypass / emit_b");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_fec_bypass");
    $finish;
  end
endmodule
