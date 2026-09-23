// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS RX AMCTL deskew (AS-0.1 §6). Factory physical=logical (U24).
// Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_pcs_rx_deskew_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [159:0] in0,
  input  logic [159:0] in1,
  input  logic [159:0] in2,
  input  logic [159:0] in3,
  input  logic         in_vld,
  input  logic         am0,
  input  logic         am1,
  input  logic         am2,
  input  logic         am3,
  output logic [159:0] out0,
  output logic [159:0] out1,
  output logic [159:0] out2,
  output logic [159:0] out3,
  output logic         out_vld,
  output logic         aligned
);
  vibe_pcs_rx_deskew u_dsk (
    .clk(clk), .rst_n(rst_n),
    .in0(in0), .in1(in1), .in2(in2), .in3(in3), .in_vld(in_vld),
    .am0(am0), .am1(am1), .am2(am2), .am3(am3),
    .out0(out0), .out1(out1), .out2(out2), .out3(out3),
    .out_vld(out_vld), .aligned(aligned)
  );
endmodule
