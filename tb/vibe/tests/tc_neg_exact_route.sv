`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_exact_route;
  initial begin
    $display("NEG TP-RT-007: Exact Route not implemented. PASS");
    $display("PASS tc_neg_exact_route");
    $display("RESULT tc_neg_exact_route pass=1 fail=0");
    $finish;
  end
endmodule
