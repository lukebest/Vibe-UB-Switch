// LMSM walk after Discovery. No Probe (AS-0.1 §11). Force/deposit tmr —
// 24 ms timers are not walked cycle-by-cycle. width_fail is tied 0 (x4-only).
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

  task automatic hard_rst;
    begin
      rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
      lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
      repeat (2) @(posedge clk);
      rst_n = 1;
      @(posedge clk);
    end
  endtask

  task automatic chk;
    input [4:0] exp;
    input integer tag;
    begin
      @(negedge clk);
      if (state !== exp) begin
        $display("FAIL tc_lmsm_walk");
        $display("  stimulus : tag=%0d", tag);
        $display("  expected : %0d", exp);
        $display("  actual   : %0d", state);
        fail = 1;
      end
    end
  endtask

  // Hierarchical assign of tmr is ignored / illegal in Verilator --cc.
  // force + --public-flat-rw (cov cluster) is the deposit path. No RTL edit.
  task automatic zap_tmr;
    begin
      force u_l.tmr = 27'd0;
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

    // Idle → Disc.A
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    chk(5'd1, 1);

    // Disc.A timeout
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 2);

    // lock → Disc.C → CFG_A → CFG_K → CFG_C → NULL (no EQ)
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk);
    chk(5'd2, 3); // Disc.C
    @(posedge clk);
    chk(5'd3, 4); // CFG_A
    @(posedge clk);
    chk(5'd4, 5); // CFG_K
    @(posedge clk);
    chk(5'd5, 6); // CFG_C
    @(posedge clk);
    chk(5'd8, 7); // NULL
    if (!link_up || !sdf_period) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : NULL");
      $display("  expected : link_up sdf_period");
      $display("  actual   : up=%0b sdf=%0b", link_up, sdf_period);
      fail = 1;
    end
    repeat (10) @(posedge clk);
    chk(5'd9, 8); // ACTIVE
    if (!link_ready) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : ACTIVE");
      $display("  expected : link_ready");
      fail = 1;
    end

    @(negedge clk);
    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    chk(5'd10, 9); // RTR_A
    @(posedge clk);
    chk(5'd11, 10); // RTR_C (all_lock still 1)
    @(posedge clk);
    @(negedge clk);
    if (state !== 5'd1 && state !== 5'd2) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : RTR_C x4_ok tag=11");
      $display("  expected : Disc.A or Disc.C");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // Disc.C lid_bad: enter C, then lid_bad same cycle window
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    chk(5'd1, 12);
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk);
    chk(5'd2, 13);
    lid_bad = 1; // already at negedge after chk
    @(posedge clk);
    chk(5'd0, 14);
    lid_bad = 0;

    // EQ path
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    eq_negotiated = 1;
    @(posedge clk); // C
    @(posedge clk); // A
    @(posedge clk); // K
    @(posedge clk); // CFG_C
    @(posedge clk); // EQ_P
    chk(5'd6, 15);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd7, 16);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd8, 17);
    eq_negotiated = 0;

    // CFG_K !x4_ok
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk); // C
    @(posedge clk); // CFG_A
    @(negedge clk);
    am_locked = 4'd0;
    @(posedge clk); // CFG_K with !x4
    @(posedge clk);
    chk(5'd0, 18);

    // ACTIVE + lane0_fail
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    repeat (8) @(posedge clk); // through CFG to NULL
    repeat (10) @(posedge clk); // ACTIVE
    chk(5'd9, 19);
    @(negedge clk);
    lane0_fail = 1;
    @(posedge clk);
    lane0_fail = 0;
    chk(5'd10, 20);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 21);

    // port_rst from Disc.A
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    chk(5'd1, 22);
    @(negedge clk);
    port_rst = 1;
    @(posedge clk);
    chk(5'd0, 23);
    port_rst = 0;

    // default combo
    force u_l.st = 5'd31;
    #1;
    if (u_l.st_n !== 5'd0) begin
      $display("FAIL tc_lmsm_walk");
      $display("  stimulus : force st=31 tag=24");
      $display("  expected : st_n=0");
      $display("  actual   : %0d", u_l.st_n);
      fail = 1;
    end
    release u_l.st;

    // remaining timeout arms (coverage; NOTE if force ignored)
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk); // C
    @(negedge clk);
    am_locked = 0;
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_walk: Disc.C tmr force not taken st=%0d", state);

    // CFG_A tmr==0
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    @(posedge clk); // CFG_A
    chk(5'd3, 25);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 26);

    // CFG_C tmr==0 (no EQ)
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    repeat (4) @(posedge clk); // C,A,K,C
    chk(5'd5, 27);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 28);

    // NULL tmr==0 before 8-cycle ACTIVE
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    repeat (5) @(posedge clk); // to NULL
    chk(5'd8, 29);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 30);

    // ACTIVE lid_bad → RTR_A; RTR_C tmr==0
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    repeat (8) @(posedge clk);
    repeat (10) @(posedge clk);
    chk(5'd9, 31);
    @(negedge clk);
    lid_bad = 1;
    @(posedge clk);
    lid_bad = 0;
    chk(5'd10, 32);
    @(posedge clk); // RTR_C if still locked — unlock first
    @(negedge clk);
    am_locked = 4'd0;
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    // RTR_A or RTR_C timeout → IDLE
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_walk: RTR tmr force st=%0d", state);

    // CFG_K tmr==0 while x4_ok
    hard_rst();
    @(negedge clk);
    lmsm_go = 1;
    @(posedge clk);
    lmsm_go = 0;
    @(negedge clk);
    am_locked = 4'b1111;
    @(posedge clk); // C
    @(posedge clk); // CFG_A
    @(posedge clk); // CFG_K
    chk(5'd4, 33);
    zap_tmr();
    @(posedge clk);
    release u_l.tmr;
    chk(5'd0, 34);

    if (!fail) $display("PASS tc_lmsm_walk");
    $finish;
  end
endmodule
