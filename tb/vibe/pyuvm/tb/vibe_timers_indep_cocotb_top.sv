// Thin wrapper: credit + VOQ share clk so their 1 µs timers can be scored independently.
// DUT RTL never edited.
`timescale 1ns/1ps

module vibe_timers_indep_cocotb_top (
  input  logic         clk, rst_n, port_rst, link_up,
  input  logic         consume_vld, is_cfg0, credit_ret,
  input  logic [7:0]   grain_n,
  input  logic [9:0]   consume_flits,
  input  logic [15:0]  credit_ret_n,
  output logic [15:0]  pending,
  output logic         credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf,
  input  logic         wr_en, wr_sop, wr_eop, rd_en,
  input  logic [3:0]   wr_vl, rd_vl,
  input  logic [511:0] wr_data,
  output logic         wr_ready, rd_sop, rd_eop,
  output logic [511:0] rd_data,
  output logic [15:0]  nonempty,
  output logic [5:0]   occ_vl0,
  output logic         deadlock_drop,
  output logic [31:0]  deadlock_cnt
);
  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(grain_n), .consume_vld(consume_vld), .consume_flits(consume_flits),
    .is_cfg0(is_cfg0), .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );
  vibe_voq_egr #(.DEPTH(32)) u_v (
    .clk(clk), .rst_n(rst_n),
    .wr_vl(wr_vl), .wr_en(wr_en), .wr_data(wr_data),
    .wr_sop(wr_sop), .wr_eop(wr_eop), .wr_ready(wr_ready),
    .rd_vl(rd_vl), .rd_en(rd_en), .rd_data(rd_data), .rd_sop(rd_sop), .rd_eop(rd_eop),
    .nonempty(nonempty), .occ_vl0(occ_vl0),
    .deadlock_drop(deadlock_drop), .deadlock_cnt(deadlock_cnt)
  );
endmodule
