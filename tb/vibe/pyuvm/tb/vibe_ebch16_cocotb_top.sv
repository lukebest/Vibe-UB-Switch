// Thin cocotb wrapper. DUT RTL never edited.
// Product eBCH-16 LUT (AS-0.1 §5 / UB 3.2.4.1 Table 3-5). Combo; no clock.
// Instance u_u matches Decision-I leaf wrappers. CHILDREN: none (leaf cell).
// ovf_l (F1) is not in this module. This is not vibe_pcs_scramble / tx / rx.
`timescale 1ns/1ps

module vibe_ebch16_cocotb_top (
  input  logic [4:0]  cw_sel,
  output logic [15:0] cw
);
  vibe_ebch16 u_u (
    .cw_sel(cw_sel),
    .cw(cw)
  );
endmodule
