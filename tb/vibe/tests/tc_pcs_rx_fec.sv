// RX FEC: bypass two 512b → 960b win; T=4 starts decoder (AS-0.1 §6).
`timescale 1ns/1ps
module tc_pcs_rx_fec;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, beat_vld, beat_ready, win_vld, win_ready, fec_fail, am_gap;
  logic [2:0] fec_mode;
  logic [511:0] beat_data;
  logic [959:0] win_data;
  integer fail, saw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_rx_fec u_f (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .am_gap(am_gap), .fec_fail(fec_fail)
  );
  initial begin
    fail = 0; saw = 0;
    rst_n = 0; fec_mode = VIBE_FEC_BYPASS; beat_vld = 0; win_ready = 1; am_gap = 0;
    beat_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    beat_data = {512{1'b1}}; beat_vld = 1;
    @(posedge clk);
    @(negedge clk);
    beat_data = 512'hA;
    @(posedge clk);
    @(negedge clk);
    beat_vld = 0;
    repeat (8) begin
      @(posedge clk);
      if (win_vld) saw = 1;
    end
    if (!saw) begin
      $display("FAIL tc_pcs_rx_fec");
      $display("  stimulus : bypass two 512b beats");
      $display("  expected : win_vld");
      $display("  actual   : 0");
      fail = 1;
    end
    // consume win
    win_ready = 1;
    repeat (2) @(posedge clk);
    // am_gap clears have_hi (:77)
    @(negedge clk);
    am_gap = 1;
    @(posedge clk);
    @(negedge clk);
    am_gap = 0;
    // T=4 feed path
    fec_mode = VIBE_FEC_T4;
    @(negedge clk);
    beat_data = 512'h1; beat_vld = 1;
    @(posedge clk);
    @(negedge clk);
    beat_data = 512'h2;
    @(posedge clk);
    @(negedge clk);
    beat_vld = 0;
    repeat (200) @(posedge clk);
    if (!fail) $display("PASS tc_pcs_rx_fec");
    $finish;
  end
endmodule
