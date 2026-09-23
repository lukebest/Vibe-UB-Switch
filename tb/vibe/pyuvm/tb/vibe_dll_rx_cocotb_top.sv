// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL RX unpack (AS-0.1.2 / FS-0.2.7 overlay B): 640b PCS → 4
// flits, pack to 512b NW, CFG0 terminate, FEC/BCRC → Go-Back-N.
// RXBUF=32 matches stock unit TCs (ovf). Product default stays 1024.
// Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_rx_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         link_up,
  input  logic         fec_fail,
  input  logic [639:0] pcs_dll_data,
  input  logic         pcs_dll_vld,
  input  logic         dll_nw_ready,
  output logic         pcs_dll_ready,
  output logic [511:0] dll_nw_data,
  output logic         dll_nw_vld,
  output logic         cfg0_hit,
  output logic         bcrc_fail,
  output logic         start_retry,
  output logic         rx_ovf,
  output logic         start_ack,
  output logic [639:0] cfg0_data
);
  vibe_dll_rx #(.RXBUF(32)) u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .fec_fail(fec_fail),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld),
    .pcs_dll_ready(pcs_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld),
    .dll_nw_ready(dll_nw_ready),
    .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data),
    .bcrc_fail(bcrc_fail), .start_retry(start_retry),
    .rx_ovf(rx_ovf), .start_ack(start_ack)
  );
endmodule
