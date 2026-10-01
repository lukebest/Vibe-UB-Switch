// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm leaf PCS units score vibe_pcs_tx_g1 / fec /
// cw2beat / pack / scramble as direct tops. Full-stack Icarus
// tc_pcs_tx stays the official wrap scorer on sim-icarus.
// Decision-I wrap leaf `tc_vibe_pcs_tx` / make pcs_tx_wrap uses this top.
// Product ports are all packed scalars (no unpacked-array flatten).
// Official CFG6 opcode 0x10 / Appendix D packing is 未知; this
// wrapper does not invent it (vibe_pcs_tx has no CFG pin). F1 ovf_l
// lives in vibe_port (do not ECO). pcs_rx / lmsm stay HOLD.
// Does not steal make top / wrap / port / top_wrap / mgmt_wrap /
// fabric_wrap.
`timescale 1ns/1ps

module vibe_pcs_tx_wrap_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         sdf_period,
  input  logic [2:0]   fec_mode,
  input  logic         afifo_afull,
  input  logic [639:0] dll_pcs_data,
  input  logic         dll_pcs_vld,
  output logic         dll_pcs_ready,
  output logic [159:0] pcs_afifo_lane0,
  output logic [159:0] pcs_afifo_lane1,
  output logic [159:0] pcs_afifo_lane2,
  output logic [159:0] pcs_afifo_lane3,
  output logic         pcs_afifo_lane_vld
);
  vibe_pcs_tx u_ptx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up),
    .sdf_period(sdf_period), .fec_mode(fec_mode),
    .afifo_afull(afifo_afull),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld),
    .dll_pcs_ready(dll_pcs_ready),
    .pcs_afifo_lane0(pcs_afifo_lane0),
    .pcs_afifo_lane1(pcs_afifo_lane1),
    .pcs_afifo_lane2(pcs_afifo_lane2),
    .pcs_afifo_lane3(pcs_afifo_lane3),
    .pcs_afifo_lane_vld(pcs_afifo_lane_vld)
  );
endmodule
