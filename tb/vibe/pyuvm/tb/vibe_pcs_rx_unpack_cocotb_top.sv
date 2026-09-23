// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS RX unpack: strip AMCTL, 4×160 → 512b beats (AS-0.1 §6 inverse G2).
// Pairs with upcoming TX pack (5×512 ↔ 4×640). Clock from entry_unit (2 ns).
// TOPLEVEL am_gap has no default (tool rejects defaults on top inputs).
`timescale 1ns/1ps

module vibe_pcs_rx_unpack_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [159:0] lane0,
  input  logic [159:0] lane1,
  input  logic [159:0] lane2,
  input  logic [159:0] lane3,
  input  logic         lane_vld,
  input  logic         am0,
  input  logic         am1,
  input  logic         am2,
  input  logic         am3,
  input  logic         am_gap,
  output logic [511:0] beat_data,
  output logic         beat_vld,
  input  logic         beat_ready
);
  vibe_pcs_rx_unpack u_u (
    .clk(clk), .rst_n(rst_n),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3),
    .lane_vld(lane_vld), .am0(am0), .am1(am1), .am2(am2), .am3(am3),
    .am_gap(am_gap),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready)
  );
endmodule
