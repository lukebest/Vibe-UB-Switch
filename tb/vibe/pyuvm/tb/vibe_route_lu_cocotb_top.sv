// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric CFG0_ROUTE_TABLE lookup (AS-0.1 §2/§8 + FS-0.2.3 G1).
// dest → 4-bit egress bitmap. RT=10/11: DROP (pulse drop_g1).
// No Dijkstra, no treat-as-RT=00, no RT rewrite. Count/irq are fabric-side.
// Clock from entry_unit (2 ns). Instantiated by vibe_fabric u_rt / g_rt.u_rti.
// Decision-I wrap leaf `tc_vibe_route_lu` / make route_lu /
// make route / make tc_vibe_route_lu uses this top. Instance u_u
// matches Decision-I leaf wrappers (product instantiator is
// vibe_fabric u_rt / g_rt.u_rti; stock Icarus tc_route_lu uses
// u_rt; not leftover u_rt / u_rti / u_lu on this wrap). Third
// fabric leaf after stage-80 vibe_fecn_mark wrap and stage-81
// vibe_vl_rr wrap.
// ovf_l (F1) is not in this module. This is not vibe_fecn_mark /
// vibe_vl_rr / vibe_nw_adapt / vibe_icrc / vibe_dll / vibe_bcrc /
// vibe_port / vibe_ub_switch.
// CHILDREN: none. Do not invent vibe_port_sel or later fabric leaves.
`timescale 1ns/1ps

module vibe_route_lu_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        device_rst,
  input  logic        wr_en,
  input  logic [15:0] wr_idx,
  input  logic [31:0] wr_data,
  input  logic [15:0] dest,
  input  logic [1:0]  rt,
  input  logic        lu_vld,
  output logic [3:0]  bitmap,
  output logic        drop_g1
);
  vibe_route_lu #(.DEPTH(256)) u_u (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(wr_en), .wr_idx(wr_idx), .wr_data(wr_data),
    .dest(dest), .rt(rt), .lu_vld(lu_vld),
    .bitmap(bitmap), .drop_g1(drop_g1)
  );
endmodule
