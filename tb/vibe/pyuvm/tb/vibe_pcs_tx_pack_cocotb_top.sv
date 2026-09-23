// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS TX pack: 5×512 → 4×640 + AMCTL insert (AS-0.1 §5 T5 G2).
// Pairs with stage-15 RX unpack (4×640 → 5×512). Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_pcs_tx_pack_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         sdf_period,
  input  logic         afifo_afull,
  input  logic [511:0] beat_data,
  input  logic         beat_vld,
  output logic         beat_ready,
  output logic [159:0] lane0,
  output logic [159:0] lane1,
  output logic [159:0] lane2,
  output logic [159:0] lane3,
  output logic         lane_vld,
  input  logic         lane_ready,
  output logic         am_word
);
  vibe_pcs_tx_pack u_u (
    .clk(clk), .rst_n(rst_n),
    .sdf_period(sdf_period), .afifo_afull(afifo_afull),
    .beat_data(beat_data), .beat_vld(beat_vld), .beat_ready(beat_ready),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3),
    .lane_vld(lane_vld), .lane_ready(lane_ready), .am_word(am_word)
  );
endmodule
