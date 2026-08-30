// VOQ rd_en path (separate from 1 us deadlock timeout).
`timescale 1ns/1ps
module tc_voq_rd;
  logic clk, rst_n, wr_en, wr_sop, wr_eop, wr_ready, rd_en, rd_sop, rd_eop;
  logic [3:0] wr_vl, rd_vl;
  logic [639:0] wr_data, rd_data;
  logic [15:0] nonempty;
  logic [5:0] occ_vl0;
  logic deadlock_drop;
  logic [31:0] deadlock_cnt;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_voq_egr #(.DEPTH(32)) u_v (
    .clk(clk), .rst_n(rst_n),
    .wr_vl(wr_vl), .wr_en(wr_en), .wr_data(wr_data),
    .wr_sop(wr_sop), .wr_eop(wr_eop), .wr_ready(wr_ready),
    .rd_vl(rd_vl), .rd_en(rd_en), .rd_data(rd_data), .rd_sop(rd_sop), .rd_eop(rd_eop),
    .nonempty(nonempty), .occ_vl0(occ_vl0),
    .deadlock_drop(deadlock_drop), .deadlock_cnt(deadlock_cnt)
  );
  initial begin
    fail = 0;
    rst_n = 0; wr_en = 0; rd_en = 0; wr_vl = 0; rd_vl = 0;
    wr_data = 640'hA5; wr_sop = 1; wr_eop = 1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    repeat (2) @(posedge clk);
    @(negedge clk);
    if (!nonempty[0]) begin
      $display("FAIL tc_voq_rd");
      $display("  stimulus : wr VL0");
      $display("  expected : nonempty[0]");
      $display("  actual   : nonempty=%h", nonempty);
      fail = 1;
    end
    rd_en = 1; rd_vl = 0;
    @(posedge clk);
    rd_en = 0;
    @(negedge clk);
    // second write/read on VL3
    wr_vl = 4'd3; wr_data = 640'h33; wr_en = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    @(posedge clk);
    @(negedge clk);
    rd_vl = 4'd3; rd_en = 1;
    @(posedge clk);
    rd_en = 0;
    if (!fail) $display("PASS tc_voq_rd");
    $finish;
  end
endmodule
