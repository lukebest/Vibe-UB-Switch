// TP-FEC-002 — T=2 (RS(144,128) mode pin VIBE_FEC_T2). Dual encoders still start.
`timescale 1ns/1ps
module tc_pcs_fec_t2;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, win_vld, win_ready, cw_vld, cw_ready;
  logic [2:0] fec_mode;
  logic [959:0] win_data;
  logic [1023:0] cw_data;
  integer fail, saw_a, saw_b, ncw;
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
    if (cw_vld) ncw <= ncw + 1;
  end
  initial begin
    fail = 0; saw_a = 0; saw_b = 0; ncw = 0;
    rst_n = 0; fec_mode = VIBE_FEC_T2; win_vld = 0; cw_ready = 1; win_data = 960'h5;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    win_vld = 1;
    @(posedge clk);
    @(negedge clk);
    win_data = 960'h6;
    @(posedge clk);
    @(negedge clk);
    win_vld = 0;
    repeat (200) @(posedge clk);
    if (!saw_a || !saw_b) begin
      $display("FAIL tc_pcs_fec_t2");
      $display("  stimulus : fec_mode=T2 two 960b windows");
      $display("  expected : enc_a_start and enc_b_start (not bypass)");
      $display("  actual   : a=%0d b=%0d cw=%0d", saw_a, saw_b, ncw);
      $display("  hier     : u_f.enc_a_start / enc_b_start / bypass");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_fec_t2");
    $finish;
  end
endmodule
