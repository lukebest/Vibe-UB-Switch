// Thin cocotb wrapper. DUT RTL never edited.
// Product PCS LTB/DLL scramble (AS-0.1 §5 / UB 3.2.2.4). Clock from entry_unit.
`timescale 1ns/1ps

module vibe_pcs_scramble_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [1:0]   lane_id,
  input  logic         seed_load,
  input  logic         en,
  input  logic         in_vld,
  input  logic [159:0] in_data,
  output logic         out_vld,
  output logic [159:0] out_data
);
  vibe_pcs_scramble u_scr (
    .clk(clk), .rst_n(rst_n), .lane_id(lane_id), .seed_load(seed_load),
    .en(en), .in_vld(in_vld), .in_data(in_data),
    .out_vld(out_vld), .out_data(out_data)
  );
endmodule
