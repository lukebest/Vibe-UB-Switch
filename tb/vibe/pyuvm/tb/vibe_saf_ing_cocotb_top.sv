// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric store-and-forward ingress (AS-0.1 §8). DEPTH=128.
// Combo in_ready / pkt_* ; async-low rst_n clears pointers /
// assemble state / len_err (mem not cleared). Do not present to
// xbar until EOP / full declared length. Length not in 16–4300 B
// → Packet Length Error, drop, len_err pulse. Instantiated by
// vibe_fabric g_saf.u_saf. Clock from entry_unit (2 ns).
// Decision-I wrap leaf `tc_vibe_saf_ing` / make saf_ing /
// make saf / make tc_vibe_saf_ing uses this top. Instance u_u
// matches Decision-I leaf wrappers (product instantiator is
// vibe_fabric g_saf.u_saf; stock Icarus tc_saf_ing uses u_s;
// not leftover u_saf / u_s on this wrap). Sixth fabric leaf
// after stage-80 vibe_fecn_mark wrap, stage-81 vibe_vl_rr wrap,
// stage-82 vibe_route_lu wrap, stage-83 vibe_port_sel wrap,
// and stage-84 vibe_voq_egr wrap.
// ovf_l (F1) is not in this module. This is not vibe_fecn_mark /
// vibe_vl_rr / vibe_route_lu / vibe_port_sel / vibe_voq_egr /
// vibe_nw_adapt / vibe_icrc / vibe_dll / vibe_bcrc / vibe_port /
// vibe_ub_switch.
// CHILDREN: none. Do not invent vibe_xbar or later fabric leaves.
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
