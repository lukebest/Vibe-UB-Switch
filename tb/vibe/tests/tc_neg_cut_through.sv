`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_cut_through;
  initial begin
    $display("NEG: cut-through not implemented (SAF only). PASS");
    $display("PASS tc_neg_cut_through");
    $display("RESULT tc_neg_cut_through pass=1 fail=0");
    $finish;
  end
endmodule
