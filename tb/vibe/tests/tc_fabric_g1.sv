// Small fabric cluster (not vibe_suite). G1 drop + default-0 + CFG6 term.
`timescale 1ns/1ps
module tc_fabric_g1;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, device_rst, rt_wr_en, drop_g1, cna_written, irq_rt;
  logic [3:0] status_up, default_bm, nw_fab_vld, nw_fab_ready, fab_nw_vld, fab_nw_ready;
  logic [3:0] len_err, deadlock_drop, fab_mgmt_cfg6_hit;
  logic [15:0] rt_wr_idx, cna;
  logic [31:0] rt_wr_data, rt_shortest_unimpl, drop_down_cnt;
  logic [511:0] nw_fab_data [0:3];
  logic [511:0] fab_nw_data [0:3];
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  integer fail, p;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_fabric u_fab (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down_cnt),
    .deadlock_drop(deadlock_drop), .irq_rt(irq_rt),
    .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data)
  );
  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; rt_wr_en = 0; status_up = 4'b1111;
    default_bm = 4'd0; nw_fab_vld = 0; fab_nw_ready = 4'b1111;
    cna = 16'h1111; cna_written = 1;
    for (p = 0; p < 4; p = p + 1) nw_fab_data[p] = 512'd0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // write route dest=2 (do not occupy SAF with a prior packet)
    @(negedge clk);
    rt_wr_en = 1; rt_wr_idx = 16'd2; rt_wr_data = 32'h0000_0002;
    @(posedge clk);
    @(negedge clk);
    rt_wr_en = 0;
    // RT=10 G1 drop (2 beats so SAF done is definite)
    @(negedge clk);
    while (!nw_fab_ready[0]) @(posedge clk);
    nw_fab_data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b10, 4'd0, 16'h1, 16'h0002, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    nw_fab_vld[0] = 1;
    @(posedge clk);
    @(negedge clk);
    nw_fab_data[0] = 512'h2;
    @(posedge clk);
    @(negedge clk);
    nw_fab_vld[0] = 0;
    repeat (40) @(posedge clk);
    if (rt_shortest_unimpl === 32'd0) begin
      $display("FAIL tc_fabric_g1");
      $display("  stimulus : RT=10 1-beat");
      $display("  expected : rt_shortest_unimpl>=1");
      $display("  actual   : 0 drop_g1=%0b", drop_g1);
      $display("  hier     : u_fab.g1_evt / rt_shortest_unimpl");
      fail = 1;
    end
    // CFG6 terminate-class
    @(negedge clk);
    nw_fab_data[1] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    nw_fab_vld[1] = 1;
    @(posedge clk);
    @(negedge clk);
    nw_fab_vld[1] = 0;
    repeat (16) @(posedge clk);
    // multi-port G1
    @(negedge clk);
    nw_fab_data[2] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b11, 4'd0, 16'h1, 16'h0003, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    nw_fab_vld[2] = 1;
    @(posedge clk);
    @(negedge clk);
    nw_fab_vld[2] = 0;
    repeat (16) @(posedge clk);
    device_rst = 1;
    @(posedge clk);
    device_rst = 0;
    if (!fail) $display("PASS tc_fabric_g1");
    $finish;
  end
endmodule
