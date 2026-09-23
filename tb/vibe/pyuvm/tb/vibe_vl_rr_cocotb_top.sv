// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric VL RR (AS-0.1 §8): RR among nonempty VOQs of an egress.
// FCFS within VL is the VOQ, not this leaf. No SL.
// On grant && valid advance rr to vl_sel+1. Reset clears rr.
// Clock from entry_unit (2 ns). Instantiated by vibe_fabric u_rr in g_egr.
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
