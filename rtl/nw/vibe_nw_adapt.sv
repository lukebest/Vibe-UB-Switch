// AS-0.1 §3/§5 T0 / §8: 640b vld/ready. LinkReady participates in ready (U21).
// Mgmt reply injects on ingress TX before nw_adapt_tx, priority over VOQ.
module vibe_nw_adapt (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_ready,
  // fabric / VOQ → TX
  input  logic [639:0] fab_tx_data,
  input  logic         fab_tx_vld,
  output logic         fab_tx_ready,
  // mgmt inject (priority)
  input  logic [639:0] mgmt_tx_data,
  input  logic         mgmt_tx_vld,
  output logic         mgmt_tx_ready,
  // to DLL TX
  output logic [639:0] dll_tx_data,
  output logic         dll_tx_vld,
  input  logic         dll_tx_ready,
  // from DLL RX
  input  logic [639:0] dll_rx_data,
  input  logic         dll_rx_vld,
  output logic         dll_rx_ready,
  // to fabric ingress
  output logic [639:0] fab_rx_data,
  output logic         fab_rx_vld,
  input  logic         fab_rx_ready
);
  assign mgmt_tx_ready = link_ready && dll_tx_ready;
  assign fab_tx_ready  = link_ready && dll_tx_ready && !mgmt_tx_vld;
  assign dll_tx_vld    = link_ready && (mgmt_tx_vld || fab_tx_vld);
  assign dll_tx_data   = mgmt_tx_vld ? mgmt_tx_data : fab_tx_data;

  assign dll_rx_ready = fab_rx_ready;
  assign fab_rx_vld   = dll_rx_vld;
  assign fab_rx_data  = dll_rx_data;
endmodule
