// eBCH-16 LUT used by AMCTL (Table 3-5 subset).
`timescale 1ns/1ps
module tc_ebch16_lut;
  logic [4:0] sel;
  logic [15:0] cw;
  integer fail;
  vibe_ebch16 u_e (.cw_sel(sel), .cw(cw));
  initial begin
    fail = 0;
    sel = 5'd0;
    #1;
    if (cw !== 16'h0000) begin
      $display("FAIL tc_ebch16_lut");
      $display("  stimulus : cw_sel=0");
      $display("  expected : 0000");
      $display("  actual   : %h", cw);
      fail = 1;
    end
    sel = 5'd1;
    #1;
    if (cw !== 16'h0A6F) begin
      $display("FAIL tc_ebch16_lut");
      $display("  stimulus : cw_sel=1");
      $display("  expected : 0A6F");
      $display("  actual   : %h", cw);
      fail = 1;
    end
    if (!fail) $display("PASS tc_ebch16_lut");
    $finish;
  end
endmodule
