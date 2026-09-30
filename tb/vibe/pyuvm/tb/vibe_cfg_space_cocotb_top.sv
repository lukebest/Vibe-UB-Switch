// Thin cocotb wrapper. DUT RTL never edited.
// Product mgmt static write (AS-0.1.2 §10 / UB Table D-103):
// cfg_wr_cmd 0=CNA, 1=route entry, 2=Default bitmap, 3=Port Reset
// RW1C per port, 4=device reset, 5=pulse lmsm_go; 6–15 ignore
// (irq_clr still pulses on any accepted write). Identity constants
// are combo assigns (GUID Type 0x3, Class 0x03/0x00, PORT_BASIC/CAP).
// No cfg_rd_* pin (AS §18). CFG6 R/W / Appendix D offsets are 未知
// — this wrapper does not invent them. Instantiated by vibe_mgmt
// u_cfg. Clock from entry_unit (2 ns). Instance u_u matches
// Decision-I leaf wrappers. Stock Icarus tc_identity_cfg_space
// remains the official TP scorer (direct vibe_cfg_space top).
`timescale 1ns/1ps

module vibe_cfg_space_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        device_rst,
  input  logic        cfg_wr_vld,
  output logic        cfg_wr_ready,
  input  logic [3:0]  cfg_wr_cmd,
  input  logic [15:0] cfg_wr_idx,
  input  logic [31:0] cfg_wr_data,
  output logic [15:0] cna,
  output logic        cna_written,
  output logic [3:0]  default_bm,
  output logic        rt_wr_en,
  output logic [15:0] rt_wr_idx,
  output logic [31:0] rt_wr_data,
  output logic [3:0]  port_rst_pulse,
  input  logic [3:0]  port_rst_hold,
  output logic [3:0]  port_rst_rw1c,
  output logic        device_rst_pulse,
  output logic [3:0]  lmsm_go_pulse,
  output logic        irq_clr,
  output logic [31:0] guid0,
  output logic [31:0] class_code,
  output logic [31:0] port_basic,
  output logic [31:0] port_cap
);
  vibe_cfg_space u_u (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx),
    .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst_pulse(port_rst_pulse), .port_rst_hold(port_rst_hold),
    .port_rst_rw1c(port_rst_rw1c),
    .device_rst_pulse(device_rst_pulse),
    .lmsm_go_pulse(lmsm_go_pulse), .irq_clr(irq_clr),
    .guid0(guid0), .class_code(class_code),
    .port_basic(port_basic), .port_cap(port_cap)
  );
endmodule
