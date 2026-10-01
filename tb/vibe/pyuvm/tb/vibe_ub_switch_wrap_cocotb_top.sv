// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm tc_top_smoke scores product-pin PMA+peer on vibe_switch_cocotb_top.
// Decision-I wrap leaf `tc_vibe_ub_switch` / make top_wrap uses this top.
`timescale 1ns/1ps

module vibe_ub_switch_wrap_cocotb_top (
  input  logic         clk_fab,
  input  logic         rst_n,
  input  logic         txclk_0,
  input  logic         txclk_1,
  input  logic         txclk_2,
  input  logic         txclk_3,
  input  logic         rxclk_0,
  input  logic         rxclk_1,
  input  logic         rxclk_2,
  input  logic         rxclk_3,
  output logic [511:0] pcs_pma_txdata_0,
  output logic [511:0] pcs_pma_txdata_1,
  output logic [511:0] pcs_pma_txdata_2,
  output logic [511:0] pcs_pma_txdata_3,
  input  logic [511:0] pma_pcs_rxdata_0,
  input  logic [511:0] pma_pcs_rxdata_1,
  input  logic [511:0] pma_pcs_rxdata_2,
  input  logic [511:0] pma_pcs_rxdata_3,
  input  logic         cfg_wr_vld,
  output logic         cfg_wr_ready,
  input  logic [3:0]   cfg_wr_cmd,
  input  logic [15:0]  cfg_wr_idx,
  input  logic [31:0]  cfg_wr_data,
  output logic         irq_logic
);
  vibe_ub_switch u_sw (
    .clk_fab(clk_fab), .rst_n(rst_n),
    .txclk_0(txclk_0), .txclk_1(txclk_1), .txclk_2(txclk_2), .txclk_3(txclk_3),
    .rxclk_0(rxclk_0), .rxclk_1(rxclk_1), .rxclk_2(rxclk_2), .rxclk_3(rxclk_3),
    .pcs_pma_txdata_0(pcs_pma_txdata_0), .pcs_pma_txdata_1(pcs_pma_txdata_1),
    .pcs_pma_txdata_2(pcs_pma_txdata_2), .pcs_pma_txdata_3(pcs_pma_txdata_3),
    .pma_pcs_rxdata_0(pma_pcs_rxdata_0), .pma_pcs_rxdata_1(pma_pcs_rxdata_1),
    .pma_pcs_rxdata_2(pma_pcs_rxdata_2), .pma_pcs_rxdata_3(pma_pcs_rxdata_3),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .irq_logic(irq_logic)
  );
endmodule
