// Thin parameter / array wrapper. DUT RTL never edited.
`timescale 1ns/1ps

module vibe_cna_ep_cocotb_top (
  input  logic         clk, rst_n, cna_written,
  input  logic [15:0]  cna,
  input  logic [3:0]   fab_mgmt_cfg6_hit, mgmt_nw_ready,
  input  logic [511:0] fab_mgmt_cfg6_data_0, fab_mgmt_cfg6_data_1,
                       fab_mgmt_cfg6_data_2, fab_mgmt_cfg6_data_3,
  output logic [3:0]   consume, mgmt_nw_vld,
  output logic         icrc_fail
);
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  logic [511:0] mgmt_nw_data [0:3];
  assign fab_mgmt_cfg6_data[0] = fab_mgmt_cfg6_data_0;
  assign fab_mgmt_cfg6_data[1] = fab_mgmt_cfg6_data_1;
  assign fab_mgmt_cfg6_data[2] = fab_mgmt_cfg6_data_2;
  assign fab_mgmt_cfg6_data[3] = fab_mgmt_cfg6_data_3;
  vibe_cna_ep u (
    .clk(clk), .rst_n(rst_n), .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data),
    .mgmt_fab_cfg6_consume(consume), .mgmt_nw_data(mgmt_nw_data),
    .mgmt_nw_vld(mgmt_nw_vld), .mgmt_nw_ready(mgmt_nw_ready), .icrc_fail(icrc_fail)
  );
endmodule
