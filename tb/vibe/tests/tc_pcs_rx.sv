// PCS RX wrapper remainder 960→640 (AS-0.1 inverse T2). Children covered separately.
`timescale 1ns/1ps
module tc_pcs_rx;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, lane_vld, dll_vld, dll_ready, fec_fail, lid_bad, deskew_ok;
  logic [2:0] fec_mode;
  logic [159:0] lane0, lane1, lane2, lane3;
  logic [639:0] dll_data;
  logic [3:0] am_locked;
  integer fail, i;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_rx u_rx (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3), .lane_vld(lane_vld),
    .dll_data(dll_data), .dll_vld(dll_vld), .dll_ready(dll_ready),
    .fec_fail(fec_fail), .am_locked(am_locked), .lid_bad(lid_bad), .deskew_ok(deskew_ok)
  );
  initial begin
    fail = 0;
    rst_n = 0; fec_mode = VIBE_FEC_BYPASS; lane_vld = 0; dll_ready = 1;
    lane0 = 0; lane1 = 0; lane2 = 0; lane3 = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    for (i = 0; i < 24; i = i + 1) begin
      @(negedge clk);
      lane0 = i[159:0]; lane1 = i + 1; lane2 = i + 2; lane3 = i + 3;
      lane_vld = 1;
      @(posedge clk);
    end
    @(negedge clk);
    lane_vld = 0;
    // remainder FSM both arms (force internal wv — wrapper lines)
    dll_ready = 1;
    force u_rx.wv = 1'b1;
    force u_rx.win = {960{1'b1}};
    @(posedge clk);
    @(posedge clk);
    force u_rx.remv = 1'b1;
    @(posedge clk);
    release u_rx.wv;
    release u_rx.win;
    release u_rx.remv;
    if (dll_vld && dll_ready)
      @(posedge clk);
    if (!fail) $display("PASS tc_pcs_rx");
    $finish;
  end
endmodule
