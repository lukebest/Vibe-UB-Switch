// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL credit / backpressure / 1us timeout (AS-0.1 §12 / FS-0.2.6).
// Consume ceil(DLLDP_flits/n); pending is cells; thresh 1024 → bp_nw.
// Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_credit_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        port_rst,
  input  logic        link_up,
  input  logic [7:0]  grain_n,
  input  logic        consume_vld,
  input  logic [9:0]  consume_flits,
  input  logic        is_cfg0,
  input  logic        credit_ret,
  input  logic [15:0] credit_ret_n,
  output logic [15:0] pending,
  output logic        credit_low,
  output logic        force_crd_ack,
  output logic        bp_nw,
  output logic        proto_err,
  output logic        fc_ovf
);
  vibe_dll_credit u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(grain_n),
    .consume_vld(consume_vld), .consume_flits(consume_flits), .is_cfg0(is_cfg0),
    .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );
endmodule
