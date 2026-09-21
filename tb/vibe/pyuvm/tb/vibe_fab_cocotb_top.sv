// Cocotb / uvm-python fabric+mgmt+psel+cna_ep top. No SV UVM.
// Flattened Overlay-B 512b ports (Icarus-friendly). Hierarchical probes
// copied to named wires. TB-only Icarus wr_vl pin (same as vibe_fabric_harness).
`timescale 1ns/1ps

module vibe_fab_cocotb_top;
  `include "vibe_ub_fn.vh"

  logic         clk;
  logic         rst_n;
  logic         cfg_wr_vld, cfg_wr_ready, irq_logic;
  logic [3:0]   cfg_wr_cmd;
  logic [15:0]  cfg_wr_idx;
  logic [31:0]  cfg_wr_data;

  logic [511:0] nw_fab_data_0, nw_fab_data_1, nw_fab_data_2, nw_fab_data_3;
  logic [3:0]   nw_fab_vld, nw_fab_ready;
  logic [511:0] fab_nw_data_0, fab_nw_data_1, fab_nw_data_2, fab_nw_data_3;
  logic [3:0]   fab_nw_vld, fab_nw_ready;

  logic [3:0]   status_up, default_bm, port_rst, lmsm_go, len_err, deadlock_drop;
  logic [3:0]   fab_mgmt_cfg6_hit, mgmt_fab_cfg6_consume;
  logic         drop_g1, device_rst, cna_written, irq_rt;
  logic [31:0]  rt_shortest_unimpl, drop_down_cnt;
  logic [15:0]  cna;
  logic [31:0]  guid0, class_code, port_basic, port_cap;
  logic [3:0]   port_rst_rw1c;
  logic [3:0]   x_in_v, saf_v, g1_comb, g1_evt, pdrop;
  logic [511:0] saf_d_0, saf_d_1, saf_d_2, saf_d_3;

  logic         preload_req, preload_done;
  logic [31:0]  preload_val;

  logic [511:0] nw_fab_data [0:3];
  logic [511:0] fab_nw_data [0:3];
  logic [511:0] cfg6_d [0:3];
  logic [511:0] reply_d [0:3];
  logic [3:0]   reply_v, reply_r;
  logic         rt_wr_en;
  logic [15:0]  rt_wr_idx;
  logic [31:0]  rt_wr_data;

  assign nw_fab_data[0] = nw_fab_data_0;
  assign nw_fab_data[1] = nw_fab_data_1;
  assign nw_fab_data[2] = nw_fab_data_2;
  assign nw_fab_data[3] = nw_fab_data_3;
  assign fab_nw_data_0 = fab_nw_data[0];
  assign fab_nw_data_1 = fab_nw_data[1];
  assign fab_nw_data_2 = fab_nw_data[2];
  assign fab_nw_data_3 = fab_nw_data[3];
  assign reply_r = 4'b1111;

  vibe_fabric #(.ROUTE_TABLE_DEPTH(256)) u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down_cnt),
    .deadlock_drop(deadlock_drop), .irq_rt(irq_rt),
    .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(cfg6_d)
  );

  vibe_mgmt #(.ROUTE_TABLE_DEPTH(256)) u_mgmt (
    .clk(clk), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(cfg6_d),
    .mgmt_fab_cfg6_consume(mgmt_fab_cfg6_consume),
    .mgmt_nw_data(reply_d), .mgmt_nw_vld(reply_v), .mgmt_nw_ready(reply_r),
    .rx_ovf(4'd0), .fc_ovf(4'd0), .proto_err(4'd0),
    .retry_error(4'd0), .len_err(len_err),
    .deadlock_drop(deadlock_drop), .drop_g1(drop_g1),
    .afifo_ovf(4'd0), .irq_logic(irq_logic)
  );

  assign x_in_v  = u_fab.x_in_v;
  assign saf_v   = u_fab.saf_v;
  assign g1_comb = u_fab.g1_comb;
  assign g1_evt  = u_fab.g1_evt;
  assign pdrop   = u_fab.pdrop;
  assign guid0      = u_mgmt.u_cfg.guid0;
  assign class_code = u_mgmt.u_cfg.class_code;
  assign port_basic = u_mgmt.u_cfg.port_basic;
  assign port_cap   = u_mgmt.u_cfg.port_cap;
  assign port_rst_rw1c = u_mgmt.u_cfg.port_rst_rw1c;
  assign saf_d_0 = u_fab.saf_d[0];
  assign saf_d_1 = u_fab.saf_d[1];
  assign saf_d_2 = u_fab.saf_d[2];
  assign saf_d_3 = u_fab.saf_d[3];

  // Isolated route_lu + port_sel (suite RT=00/01 sticky/RR).
  logic        psel_rst_n, psel_device_rst, psel_wr_en, psel_sel_vld;
  logic        psel_drop_g1, psel_drop;
  logic [3:0]  psel_bitmap, psel_status_up, psel_default_bm, psel_cfg, psel_vl;
  logic [1:0]  psel_rt, psel_egr;
  logic [15:0] psel_wr_idx, psel_src, psel_dest;
  logic [31:0] psel_wr_data, psel_drop_down;

  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(psel_rst_n), .device_rst(psel_device_rst),
    .wr_en(psel_wr_en), .wr_idx(psel_wr_idx), .wr_data(psel_wr_data),
    .dest(psel_dest), .rt(psel_rt), .lu_vld(psel_sel_vld),
    .bitmap(psel_bitmap), .drop_g1(psel_drop_g1)
  );
  vibe_port_sel u_ps (
    .clk(clk), .rst_n(psel_rst_n),
    .bitmap(psel_bitmap), .status_up(psel_status_up), .default_bm(psel_default_bm),
    .rt(psel_rt), .drop_g1(psel_drop_g1), .sel_vld(psel_sel_vld),
    .cfg(psel_cfg), .src(psel_src), .dest(psel_dest), .vl(psel_vl),
    .egr(psel_egr), .drop(psel_drop), .drop_down_cnt(psel_drop_down)
  );

  // Isolated cna_ep (CFG6 term vs fwd).
  logic [15:0]  c6_cna;
  logic         c6_written;
  logic [3:0]   c6_hit, c6_cons, c6_rready, c6_rvld;
  logic [511:0] c6_data_0, c6_data_1, c6_data_2, c6_data_3;
  logic [511:0] c6_data [0:3];
  logic [511:0] c6_reply [0:3];
  logic         c6_icrc;

  assign c6_data[0] = c6_data_0;
  assign c6_data[1] = c6_data_1;
  assign c6_data[2] = c6_data_2;
  assign c6_data[3] = c6_data_3;

  vibe_cna_ep u_c6 (
    .clk(clk), .rst_n(rst_n), .cna(c6_cna), .cna_written(c6_written),
    .fab_mgmt_cfg6_hit(c6_hit), .fab_mgmt_cfg6_data(c6_data),
    .mgmt_fab_cfg6_consume(c6_cons), .mgmt_nw_data(c6_reply), .mgmt_nw_vld(c6_rvld),
    .mgmt_nw_ready(c6_rready), .icrc_fail(c6_icrc)
  );

  // Icarus: VOQ wr_vl combo-feeds xbar out_ready (same pin as vibe_fabric_harness).
`ifndef VERILATOR
  always @(posedge rst_n) begin
    force u_fab.g_egr[0].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[1].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[2].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[3].u_voq.wr_vl = 4'd0;
  end
`endif

  // Saturation preload (Icarus force). Verilator uses cocotb deposit on this path.
  initial begin
    preload_done = 1'b0;
    forever begin
      @(posedge preload_req);
`ifndef VERILATOR
      force u_fab.rt_shortest_unimpl = preload_val;
      repeat (2) @(posedge clk);
      release u_fab.rt_shortest_unimpl;
      @(posedge clk);
`else
      repeat (3) @(posedge clk);
`endif
      preload_done = 1'b1;
      @(negedge preload_req);
      preload_done = 1'b0;
    end
  end
endmodule
