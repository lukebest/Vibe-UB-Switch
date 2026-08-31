// --cc: bypass second-CW arm (emit_b==1 && !cw_vld).
// First emit sets emit_b and cw_vld; pulse cw_ready to drop cw_vld, then
// the next cycle takes `else if (cw_ready || !cw_vld)`.
`timescale 1ns/1ps
module tc_pcs_fec_emitb;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, win_vld, win_ready, cw_vld, cw_ready;
  logic [2:0] fec_mode;
  logic [959:0] win_data;
  logic [1023:0] cw_data;
  integer fail, saw1, saw2, n;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_fec u_f (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .cw_data(cw_data), .cw_vld(cw_vld), .cw_ready(cw_ready)
  );
  initial begin
    fail = 0; saw1 = 0; saw2 = 0;
    rst_n = 0; fec_mode = VIBE_FEC_BYPASS; win_vld = 0; cw_ready = 0;
    win_data = 960'h1;
    repeat (4) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    win_vld = 1; win_data = 960'hAA;
    @(posedge clk);
    @(negedge clk);
    win_data = 960'hBB;
    @(posedge clk);
    @(negedge clk);
    win_vld = 0;
    cw_ready = 0;
    // wait first emit (emit_b<=1, cw_vld<=1) without accepting
    n = 0;
    while (!cw_vld && n < 20) begin
      @(posedge clk);
      n = n + 1;
    end
    if (!cw_vld) begin
      $display("FAIL tc_pcs_fec_emitb");
      $display("  stimulus : two bypass windows, cw_ready=0");
      $display("  expected : first cw_vld");
      $display("  actual   : 0 emit_b=%0b", u_f.emit_b);
      fail = 1;
    end else
      saw1 = 1;
    @(negedge clk);
    // accept first CW → cw_vld<=0, emit_b still 1
    cw_ready = 1;
    @(posedge clk);
    @(negedge clk);
    cw_ready = 0;
    @(posedge clk); // !cw_vld && emit_b → else if (line 96)
    @(negedge clk);
    if (cw_vld) saw2 = 1;
    // Hold cw_ready=0 so the second CW is still visible next posedge.
    @(posedge clk);
    @(negedge clk);
    if (cw_vld) saw2 = 1;
    if (!saw2) begin
      $display("FAIL tc_pcs_fec_emitb");
      $display("  stimulus : ack first CW, emit_b held");
      $display("  expected : second cw_vld (line 96 else)");
      $display("  actual   : 0 emit_b=%0b have0=%0b have1=%0b",
               u_f.emit_b, u_f.have0, u_f.have1);
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_fec_emitb");
    $finish;
  end
endmodule
