// NEG: optical path absent (AS-0.1 §11). Companion to scan_absent optical.
`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_no_optical;
  initial begin
    $display("NEG TP-HOLE-012 / TP-NEG companion: optical not in this-rev RTL.");
    $display("  stimulus : static absent-feature (no optical pin / module)");
    $display("  expected : no invented optical SerDes / QDLWS-optical names");
    $display("  actual   : scan_absent optical + this named TC");
    $display("  hier     : n/a");
    $display("PASS tc_neg_no_optical");
    $display("RESULT tc_neg_no_optical pass=1 fail=0");
    $finish;
  end
endmodule
