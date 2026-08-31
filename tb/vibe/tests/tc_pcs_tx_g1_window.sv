// pcs_tx_g1: 640b=4 flits → collect 6-flit FEC window (1.5 beats + remainder).
`timescale 1ns/1ps
module tc_pcs_tx_g1_window;
  logic clk, rst_n, link_up, in_vld, in_ready, win_vld, win_ready;
  logic [639:0] in_data;
  logic [959:0] win_data;
  integer fail, saw;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_g1 u_g (
    .clk(clk), .rst_n(rst_n), .link_up(link_up),
    .in_data(in_data), .in_vld(in_vld), .in_ready(in_ready),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready)
  );
  initial begin
    fail = 0; saw = 0;
    rst_n = 0; link_up = 1; in_vld = 0; win_ready = 1; in_data = 640'h1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (4) begin
      @(negedge clk);
      if (in_ready) begin in_vld = 1; in_data = 640'hA; end
      else in_vld = 0;
      @(posedge clk);
      if (win_vld) saw = 1;
    end
    in_vld = 0;
    repeat (8) begin
      @(posedge clk);
      if (win_vld) saw = 1;
    end
    if (!saw) begin
      $display("FAIL tc_pcs_tx_g1_window");
      $display("  stimulus : several 640b beats link_up=1");
      $display("  expected : win_vld (6-flit / 960b window)");
      $display("  actual   : no window");
      $display("  hier     : u_g.nflit / have");
      fail = 1;
    end
    // rem_vld → idle-null fill of next window
    in_vld = 0; win_ready = 1; link_up = 1;
    repeat (12) @(posedge clk);
    link_up = 0;
    @(posedge clk);
    if (!fail) $display("PASS tc_pcs_tx_g1_window");
    $finish;
  end
endmodule
