// --cc LMSM arms that Icarus force-walks miss: Disc.C / EQ / RTR.
// 2-posedge sample (like tc_lmsm_idle_discovery). Deposit tmr=1 then let
// the RTL decrement to 0 (force-to-0 races the sequential reload).
// No Probe (AS-0.1 §11). Do not edit rtl/.
`timescale 1ns/1ps
module tc_lmsm_cc;
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
      @(posedge clk);
    end
  endtask

  // Sit in Disc.C with !x4_ok && !lid_bad (58 else).
  task automatic enter_disc_c_hold;
    begin
      go_disc();                 // Disc.A
      am_locked = 4'b1111;
      @(posedge clk);            // Disc.C
      @(negedge clk);
      am_locked = 4'b0111;       // not all_lock, not lid_bad → stay C
      @(posedge clk);
      @(posedge clk);
    end
  endtask

  // tmr=1 → next posedge decrements to 0 → following combo sees tmr==0.
  task automatic expire_tmr;
    begin
      @(negedge clk);
      force u_l.tmr = 27'd1;
`ifdef VERILATOR
      $c("u_l__DOT__tmr = 1;");
`endif
      @(posedge clk);
      release u_l.tmr;
      @(posedge clk); // tmr<=0 (stay in state)
      @(posedge clk); // tmr==0 arm taken
    end
  endtask

  task automatic to_active;
    begin
      go_disc();
      am_locked = 4'b1111;
      eq_negotiated = 0;
      repeat (5) @(posedge clk); // C,A,K,C,NULL
      repeat (12) @(posedge clk); // ACTIVE
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
    lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    // --- Disc.C stay (58 else) then tmr==0 (56) ---
    enter_disc_c_hold();
    if (state !== 5'd2) begin
      $display("FAIL tc_lmsm_cc");
      $display("  stimulus : Disc.C hold partial lock");
      $display("  expected : Disc.C (2)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    expire_tmr();
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: Disc.C tmr==0 → IDLE got %0d", state);

    // --- Disc.C lid_bad (58 if): arrive C, lid_bad same window ---
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    @(posedge clk); // Disc.C
    @(negedge clk);
    lid_bad = 1;    // x4_ok=0, lid_bad=1
    @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: Disc.C lid_bad → IDLE got %0d", state);
    lid_bad = 0;

    // --- CFG_C eq_negotiated (70): walk to CFG_C then raise eq ---
    hard_rst();
    go_disc();
    am_locked = 4'b1111;
    eq_negotiated = 0;
    @(posedge clk); // C
    @(posedge clk); // CFG_A
    @(posedge clk); // CFG_K
    @(posedge clk); // CFG_C
    @(negedge clk);
    eq_negotiated = 1;
    @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    if (state !== 5'd6)
      $display("NOTE tc_lmsm_cc: CFG_C eq → EQ_P got %0d", state);

    // --- EQ_P expire → EQ_A hold (75 else: tmr!=0) then expire ---
    expire_tmr(); // EQ_P tmr==0 → EQ_A, reloads 24ms
    @(posedge clk); // sit EQ_A with tmr!=0 (75 else)
    @(posedge clk);
    expire_tmr(); // EQ_A tmr==0 → NULL
    eq_negotiated = 0;

    // --- RTR_A stay (86 else) then tmr==0 (85) ---
    hard_rst();
    to_active();
    @(negedge clk);
    if (state !== 5'd9) begin
      $display("FAIL tc_lmsm_cc");
      $display("  stimulus : lock walk to ACTIVE");
      $display("  expected : 9");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    am_locked = 4'b0000;
    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    @(posedge clk); // RTR_A, !all_lock → stay (86 else)
    @(posedge clk);
    expire_tmr();   // 85
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: RTR_A tmr==0 → IDLE got %0d", state);

    // --- RTR_C stay then timeout (hits tmr_load RTR_*) ---
    hard_rst();
    to_active();
    retrain_req = 1;
    @(posedge clk);
    retrain_req = 0;
    @(posedge clk); // RTR_A, still locked → RTR_C next
    @(posedge clk);
    @(negedge clk);
    am_locked = 4'b0111; // !x4_ok
    @(posedge clk); // RTR_C stay
    expire_tmr();

    if (!fail) $display("PASS tc_lmsm_cc");
    $finish;
  end
endmodule
