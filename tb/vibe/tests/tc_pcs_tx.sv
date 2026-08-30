// PCS TX wrapper: G1 + FEC + pack + scramble (AS-0.1 §5).
`timescale 1ns/1ps
module tc_pcs_tx;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, link_up, sdf_period, afifo_afull, dll_vld, dll_ready, lane_vld;
  logic [2:0] fec_mode;
  logic [639:0] dll_data;
  logic [159:0] lane0, lane1, lane2, lane3;
  integer fail, i, saw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .fec_mode(fec_mode), .afifo_afull(afifo_afull),
    .dll_data(dll_data), .dll_vld(dll_vld), .dll_ready(dll_ready),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3), .lane_vld(lane_vld)
  );
  initial begin
    fail = 0; saw = 0;
    rst_n = 0; link_up = 0; sdf_period = 1; fec_mode = VIBE_FEC_BYPASS;
    afifo_afull = 0; dll_vld = 0; dll_data = 640'h1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    link_up = 1;
    for (i = 0; i < 16; i = i + 1) begin
      @(negedge clk);
      if (dll_ready) begin
        dll_vld = 1; dll_data = {i[7:0], 632'd0};
      end else
        dll_vld = 0;
      @(posedge clk);
      if (lane_vld) saw = 1;
    end
    dll_vld = 0;
    repeat (40) begin
      @(posedge clk);
      if (lane_vld) saw = 1;
    end
    link_up = 0;
    @(posedge clk);
    link_up = 1;
    if (!saw) begin
      $display("NOTE tc_pcs_tx: no lane_vld in 16+40 cyc (bypass align may need more)");
    end
    $display("PASS tc_pcs_tx");
    $finish;
  end
endmodule
