// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric VL RR (AS-0.1 §8): RR among nonempty VOQs of an egress.
// FCFS within VL is the VOQ, not this leaf. No SL.
// On grant && valid advance rr to vl_sel+1. Reset clears rr.
// Clock from entry_unit (2 ns). Instantiated by vibe_fabric u_rr in g_egr.
// Decision-I wrap leaf `tc_vibe_vl_rr` / make vl_rr /
// make vl / make tc_vibe_vl_rr uses this top. Instance u_u
// matches Decision-I leaf wrappers (product instantiator is
// vibe_fabric u_rr in g_egr; stock Icarus tc_vl_rr /
// tc_vl_rr_0_15 use u_rr; not leftover u_rr / u_vl on this
// wrap). Second fabric leaf after stage-80 vibe_fecn_mark wrap.
// ovf_l (F1) is not in this module. This is not vibe_fecn_mark /
// vibe_nw_adapt / vibe_icrc / vibe_dll / vibe_bcrc / vibe_port /
// vibe_ub_switch.
// CHILDREN: none. Do not invent vibe_route_lu or later fabric leaves.
`timescale 1ns/1ps

module vibe_vl_rr_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [15:0] nonempty,
  input  logic        grant,
  output logic [3:0]  vl_sel,
  output logic        valid
);
  vibe_vl_rr u_u (
    .clk(clk), .rst_n(rst_n), .nonempty(nonempty),
    .grant(grant), .vl_sel(vl_sel), .valid(valid)
  );
endmodule
