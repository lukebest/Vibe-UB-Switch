// AS-0.1 §3/§5 T0 / §8 / FS-0.2.7: 512b NW vld/ready. LinkReady in ready (U21).
// Mgmt reply injects on ingress TX before nw_adapt_tx, priority over VOQ.
module vibe_nw_adapt (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_ready,
  // FAB → NW (VOQ egress)
  input  logic [511:0] fab_nw_data,
  input  logic         fab_nw_vld,
  output logic         fab_nw_ready,
  // mgmt → NW inject (priority)
  input  logic [511:0] mgmt_nw_data,
  input  logic         mgmt_nw_vld,
  output logic         mgmt_nw_ready,
  // NW → DLL
  output logic [511:0] nw_dll_data,
  output logic         nw_dll_vld,
  input  logic         nw_dll_ready,
  // DLL → NW
  input  logic [511:0] dll_nw_data,
  input  logic         dll_nw_vld,
  output logic         dll_nw_ready,
  // NW → FAB (SAF ingress)
  output logic [511:0] nw_fab_data,
  output logic         nw_fab_vld,
  input  logic         nw_fab_ready
);
  assign mgmt_nw_ready = link_ready && nw_dll_ready;
  assign fab_nw_ready  = link_ready && nw_dll_ready && !mgmt_nw_vld;
  assign nw_dll_vld    = link_ready && (mgmt_nw_vld || fab_nw_vld);
  assign nw_dll_data   = mgmt_nw_vld ? mgmt_nw_data : fab_nw_data;

  assign dll_nw_ready = nw_fab_ready;
  assign nw_fab_vld   = dll_nw_vld;
  assign nw_fab_data  = dll_nw_data;
endmodule
