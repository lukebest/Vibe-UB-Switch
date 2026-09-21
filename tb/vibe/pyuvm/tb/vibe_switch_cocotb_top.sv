// Product-pin cocotb top: vibe_ub_switch + peer vibe_port (tc_top_smoke mapping).
// Peer TX is held on last packed PMA beat so idle-PRBS does not slip DUT RX.
`timescale 1ns/1ps

module vibe_switch_cocotb_top;
  logic         clk_fab, rst_n;
  logic         txclk_0, txclk_1, txclk_2, txclk_3;
  logic [511:0] pcs_pma_txdata_0, pcs_pma_txdata_1, pcs_pma_txdata_2, pcs_pma_txdata_3;
  logic [511:0] pma_pcs_rxdata_0, pma_pcs_rxdata_1, pma_pcs_rxdata_2, pma_pcs_rxdata_3;
  logic         cfg_wr_vld, cfg_wr_ready, irq_logic;
  logic [3:0]   cfg_wr_cmd;
  logic [15:0]  cfg_wr_idx;
  logic [31:0]  cfg_wr_data;

  logic prst, pdrst, plgo;
  logic [511:0] ptx, prx;
  logic [511:0] p_fab_tx, p_fab_rx, p_mgmt;
  logic [639:0] p_cfg0;
  logic p_ftv, p_ftr, p_frv, p_frr, p_mv, p_mr, p_up, p_dis;
  logic p_rty, p_pe, p_fc, p_rxo, p_afo, p_c0;
  logic [511:0] lb_pcs;

  assign pma_pcs_rxdata_0 = lb_pcs;
  assign pma_pcs_rxdata_1 = 512'd0;
  assign pma_pcs_rxdata_2 = 512'd0;
  assign pma_pcs_rxdata_3 = 512'd0;
  assign prx = 512'd0;

  always @(posedge txclk_0) begin
    if (u_peer.afifo_pma_lane_vld)
      lb_pcs <= {u_peer.afifo_pma_lane3, u_peer.afifo_pma_lane2,
                 u_peer.afifo_pma_lane1, u_peer.afifo_pma_lane0};
  end

  vibe_ub_switch dut (
    .clk_fab(clk_fab), .rst_n(rst_n),
    .txclk_0(txclk_0), .txclk_1(txclk_1), .txclk_2(txclk_2), .txclk_3(txclk_3),
    .rxclk_0(txclk_0), .rxclk_1(txclk_1), .rxclk_2(txclk_2), .rxclk_3(txclk_3),
    .pcs_pma_txdata_0(pcs_pma_txdata_0), .pcs_pma_txdata_1(pcs_pma_txdata_1),
    .pcs_pma_txdata_2(pcs_pma_txdata_2), .pcs_pma_txdata_3(pcs_pma_txdata_3),
    .pma_pcs_rxdata_0(pma_pcs_rxdata_0), .pma_pcs_rxdata_1(pma_pcs_rxdata_1),
    .pma_pcs_rxdata_2(pma_pcs_rxdata_2), .pma_pcs_rxdata_3(pma_pcs_rxdata_3),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .irq_logic(irq_logic)
  );

  vibe_port u_peer (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(prst), .device_rst(pdrst),
    .lmsm_go(plgo), .txclk(txclk_0), .rxclk(txclk_0),
    .pcs_pma_txdata(ptx), .pma_pcs_rxdata(prx),
    .fab_nw_data(p_fab_tx), .fab_nw_vld(p_ftv), .fab_nw_ready(p_ftr),
    .nw_fab_data(p_fab_rx), .nw_fab_vld(p_frv), .nw_fab_ready(p_frr),
    .mgmt_nw_data(p_mgmt), .mgmt_nw_vld(p_mv), .mgmt_nw_ready(p_mr),
    .status_up(p_up), .disabled(p_dis),
    .retry_error(p_rty), .proto_err(p_pe), .fc_ovf(p_fc),
    .rx_ovf(p_rxo), .afifo_ovf(p_afo), .cfg0_hit(p_c0), .cfg0_data(p_cfg0)
  );
endmodule
