// FECN rewrite only if CCI.Mode 100/010 and local cong worse. Not CAQM.
`timescale 1ns/1ps
module tc_fecn_mark;
  logic [15:0] cci_in, cci_out;
  logic [5:0] voq_occ;
  logic marked;
  integer fail;
  vibe_fecn_mark #(.FECN_WM(24)) u_f (
    .cci_in(cci_in), .voq_occ(voq_occ), .cci_out(cci_out), .marked(marked)
  );
  initial begin
    fail = 0;
    cci_in = 16'd0; voq_occ = 6'd0;
    #1;
    if (marked) begin
      $display("FAIL tc_fecn_mark");
      $display("  stimulus : empty VOQ mode 0");
      $display("  expected : not marked");
      fail = 1;
    end
    // mode 3'b100, fecn light 01, occ>=24
    cci_in = {3'b100, 11'd0, 2'b01};
    voq_occ = 6'd24;
    #1;
    if (!marked) begin
      $display("FAIL tc_fecn_mark");
      $display("  stimulus : Mode=100 FECN=01 occ=24");
      $display("  expected : marked (local worse)");
      $display("  actual   : marked=0 cci_out=%h", cci_out);
      fail = 1;
    end
    if (!fail) $display("PASS tc_fecn_mark");
    $finish;
  end
endmodule
