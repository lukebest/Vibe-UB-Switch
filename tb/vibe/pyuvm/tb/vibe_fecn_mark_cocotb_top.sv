// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric FECN mark (AS-0.1 §8): combo; no clock.
// Mode 100/010 + local cong (voq_occ >= FECN_WM, default 24)
// worse than packet FECN → rewrite FECN and LoC. Else pass-through.
// Not CAQM. Instantiated by vibe_fabric u_fecn.
`timescale 1ns/1ps

module vibe_fecn_mark_cocotb_top (
  input  logic [15:0] cci_in,
  input  logic [5:0]  voq_occ,
  output logic [15:0] cci_out,
  output logic        marked
);
  vibe_fecn_mark u_u (
    .cci_in(cci_in), .voq_occ(voq_occ),
    .cci_out(cci_out), .marked(marked)
  );
endmodule
