// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm fabric suite scores vibe_fab_cocotb_top + vibe_mgmt.
// Decision-I wrap leaf `tc_vibe_fabric` / make fabric_wrap uses this top.
// Flattened nw_fab_data_* / fab_nw_data_* / fab_mgmt_cfg6_data_* —
// cocotb cannot drive unpacked array ports. Official CFG6 opcode 0x10 /
// Appendix D packing is 未知; this wrapper does not invent it. F1 ovf_l
// lives in vibe_port (do not ECO). Does not steal make top / wrap / port /
// top_wrap / mgmt_wrap.
`timescale 1ns/1ps

module vibe_fabric_wrap_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         device_rst,
  input  logic [3:0]   status_up,
  input  logic [3:0]   default_bm,
  input  logic         rt_wr_en,
  input  logic [15:0]  rt_wr_idx,
  input  logic [31:0]  rt_wr_data,
  input  logic [511:0] nw_fab_data_0,
  input  logic [511:0] nw_fab_data_1,
  input  logic [511:0] nw_fab_data_2,
  input  logic [511:0] nw_fab_data_3,
  input  logic [3:0]   nw_fab_vld,
  output logic [3:0]   nw_fab_ready,
  output logic [511:0] fab_nw_data_0,
  output logic [511:0] fab_nw_data_1,
  output logic [511:0] fab_nw_data_2,
  output logic [511:0] fab_nw_data_3,
  output logic [3:0]   fab_nw_vld,
  input  logic [3:0]   fab_nw_ready,
  output logic [3:0]   len_err,
  output logic         drop_g1,
  output logic [31:0]  rt_shortest_unimpl,
  output logic [31:0]  drop_down_cnt,
  output logic [3:0]   deadlock_drop,
  output logic         irq_rt,
  input  logic [15:0]  cna,
  input  logic         cna_written,
  output logic [3:0]   fab_mgmt_cfg6_hit,
  output logic [511:0] fab_mgmt_cfg6_data_0,
  output logic [511:0] fab_mgmt_cfg6_data_1,
  output logic [511:0] fab_mgmt_cfg6_data_2,
  output logic [511:0] fab_mgmt_cfg6_data_3
);
  logic [511:0] nw_fab_data [0:3];
  logic [511:0] fab_nw_data [0:3];
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  assign nw_fab_data[0] = nw_fab_data_0;
  assign nw_fab_data[1] = nw_fab_data_1;
  assign nw_fab_data[2] = nw_fab_data_2;
  assign nw_fab_data[3] = nw_fab_data_3;
  assign fab_nw_data_0 = fab_nw_data[0];
  assign fab_nw_data_1 = fab_nw_data[1];
  assign fab_nw_data_2 = fab_nw_data[2];
  assign fab_nw_data_3 = fab_nw_data[3];
  assign fab_mgmt_cfg6_data_0 = fab_mgmt_cfg6_data[0];
  assign fab_mgmt_cfg6_data_1 = fab_mgmt_cfg6_data[1];
  assign fab_mgmt_cfg6_data_2 = fab_mgmt_cfg6_data[2];
  assign fab_mgmt_cfg6_data_3 = fab_mgmt_cfg6_data[3];
  vibe_fabric u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld),
    .nw_fab_ready(nw_fab_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld),
    .fab_nw_ready(fab_nw_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down_cnt),
    .deadlock_drop(deadlock_drop), .irq_rt(irq_rt),
    .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit),
    .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data)
  );
endmodule
