// Thin cocotb wrapper. DUT RTL never edited.
// Product RS(128,120) syndrome-check decoder, GF(256) (AS-0.1 §6).
// Clock from entry_unit (2 ns). Include path: rtl/common (vibe_ub_fn.vh).
`timescale 1ns/1ps

module vibe_rs128_120_dec_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_sym,
  output logic         in_ready,
  output logic         done,
  output logic         fec_fail,
  output logic [959:0] data_out
);
  vibe_rs128_120_dec u_dec (
    .clk(clk), .rst_n(rst_n), .start(start),
    .in_vld(in_vld), .in_sym(in_sym), .in_ready(in_ready),
    .done(done), .fec_fail(fec_fail), .data_out(data_out)
  );
endmodule
