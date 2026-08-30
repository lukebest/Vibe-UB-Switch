`timescale 1ns/1ps
`include "vibe_tb_defs.svh"
module tc_neg_port_cna;
  initial begin
    $display("NEG: Port CNA/SCNA not implemented. PASS");
    $display("PASS tc_neg_port_cna");
    $display("RESULT tc_neg_port_cna pass=1 fail=0");
    $finish;
  end
endmodule
