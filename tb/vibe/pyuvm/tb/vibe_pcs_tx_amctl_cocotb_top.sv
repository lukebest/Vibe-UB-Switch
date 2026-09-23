// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS TX AMCTL 40-symbol eBCH-16 assemble (AS-0.1 §5).
// Clock from entry_unit (combo body does not sample clk / rst_n / sdf_period).
`timescale 1ns/1ps

module vibe_pcs_tx_amctl_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         sdf_period,
  input  logic [1:0]   lane_id,
  input  logic         req,
  output logic         ack,
  output logic [319:0] amctl_40B
);
  vibe_pcs_tx_amctl u_a (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .lane_id(lane_id), .req(req), .ack(ack), .amctl_40B(amctl_40B)
  );
endmodule
