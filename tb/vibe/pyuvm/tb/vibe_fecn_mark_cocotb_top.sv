// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric FECN mark (AS-0.1 §8): combo; no clock.
// Mode 100/010 + local cong (voq_occ >= FECN_WM, default 24)
// worse than packet FECN → rewrite FECN and LoC. Else pass-through.
// Not CAQM. Instantiated by vibe_fabric u_fecn.
// Decision-I wrap leaf `tc_vibe_fecn_mark` / make fecn_mark /
// make fecn / make tc_vibe_fecn_mark uses this top. Instance u_u
// matches Decision-I leaf wrappers (product instantiator is
// vibe_fabric u_fecn; stock Icarus tc_fecn_mark uses u_f; not
// leftover u_fecn / u_f on this wrap). First fabric leaf after
// NW tip-align wave complete (stage-79 vibe_nw_adapt wrap).
// ovf_l (F1) is not in this module. This is not vibe_nw_adapt /
// vibe_icrc / vibe_dll / vibe_bcrc / vibe_port / vibe_ub_switch.
// CHILDREN: none. Do not invent vibe_vl_rr or later fabric leaves.
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
