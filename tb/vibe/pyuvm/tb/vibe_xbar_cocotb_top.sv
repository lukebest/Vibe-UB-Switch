// Thin parameter / array wrapper. DUT RTL never edited.
`timescale 1ns/1ps

module vibe_xbar_cocotb_top (
  input  logic         clk, rst_n,
  input  logic [3:0]   status_up, in_vld, in_sop, in_eop, out_ready,
  input  logic [511:0] in_data_0, in_data_1, in_data_2, in_data_3,
  input  logic [1:0]   in_dst_0, in_dst_1, in_dst_2, in_dst_3,
  output logic [3:0]   in_ready, out_vld, out_sop, out_eop,
  output logic [511:0] out_data_0, out_data_1, out_data_2, out_data_3
);
  logic [511:0] in_data [0:3];
  logic [511:0] out_data [0:3];
  logic [1:0]   in_dst [0:3];
  assign in_data[0] = in_data_0;
  assign in_data[1] = in_data_1;
  assign in_data[2] = in_data_2;
  assign in_data[3] = in_data_3;
  assign in_dst[0] = in_dst_0;
  assign in_dst[1] = in_dst_1;
  assign in_dst[2] = in_dst_2;
  assign in_dst[3] = in_dst_3;
  assign out_data_0 = out_data[0];
  assign out_data_1 = out_data[1];
  assign out_data_2 = out_data[2];
  assign out_data_3 = out_data[3];
  vibe_xbar u (
    .clk(clk), .rst_n(rst_n), .status_up(status_up),
    .in_data(in_data), .in_vld(in_vld), .in_sop(in_sop), .in_eop(in_eop),
    .in_dst(in_dst), .in_ready(in_ready),
    .out_data(out_data), .out_vld(out_vld), .out_sop(out_sop), .out_eop(out_eop),
    .out_ready(out_ready)
  );
endmodule
