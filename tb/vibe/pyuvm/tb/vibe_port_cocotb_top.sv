// Cocotb port top: vibe_port with optional PMA near-end loopback.
`timescale 1ns/1ps

module vibe_port_cocotb_top;
  logic         clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata_drv;
  logic [511:0] fab_nw_data, nw_fab_data, mgmt_nw_data;
  logic [639:0] cfg0_data;
  logic         fab_nw_vld, fab_nw_ready, nw_fab_vld, nw_fab_ready;
  logic         mgmt_nw_vld, mgmt_nw_ready, status_up, disabled;
  logic         retry_error, proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  logic         loopback;

  assign rxclk = txclk;
  wire [511:0] pma_pcs_rxdata = loopback ? pcs_pma_txdata : pma_pcs_rxdata_drv;

  vibe_port u_p (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .lmsm_go(lmsm_go), .txclk(txclk), .rxclk(rxclk),
    .pcs_pma_txdata(pcs_pma_txdata), .pma_pcs_rxdata(pma_pcs_rxdata),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld), .mgmt_nw_ready(mgmt_nw_ready),
    .status_up(status_up), .disabled(disabled),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .afifo_ovf(afifo_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );
endmodule
