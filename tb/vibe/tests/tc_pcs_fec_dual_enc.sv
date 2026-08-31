// FEC T=4: two RS(128,120) encoders start together (dual interleave).
`timescale 1ns/1ps
module tc_pcs_fec_dual_enc;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, win_vld, win_ready, cw_vld, cw_ready;
  logic [2:0] fec_mode;
  logic [959:0] win_data;
  logic [1023:0] cw_data;
  integer fail, saw_a, saw_b;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_fec u_f (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .cw_data(cw_data), .cw_vld(cw_vld), .cw_ready(cw_ready)
  );
  always @(posedge clk) begin
    if (u_f.enc_a_start) saw_a <= 1;
    if (u_f.enc_b_start) saw_b <= 1;
  end
  initial begin
    fail = 0; saw_a = 0; saw_b = 0;
    rst_n = 0; fec_mode = VIBE_FEC_T4; win_vld = 0; cw_ready = 1; win_data = 960'h3;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    win_vld = 1;
    @(posedge clk);
    @(negedge clk);
    @(posedge clk);
    @(negedge clk);
    win_vld = 0;
    // 120 symbols + emit both CWs
    repeat (280) @(posedge clk);
    if (!saw_a || !saw_b) begin
      $display("FAIL tc_pcs_fec_dual_enc");
      $display("  stimulus : fec_mode=T4 two windows");
      $display("  expected : enc_a_start and enc_b_start (dual interleave)");
      $display("  actual   : a=%0d b=%0d", saw_a, saw_b);
      $display("  hier     : u_f.enc_a_start / enc_b_start");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_fec_dual_enc");
    $finish;
  end
endmodule
