// LMSM: Idle → Discovery on lmsm_go. Not Probe. Width x4-only subset.
`timescale 1ns/1ps
module tc_lmsm_idle_discovery;
  logic clk, rst_n, port_rst, lmsm_go, lid_bad, lane0_fail, eq_negotiated, retrain_req;
  logic [3:0] am_locked;
  logic link_up, link_ready, sdf_period, width_fail;
  logic [4:0] state;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_lmsm u_l (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .lmsm_go(lmsm_go),
    .am_locked(am_locked), .lid_bad(lid_bad), .lane0_fail(lane0_fail),
    .eq_negotiated(eq_negotiated), .retrain_req(retrain_req),
    .link_up(link_up), .link_ready(link_ready), .sdf_period(sdf_period),
    .state(state), .width_fail(width_fail)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
    lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_idle_discovery");
      $display("  stimulus : reset");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(posedge clk);
    if (state !== 5'd1) begin
      $display("FAIL tc_lmsm_idle_discovery");
      $display("  stimulus : lmsm_go");
      $display("  expected : Discovery.Active (1), not Probe");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    if (!fail) $display("PASS tc_lmsm_idle_discovery");
    $finish;
  end
endmodule
