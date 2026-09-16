// Per-port UVM top: vibe_port with Overlay-B + PMA loopback control.
`timescale 1ns/1ps

module vibe_port_tb_top;
  import uvm_pkg::*;
  import vibe_uvm_pkg::*;
  `include "uvm_macros.svh"

  vibe_clk_rst_if clk_if();
  wire clk_fab = clk_if.clk;

  logic txclk, rxclk;
  initial begin
    txclk = 0;
    rxclk = 0;
  end
  always #2 txclk = ~txclk;
  always #2 rxclk = ~rxclk;

  vibe_port_if pif (clk_fab, txclk, rxclk);

  assign pif.pma_pcs_rxdata = pif.loop_en ? pif.pcs_pma_txdata : 512'd0;

  initial clk_if.rst_n = 1'b0;

  vibe_port u_p (
    .clk_fab(clk_fab), .rst_n(pif.rst_n), .port_rst(pif.port_rst),
    .device_rst(pif.device_rst),
    .lmsm_go(pif.lmsm_go), .txclk(txclk), .rxclk(rxclk),
    .pcs_pma_txdata(pif.pcs_pma_txdata), .pma_pcs_rxdata(pif.pma_pcs_rxdata),
    .fab_nw_data(pif.fab_nw_data), .fab_nw_vld(pif.fab_nw_vld),
    .fab_nw_ready(pif.fab_nw_ready),
    .nw_fab_data(pif.nw_fab_data), .nw_fab_vld(pif.nw_fab_vld),
    .nw_fab_ready(pif.nw_fab_ready),
    .mgmt_nw_data(pif.mgmt_nw_data), .mgmt_nw_vld(pif.mgmt_nw_vld),
    .mgmt_nw_ready(pif.mgmt_nw_ready),
    .status_up(pif.status_up), .disabled(pif.disabled),
    .retry_error(pif.retry_error), .proto_err(pif.proto_err), .fc_ovf(pif.fc_ovf),
    .rx_ovf(pif.rx_ovf), .afifo_ovf(pif.afifo_ovf),
    .cfg0_hit(pif.cfg0_hit), .cfg0_data(pif.cfg0_data)
  );

  assign pif.link_ready = u_p.link_ready;
  assign pif.fec_fail   = u_p.fec_fail;
  assign pif.deskew_ok  = u_p.deskew_ok;
  assign pif.lmsm_st    = u_p.lmsm_st;
  assign pif.am_locked  = u_p.am_locked;
  assign pif.nw_dll_data = u_p.nw_dll_data;
  assign pif.nw_dll_vld  = u_p.nw_dll_vld;
  assign pif.nw_dll_ready = u_p.nw_dll_ready;
  assign pif.dll_nw_data = u_p.dll_nw_data;
  assign pif.dll_nw_vld  = u_p.dll_nw_vld;
  assign pif.dll_nw_ready = u_p.dll_nw_ready;
  assign pif.dll_pcs_data = u_p.dll_pcs_data;
  assign pif.dll_pcs_vld  = u_p.dll_pcs_vld;
  assign pif.dll_pcs_ready = u_p.dll_pcs_ready;
  assign pif.pcs_dll_data = u_p.pcs_dll_data;
  assign pif.pcs_dll_vld  = u_p.pcs_dll_vld;
  assign pif.pcs_dll_ready = u_p.pcs_dll_ready;
  assign pif.pcs_afifo_lane0 = u_p.pcs_afifo_lane0;
  assign pif.pcs_afifo_lane1 = u_p.pcs_afifo_lane1;
  assign pif.pcs_afifo_lane2 = u_p.pcs_afifo_lane2;
  assign pif.pcs_afifo_lane3 = u_p.pcs_afifo_lane3;
  assign pif.pcs_afifo_lane_vld = u_p.pcs_afifo_lane_vld;
  assign pif.afifo_pma_lane0 = u_p.afifo_pma_lane0;
  assign pif.afifo_pma_lane1 = u_p.afifo_pma_lane1;
  assign pif.afifo_pma_lane2 = u_p.afifo_pma_lane2;
  assign pif.afifo_pma_lane3 = u_p.afifo_pma_lane3;
  assign pif.afifo_pma_lane_vld = u_p.afifo_pma_lane_vld;
  assign pif.afrv0 = u_p.afrv0;
  assign pif.afrv1 = u_p.afrv1;
  assign pif.afrv2 = u_p.afrv2;
  assign pif.afrv3 = u_p.afrv3;
  assign pif.crd_cells = u_p.u_dll.u_crd.cells;
  assign pif.crd_pend  = u_p.u_dll.u_crd.pend;
  assign pif.credit_low = u_p.u_dll.u_crd.credit_low;
  assign pif.bp_nw = u_p.u_dll.u_crd.bp_nw;
  assign pif.can_send = u_p.u_dll.can_send;
  assign pif.dll_sm_st = u_p.u_dll.sm_st;

  always @* begin
    // Force the port net (PCS RX output + LMSM input). Forcing only
    // u_lmsm.am_locked does not back-drive u_p.am_locked, so waves stay 0
    // while Link_Active (AS-0.1) requires all four lanes locked.
    if (pif.force_am_lock) force u_p.am_locked = 4'b1111;
    else release u_p.am_locked;
    if (pif.force_lid_ok) force u_p.lid_bad = 1'b0;
    else release u_p.lid_bad;
    if (pif.force_st_active) force u_p.u_lmsm.st = 5'd9;
    else release u_p.u_lmsm.st;
    if (pif.force_crd64) force u_p.u_dll.u_crd.cells = 16'd64;
    else if (pif.force_crd512) force u_p.u_dll.u_crd.cells = 16'd512;
    else release u_p.u_dll.u_crd.cells;
    if (pif.force_pend0) force u_p.u_dll.u_crd.pend = 16'd0;
    else release u_p.u_dll.u_crd.pend;
  end

  initial begin
    pif.rst_n = 0; pif.port_rst = 0; pif.device_rst = 0; pif.lmsm_go = 0;
    pif.loop_en = 0; pif.fab_nw_vld = 0; pif.nw_fab_ready = 1; pif.mgmt_nw_vld = 0;
    pif.fab_nw_data = 0; pif.mgmt_nw_data = 0;
    pif.force_am_lock = 0; pif.force_lid_ok = 0; pif.force_st_active = 0;
    pif.force_crd64 = 0; pif.force_crd512 = 0; pif.force_pend0 = 0;
    uvm_config_db#(virtual vibe_clk_rst_if)::set(null, "*", "clk_vif", clk_if);
    uvm_config_db#(virtual vibe_port_if)::set(null, "*", "port", pif);
    run_test();
  end
endmodule
