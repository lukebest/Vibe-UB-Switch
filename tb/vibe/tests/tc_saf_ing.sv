// SAF: do not present until declared beats assembled (AS-0.1 §8).
`timescale 1ns/1ps
module tc_saf_ing;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, in_vld, in_ready, pkt_vld, pkt_ready, pkt_sop, pkt_eop, len_err;
  logic [639:0] in_data, pkt_data;
  logic [15:0] pkt_bytes;
  integer fail, early, i, nbeat;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_saf_ing #(.DEPTH(128)) u_s (
    .clk(clk), .rst_n(rst_n),
    .in_data(in_data), .in_vld(in_vld), .in_ready(in_ready),
    .pkt_data(pkt_data), .pkt_vld(pkt_vld), .pkt_ready(pkt_ready),
    .pkt_sop(pkt_sop), .pkt_eop(pkt_eop), .pkt_bytes(pkt_bytes), .len_err(len_err)
  );
  initial begin
    fail = 0; early = 0;
    rst_n = 0; in_vld = 0; pkt_ready = 0; in_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // 5 flits → 2 declared beats; drive only first
    nbeat = vibe_tb_decl_beats(vibe_tb_plen_nflit(5));
    @(negedge clk);
    while (!in_ready) @(posedge clk);
    in_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    in_vld = 1;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    repeat (4) begin
      @(posedge clk);
      if (pkt_vld) early = 1;
    end
    if (early) begin
      $display("FAIL tc_saf_ing");
      $display("  stimulus : 1 of 2 declared beats");
      $display("  expected : pkt_vld=0 (SAF, not cut-through)");
      $display("  actual   : 1");
      fail = 1;
    end
    // second beat
    @(negedge clk);
    in_data = 640'hB;
    in_vld = 1;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    repeat (4) @(posedge clk);
    if (!pkt_vld) begin
      $display("FAIL tc_saf_ing");
      $display("  stimulus : 2nd beat of 2");
      $display("  expected : pkt_vld");
      $display("  actual   : 0 nbeat=%0d", nbeat);
      fail = 1;
    end
    // drain
    pkt_ready = 1;
    repeat (8) @(posedge clk);
    pkt_ready = 0;
    // oversize → len_err
    @(negedge clk);
    in_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_oversize(),
        16'd0, 8'd0, 3'd0, 8'd0));
    in_vld = 1;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    @(posedge clk);
    if (!len_err) begin
      $display("FAIL tc_saf_ing");
      $display("  stimulus : oversize PLEN");
      $display("  expected : len_err");
      $display("  actual   : 0");
      fail = 1;
    end
    // 9-flit / 3 declared beats: mid-assemble else (beat 2 of 3)
    @(negedge clk);
    in_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_nflit(9),
        16'd0, 8'd0, 3'd0, 8'd0));
    in_vld = 1; pkt_ready = 0;
    @(posedge clk);
    @(negedge clk);
    in_data = 640'hC1;
    @(posedge clk);
    @(negedge clk);
    if (pkt_vld) begin
      $display("FAIL tc_saf_ing");
      $display("  stimulus : 2 of 3 declared beats");
      $display("  expected : pkt_vld=0 (still assembling)");
      fail = 1;
    end
    in_data = 640'hC2;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    repeat (3) @(posedge clk);
    pkt_ready = 1;
    repeat (8) @(posedge clk);
    pkt_ready = 0;
    // 1-beat legal
    @(negedge clk);
    in_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    in_vld = 1;
    @(posedge clk);
    @(negedge clk);
    in_vld = 0;
    repeat (3) @(posedge clk);
    pkt_ready = 1;
    repeat (4) @(posedge clk);
    if (!fail) $display("PASS tc_saf_ing");
    $finish;
  end
endmodule
