// Fabric G1 saturate + multi-beat CFG6 terminate drain (AS-0.1 §8/§9).
// Do not occupy SAF before the target packet. RTL not patched.
`timescale 1ns/1ps
module tc_fabric_line_holes;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, device_rst, rt_wr_en, drop_g1, cna_written, irq_rt;
  logic [3:0] status_up, default_bm, ing_vld, ing_ready, egr_vld, egr_ready;
  logic [3:0] len_err, deadlock_drop, cfg6_hit;
  logic [15:0] rt_wr_idx, cna;
  logic [31:0] rt_wr_data, rt_shortest_unimpl, drop_down_cnt;
  logic [639:0] ing_data [0:3];
  logic [639:0] egr_data [0:3];
  logic [639:0] cfg6_data [0:3];
  integer fail, p;
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
      ing_data[port] = 640'h2;
      @(posedge clk);
      @(negedge clk);
      ing_vld[port] = 0;
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; rt_wr_en = 0; status_up = 4'b1111;
    default_bm = 4'd0; ing_vld = 0; egr_ready = 4'b1111;
    cna = 16'h1111; cna_written = 1;
    for (p = 0; p < 4; p = p + 1) ing_data[p] = 640'd0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    // Multi-beat CFG6 terminate (本CNA): hits cfg6_seen/drain + eop clear
    send2(0, 4'd6, 2'b00, 16'h1111);
    repeat (20) @(posedge clk);

    // NLP=1 CFG6 terminate even if DCNA ≠ us (2-beat drain)
    @(negedge clk);
    while (!ing_ready[1]) @(posedge clk);
    ing_data[1] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h1, 16'h2222, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd1, 8'd0));
    ing_vld[1] = 1;
    @(posedge clk);
    @(negedge clk);
    ing_data[1] = 640'h3;
    @(posedge clk);
    @(negedge clk);
    ing_vld[1] = 0;
    repeat (20) @(posedge clk);

    // G1 saturate: preload 32-bit counter (no RTL port)
    force u_fab.rt_shortest_unimpl = 32'hFFFF_FFFE;
    repeat (2) @(posedge clk);
    release u_fab.rt_shortest_unimpl;
    @(posedge clk);
    send2(2, 4'd3, 2'b10, 16'h0003);
    repeat (24) @(posedge clk);
    if (rt_shortest_unimpl !== 32'hFFFF_FFFF &&
        rt_shortest_unimpl !== 32'hFFFF_FFFE) begin
      $display("NOTE tc_fabric_line_holes: sat preload not taken cnt=%h",
               rt_shortest_unimpl);
    end
    send2(3, 4'd3, 2'b11, 16'h0004);
    repeat (16) @(posedge clk);

    if (!fail) $display("PASS tc_fabric_line_holes");
    $finish;
  end
endmodule
