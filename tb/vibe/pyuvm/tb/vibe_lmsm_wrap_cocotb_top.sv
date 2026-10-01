// Thin cocotb wrapper. DUT RTL never edited.
// Stock Icarus / pyuvm tc_lmsm_walk / tc_lmsm_vlock / tc_lmsm_cc /
// tc_lmsm_idle_discovery remain the official leaf-FSM scorers.
// Decision-I wrap leaf `tc_vibe_lmsm` / make lmsm_wrap uses this top.
// Product ports are all packed scalars (no unpacked-array flatten).
// CHILDREN is empty (FSM leaf; header/footer only — no child
// instances). Official CFG6 opcode 0x10 / Appendix D packing is 未知;
// this wrapper does not invent it (vibe_lmsm has no CFG pin). F1 ovf_l
// lives in vibe_port (do not ECO).
// Does not steal make top / wrap / port / top_wrap / mgmt_wrap /
// fabric_wrap / pcs_tx_wrap / pcs_rx_wrap.
`timescale 1ns/1ps

module vibe_lmsm_wrap_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       lmsm_go,
  input  logic [3:0] am_locked,
  input  logic       lid_bad,
  input  logic       lane0_fail,
  input  logic       eq_negotiated,
  input  logic       retrain_req,
  output logic       link_up,
  output logic       link_ready,
  output logic       sdf_period,
  output logic [4:0] state,
  output logic       width_fail
);
  vibe_lmsm u_lmsm (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .lmsm_go(lmsm_go),
    .am_locked(am_locked), .lid_bad(lid_bad), .lane0_fail(lane0_fail),
    .eq_negotiated(eq_negotiated), .retrain_req(retrain_req),
    .link_up(link_up), .link_ready(link_ready), .sdf_period(sdf_period),
    .state(state), .width_fail(width_fail)
  );
endmodule
