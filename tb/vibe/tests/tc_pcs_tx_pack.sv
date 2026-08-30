// G2 pack 512b + AMCTL insert (AS-0.1 §5 T5).
`timescale 1ns/1ps
module tc_pcs_tx_pack;
  logic clk, rst_n, sdf_period, afifo_afull, beat_vld, beat_ready, lane_vld, lane_ready;
  logic [511:0] beat_data;
  logic [159:0] lane0, lane1, lane2, lane3;
  integer fail, i, saw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_pack u_p (
    .clk(clk), .rst_n(rst_n), .sdf_period(sdf_period), .afifo_afull(afifo_afull),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3),
    .lane_vld(lane_vld), .lane_ready(lane_ready)
  );
  initial begin
    fail = 0; saw = 0;
    rst_n = 0; sdf_period = 0; afifo_afull = 0; beat_vld = 0; lane_ready = 1;
    beat_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    // 5 beats → pack_vld
    for (i = 0; i < 8; i = i + 1) begin
      @(negedge clk);
      if (beat_ready) begin
        beat_vld = 1; beat_data = {i[7:0], 504'd0};
      end else
        beat_vld = 0;
      @(posedge clk);
      if (lane_vld) saw = 1;
    end
    @(negedge clk);
    beat_vld = 0;
    repeat (16) begin
      @(posedge clk);
      if (lane_vld) saw = 1;
    end
    // AM insert: idle until sym_cnt>=512 (period 512 when !sdf)
    // force insert path
    force u_p.sym_cnt = 10'd512;
    @(negedge clk);
    beat_vld = 1; beat_data = 512'h55;
    @(posedge clk);
    release u_p.sym_cnt;
    @(negedge clk);
    beat_vld = 0;
    repeat (8) @(posedge clk);
    // afifo backpressure
    afifo_afull = 1;
    @(posedge clk);
    afifo_afull = 0;
    sdf_period = 1;
    @(posedge clk);
    if (!saw) begin
      $display("FAIL tc_pcs_tx_pack");
      $display("  stimulus : 8 beats");
      $display("  expected : lane_vld");
      $display("  actual   : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_tx_pack");
    $finish;
  end
endmodule
