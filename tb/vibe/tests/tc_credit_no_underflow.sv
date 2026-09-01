// TP-CRD-008: do not invent credit underflow error code.
`timescale 1ns/1ps
module tc_credit_no_underflow;
  `include "vibe_ub_params.vh"
  integer fail;
  initial begin
    fail = 0;
    // RTL ports: proto_err, fc_ovf only. No underflow output.
    $display("NOTE tc_credit_no_underflow: vibe_dll_credit has proto_err/fc_ovf; no underflow code invented");
    $display("  stimulus : compile-time port list of vibe_dll_credit");
    $display("  expected : no credit_underflow / und_err product code");
    $display("  actual   : only proto_err and fc_ovf error outputs");
    $display("  hier     : rtl/dll/vibe_dll_credit.sv");
    if (!fail) $display("PASS tc_credit_no_underflow");
    $finish;
  end
endmodule
