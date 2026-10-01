// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm tc_port_smoke scores PMA loopback on vibe_port_cocotb_top.
// Decision-I wrap leaf `tc_vibe_port` / make vibe_port_wrap uses this top.
// Product ports are all packed scalars (no unpacked-array flatten).
// CHILDREN from rtl/port/vibe_port.sv (AS-0.1 §4). Official CFG6 opcode
// 0x10 / Appendix D packing is 未知; this wrapper does not invent it
// (vibe_port has no cfg_wr_* / cfg_rd_* pin). F1 ovf_l CDC stays stock
// inside vibe_port (do not ECO).
// Does not steal make top / wrap / port / top_wrap / mgmt_wrap /
// fabric_wrap / pcs_tx_wrap / pcs_rx_wrap / lmsm_wrap.
`timescale 1ns/1ps

module vibe_port_wrap_cocotb_top (
  input  logic         clk_fab,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         device_rst,
  input  logic         lmsm_go,
  input  logic         txclk,
  input  logic         rxclk,
  output logic [511:0] pcs_pma_txdata,
  input  logic [511:0] pma_pcs_rxdata,
  input  logic [511:0] fab_nw_data,
  input  logic         fab_nw_vld,
  output logic         fab_nw_ready,
  output logic [511:0] nw_fab_data,
  output logic         nw_fab_vld,
  input  logic         nw_fab_ready,
  input  logic [511:0] mgmt_nw_data,
  input  logic         mgmt_nw_vld,
  output logic         mgmt_nw_ready,
  output logic         status_up,
  output logic         disabled,
  output logic         retry_error,
  output logic         proto_err,
  output logic         fc_ovf,
  output logic         rx_ovf,
  output logic         afifo_ovf,
  output logic         cfg0_hit,
  output logic [639:0] cfg0_data
);
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
