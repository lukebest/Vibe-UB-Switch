// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL TX pack (AS-0.1.2 / FS-0.2.7 overlay B): 512b NW → 20B
// flits with cross-beat rem (64B beat, 20B flit, rem 4B). Emit one
// 640b beat (4 flits + BCRC in last 32b) when a group is ready. Short
// EOP Null-pads to the next 4-flit group. Credit consume counts data
// flits only. CFG0 does not consume credit. Backpressure if credit
// low / retry full / REQ|WAIT dropping data / pending ≥ 1024.
// Async-low rst_n clears rem / pkt / fq / dll_pcs_*. Instantiated by
// vibe_dll u_tx. Clock from entry_unit (2 ns). Instance u_u matches
// Decision-I leaf wrappers. Stock Icarus tc_dll_tx_cfg0 still uses
// vibe_dll_tx_cfg0_cocotb_top (tx + credit).
`timescale 1ns/1ps

module vibe_dll_tx_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         status_up,
  input  logic         credit_low,
  input  logic         bp_pending,
  input  logic         drop_data,
  input  logic         can_send,
  input  logic         replay,
  input  logic [159:0] replay_flit,
  input  logic         send_idle,
  input  logic         send_req,
  input  logic         send_ack,
  input  logic [511:0] nw_dll_data,
  input  logic         nw_dll_vld,
  input  logic         dll_pcs_ready,
  output logic         nw_dll_ready,
  output logic [639:0] dll_pcs_data,
  output logic         dll_pcs_vld,
  output logic         wr_en,
  output logic [159:0] wr_flit,
  output logic         is_null,
  output logic         is_retry,
  output logic [9:0]   consume_flits,
  output logic         consume_vld,
  output logic         consume_cfg0
);
  vibe_dll_tx u_u (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .status_up(status_up),
    .credit_low(credit_low), .bp_pending(bp_pending), .drop_data(drop_data),
    .can_send(can_send), .replay(replay), .replay_flit(replay_flit),
    .send_idle(send_idle), .send_req(send_req), .send_ack(send_ack),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld),
    .nw_dll_ready(nw_dll_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld),
    .dll_pcs_ready(dll_pcs_ready),
    .wr_en(wr_en), .wr_flit(wr_flit), .is_null(is_null), .is_retry(is_retry),
    .consume_flits(consume_flits), .consume_vld(consume_vld),
    .consume_cfg0(consume_cfg0)
  );
endmodule
