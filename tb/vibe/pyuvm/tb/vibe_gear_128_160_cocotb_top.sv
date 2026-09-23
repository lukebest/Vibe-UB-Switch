// Thin cocotb wrapper. DUT RTL never edited.
// Product RX 128→160 dual-residue gearbox. Clock comes from entry_unit.
`timescale 1ns/1ps

module vibe_gear_128_160_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  output logic         in_ready,
  input  logic [127:0] in_data,
  output logic         out_vld,
  input  logic         out_ready,
  output logic [159:0] out_data
);
  vibe_gear_128_160 u_gear (
    .clk(clk), .rst_n(rst_n), .in_vld(in_vld), .in_ready(in_ready),
    .in_data(in_data), .out_vld(out_vld), .out_ready(out_ready),
    .out_data(out_data)
  );
endmodule
