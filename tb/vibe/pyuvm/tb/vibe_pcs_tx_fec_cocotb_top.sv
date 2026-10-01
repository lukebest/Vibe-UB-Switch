// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS TX FEC wrap: two-window RS(128,120) / bypass (AS-0.1 §5 T3).
// Instantiates stage-11 vibe_rs128_120_enc x2. Clock comes from entry_unit.
// Instance u_u matches Decision-I leaf wrappers.
// CHILDREN: u_enc_a / u_enc_b (vibe_rs128_120_enc).
// ovf_l (F1) is not in this module. This is not vibe_pcs_tx / rx.
`timescale 1ns/1ps

module vibe_pcs_tx_fec_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [2:0]   fec_mode,
  input  logic [959:0] win_data,
  input  logic         win_vld,
  output logic         win_ready,
  output logic [1023:0] cw_data,
  output logic         cw_vld,
  input  logic         cw_ready
);
  vibe_pcs_tx_fec u_u (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready),
    .cw_data(cw_data), .cw_vld(cw_vld), .cw_ready(cw_ready)
  );
endmodule
