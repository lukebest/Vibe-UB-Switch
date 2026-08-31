// eBCH-16 LUT used by AMCTL (Table 3-5 subset).
`timescale 1ns/1ps
module tc_ebch16_lut;
  logic [4:0] sel;
  logic [15:0] cw;
  integer fail;
  vibe_ebch16 u_e (.cw_sel(sel), .cw(cw));
  // Table 3-5 subset used by AMCTL (sel 0..30) plus default (31).
  logic [15:0] exp [0:31];
  integer i;
  initial begin
    fail = 0;
    exp[0]  = 16'h0000; exp[1]  = 16'h0A6F; exp[2]  = 16'h14DD; exp[3]  = 16'h1EB2;
    exp[4]  = 16'h23D6; exp[5]  = 16'h29B9; exp[6]  = 16'h370B; exp[7]  = 16'h3D64;
    exp[8]  = 16'h47AC; exp[9]  = 16'h4DC3; exp[10] = 16'h5371; exp[11] = 16'h591E;
    exp[12] = 16'h647A; exp[13] = 16'h6E15; exp[14] = 16'h70A7; exp[15] = 16'h7AC8;
    exp[16] = 16'h8537; exp[17] = 16'h8F58; exp[18] = 16'h91EA; exp[19] = 16'h9B85;
    exp[20] = 16'hA6E1; exp[21] = 16'hAC8E; exp[22] = 16'hB23C; exp[23] = 16'hB853;
    exp[24] = 16'hC29B; exp[25] = 16'hC8F4; exp[26] = 16'hD646; exp[27] = 16'hDC29;
    exp[28] = 16'hE14D; exp[29] = 16'hEB22; exp[30] = 16'hF590; exp[31] = 16'hFFFF;
    for (i = 0; i < 32; i = i + 1) begin
      sel = i[4:0];
      #1;
      if (cw !== exp[i]) begin
        $display("FAIL tc_ebch16_lut");
        $display("  stimulus : cw_sel=%0d", i);
        $display("  expected : %h", exp[i]);
        $display("  actual   : %h", cw);
        fail = 1;
      end
    end
    if (!fail) $display("PASS tc_ebch16_lut");
    $finish;
  end
endmodule
