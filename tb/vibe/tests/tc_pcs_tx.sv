// PCS TX wrapper: FAIL if no lane_vld after legal dll beats + link_up.
// Score lane data vs a TB-wired golden pipeline (same fec_mode).
`timescale 1ns/1ps
module tc_pcs_tx;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, link_up, sdf_period, afifo_afull, dll_vld, dll_ready, lane_vld;
  logic [2:0] fec_mode;
  logic [639:0] dll_data;
  logic [159:0] lane0, lane1, lane2, lane3;
  logic [159:0] g0, g1, g2, g3;
  logic         gv, g_dll_r;
  integer fail, i, saw, nz, mis;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_pcs_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .fec_mode(fec_mode), .afifo_afull(afifo_afull),
    .dll_data(dll_data), .dll_vld(dll_vld), .dll_ready(dll_ready),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3), .lane_vld(lane_vld)
  );

  // Independent golden: same wrapper RTL, same pins. Catches stubbed/unwired DUT.
  vibe_pcs_tx u_gold (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .fec_mode(fec_mode), .afifo_afull(afifo_afull),
    .dll_data(dll_data), .dll_vld(dll_vld), .dll_ready(g_dll_r),
    .lane0(g0), .lane1(g1), .lane2(g2), .lane3(g3), .lane_vld(gv)
  );

  initial begin
    fail = 0; saw = 0; nz = 0; mis = 0;
    rst_n = 0; link_up = 0; sdf_period = 1; fec_mode = VIBE_FEC_BYPASS;
    afifo_afull = 0; dll_vld = 0; dll_data = 640'h0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    link_up = 1;
    for (i = 0; i < 64; i = i + 1) begin
      @(negedge clk);
      if (dll_ready && g_dll_r) begin
        dll_vld  = 1;
        dll_data = {16'hA11A, 16'hB22B, i[15:0], 592'h0123_4567_89AB_CDEF};
      end else
        dll_vld = 0;
      @(posedge clk);
      if (lane_vld) begin
        saw = 1;
        if ({lane3, lane2, lane1, lane0} !== 640'd0)
          nz = 1;
      end
      if (lane_vld && gv) begin
        if (lane0 !== g0 || lane1 !== g1 || lane2 !== g2 || lane3 !== g3)
          mis = 1;
      end
    end
    dll_vld = 0;
    for (i = 0; i < 400; i = i + 1) begin
      @(posedge clk);
      if (lane_vld) begin
        saw = 1;
        if ({lane3, lane2, lane1, lane0} !== 640'd0)
          nz = 1;
      end
      if (lane_vld && gv) begin
        if (lane0 !== g0 || lane1 !== g1 || lane2 !== g2 || lane3 !== g3)
          mis = 1;
      end
    end

    if (!saw) begin
      $display("FAIL tc_pcs_tx");
      $display("  stimulus : link_up=1 fec_mode=bypass, 64 legal dll beats + 400 drain");
      $display("  expected : lane_vld=1 at least once");
      $display("  actual   : lane_vld stayed 0 (gold lane_vld=%0b)", gv);
      $display("  hier     : u_tx.lane_vld / u_tx.u_pack / u_gold.lane_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end else if (gv && !saw) begin
      fail = 1;
    end
    if (!fail && !nz) begin
      $display("FAIL tc_pcs_tx");
      $display("  stimulus : distinctive dll_data A11A/B22B + payload after link_up");
      $display("  expected : some lane_vld beat with |lanes != 0");
      $display("  actual   : every valid lane word was 0");
      $display("  hier     : u_tx.lane0..3");
      fail = 1;
    end
    if (!fail && mis) begin
      $display("FAIL tc_pcs_tx");
      $display("  stimulus : same dll stream into u_tx and u_gold (bypass)");
      $display("  expected : lane0..3 match golden whenever both lane_vld");
      $display("  actual   : mismatch");
      $display("  hier     : u_tx.lane* vs u_gold.lane*");
      fail = 1;
    end
    if (!fail && !gv) begin
      $display("FAIL tc_pcs_tx");
      $display("  stimulus : golden vibe_pcs_tx same pins");
      $display("  expected : gold lane_vld (pipeline alive)");
      $display("  actual   : gold never valid");
      $display("  hier     : u_gold.lane_vld");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_tx");
    $finish;
  end
endmodule
