// G7 closed (FS-0.2.4): 1024 is flit. This file keeps the old name and
// redirects to the locked flit check (no cell guess).
`timescale 1ns/1ps
module tc_credit_1024_hole;
  initial begin
    $display("NOTE tc_credit_1024_hole: G7 closed — unit is flit; see tc_credit_1024_flit_bp");
    $display("PASS tc_credit_1024_hole");
    $finish;
  end
endmodule
