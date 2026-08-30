// LMSM lock-path walk for --cc (2 posedges after stimulus, like
// tc_lmsm_idle_discovery). Icarus walk stays in tc_lmsm_walk.
// No Probe (AS-0.1 §11).
`timescale 1ns/1ps
module tc_lmsm_vlock;
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

  task automatic hard_rst;
    begin
      rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
      lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
      repeat (4) @(posedge clk);
      rst_n = 1;
      repeat (2) @(posedge clk);
    end
  endtask

  task automatic go_disc;
    begin
      lmsm_go = 1;
      @(posedge clk);
      lmsm_go = 0;
      @(posedge clk); // extra edge: Verilator NBA
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
    lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    go_disc();
    if (state !== 5'd1) begin
      $display("FAIL tc_lmsm_vlock");
      $display("  stimulus : lmsm_go + 2 posedge");
      $display("  expected : Disc.A (1)");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    am_locked = 4'b1111;
    @(posedge clk);
    @(posedge clk); // Disc.C
    if (state !== 5'd2 && state !== 5'd3) begin
      $display("FAIL tc_lmsm_vlock");
      $display("  stimulus : am_locked=1111");
      $display("  expected : Disc.C or CFG_A");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    repeat (6) @(posedge clk); // A,K,C,NULL
    repeat (12) @(posedge clk); // ACTIVE
    if (state !== 5'd9) begin
      $display("FAIL tc_lmsm_vlock");
      $display("  stimulus : lock walk");
      $display("  expected : ACTIVE (9)");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    @(posedge clk);
    // RTR_A or RTR_C
    if (state < 5'd10) begin
      $display("FAIL tc_lmsm_vlock");
      $display("  stimulus : retrain_req");
      $display("  expected : RTR_A/C");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    repeat (4) @(posedge clk); // back toward Disc

    // EQ path
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    eq_negotiated = 1;
    repeat (8) @(posedge clk);
    if (state !== 5'd6 && state !== 5'd7 && state !== 5'd8) begin
      $display("FAIL tc_lmsm_vlock");
      $display("  stimulus : eq_negotiated");
      $display("  expected : EQ_P/EQ_A/NULL");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    force u_l.tmr = 27'd0;
    repeat (3) @(posedge clk);
    release u_l.tmr;
    force u_l.tmr = 27'd0;
    repeat (3) @(posedge clk);
    release u_l.tmr;
    eq_negotiated = 0;

    // lid_bad from Disc.C (same arrival cycle — next edge would be CFG_A)
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // enter Disc.C
    lid_bad = 1;
    @(posedge clk); // 58 if
    @(posedge clk);
    lid_bad = 0;

    // CFG_K !x4
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // C
    @(posedge clk); // A
    am_locked = 0;
    @(posedge clk);
    @(posedge clk);

    // lane0 from ACTIVE
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    repeat (8) @(posedge clk);
    repeat (12) @(posedge clk);
    lane0_fail = 1;
    @(posedge clk);
    lane0_fail = 0;
    @(posedge clk);
    force u_l.tmr = 27'd0;
    repeat (3) @(posedge clk);
    release u_l.tmr;

    // port_rst
    port_rst = 1;
    @(posedge clk);
    @(posedge clk);
    port_rst = 0;

    // default st
    force u_l.st = 5'd31;
    @(posedge clk);
    release u_l.st;
    @(posedge clk);

    // remaining timeout deposits
    hard_rst();
    go_disc();
    force u_l.tmr = 27'd0;
    repeat (3) @(posedge clk);
    release u_l.tmr;
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk);
    @(posedge clk);
    force u_l.tmr = 27'd0;
    repeat (3) @(posedge clk);
    release u_l.tmr;

    // Disc.C timeout / lid_bad / stay
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk);
    @(posedge clk); // Disc.C
    am_locked = 0;
    @(posedge clk); // stay C or tmr path
    force u_l.tmr = 27'd0;
    @(posedge clk);
    @(posedge clk);
    release u_l.tmr;
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk);
    @(posedge clk);
    lid_bad = 1;
    @(posedge clk);
    @(posedge clk);
    lid_bad = 0;

    // CFG_K !x4_ok ; CFG_C eq ; EQ_A hold
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); @(posedge clk); @(posedge clk); // C,A,K
    am_locked = 0;
    @(posedge clk);
    @(posedge clk);
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    eq_negotiated = 1;
    repeat (6) @(posedge clk); // to EQ_P
    @(posedge clk); // EQ_A if tmr forced
    force u_l.tmr = 27'd0;
    @(posedge clk);
    @(posedge clk); // EQ_P→EQ_A
    release u_l.tmr;
    @(posedge clk); // EQ_A hold (tmr just loaded)
    force u_l.tmr = 27'd0;
    @(posedge clk);
    @(posedge clk);
    release u_l.tmr;
    eq_negotiated = 0;

    // ACTIVE lid_bad ; RTR_A timeout / stay ; RTR_C stay
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    repeat (8) @(posedge clk);
    repeat (12) @(posedge clk);
    lid_bad = 1;
    @(posedge clk);
    @(posedge clk);
    lid_bad = 0;
    am_locked = 0;
    @(posedge clk); // RTR_A stay
    force u_l.tmr = 27'd0;
    @(posedge clk);
    @(posedge clk);
    release u_l.tmr;
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    repeat (8) @(posedge clk);
    repeat (12) @(posedge clk);
    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    @(posedge clk);
    @(posedge clk); // RTR_C
    am_locked = 0;
    @(posedge clk); // RTR_C stay (90 else)
    force u_l.tmr = 27'd0;
    @(posedge clk);
    @(posedge clk);
    release u_l.tmr;

    if (!fail) $display("PASS tc_lmsm_vlock");
    $finish;
  end
endmodule
