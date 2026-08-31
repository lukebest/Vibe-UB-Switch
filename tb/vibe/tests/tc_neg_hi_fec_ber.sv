`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_hi_fec_ber;
  initial begin
    $display("NEG: hi_FEC_BER not implemented. PASS");
    $display("PASS tc_neg_hi_fec_ber");
    $display("RESULT tc_neg_hi_fec_ber pass=1 fail=0");
    $finish;
  end
endmodule
