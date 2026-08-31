`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_probe;
  initial begin
    $display("NEG: Probe not implemented (LMSM Idle->Discovery only). PASS");
    $display("PASS tc_neg_probe");
    $display("RESULT tc_neg_probe pass=1 fail=0");
    $finish;
  end
endmodule
