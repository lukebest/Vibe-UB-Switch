// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric store-and-forward ingress (AS-0.1 §8). DEPTH=128.
// Combo in_ready / pkt_* ; async-low rst_n clears pointers /
// assemble state / len_err (mem not cleared). Do not present to
// xbar until EOP / full declared length. Length not in 16–4300 B
// → Packet Length Error, drop, len_err pulse. Instantiated by
// vibe_fabric g_saf.u_saf. Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_saf_ing_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [511:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [511:0] pkt_data,
  output logic         pkt_vld,
  input  logic         pkt_ready,
  output logic         pkt_sop,
  output logic         pkt_eop,
  output logic [15:0]  pkt_bytes,
  output logic         len_err
);
  vibe_saf_ing #(.DEPTH(128)) u_u (
    .clk(clk), .rst_n(rst_n),
    .in_data(in_data), .in_vld(in_vld), .in_ready(in_ready),
    .pkt_data(pkt_data), .pkt_vld(pkt_vld), .pkt_ready(pkt_ready),
    .pkt_sop(pkt_sop), .pkt_eop(pkt_eop), .pkt_bytes(pkt_bytes),
    .len_err(len_err)
  );
endmodule
