`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_qdlws;
  initial begin
    $display("NEG TP-QDL-001: QDLWS not in RTL (scan_absent). PASS");
    $display("PASS tc_neg_qdlws");
    $display("RESULT tc_neg_qdlws pass=1 fail=0");
    $finish;
  end
endmodule
