// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus tc_dll instantiates vibe_dll #(.RETRY_WAIT_CYC(4)).
// TP-DLL-004 scores a >32-flit DLLDP split on this full wrapper.
`timescale 1ns/1ps

module vibe_dll_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         device_rst,
  input  logic         link_up,
  input  logic         fec_fail,
  input  logic [511:0] nw_dll_data,
  input  logic         nw_dll_vld,
  output logic         nw_dll_ready,
  output logic [511:0] dll_nw_data,
  output logic         dll_nw_vld,
  input  logic         dll_nw_ready,
  output logic [639:0] dll_pcs_data,
  output logic         dll_pcs_vld,
  input  logic         dll_pcs_ready,
  input  logic [639:0] pcs_dll_data,
  input  logic         pcs_dll_vld,
  output logic         pcs_dll_ready,
  output logic         status_up,
  output logic         disabled,
  output logic         retrain_req,
  output logic         retry_error,
  output logic         proto_err,
  output logic         fc_ovf,
  output logic         rx_ovf,
  output logic         cfg0_hit,
  output logic [639:0] cfg0_data
);
  vibe_dll #(.RETRY_WAIT_CYC(4)) u_dll (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .link_up(link_up), .fec_fail(fec_fail),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .status_up(status_up), .disabled(disabled), .retrain_req(retrain_req),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );
endmodule
