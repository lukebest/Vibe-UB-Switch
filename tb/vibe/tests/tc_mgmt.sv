// vibe_mgmt wrapper: cfg + cna_ep + irq + rst (AS-0.1 §4/§10).
`timescale 1ns/1ps
module tc_mgmt;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, cfg_wr_vld, cfg_wr_ready, cna_written, rt_wr_en, device_rst, irq_logic;
  logic [2:0] cfg_wr_cmd;
  logic [15:0] cfg_wr_idx, cna, rt_wr_idx;
  logic [31:0] cfg_wr_data, rt_wr_data;
  logic [3:0] default_bm, port_rst, lmsm_go, cfg6_hit, cfg6_consume, reply_vld, reply_ready;
  logic [3:0] rx_ovf, fc_ovf, proto_err, retry_error, len_err, deadlock_drop, afifo_ovf;
  logic drop_g1;
  logic [639:0] cfg6_data [0:3];
  logic [639:0] reply_data [0:3];
  integer fail, p;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_mgmt u_m (
    .clk(clk), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_data),
    .cfg6_consume(cfg6_consume), .reply_data(reply_data), .reply_vld(reply_vld),
    .reply_ready(reply_ready),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .len_err(len_err), .deadlock_drop(deadlock_drop),
    .drop_g1(drop_g1), .afifo_ovf(afifo_ovf), .irq_logic(irq_logic)
  );
  initial begin
    fail = 0;
    rst_n = 0; cfg_wr_vld = 0; cfg_wr_cmd = 0; cfg_wr_idx = 0; cfg_wr_data = 0;
    cfg6_hit = 0; reply_ready = 4'b1111;
    rx_ovf = 0; fc_ovf = 0; proto_err = 0; retry_error = 0;
    len_err = 0; deadlock_drop = 0; drop_g1 = 0; afifo_ovf = 0;
    for (p = 0; p < 4; p = p + 1) cfg6_data[p] = 640'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (!cfg_wr_ready) begin
      $display("FAIL tc_mgmt");
      $display("  stimulus : reset");
      $display("  expected : cfg_wr_ready");
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_cmd = 3'd0; cfg_wr_data = 32'h0000_1111; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cfg_wr_vld = 0;
    @(posedge clk);
    if (cna !== 16'h1111 || !cna_written) begin
      $display("FAIL tc_mgmt");
      $display("  stimulus : CNA write");
      $display("  expected : cna=1111 written");
      $display("  actual   : %h %0b", cna, cna_written);
      fail = 1;
    end
    @(negedge clk);
    drop_g1 = 1;
    @(posedge clk);
    @(negedge clk);
    if (!irq_logic) begin
      $display("FAIL tc_mgmt");
      $display("  stimulus : drop_g1");
      $display("  expected : irq_logic sticky");
      fail = 1;
    end
    cfg6_data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    #1; cfg6_hit[0] = 1; #1;
    if (!cfg6_consume[0]) begin
      $display("FAIL tc_mgmt");
      $display("  stimulus : CFG6 本CNA");
      $display("  expected : consume");
      fail = 1;
    end
    cfg6_hit = 0;
    @(negedge clk);
    cfg_wr_cmd = 3'd3; cfg_wr_idx = 16'd0; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cfg_wr_vld = 0;
    repeat (2) @(posedge clk);
    if (!fail) $display("PASS tc_mgmt");
    $finish;
  end
endmodule
