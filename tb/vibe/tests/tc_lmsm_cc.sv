// --cc LMSM arms that Icarus force-walks miss: Disc.C / EQ / RTR.
// Park via force st+tmr (--public-flat-rw). Verilator 5.020 keeps stale
// st_n if inputs change on the negedge after a 1-cycle state.
// force must not use automatic task args (Icarus). Deposit tmr=1 then
// RTL decrement (force-to-0 races tmr_load). No Probe. Do not edit rtl/.
`timescale 1ns/1ps
module tc_lmsm_cc;
  logic clk, rst_n, port_rst, lmsm_go, lid_bad, lane0_fail, eq_negotiated, retrain_req;
  logic [3:0] am_locked;
  logic link_up, link_ready, sdf_period, width_fail;
  logic [4:0] state;
  logic [4:0] park_s;
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

  task park_do;
    begin
      @(negedge clk);
      force u_l.st  = park_s;
      force u_l.tmr = 27'd8;
      @(posedge clk);
      release u_l.st;
      release u_l.tmr;
      @(posedge clk);
    end
  endtask

  task expire_tmr;
    begin
      @(negedge clk);
      force u_l.tmr = 27'd1;
      @(posedge clk);
      release u_l.tmr;
      @(posedge clk);
      @(posedge clk);
    end
  endtask

  // 1-cycle states (CFG_C + eq=0 → NULL) cannot sit until tmr expires.
  // Force tmr=0 in the same window as st so combo takes the timeout arm.
  task park_tmr0;
    begin
      @(negedge clk);
      force u_l.st  = park_s;
      force u_l.tmr = 27'd0;
      @(posedge clk);
      release u_l.st;
      release u_l.tmr;
      @(posedge clk);
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; lmsm_go = 0; am_locked = 0;
    lid_bad = 0; lane0_fail = 0; eq_negotiated = 0; retrain_req = 0;
    park_s = 0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    // Disc.C stay (58 else) then tmr==0 (56)
    am_locked = 4'b0111;
    lid_bad = 0;
    park_s = 5'd2;
    park_do();
    @(negedge clk);
    if (state !== 5'd2) begin
      $display("FAIL tc_lmsm_cc");
      $display("  stimulus : park Disc.C partial lock");
      $display("  expected : 2");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    expire_tmr();
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: Disc.C tmr==0 → IDLE got %0d", state);

    // Disc.C lid_bad (58 if)
    am_locked = 4'b0111;
    lid_bad = 1;
    park_s = 5'd2;
    park_do();
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: Disc.C lid_bad → IDLE got %0d", state);
    lid_bad = 0;

    // CFG_C tmr==0 (70) with eq=0. CFG_C is 1-cycle if tmr!=0 (!eq → NULL).
    am_locked = 4'b1111;
    eq_negotiated = 0;
    park_s = 5'd5;
    park_tmr0();

    // CFG_C eq_negotiated (71)
    eq_negotiated = 1;
    park_s = 5'd5;
    park_do();
    @(negedge clk);
    if (state !== 5'd6)
      $display("NOTE tc_lmsm_cc: CFG_C eq → EQ_P got %0d", state);

    // EQ_P hold / expire → EQ_A hold (75 else) / expire
    if (state !== 5'd6) begin
      park_s = 5'd6;
      park_do();
    end
    @(posedge clk);
    @(posedge clk);
    expire_tmr();
    @(posedge clk);
    @(posedge clk);
    expire_tmr();
    eq_negotiated = 0;

    // RTR_A stay (86 else) then tmr==0 (85)
    am_locked = 4'b0000;
    park_s = 5'd10;
    park_do();
    @(negedge clk);
    if (state !== 5'd10)
      $display("NOTE tc_lmsm_cc: park RTR_A got %0d", state);
    @(posedge clk);
    @(posedge clk);
    expire_tmr();
    @(negedge clk);
    if (state !== 5'd0)
      $display("NOTE tc_lmsm_cc: RTR_A tmr==0 → IDLE got %0d", state);

    // RTR_C stay then timeout
    am_locked = 4'b0111;
    park_s = 5'd11;
    park_do();
    @(posedge clk);
    expire_tmr();

    if (!fail) $display("PASS tc_lmsm_cc");
    $finish;
  end
endmodule
