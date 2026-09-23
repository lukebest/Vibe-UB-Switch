// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS TX G1: 640b=4 flits → 6-flit / 960b FEC window + Null fill
// (AS-0.1 §5 T2). Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_pcs_tx_g1_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic [639:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [959:0] win_data,
  output logic         win_vld,
  input  logic         win_ready
);
  vibe_pcs_tx_g1 u_u (
    .clk(clk), .rst_n(rst_n), .link_up(link_up),
    .in_data(in_data), .in_vld(in_vld), .in_ready(in_ready),
    .win_data(win_data), .win_vld(win_vld), .win_ready(win_ready)
  );
endmodule
