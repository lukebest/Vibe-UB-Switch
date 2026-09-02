// CFG6 terminate-class (AS-0.1 §9). Standalone for Verilator line coverage.
`timescale 1ns/1ps
module tc_cna_ep;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, cna_written, icrc_fail;
  logic [15:0] cna;
  logic [3:0] cfg6_hit, consume, reply_vld, reply_ready;
  logic [511:0] cfg6_data [0:3];
  logic [511:0] reply_data [0:3];
  integer fail, p;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_cna_ep u_c (
    .clk(clk), .rst_n(rst_n), .cna(cna), .cna_written(cna_written),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_data),
    .consume(consume), .reply_data(reply_data), .reply_vld(reply_vld),
    .reply_ready(reply_ready), .icrc_fail(icrc_fail)
  );
  initial begin
    fail = 0;
    rst_n = 0; cna = 16'h1111; cna_written = 1; cfg6_hit = 0; reply_ready = 4'b1111;
    for (p = 0; p < 4; p = p + 1) cfg6_data[p] = 512'd0;
    repeat (2) @(posedge clk);
    rst_n = 1;
    // 本CNA
    cfg6_data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    #1; cfg6_hit[0] = 1; #1;
    if (!consume[0] || !reply_vld[0]) begin
      $display("FAIL tc_cna_ep");
      $display("  stimulus : DCNA==written CNA");
      $display("  expected : consume+reply (terminate)");
      $display("  actual   : cons=%0b vld=%0b", consume[0], reply_vld[0]);
      fail = 1;
    end
    cfg6_hit[0] = 0; #1;
    // NLP=1
    cfg6_data[1] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd1, 8'd0));
    cfg6_hit[1] = 1; #1;
    if (!consume[1]) begin
      $display("FAIL tc_cna_ep");
      $display("  stimulus : NLP=1 DCNA!=CNA");
      $display("  expected : consume");
      $display("  actual   : 0");
      fail = 1;
    end
    cfg6_hit[1] = 0; #1;
    // else forward
    cfg6_data[2] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    cfg6_hit[2] = 1; #1;
    if (consume[2]) begin
      $display("FAIL tc_cna_ep");
      $display("  stimulus : miss CNA NLP=0");
      $display("  expected : forward (no consume)");
      $display("  actual   : consume=1");
      fail = 1;
    end
    cfg6_hit = 0;
    // unwritten
    cna_written = 0;
    cfg6_data[3] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    cfg6_hit[3] = 1; #1;
    if (consume[3]) begin
      $display("FAIL tc_cna_ep");
      $display("  stimulus : CNA unwritten");
      $display("  expected : no match");
      $display("  actual   : consume=1");
      fail = 1;
    end
    if (icrc_fail) begin
      $display("FAIL tc_cna_ep");
      $display("  stimulus : echo path");
      $display("  expected : icrc_fail=0 (RTL gap: no vibe_icrc in cna_ep)");
      $display("  actual   : 1");
      fail = 1;
    end
    if (!fail) $display("PASS tc_cna_ep");
    $finish;
  end
endmodule
