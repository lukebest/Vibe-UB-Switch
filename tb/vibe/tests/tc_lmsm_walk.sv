// LMSM walk after Discovery. No Probe (AS-0.1 §11). Force tmr — 24 ms timers
// are not simulated cycle-by-cycle. width_fail is tied 0 (x4-only).
`timescale 1ns/1ps
module tc_lmsm_walk;
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

  task automatic go_disc;
    begin
      lmsm_go = 1;
      @(posedge clk);
      lmsm_go = 0;
      @(posedge clk);
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
    lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (width_fail !== 1'b0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : reset");
      $display("  expected : width_fail=0 (x4-only; no Probe)");
      $display("  actual   : 1");
      fail = 1;
    end
    go_disc();
    if (state !== 5'd1) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : lmsm_go");
      $display("  expected : Disc.A (1), not Probe");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    // Disc.A timeout → Idle (force tmr; 24 ms not walked)
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : Disc.A tmr=0");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // Happy path: lock → CFG → NULL → ACTIVE (no EQ)
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    @(posedge clk); // CFG_A
    @(posedge clk); // CFG_K
    @(posedge clk); // CFG_C
    eq_negotiated = 0;
    @(posedge clk); // NULL
    if (state !== 5'd8) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : lock, no EQ");
      $display("  expected : NULL (8)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    if (!link_up || !sdf_period) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : NULL");
      $display("  expected : link_up sdf_period");
      $display("  actual   : up=%0b sdf=%0b", link_up, sdf_period);
      fail = 1;
    end
    repeat (10) @(posedge clk); // null_cnt → ACTIVE
    if (state !== 5'd9 || !link_ready) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : 8+ NULL cycles");
      $display("  expected : ACTIVE link_ready");
      $display("  actual   : st=%0d ready=%0b", state, link_ready);
      fail = 1;
    end

    // Retrain: ACTIVE → RTR_A on retrain_req
    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    if (state !== 5'd10) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : retrain_req in ACTIVE");
      $display("  expected : RTR_A (10)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    am_locked = 4'b1111;
    @(posedge clk); // RTR_C
    @(posedge clk); // Disc.A (from retrain)
    if (state !== 5'd1) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : RTR lock x4_ok");
      $display("  expected : Disc.A");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // lid_bad in Disc.C → Idle
    rst_n = 0;
    repeat (2) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    lid_bad = 1;
    @(posedge clk);
    lid_bad = 0;
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : Disc.C lid_bad");
      $display("  expected : Idle (U24)");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // EQ path: CFG_C eq_negotiated → EQ_P → force tmr → EQ_A → NULL
    go_disc();
    am_locked = 4'b1111; lid_bad = 0;
    @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); // CFG_C
    eq_negotiated = 1;
    @(posedge clk);
    eq_negotiated = 0;
    if (state !== 5'd6) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : CFG_C eq_negotiated");
      $display("  expected : EQ_P (6)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd7) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : EQ_P tmr=0");
      $display("  expected : EQ_A (7)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd8) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : EQ_A tmr=0");
      $display("  expected : NULL");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // CFG_K !x4_ok → Idle
    rst_n = 0;
    repeat (2) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    @(posedge clk); // CFG_A
    am_locked = 4'd0;
    @(posedge clk); // CFG_K with !x4_ok
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : CFG_K unlock");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // ACTIVE lid_bad / lane0_fail
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); // NULL
    repeat (10) @(posedge clk); // ACTIVE
    lane0_fail = 1;
    @(posedge clk);
    lane0_fail = 0;
    if (state !== 5'd10) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : ACTIVE lane0_fail");
      $display("  expected : RTR_A");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : RTR_A tmr=0");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // port_rst
    go_disc();
    port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : port_rst");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // illegal st → default Idle
    force u_l.st = 5'd31;
    #1;
    if (u_l.st_n !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : force st=31");
      $display("  expected : st_n=Idle (default)");
      $display("  actual   : %0d", u_l.st_n);
      fail = 1;
    end
    release u_l.st;
    @(posedge clk);

    // NULL timeout
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : NULL tmr=0");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // remaining timeout arms: Disc.C / CFG_* / RTR_C
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    am_locked = 4'd0; // stay Disc.C (not x4, not lid_bad)
    force u_l.tmr = 27'd0;
    @(posedge clk);
    release u_l.tmr;
    @(posedge clk);
    if (state !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : Disc.C tmr=0");
      $display("  expected : Idle");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    if (!fail) $display("PASS tc_lmsm_walk");
    $finish;
  end
endmodule
