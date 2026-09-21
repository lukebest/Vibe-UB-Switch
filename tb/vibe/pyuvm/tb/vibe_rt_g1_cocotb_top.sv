// Thin parameter / array wrapper. DUT RTL never edited.
`timescale 1ns/1ps

module vibe_rt_g1_cocotb_top (
  input  logic        clk, rst_n, device_rst, wr_en, lu_vld,
  input  logic [15:0] wr_idx, dest, src,
  input  logic [31:0] wr_data,
  input  logic [3:0]  status_up, default_bm, cfg, vl,
  input  logic [1:0]  rt,
  output logic        drop_g1, drop,
  output logic [3:0]  bitmap,
  output logic [1:0]  egr,
  output logic [31:0] drop_down
);
  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(wr_en), .wr_idx(wr_idx), .wr_data(wr_data),
    .dest(dest), .rt(rt), .lu_vld(lu_vld),
    .bitmap(bitmap), .drop_g1(drop_g1)
  );
  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(lu_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down)
  );
endmodule
