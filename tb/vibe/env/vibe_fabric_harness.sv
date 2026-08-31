// Hierarchical fabric+mgmt harness (AS-0.1).
// Drives 640b NW beats into vibe_fabric; observes egress, G1 counter, irq_logic.
// PMA 512b is not used here — full-stack packet BFMs are out of scope for G1.

`timescale 1ns/1ps

module vibe_fabric_harness (
  output logic         clk,
  output logic         rst_n,
  output logic         irq_logic,
  output logic [31:0]  rt_shortest_unimpl,
  output logic         drop_g1,
  output logic [3:0]   len_err,
  output logic [3:0]   egr_vld,
  output logic [3:0]   ing_ready
);
  `include "vibe_tb_defs.svh"

  logic         cfg_wr_vld, cfg_wr_ready;
  logic [2:0]   cfg_wr_cmd;
  logic [15:0]  cfg_wr_idx;
  logic [31:0]  cfg_wr_data;
  logic [3:0]   status_up;
  logic [3:0]   default_bm;
  logic         rt_wr_en;
  logic [15:0]  rt_wr_idx;
  logic [31:0]  rt_wr_data;
  logic         device_rst;
  logic [3:0]   port_rst;
  logic [3:0]   lmsm_go;
  logic [15:0]  cna;
  logic         cna_written;

  logic [639:0] ing_data [0:3];
  logic [3:0]   ing_vld;
  logic [639:0] egr_data [0:3];
  logic [3:0]   egr_ready;
  logic [31:0]  drop_down;
  logic [3:0]   deadlock_drop;
  logic [3:0]   cfg6_hit, cfg6_cons;
  logic [639:0] cfg6_d [0:3];
  logic [639:0] reply_d [0:3];
  logic [3:0]   reply_v, reply_r;

  logic         saw_drop_g1;
  logic [3:0]   saw_len_err;
  logic [3:0]   saw_egr;
  integer       egr_cnt [0:3];
  logic [639:0] egr_last [0:3];
  logic [1:0]   last_rt_egr [0:3];
  integer       fail_count = 0;
  integer       pass_count = 0;
  logic [31:0]  preload_val;

  initial clk = 1'b0;
  always #1 clk = ~clk;

  vibe_fabric #(.ROUTE_TABLE_DEPTH(256)) u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .ing_data(ing_data), .ing_vld(ing_vld), .ing_ready(ing_ready),
    .egr_data(egr_data), .egr_vld(egr_vld), .egr_ready(egr_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down),
    .deadlock_drop(deadlock_drop), .irq_rt(),
    .cna(cna), .cna_written(cna_written),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_d)
  );

  vibe_mgmt #(.ROUTE_TABLE_DEPTH(256)) u_mgmt (
    .clk(clk), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_d),
    .cfg6_consume(cfg6_cons),
    .reply_data(reply_d), .reply_vld(reply_v), .reply_ready(reply_r),
    .rx_ovf(4'd0), .fc_ovf(4'd0), .proto_err(4'd0),
    .retry_error(4'd0), .len_err(len_err),
    .deadlock_drop(deadlock_drop), .drop_g1(drop_g1),
    .afifo_ovf(4'd0), .irq_logic(irq_logic)
  );

  assign reply_r = 4'b1111;

  integer mi;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      saw_drop_g1 <= 1'b0;
      saw_len_err <= 4'd0;
      saw_egr     <= 4'd0;
      for (mi = 0; mi < 4; mi = mi + 1) begin
        egr_cnt[mi]     <= 0;
        egr_last[mi]    <= 640'd0;
        last_rt_egr[mi] <= 2'd0;
      end
    end else begin
      if (drop_g1) saw_drop_g1 <= 1'b1;
      saw_len_err <= saw_len_err | len_err;
      for (mi = 0; mi < 4; mi = mi + 1) begin
        if (egr_vld[mi] && egr_ready[mi]) begin
          saw_egr[mi]     <= 1'b1;
          egr_cnt[mi]     <= egr_cnt[mi] + 1;
          egr_last[mi]    <= egr_data[mi];
          last_rt_egr[mi] <= vibe_lph_rt(egr_data[mi][639:480]);
        end
      end
    end
  end

  task automatic tb_clr_mon;
    begin
      saw_drop_g1 = 1'b0;
      saw_len_err = 4'd0;
      saw_egr     = 4'd0;
      egr_cnt[0] = 0; egr_cnt[1] = 0; egr_cnt[2] = 0; egr_cnt[3] = 0;
      egr_last[0] = 640'd0; egr_last[1] = 640'd0;
      egr_last[2] = 640'd0; egr_last[3] = 640'd0;
    end
  endtask

  task automatic tb_cycles;
    input integer n;
    integer i;
    begin
      for (i = 0; i < n; i = i + 1) @(posedge clk);
    end
  endtask

  task automatic tb_reset;
    integer p;
    begin
      rst_n       = 1'b0;
      cfg_wr_vld  = 1'b0;
      cfg_wr_cmd  = 3'd0;
      cfg_wr_idx  = 16'd0;
      cfg_wr_data = 32'd0;
      status_up   = 4'b1111;
      ing_vld     = 4'd0;
      egr_ready   = 4'b1111;
      // pass/fail accumulate across TCs; do not clear here
      for (p = 0; p < 4; p = p + 1) ing_data[p] = 640'd0;
      tb_cycles(4);
      rst_n = 1'b1;
      tb_cycles(4);
      tb_clr_mon;
    end
  endtask

  task automatic tb_cfg;
    input [2:0]  cmd;
    input [15:0] idx;
    input [31:0] data;
    begin
      @(negedge clk);
      cfg_wr_cmd  = cmd;
      cfg_wr_idx  = idx;
      cfg_wr_data = data;
      cfg_wr_vld  = 1'b1;
      @(posedge clk);
      while (!cfg_wr_ready) @(posedge clk);
      @(negedge clk);
      cfg_wr_vld  = 1'b0;
      tb_cycles(3);
    end
  endtask

  task automatic tb_wr_route;
    input [15:0] dest;
    input [3:0]  bm;
    begin
      tb_cfg(VIBE_TB_CMD_ROUTE, dest, {28'd0, bm});
    end
  endtask

  // SAF completes on the last declared beat (1-beat when decl_flits<=4).
  task automatic tb_inject;
    input integer     port;
    input [639:0]     beat0;
    input integer     extra_beats;
    integer           n, b;
    begin
      n = extra_beats;
      if (n < 1) n = 1;
      for (b = 0; b < n; b = b + 1) begin
        @(negedge clk);
        while (!ing_ready[port]) @(posedge clk);
        ing_data[port] = (b == 0) ? beat0 : {160'd0, beat0[479:0]};
        ing_vld[port]  = 1'b1;
        @(posedge clk);
      end
      @(negedge clk);
      ing_vld[port] = 1'b0;
    end
  endtask

  task automatic tb_inject_hdr;
    input integer     port;
    input [3:0]       cfg;
    input [1:0]       rt;
    input [3:0]       vl;
    input [15:0]      scna;
    input [15:0]      dcna;
    input [13:0]      plen;
    input [2:0]       nlp;
    input [7:0]       opc;
    reg   [159:0]     fl;
    integer           nb;
    begin
      fl = vibe_tb_mk_flit(cfg, rt, vl, scna, dcna, plen, 16'd0, 8'd0, nlp, opc);
      nb = vibe_tb_decl_beats(plen);
      tb_inject(port, vibe_tb_mk_beat(fl), nb);
    end
  endtask

  task automatic tb_hold_egr;
    input hold;
    begin
      egr_ready = hold ? 4'd0 : 4'b1111;
    end
  endtask

  task automatic tb_wait_egr;
    input integer timeout;
    integer t, any;
    begin
      t = 0;
      any = 0;
      while ((t < timeout) && !any) begin
        @(posedge clk);
        t = t + 1;
        any = |egr_vld;
      end
    end
  endtask

  task automatic tb_expect_no_egr;
    input integer timeout;
    integer t;
    begin
      t = 0;
      while (t < timeout) begin
        @(posedge clk);
        t = t + 1;
      end
    end
  endtask

  task automatic tb_pass;
    input [8*48-1:0] name;
    begin
      pass_count = pass_count + 1;
      $display("PASS %0s", name);
    end
  endtask

  task automatic tb_fail;
    input [8*48-1:0] name;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail_count = fail_count + 1;
      $display("FAIL %0s", name);
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe TC=%0s", name);
      $display("  dump     : irq=%0b drop_g1=%0b cnt=%0h egr_vld=%04b saw_egr=%04b len_err=%04b",
               irq_logic, drop_g1, rt_shortest_unimpl, egr_vld, saw_egr, len_err);
      $display("  dump     : u_fab.g1_evt=%04b u_fab.g1_comb=%04b u_fab.saf_v=%04b pdrop=%04b",
               u_fab.g1_evt, u_fab.g1_comb, u_fab.saf_v, u_fab.pdrop);
      $display("  dump     : x_in_v=%04b saf_r=%04b xb_in_r=%04b xb_v=%04b egr0=%0d bm=%04b",
               u_fab.x_in_v, u_fab.saf_r, u_fab.xb_in_r, u_fab.xb_v, u_fab.egr[0], u_fab.bm);
      $display("  dump     : status_up=%04b xb_r=%04b xbar_in_vld=%04b xbar_dst0=%0d xbar_locked0=%0b",
               u_fab.status_up, u_fab.xb_r, u_fab.u_xbar.in_vld, u_fab.u_xbar.in_dst[0],
               u_fab.u_xbar.locked[0]);
    end
  endtask

  task tb_preload_cnt;
    input [31:0] v;
    begin
      // Hierarchical preload of architecture-chosen saturating counter.
      // Do not add a top-level port (RTL change).
      preload_val = v;
      force u_fab.rt_shortest_unimpl = preload_val;
      tb_cycles(2);
      release u_fab.rt_shortest_unimpl;
      tb_cycles(1);
    end
  endtask

endmodule
