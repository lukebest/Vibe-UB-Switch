// Thin cocotb wrapper. DUT RTL never edited.
// Product NW 512b vld/ready adapter (AS-0.1 §3/§5 T0 / §8 /
// FS-0.2.7): combo; LinkReady in ready (U21); mgmt inject
// priority over VOQ. Clock from entry_unit (2 ns) is unused in
// the combo body (port present). rst_n unused in combo body.
// Decision-I wrap leaf `tc_vibe_nw_adapt` / make nw_adapt /
// make tc_vibe_nw_adapt uses this top. Instance u_u matches
// Decision-I leaf wrappers (product instantiator is vibe_port
// u_nw; stock Icarus tc_nw_adapt_linkready uses u_n; not leftover
// u_n / u_nw on this wrap). Last NW leaf after stage-78 vibe_icrc
// wrap. ovf_l (F1) is not in this module. This is not vibe_icrc /
// vibe_dll / vibe_bcrc / vibe_port / vibe_ub_switch.
// CHILDREN: none.
`timescale 1ns/1ps

module vibe_nw_adapt_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_ready,
  input  logic [511:0] fab_nw_data,
  input  logic         fab_nw_vld,
  output logic         fab_nw_ready,
  input  logic [511:0] mgmt_nw_data,
  input  logic         mgmt_nw_vld,
  output logic         mgmt_nw_ready,
  output logic [511:0] nw_dll_data,
  output logic         nw_dll_vld,
  input  logic         nw_dll_ready,
  input  logic [511:0] dll_nw_data,
  input  logic         dll_nw_vld,
  output logic         dll_nw_ready,
  output logic [511:0] nw_fab_data,
  output logic         nw_fab_vld,
  input  logic         nw_fab_ready
);
  vibe_nw_adapt u_u (
    .clk(clk), .rst_n(rst_n), .link_ready(link_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld),
    .fab_nw_ready(fab_nw_ready),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld),
    .mgmt_nw_ready(mgmt_nw_ready),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld),
    .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld),
    .dll_nw_ready(dll_nw_ready),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld),
    .nw_fab_ready(nw_fab_ready)
  );
endmodule
