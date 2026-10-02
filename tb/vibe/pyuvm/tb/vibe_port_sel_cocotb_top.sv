// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric port select (AS-0.1 §2/§8).
// available = bitmap & status_up (0 if drop_g1). Empty → Default;
// Default all-0 → port 0; if still empty drop+count, no flood.
// RT=00 per-flow sticky RR (slot=vl); else per-packet RR via rr.
// Clock from entry_unit (2 ns). Instantiated by vibe_fabric u_ps / g_rt.u_psi.
// Decision-I wrap leaf `tc_vibe_port_sel` / make port_sel /
// make psel / make tc_vibe_port_sel uses this top. Instance u_u
// matches Decision-I leaf wrappers (product instantiator is
// vibe_fabric u_ps / g_rt.u_psi; stock Icarus tc_p0_down_drop uses
// u_ps; not leftover u_ps / u_psi / u_rt on this wrap). Fourth
// fabric leaf after stage-80 vibe_fecn_mark wrap, stage-81
// vibe_vl_rr wrap, and stage-82 vibe_route_lu wrap.
// ovf_l (F1) is not in this module. This is not vibe_fecn_mark /
// vibe_vl_rr / vibe_route_lu / vibe_nw_adapt / vibe_icrc /
// vibe_dll / vibe_bcrc / vibe_port / vibe_ub_switch.
// CHILDREN: none. Do not invent vibe_voq_egr or later fabric leaves.
`timescale 1ns/1ps

module vibe_port_sel_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [3:0]  bitmap,
  input  logic [3:0]  status_up,
  input  logic [3:0]  default_bm,
  input  logic [1:0]  rt,
  input  logic        drop_g1,
  input  logic        sel_vld,
  input  logic [3:0]  cfg,
  input  logic [15:0] src,
  input  logic [15:0] dest,
  input  logic [3:0]  vl,
  output logic [1:0]  egr,
  output logic        drop,
  output logic [31:0] drop_down_cnt
);
  vibe_port_sel u_u (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(sel_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down_cnt)
  );
endmodule
