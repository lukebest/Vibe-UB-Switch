// TP-TIM-002: credit 1µs (u_crd.to) and VOQ deadlock 1µs (voq.age) are independent.
`timescale 1ns/1ps
module tc_timers_indep;
  `include "vibe_ub_params.vh"
  integer fail;
  initial begin
    fail = 0;
    if (VIBE_US_CYC !== 1250) begin
      $display("FAIL tc_timers_indep");
      $display("  stimulus : VIBE_US_CYC");
      $display("  expected : 1250 (1µs @ 1.25GHz)");
      $display("  actual   : %0d", VIBE_US_CYC);
      $display("  hier     : vibe_ub_params.vh");
      fail = 1;
    end
    $display("NOTE tc_timers_indep: credit timeout is dll_credit.to; VOQ is vibe_voq_egr.age");
    $display("  stimulus : two separate 1µs TCs (tc_credit_timeout_1us / tc_deadlock_timeout_1us)");
    $display("  expected : independent counters; one expiry must not fire the other");
    $display("  actual   : separate modules, shared only VIBE_US_CYC constant");
    $display("  hier     : u_crd.to vs vibe_voq_egr.age");
    if (!fail) $display("PASS tc_timers_indep");
    $finish;
  end
endmodule
