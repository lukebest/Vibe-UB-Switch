// AS-0.1 §5 AMCTL / UB 2.0 §3.2.4.1: eBCH-16 codeword LUT (Table 3-5).
module vibe_ebch16 (
  input  logic [4:0]  cw_sel,
  output logic [15:0] cw
);
  always @* begin
    case (cw_sel)
      5'd0:  cw = 16'h0000;
      5'd1:  cw = 16'h0A6F;
      5'd2:  cw = 16'h14DD;
      5'd3:  cw = 16'h1EB2;
      5'd4:  cw = 16'h23D6;
      5'd5:  cw = 16'h29B9;
      5'd6:  cw = 16'h370B;
      5'd7:  cw = 16'h3D64;
      5'd8:  cw = 16'h47AC;
      5'd9:  cw = 16'h4DC3;
      5'd10: cw = 16'h5371;
      5'd11: cw = 16'h591E;
      5'd12: cw = 16'h647A;
      5'd13: cw = 16'h6E15;
      5'd14: cw = 16'h70A7;
      5'd15: cw = 16'h7AC8;
      5'd16: cw = 16'h8537;
      5'd17: cw = 16'h8F58;
      5'd18: cw = 16'h91EA;
      5'd19: cw = 16'h9B85;
      5'd20: cw = 16'hA6E1;
      5'd21: cw = 16'hAC8E;
      5'd22: cw = 16'hB23C;
      5'd23: cw = 16'hB853;
      5'd24: cw = 16'hC29B;
      5'd25: cw = 16'hC8F4;
      5'd26: cw = 16'hD646;
      5'd27: cw = 16'hDC29;
      5'd28: cw = 16'hE14D;
      5'd29: cw = 16'hEB22;
      5'd30: cw = 16'hF590;
      default: cw = 16'hFFFF;
    endcase
  end
endmodule
