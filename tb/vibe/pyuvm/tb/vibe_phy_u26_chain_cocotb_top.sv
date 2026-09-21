// Thin structural top for tc_phy_u26_chain (three default-param DUTs).
// Same instances/pins as tb/vibe/tests/tc_phy_u26_chain.sv. TB-only.
`timescale 1ns/1ps

module vibe_phy_u26_chain_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         txclk,
  input  logic         rxclk,
  input  logic         g1_iv,
  output logic         g1_ir,
  input  logic [159:0] g1_id,
  output logic         g1_ov,
  input  logic         g1_or,
  output logic [127:0] g1_od,
  input  logic         g2_iv,
  output logic         g2_ir,
  input  logic [127:0] g2_id,
  output logic         g2_ov,
  input  logic         g2_or,
  output logic [159:0] g2_od,
  input  logic [127:0] t0,
  input  logic [127:0] t1,
  input  logic [127:0] t2,
  input  logic [127:0] t3,
  input  logic         tvl,
  output logic [511:0] pcs_pma_txdata,
  input  logic [511:0] pma_pcs_rxdata,
  output logic [127:0] r0,
  output logic [127:0] r1,
  output logic [127:0] r2,
  output logic [127:0] r3,
  output logic         rvl
);
  vibe_gear_160_128 u_txg (
    .clk(clk), .rst_n(rst_n), .in_vld(g1_iv), .in_ready(g1_ir),
    .in_data(g1_id), .out_vld(g1_ov), .out_ready(g1_or), .out_data(g1_od)
  );
  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk),
    .txrst_n(1'b1), .rxrst_n(1'b1),
    .afifo_pma_lane0(t0), .afifo_pma_lane1(t1),
    .afifo_pma_lane2(t2), .afifo_pma_lane3(t3),
    .afifo_pma_lane_vld(tvl), .pcs_pma_txdata(pcs_pma_txdata),
    .pma_pcs_rxdata(pma_pcs_rxdata),
    .pma_afifo_lane0(r0), .pma_afifo_lane1(r1),
    .pma_afifo_lane2(r2), .pma_afifo_lane3(r3),
    .pma_afifo_lane_vld(rvl)
  );
  vibe_gear_128_160 u_rxg (
    .clk(clk), .rst_n(rst_n), .in_vld(g2_iv), .in_ready(g2_ir),
    .in_data(g2_id), .out_vld(g2_ov), .out_ready(g2_or), .out_data(g2_od)
  );
endmodule
