// Fabric + mgmt + route_lu/port_sel + cna_ep UVM top (AS-0.1 §8/§9/§10).
`timescale 1ns/1ps

module vibe_fab_tb_top;
  import uvm_pkg::*;
  import vibe_uvm_pkg::*;
  `include "uvm_macros.svh"
  `include "vibe_ub_fn.vh"

  vibe_clk_rst_if clk_if();
  wire clk   = clk_if.clk;
  wire rst_n = clk_if.rst_n;

  vibe_cfg_if       cfg_if (clk, rst_n);
  vibe_nw4_if       ing_if (clk, rst_n);
  vibe_nw4_if       egr_if (clk, rst_n);
  vibe_fab_probe_if probe  (clk, rst_n);
  vibe_psel_if      psel   (clk);
  vibe_cna_if       cna    (clk);

  logic [511:0] reply_d [0:3];
  logic [3:0]   reply_v, reply_r;
  logic         rt_wr_en;
  logic [15:0]  rt_wr_idx;
  logic [31:0]  rt_wr_data;
  logic [511:0] cfg6_d [0:3];
  assign reply_r = 4'b1111;

  initial clk_if.rst_n = 1'b0;

  vibe_fabric #(.ROUTE_TABLE_DEPTH(256)) u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(probe.device_rst),
    .status_up(probe.status_up), .default_bm(probe.default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .nw_fab_data(ing_if.data), .nw_fab_vld(ing_if.vld), .nw_fab_ready(ing_if.ready),
    .fab_nw_data(egr_if.data), .fab_nw_vld(egr_if.vld), .fab_nw_ready(egr_if.ready),
    .len_err(probe.len_err), .drop_g1(probe.drop_g1),
    .rt_shortest_unimpl(probe.rt_shortest_unimpl), .drop_down_cnt(probe.drop_down_cnt),
    .deadlock_drop(probe.deadlock_drop), .irq_rt(probe.irq_rt),
    .cna(probe.cna), .cna_written(probe.cna_written),
    .fab_mgmt_cfg6_hit(probe.fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(cfg6_d)
  );

  vibe_mgmt #(.ROUTE_TABLE_DEPTH(256)) u_mgmt (
    .clk(clk), .rst_n(rst_n),
    .cfg_wr_vld(cfg_if.vld), .cfg_wr_ready(cfg_if.ready),
    .cfg_wr_cmd(cfg_if.cmd), .cfg_wr_idx(cfg_if.idx), .cfg_wr_data(cfg_if.data),
    .cna(probe.cna), .cna_written(probe.cna_written), .default_bm(probe.default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(probe.port_rst), .device_rst(probe.device_rst), .lmsm_go(probe.lmsm_go),
    .fab_mgmt_cfg6_hit(probe.fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(cfg6_d),
    .mgmt_fab_cfg6_consume(probe.mgmt_fab_cfg6_consume),
    .mgmt_nw_data(reply_d), .mgmt_nw_vld(reply_v), .mgmt_nw_ready(reply_r),
    .rx_ovf(4'd0), .fc_ovf(4'd0), .proto_err(4'd0),
    .retry_error(4'd0), .len_err(probe.len_err),
    .deadlock_drop(probe.deadlock_drop), .drop_g1(probe.drop_g1),
    .afifo_ovf(4'd0), .irq_logic(cfg_if.irq_logic)
  );

  assign probe.irq_logic = cfg_if.irq_logic;

  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(psel.rst_n), .device_rst(psel.device_rst),
    .wr_en(psel.wr_en), .wr_idx(psel.wr_idx), .wr_data(psel.wr_data),
    .dest(psel.dest), .rt(psel.rt), .lu_vld(psel.sel_vld),
    .bitmap(psel.bitmap), .drop_g1(psel.drop_g1)
  );
  vibe_port_sel u_ps (
    .clk(clk), .rst_n(psel.rst_n),
    .bitmap(psel.bitmap), .status_up(psel.status_up), .default_bm(psel.default_bm),
    .rt(psel.rt), .drop_g1(psel.drop_g1), .sel_vld(psel.sel_vld),
    .cfg(psel.cfg), .src(psel.src), .dest(psel.dest), .vl(psel.vl),
    .egr(psel.egr), .drop(psel.drop), .drop_down_cnt(psel.drop_down)
  );

  vibe_cna_ep u_c6 (
    .clk(clk), .rst_n(rst_n), .cna(cna.cna), .cna_written(cna.cna_written),
    .fab_mgmt_cfg6_hit(cna.hit), .fab_mgmt_cfg6_data(cna.data),
    .mgmt_fab_cfg6_consume(cna.cons), .mgmt_nw_data(cna.reply), .mgmt_nw_vld(cna.rvld),
    .mgmt_nw_ready(cna.rready), .icrc_fail(cna.icrc)
  );

  assign probe.x_in_v     = u_fab.x_in_v;
  assign probe.saf_v      = u_fab.saf_v;
  assign probe.g1_comb    = u_fab.g1_comb;
  assign probe.g1_evt     = u_fab.g1_evt;
  assign probe.pdrop      = u_fab.pdrop;
  assign probe.guid0      = u_mgmt.u_cfg.guid0;
  assign probe.class_code = u_mgmt.u_cfg.class_code;
  assign probe.port_basic = u_mgmt.u_cfg.port_basic;
  assign probe.port_cap   = u_mgmt.u_cfg.port_cap;
  assign probe.port_rst_rw1c = u_mgmt.u_cfg.port_rst_rw1c;

  integer pi;
  always @(*) begin
    for (pi = 0; pi < 4; pi = pi + 1)
      probe.saf_d[pi] = u_fab.saf_d[pi];
  end

  integer mi;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      probe.saw_drop_g1 <= 1'b0;
      probe.saw_len_err <= 4'd0;
      probe.saw_egr     <= 4'd0;
      probe.saw_xin     <= 4'd0;
      for (mi = 0; mi < 4; mi = mi + 1) begin
        probe.egr_cnt[mi]     <= 0;
        probe.egr_last[mi]    <= 512'd0;
        probe.last_rt_egr[mi] <= 2'd0;
      end
    end else begin
      if (probe.drop_g1) probe.saw_drop_g1 <= 1'b1;
      probe.saw_len_err <= probe.saw_len_err | probe.len_err;
      probe.saw_xin     <= probe.saw_xin | u_fab.x_in_v;
      for (mi = 0; mi < 4; mi = mi + 1) begin
        if (egr_if.vld[mi] && egr_if.ready[mi]) begin
          probe.saw_egr[mi]     <= 1'b1;
          probe.egr_cnt[mi]     <= probe.egr_cnt[mi] + 1;
          probe.egr_last[mi]    <= egr_if.data[mi];
          probe.last_rt_egr[mi] <= vibe_lph_rt(vibe_nw512_flit0(egr_if.data[mi]));
        end
      end
    end
  end

  initial begin
    probe.preload_req  = 1'b0;
    probe.preload_done = 1'b0;
    probe.status_up    = 4'b1111;
    forever begin
      @(posedge probe.preload_req);
      force u_fab.rt_shortest_unimpl = probe.preload_val;
      repeat (2) @(posedge clk);
      release u_fab.rt_shortest_unimpl;
      @(posedge clk);
      probe.preload_done = 1'b1;
      @(negedge probe.preload_req);
      probe.preload_done = 1'b0;
    end
  end

  initial begin
    egr_if.idle_slave_ready();
    ing_if.idle_master();
    cfg_if.idle();
    uvm_config_db#(virtual vibe_clk_rst_if)::set(null, "*", "clk_vif", clk_if);
    uvm_config_db#(virtual vibe_cfg_if)::set(null, "*", "cfg_vif", cfg_if);
    uvm_config_db#(virtual vibe_nw4_if)::set(null, "*", "ing_vif", ing_if);
    uvm_config_db#(virtual vibe_nw4_if)::set(null, "*", "egr_vif", egr_if);
    uvm_config_db#(virtual vibe_fab_probe_if)::set(null, "*", "probe", probe);
    uvm_config_db#(virtual vibe_psel_if)::set(null, "*", "psel", psel);
    uvm_config_db#(virtual vibe_cna_if)::set(null, "*", "cna", cna);
    run_test();
  end
endmodule
