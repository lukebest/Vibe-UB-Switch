// Thin cocotb wrapper. DUT RTL never edited.
// Product TX 160→128 residue gearbox (AS-0.1 §5 T7).
// Clock comes from entry_unit. Instance u_u matches Decision-I
// leaf wrappers. CHILDREN: none (leaf cell).
// ovf_l (F1) is not in this module. This is not vibe_gear_128_160.
`timescale 1ns/1ps

module vibe_gear_160_128_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  output logic         in_ready,
  input  logic [159:0] in_data,
  output logic         out_vld,
  input  logic         out_ready,
  output logic [127:0] out_data
);
  vibe_gear_160_128 u_u (
    .clk(clk), .rst_n(rst_n), .in_vld(in_vld), .in_ready(in_ready),
    .in_data(in_data), .out_vld(out_vld), .out_ready(out_ready),
    .out_data(out_data)
  );
endmodule
