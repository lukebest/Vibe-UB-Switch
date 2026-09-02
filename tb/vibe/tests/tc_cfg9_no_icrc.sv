// TP-ICRC-003 / AS-0.1 §13: CFG9 has no ICRC. Transit/forward path must not recompute.
`timescale 1ns/1ps
module tc_cfg9_no_icrc;
  `include "vibe_tb_defs.svh"

  logic clk, rst_n, device_rst, rt_wr_en, drop_g1, cna_written, irq_rt;
  logic [3:0] status_up, default_bm, ing_vld, ing_ready, egr_vld, egr_ready;
  logic [3:0] len_err, deadlock_drop, cfg6_hit;
  logic [15:0] rt_wr_idx, cna;
  logic [31:0] rt_wr_data, rt_shortest_unimpl, drop_down_cnt;
  logic [511:0] ing_data [0:3];
  logic [511:0] egr_data [0:3];
  logic [511:0] cfg6_data [0:3];
  integer fail, p;
  reg [159:0] in_f, saf_f;

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

  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; rt_wr_en = 0; status_up = 4'b1111;
    default_bm = 4'd0; ing_vld = 0; egr_ready = 4'b1111;
    cna = 16'h1111; cna_written = 1;
    for (p = 0; p < 4; p = p + 1) ing_data[p] = 512'd0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    @(negedge clk);
    rt_wr_en = 1; rt_wr_idx = 16'h0001; rt_wr_data = 32'h0000_000F;
    @(posedge clk);
    @(negedge clk);
    rt_wr_en = 0;

    in_f = vibe_tb_mk_flit(4'd9, 2'b00, 4'd0, 16'h0002, 16'h0001,
                           vibe_tb_plen_nflit(5), 16'hA5A5, 8'h5A, 3'd0, 8'h00);
    @(negedge clk);
    while (!ing_ready[0]) @(posedge clk);
    ing_data[0] = vibe_tb_mk_beat(in_f);
    ing_vld[0] = 1;
    @(posedge clk);
    @(negedge clk);
    ing_data[0] = 512'h2;
    @(posedge clk);
    @(negedge clk);
    ing_vld[0] = 0;
    repeat (16) @(posedge clk);

    saf_f = u_fab.saf_d[0][511:352];
    if (cfg6_hit[0]) begin
      $display("FAIL tc_cfg9_no_icrc");
      $display("  stimulus : CFG9 RT=00 dest=1 (not terminate class)");
      $display("  expected : cfg6_hit=0 (CFG9 has no ICRC; forward)");
      $display("  actual   : cfg6_hit=1");
      $display("  hier     : u_fab.cfg6_hit");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end else if (vibe_nth_cci(saf_f) !== vibe_nth_cci(in_f) ||
                 vibe_nth_lbf(saf_f) !== vibe_nth_lbf(in_f)) begin
      $display("FAIL tc_cfg9_no_icrc");
      $display("  stimulus : CFG9 sitting in SAF (AS-0.1 §13 no ICRC)");
      $display("  expected : CCI/LBF unchanged (fabric has no vibe_icrc)");
      $display("  actual   : SAF CCI/LBF rewritten");
      $display("  hier     : u_fab.saf_d (no ICRC unit)");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end else if (!u_fab.x_in_v[0] && !u_fab.g1_comb[0]) begin
      $display("FAIL tc_cfg9_no_icrc");
      $display("  stimulus : CFG9 RT=00 dest=1 bitmap=1111");
      $display("  expected : x_in_v=1 (forward; no ICRC terminate)");
      $display("  actual   : not presented to xbar");
      $display("  hier     : u_fab.x_in_v / cfg6_hit");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_cfg9_no_icrc");
    $finish;
  end
endmodule
