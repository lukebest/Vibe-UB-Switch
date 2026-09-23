// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS RX FEC wrap: 2×512 → 960b unwrap / RS check (AS-0.1 §6).
// Inlines stage-12 Horner (not an instance). Clock from entry_unit (2 ns).
// TOPLEVEL am_gap has no default (tool rejects defaults on top inputs).
`timescale 1ns/1ps

module vibe_pcs_rx_fec_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [2:0]   fec_mode,
  input  logic [511:0] beat_data,
  input  logic         beat_vld,
  output logic         beat_ready,
  output logic [959:0] win_data,
  output logic         win_vld,
  input  logic         win_ready,
  input  logic         am_gap,
  output logic         fec_fail
);
  vibe_pcs_rx_fec u_u (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .am_gap(am_gap), .fec_fail(fec_fail)
  );
endmodule
