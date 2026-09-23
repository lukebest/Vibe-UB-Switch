// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS TX 1024→2×512 split (AS-0.1 §5 T4). Clock from entry_unit.
`timescale 1ns/1ps

module vibe_pcs_tx_cw2beat_cocotb_top (
  input  logic          clk,
  input  logic          rst_n,
  input  logic [1023:0] cw_data,
  input  logic          cw_vld,
  output logic          cw_ready,
  output logic [511:0]  beat_data,
  output logic          beat_vld,
  input  logic          beat_ready
);
  vibe_pcs_tx_cw2beat u_cw (
    .clk(clk), .rst_n(rst_n), .cw_data(cw_data), .cw_vld(cw_vld),
    .cw_ready(cw_ready), .beat_data(beat_data), .beat_vld(beat_vld),
    .beat_ready(beat_ready)
  );
endmodule
