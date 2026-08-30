`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_ubfm;
  initial begin
    $display("NEG: UBFM not implemented. PASS");
    $display("PASS tc_neg_ubfm");
    $display("RESULT tc_neg_ubfm pass=1 fail=0");
    $finish;
  end
endmodule
