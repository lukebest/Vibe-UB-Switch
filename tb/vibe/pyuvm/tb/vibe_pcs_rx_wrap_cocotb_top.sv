// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm leaf PCS units score vibe_pcs_rx_amctl_lock /
// deskew / unpack / fec / scramble as direct tops. Full-stack Icarus
// tc_pcs_rx stays the official wrap scorer on sim-icarus.
// Decision-I wrap leaf `tc_vibe_pcs_rx` / make pcs_rx_wrap uses this top.
// Product ports are all packed scalars (no unpacked-array flatten).
// Official CFG6 opcode 0x10 / Appendix D packing is 未知; this
// wrapper does not invent it (vibe_pcs_rx has no CFG pin). F1 ovf_l
// lives in vibe_port (do not ECO). lmsm stays HOLD.
// Does not steal make top / wrap / port / top_wrap / mgmt_wrap /
// fabric_wrap / pcs_tx_wrap.
`timescale 1ns/1ps

module vibe_pcs_rx_wrap_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic [2:0]   fec_mode,
  input  logic [159:0] afifo_pcs_lane0,
  input  logic [159:0] afifo_pcs_lane1,
  input  logic [159:0] afifo_pcs_lane2,
  input  logic [159:0] afifo_pcs_lane3,
  input  logic         afifo_pcs_lane_vld,
  output logic [639:0] pcs_dll_data,
  output logic         pcs_dll_vld,
  input  logic         pcs_dll_ready,
  output logic         fec_fail,
  output logic [3:0]   am_locked,
  output logic         lid_bad,
  output logic         deskew_ok
);
  vibe_pcs_rx u_prx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up),
    .fec_mode(fec_mode),
    .afifo_pcs_lane0(afifo_pcs_lane0),
    .afifo_pcs_lane1(afifo_pcs_lane1),
    .afifo_pcs_lane2(afifo_pcs_lane2),
    .afifo_pcs_lane3(afifo_pcs_lane3),
    .afifo_pcs_lane_vld(afifo_pcs_lane_vld),
    .pcs_dll_data(pcs_dll_data),
    .pcs_dll_vld(pcs_dll_vld),
    .pcs_dll_ready(pcs_dll_ready),
    .fec_fail(fec_fail),
    .am_locked(am_locked),
    .lid_bad(lid_bad),
    .deskew_ok(deskew_ok)
  );
endmodule
