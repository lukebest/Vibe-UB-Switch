// Thin cocotb wrapper. DUT RTL never edited.
// Product mgmt reset stretch (AS-0.1.2 §10 / Table D-103):
// device_rst_pulse / port_rst_pulse start a 7-dest-clock hold
// (dct / pct load 3'd7). HW clears the hold when the counter
// falls through 1. Async-low rst_n clears holds without a dest
// posedge. Device reset MUST NOT force DLL_Disabled (that is
// wrap / LMSM). Port Reset RW1C lives in vibe_cfg_space; this
// leaf only stretches the pulse. Instantiated by vibe_mgmt
// u_rst. Clock from entry_unit (2 ns). Instance u_u matches
// Decision-I leaf wrappers. Stock Icarus tc_rst_port_device
// remains the official TP scorer (direct vibe_rst_ctl top,
// instance u_r). Fourth mgmt leaf after stage-40 vibe_irq_agg,
// stage-41 vibe_cna_ep, and stage-42 vibe_cfg_space.
// ovf_l (F1) is not in this module. This is not vibe_rst_sync /
// vibe_irq_agg / vibe_cna_ep / vibe_cfg_space / vibe_mgmt.
// CHILDREN: none. Tip-align leaf wave done; do not invent
// further tip-align leaves.
`timescale 1ns/1ps

module vibe_rst_ctl_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       device_rst_pulse,
  input  logic [3:0] port_rst_pulse,
  output logic       device_rst,
  output logic [3:0] port_rst
);
  vibe_rst_ctl u_u (
    .clk(clk), .rst_n(rst_n),
    .device_rst_pulse(device_rst_pulse),
    .port_rst_pulse(port_rst_pulse),
    .device_rst(device_rst),
    .port_rst(port_rst)
  );
endmodule
