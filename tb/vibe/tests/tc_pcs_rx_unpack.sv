// 4×160 → 512b beats; skip AMCTL (AS-0.1 §6 inverse G2).
`timescale 1ns/1ps
module tc_pcs_rx_unpack;
  logic clk, rst_n, lane_vld, am0, am1, am2, am3, am_gap, beat_vld, beat_ready;
  logic [159:0] lane0, lane1, lane2, lane3;
  logic [511:0] beat_data;
  integer fail, n, saw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_rx_unpack u_u (
    .clk(clk), .rst_n(rst_n),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3),
    .lane_vld(lane_vld), .am0(am0), .am1(am1), .am2(am2), .am3(am3),
    .am_gap(am_gap),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready)
  );
  initial begin
    fail = 0; saw = 0;
    rst_n = 0; lane_vld = 0; am0 = 0; am1 = 0; am2 = 0; am3 = 0; am_gap = 0;
    beat_ready = 1; lane0 = 0; lane1 = 0; lane2 = 0; lane3 = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    // skip AM
    @(negedge clk);
    am0 = 1; lane_vld = 1; lane0 = 160'hAA;
    @(posedge clk);
    @(negedge clk);
    am0 = 0;
    // 4 data groups → have
    for (n = 0; n < 5; n = n + 1) begin
      lane0 = n[159:0]; lane1 = n + 16; lane2 = n + 32; lane3 = n + 48;
      lane_vld = 1;
      @(posedge clk);
      if (beat_vld) saw = 1;
    end
    @(negedge clk);
    lane_vld = 0;
    repeat (8) begin
      @(posedge clk);
      if (beat_vld) saw = 1;
    end
    if (!saw) begin
      $display("FAIL tc_pcs_rx_unpack");
      $display("  stimulus : 4+ lane groups");
      $display("  expected : beat_vld");
      $display("  actual   : 0");
      fail = 1;
    end
    beat_ready = 0;
    @(posedge clk);
    beat_ready = 1;
    repeat (6) @(posedge clk);
    // am_gap resets n (:48)
    @(negedge clk);
    am_gap = 1;
    @(posedge clk);
    @(negedge clk);
    am_gap = 0;
    // Dual-buffer: keep feeding 640s while emitting so n==3 hits nxt_full
    // (:70 else / :56 swap). 8 groups while beat_ready=1.
    beat_ready = 1;
    for (n = 0; n < 8; n = n + 1) begin
      lane0 = n[159:0]; lane1 = n + 16; lane2 = n + 32; lane3 = n + 48;
      lane_vld = 1;
      @(posedge clk);
    end
    @(negedge clk);
    lane_vld = 0;
    repeat (10) @(posedge clk);
    // n==0 && have drain else (coverage; NOTE if force ignored)
    force u_u.n = 3'd0;
    force u_u.have = 1'b1;
    beat_ready = 1;
    @(posedge clk);
    release u_u.n;
    release u_u.have;
    @(posedge clk);
    if (!fail) $display("PASS tc_pcs_rx_unpack");
    $finish;
  end
endmodule
