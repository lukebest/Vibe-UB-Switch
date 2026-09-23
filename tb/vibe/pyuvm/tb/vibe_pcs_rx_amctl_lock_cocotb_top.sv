// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS RX AMCTL lock per lane (AS-0.1 §6 / §14).
// CONFIRM_N = UNLOCK_N = 3. Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_pcs_rx_amctl_lock_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  input  logic [159:0] in_data,
  output logic         locked,
  output logic [1:0]   lid,
  output logic         lid_bad,
  output logic         is_amctl,
  output logic         sdf,
  output logic         edf
);
  vibe_pcs_rx_amctl_lock u_l (
    .clk(clk), .rst_n(rst_n), .in_vld(in_vld), .in_data(in_data),
    .locked(locked), .lid(lid), .lid_bad(lid_bad),
    .is_amctl(is_amctl), .sdf(sdf), .edf(edf)
  );
endmodule
