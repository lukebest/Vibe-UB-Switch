// Product-pin UVM top: vibe_ub_switch (AS-0.1 §18).
`timescale 1ns/1ps

module vibe_switch_tb_top;
  import uvm_pkg::*;
  import vibe_uvm_pkg::*;
  `include "uvm_macros.svh"

  vibe_clk_rst_if clk_if();
  wire clk_fab = clk_if.clk;
  wire rst_n   = clk_if.rst_n;

  logic txclk_0, txclk_1, txclk_2, txclk_3;
  initial begin
    txclk_0 = 0; txclk_1 = 0; txclk_2 = 0; txclk_3 = 0;
  end
  always #2 txclk_0 = ~txclk_0;
  always #2 txclk_1 = ~txclk_1;
  always #2 txclk_2 = ~txclk_2;
  always #2 txclk_3 = ~txclk_3;

  vibe_cfg_if cfg_if (clk_fab, rst_n);
  vibe_pma_if pma0 (txclk_0, txclk_0);
  vibe_pma_if pma1 (txclk_1, txclk_1);
  vibe_pma_if pma2 (txclk_2, txclk_2);
  vibe_pma_if pma3 (txclk_3, txclk_3);

  initial clk_if.rst_n = 1'b0;

  vibe_ub_switch dut (
    .clk_fab(clk_fab), .rst_n(rst_n),
    .txclk_0(txclk_0), .txclk_1(txclk_1), .txclk_2(txclk_2), .txclk_3(txclk_3),
    .rxclk_0(txclk_0), .rxclk_1(txclk_1), .rxclk_2(txclk_2), .rxclk_3(txclk_3),
    .pcs_pma_txdata_0(pma0.pcs_pma_txdata), .pcs_pma_txdata_1(pma1.pcs_pma_txdata),
    .pcs_pma_txdata_2(pma2.pcs_pma_txdata), .pcs_pma_txdata_3(pma3.pcs_pma_txdata),
    .pma_pcs_rxdata_0(pma0.pma_pcs_rxdata), .pma_pcs_rxdata_1(pma1.pma_pcs_rxdata),
    .pma_pcs_rxdata_2(pma2.pma_pcs_rxdata), .pma_pcs_rxdata_3(pma3.pma_pcs_rxdata),
    .cfg_wr_vld(cfg_if.vld), .cfg_wr_ready(cfg_if.ready),
    .cfg_wr_cmd(cfg_if.cmd), .cfg_wr_idx(cfg_if.idx), .cfg_wr_data(cfg_if.data),
    .irq_logic(cfg_if.irq_logic)
  );

  initial begin
    cfg_if.idle();
    pma0.idle_rx(); pma1.idle_rx(); pma2.idle_rx(); pma3.idle_rx();
    uvm_config_db#(virtual vibe_clk_rst_if)::set(null, "*", "clk_vif", clk_if);
    uvm_config_db#(virtual vibe_cfg_if)::set(null, "*", "cfg_vif", cfg_if);
    uvm_config_db#(virtual vibe_pma_if)::set(null, "*", "pma_0", pma0);
    uvm_config_db#(virtual vibe_pma_if)::set(null, "*", "pma_1", pma1);
    uvm_config_db#(virtual vibe_pma_if)::set(null, "*", "pma_2", pma2);
    uvm_config_db#(virtual vibe_pma_if)::set(null, "*", "pma_3", pma3);
    run_test();
  end
endmodule
