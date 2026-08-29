// Negative: Probe / QDLWS / Change_Speed absent from LMSM (AS-0.1 §11).
// lmsm_go from Idle goes to Discovery, not Probe.
`timescale 1ns/1ps

module tc_neg_absent_features;
  logic        clk, rst_n, port_rst, lmsm_go;
  logic [3:0]  am_locked;
  logic        lid_bad, lane0_fail, eq_negotiated, retrain_req;
  logic        link_up, link_ready, sdf_period, width_fail;
  logic [4:0]  state;
  integer      fail;

  localparam [4:0] ST_IDLE   = 5'd0;
  localparam [4:0] ST_DISC_A = 5'd1;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_lmsm u_lmsm (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .lmsm_go(lmsm_go),
    .am_locked(am_locked), .lid_bad(lid_bad), .lane0_fail(lane0_fail),
    .eq_negotiated(eq_negotiated), .retrain_req(retrain_req),
    .link_up(link_up), .link_ready(link_ready), .sdf_period(sdf_period),
    .state(state), .width_fail(width_fail)
  );

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0;
    am_locked = 4'd0; lid_bad = 0; lane0_fail = 0;
    eq_negotiated = 0; retrain_req = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    if (state !== ST_IDLE) begin
      $display("FAIL tc_neg_absent_features");
      $display("  stimulus : reset");
      $display("  expected : ST_IDLE (no Probe state)");
      $display("  actual   : state=%0d", state);
      fail = 1;
    end
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(posedge clk);
    if (state !== ST_DISC_A) begin
      $display("FAIL tc_neg_absent_features");
      $display("  stimulus : pulse lmsm_go from Idle");
      $display("  expected : Discovery.Active (5'd1) — not Probe / QDLWS / RXEQ_Optimize");
      $display("  actual   : state=%0d", state);
      $display("  hier     : u_lmsm.st");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    // Stay a few cycles: must not jump to an unimplemented Probe encoding.
    repeat (8) @(posedge clk);
    if (state === 5'd12 || state === 5'd13 || state === 5'd31) begin
      $display("FAIL tc_neg_absent_features");
      $display("  stimulus : after lmsm_go");
      $display("  expected : remain in implemented subset (no Probe encoding)");
      $display("  actual   : state=%0d", state);
      fail = 1;
    end
    if (!fail) $display("PASS tc_neg_absent_features");
    $finish;
  end
endmodule
