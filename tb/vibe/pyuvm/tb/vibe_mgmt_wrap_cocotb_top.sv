// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm tc_mgmt scores vibe_mgmt as a direct top.
// Decision-I wrap leaf `tc_vibe_mgmt` / make mgmt_wrap uses this top.
// Flattened fab_mgmt_cfg6_data_* / mgmt_nw_data_* — cocotb cannot
// drive unpacked array ports. Official CFG6 opcode 0x10 / Appendix D
// packing is 未知; this wrapper does not invent it. F1 ovf_l lives
// in vibe_port (do not ECO). Does not steal make top / wrap / port / top_wrap.
`timescale 1ns/1ps

module vibe_mgmt_wrap_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         cfg_wr_vld,
  output logic         cfg_wr_ready,
  input  logic [3:0]   cfg_wr_cmd,
  input  logic [15:0]  cfg_wr_idx,
  input  logic [31:0]  cfg_wr_data,
  output logic [15:0]  cna,
  output logic         cna_written,
  output logic [3:0]   default_bm,
  output logic         rt_wr_en,
  output logic [15:0]  rt_wr_idx,
  output logic [31:0]  rt_wr_data,
  output logic [3:0]   port_rst,
  output logic         device_rst,
  output logic [3:0]   lmsm_go,
  input  logic [3:0]   fab_mgmt_cfg6_hit,
  input  logic [511:0] fab_mgmt_cfg6_data_0,
  input  logic [511:0] fab_mgmt_cfg6_data_1,
  input  logic [511:0] fab_mgmt_cfg6_data_2,
  input  logic [511:0] fab_mgmt_cfg6_data_3,
  output logic [3:0]   mgmt_fab_cfg6_consume,
  output logic [511:0] mgmt_nw_data_0,
  output logic [511:0] mgmt_nw_data_1,
  output logic [511:0] mgmt_nw_data_2,
  output logic [511:0] mgmt_nw_data_3,
  output logic [3:0]   mgmt_nw_vld,
  input  logic [3:0]   mgmt_nw_ready,
  input  logic [3:0]   rx_ovf,
  input  logic [3:0]   fc_ovf,
  input  logic [3:0]   proto_err,
  input  logic [3:0]   retry_error,
  input  logic [3:0]   len_err,
  input  logic [3:0]   deadlock_drop,
  input  logic         drop_g1,
  input  logic [3:0]   afifo_ovf,
  output logic         irq_logic
);
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  logic [511:0] mgmt_nw_data [0:3];
  assign fab_mgmt_cfg6_data[0] = fab_mgmt_cfg6_data_0;
  assign fab_mgmt_cfg6_data[1] = fab_mgmt_cfg6_data_1;
  assign fab_mgmt_cfg6_data[2] = fab_mgmt_cfg6_data_2;
  assign fab_mgmt_cfg6_data[3] = fab_mgmt_cfg6_data_3;
  assign mgmt_nw_data_0 = mgmt_nw_data[0];
  assign mgmt_nw_data_1 = mgmt_nw_data[1];
  assign mgmt_nw_data_2 = mgmt_nw_data[2];
  assign mgmt_nw_data_3 = mgmt_nw_data[3];
  vibe_mgmt u_m (
    .clk(clk), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit),
    .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data),
    .mgmt_fab_cfg6_consume(mgmt_fab_cfg6_consume),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld),
    .mgmt_nw_ready(mgmt_nw_ready),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .len_err(len_err),
    .deadlock_drop(deadlock_drop), .drop_g1(drop_g1), .afifo_ovf(afifo_ovf),
    .irq_logic(irq_logic)
  );
endmodule
