// 1024b codeword → two 512b beats.
`timescale 1ns/1ps
module tc_pcs_cw2beat;
  logic clk, rst_n, cw_vld, cw_ready, beat_vld, beat_ready;
  logic [1023:0] cw_data;
  logic [511:0] beat_data;
  integer fail, n;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_cw2beat u_c (
    .clk(clk), .rst_n(rst_n), .cw_data(cw_data), .cw_vld(cw_vld), .cw_ready(cw_ready),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready)
  );
  initial begin
    fail = 0; n = 0;
    rst_n = 0; cw_vld = 0; beat_ready = 1; cw_data = {512'hA, 512'hB};
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    cw_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cw_vld = 0;
    repeat (6) begin
      @(posedge clk);
      if (beat_vld) n = n + 1;
    end
    if (n < 2) begin
      $display("FAIL tc_pcs_cw2beat");
      $display("  stimulus : one 1024b cw");
      $display("  expected : two 512b beats");
      $display("  actual   : %0d", n);
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_cw2beat");
    $finish;
  end
endmodule
