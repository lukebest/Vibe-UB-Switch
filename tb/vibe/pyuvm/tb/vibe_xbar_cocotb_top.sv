// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric 4-port crossbar (AS-0.1 §8). Output queued.
// Ingress RR on conflict. One full packet per grant (lock until
// EOP). Down ports get no data DLLDP. Mgmt bypass does not enter
// xbar. Candidate grant (out_data / out_sop / out_eop) is
// independent of out_ready; accept (out_vld / in_ready) still
// requires out_ready. Async-low rst_n clears lock / locked / rr.
// Instantiated by vibe_fabric u_xbar. Clock from entry_unit (2 ns).
// Flattened in_data_* / in_dst_* / out_data_* — cocotb cannot
// drive unpacked array ports. Instance u_u matches Decision-I
// leaf wrappers (tc_xbar_unit still uses flattened ports only).
// Icarus 12 VPI leaves 512-bit unpacked out_data X (stock
// tc_xbar_unit note); packed in_ready / out_vld / sop / eop
// and lock / locked / rr remain the Icarus-readable scorers.
`timescale 1ns/1ps

module vibe_xbar_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [3:0]   status_up,
  input  logic [3:0]   in_vld,
  input  logic [3:0]   in_sop,
  input  logic [3:0]   in_eop,
  input  logic [3:0]   out_ready,
  input  logic [511:0] in_data_0,
  input  logic [511:0] in_data_1,
  input  logic [511:0] in_data_2,
  input  logic [511:0] in_data_3,
  input  logic [1:0]   in_dst_0,
  input  logic [1:0]   in_dst_1,
  input  logic [1:0]   in_dst_2,
  input  logic [1:0]   in_dst_3,
  output logic [3:0]   in_ready,
  output logic [3:0]   out_vld,
  output logic [3:0]   out_sop,
  output logic [3:0]   out_eop,
  output logic [511:0] out_data_0,
  output logic [511:0] out_data_1,
  output logic [511:0] out_data_2,
  output logic [511:0] out_data_3
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
  vibe_xbar u_u (
    .clk(clk), .rst_n(rst_n), .status_up(status_up),
    .in_data(in_data), .in_vld(in_vld), .in_sop(in_sop), .in_eop(in_eop),
    .in_dst(in_dst), .in_ready(in_ready),
    .out_data(out_data), .out_vld(out_vld), .out_sop(out_sop), .out_eop(out_eop),
    .out_ready(out_ready)
  );
endmodule
