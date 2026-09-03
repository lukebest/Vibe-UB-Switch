// TP-RT-013 sat + CFG6 terminate drain. Real expected vs actual (not coverage).
`timescale 1ns/1ps
module tc_fabric_line_holes;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, device_rst, rt_wr_en, drop_g1, cna_written, irq_rt;
  logic [3:0] status_up, default_bm, ing_vld, ing_ready, egr_vld, egr_ready;
  logic [3:0] len_err, deadlock_drop, cfg6_hit;
  logic [15:0] rt_wr_idx, cna;
  logic [31:0] rt_wr_data, rt_shortest_unimpl, drop_down_cnt;
  logic [511:0] ing_data [0:3];
  logic [511:0] egr_data [0:3];
  logic [511:0] cfg6_data [0:3];
  integer fail, p, saw6, saw6b;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_fabric u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .ing_data(ing_data), .ing_vld(ing_vld), .ing_ready(ing_ready),
    .egr_data(egr_data), .egr_vld(egr_vld), .egr_ready(egr_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down_cnt),
    .deadlock_drop(deadlock_drop), .irq_rt(irq_rt),
    .cna(cna), .cna_written(cna_written),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_data)
  );

  task automatic fail_at;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail = 1;
      $display("FAIL tc_fabric_line_holes");
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe units");
    end
  endtask

  task automatic send2;
    input integer port;
    input [3:0]  cfg;
    input [1:0]  rt;
    input [15:0] dcna;
    begin
      @(negedge clk);
      while (!ing_ready[port]) @(posedge clk);
      ing_data[port] = vibe_tb_mk_beat(vibe_tb_mk_flit(
          cfg, rt, 4'd0, 16'h1, dcna, vibe_tb_plen_nflit(5),
          16'd0, 8'd0, 3'd0, 8'd0));
      ing_vld[port] = 1;
      @(posedge clk);
      @(negedge clk);
      ing_data[port] = 512'h2;
      @(posedge clk);
      @(negedge clk);
      ing_vld[port] = 0;
    end
  endtask

  initial begin
    fail = 0; saw6 = 0; saw6b = 0;
    // Icarus: pin VOQ wr_vl so vibe_nw512_flit0(xb_d) does not combo-storm
    // on the first RT=00 xbar grant (same as harness / tc_cfg9_no_icrc).
    force u_fab.g_egr[0].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[1].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[2].u_voq.wr_vl = 4'd0;
    force u_fab.g_egr[3].u_voq.wr_vl = 4'd0;
    rst_n = 0; device_rst = 0; rt_wr_en = 0; status_up = 4'b1111;
    default_bm = 4'd0; ing_vld = 0; egr_ready = 4'b1111;
    cna = 16'h1111; cna_written = 1;
    for (p = 0; p < 4; p = p + 1) ing_data[p] = 512'd0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    // 1-beat CFG6 terminate (本CNA)
    @(negedge clk);
    while (!ing_ready[0]) @(posedge clk);
    ing_data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h1, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    ing_vld[0] = 1;
    @(posedge clk);
    if (cfg6_hit[0]) saw6 = 1;
    @(negedge clk);
    ing_vld[0] = 0;
    repeat (12) begin
      @(posedge clk);
      if (cfg6_hit[0]) saw6 = 1;
    end
    if (!saw6) begin
      fail_at("1-beat CFG6 DCNA==CNA written",
              "cfg6_hit[0]=1 (terminate, not xbar)",
              "cfg6_hit stayed 0",
              "u_fab.cfg6_hit / cfg6_term");
    end

    // Multi-beat CFG6 terminate
    send2(0, 4'd6, 2'b00, 16'h1111);
    repeat (20) begin
      @(posedge clk);
      if (cfg6_hit[0]) saw6b = 1;
    end
    if (!fail && !saw6b) begin
      fail_at("2-beat CFG6 DCNA==CNA (drain)",
              "cfg6_hit[0]=1 during SOP or drain",
              "cfg6_hit stayed 0",
              "u_fab.cfg6_drain");
    end

    // TP-RT-013: sat at 32'hFFFF_FFFF
    force u_fab.rt_shortest_unimpl = 32'hFFFF_FFFE;
    repeat (2) @(posedge clk);
    release u_fab.rt_shortest_unimpl;
    @(posedge clk);
    if (rt_shortest_unimpl !== 32'hFFFF_FFFE) begin
      fail_at("hierarchical preload rt_shortest_unimpl=FFFFFFFE",
              "counter reads FFFFFFFE after release",
              "preload did not stick",
              "u_fab.rt_shortest_unimpl");
    end else begin
      send2(2, 4'd3, 2'b10, 16'h0003);
      repeat (24) @(posedge clk);
      if (rt_shortest_unimpl !== 32'hFFFF_FFFF) begin
        fail_at("preload FFFFFFFE + one RT=10",
                "FFFFFFFF (sat, no wrap)",
                "counter not FFFFFFFF",
                "u_fab.rt_shortest_unimpl");
      end else begin
        send2(3, 4'd3, 2'b11, 16'h0004);
        repeat (16) @(posedge clk);
        if (rt_shortest_unimpl !== 32'hFFFF_FFFF) begin
          fail_at("second G1 at FFFFFFFF",
                  "stay FFFFFFFF (no wrap to 0)",
                  "counter wrapped or changed",
                  "u_fab.rt_shortest_unimpl");
        end
      end
    end
    // RT=00 dest in table → xbar grant (xb_v&&xb_sop / egr_sop header capture)
    begin : fwd_rt00
      integer saw_egr;
      saw_egr = 0;
      @(negedge clk);
      rt_wr_en = 1; rt_wr_idx = 16'd5; rt_wr_data = 32'h0000_0001;
      @(posedge clk);
      @(negedge clk);
      rt_wr_en = 0;
      send2(1, 4'd3, 2'b00, 16'h0005);
      repeat (40) begin
        @(posedge clk);
        if (egr_vld[0]) saw_egr = 1;
      end
      if (!fail && !saw_egr) begin
        fail_at("RT=00 DCNA=5 bitmap port0",
                "egr_vld[0] (xbar grant + VOQ pop)",
                "no egress",
                "u_fab.xb_v / egr_sop");
      end
    end
    if (!fail) $display("PASS tc_fabric_line_holes");
    $finish;
  end
endmodule
