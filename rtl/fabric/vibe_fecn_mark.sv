// AS-0.1 §8: if CCI.Mode is 3'b100 or 3'b010 and local congestion (VOQ occ >= FECN_WM)
// worse than packet mark, rewrite FECN and LoC. Else don't. Not CAQM.
module vibe_fecn_mark #(
  parameter int FECN_WM = 24
) (
  input  logic [15:0] cci_in,
  input  logic [5:0]  voq_occ,
  output logic [15:0] cci_out,
  output logic        marked
);
  wire [2:0] mode = cci_in[15:13];
  wire [1:0] fecn = cci_in[1:0];
  wire       cong = (voq_occ >= FECN_WM[5:0]);
  wire       markable_mode = (mode == 3'b100) || (mode == 3'b010);
  // 2'b00 unmarkable; 2'b10 none; 2'b01 light; 2'b11 severe
  wire [1:0] local_lvl = cong ? 2'b11 : 2'b10;
  wire       worse = cong && (fecn != 2'b00) && (local_lvl > fecn);

  assign marked  = markable_mode && worse;
  assign cci_out = marked ? {mode, 3'b000, /*LoC*/ 1'b0, cci_in[8:2], local_lvl} : cci_in;
endmodule
