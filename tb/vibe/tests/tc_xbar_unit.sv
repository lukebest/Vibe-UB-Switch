// Unit probe of vibe_xbar (debug why fabric xb_in_r stays 0).
`timescale 1ns/1ps

module tc_xbar_unit;
  logic         clk, rst_n;
  logic [3:0]   status_up, in_vld, in_sop, in_eop, in_ready;
  logic [3:0]   out_vld, out_sop, out_eop, out_ready;
  logic [639:0] in_data [0:3];
  logic [639:0] out_data [0:3];
  logic [1:0]   in_dst [0:3];
  integer       i;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_xbar u_xbar (
    .clk(clk), .rst_n(rst_n), .status_up(status_up),
    .in_data(in_data), .in_vld(in_vld), .in_sop(in_sop), .in_eop(in_eop),
    .in_dst(in_dst), .in_ready(in_ready),
    .out_data(out_data), .out_vld(out_vld), .out_sop(out_sop), .out_eop(out_eop),
    .out_ready(out_ready)
  );

  initial begin
    rst_n = 0; status_up = 4'b1111;
    in_vld = 0; in_sop = 0; in_eop = 0; out_ready = 4'b1111;
    for (i = 0; i < 4; i = i + 1) begin
      in_data[i] = 640'd0;
      in_dst[i]  = 2'd0;
    end
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    in_data[0] = {160'hA, 480'd0};
    in_dst[0]  = 2'd1;
    in_vld[0]  = 1'b1;
    in_sop[0]  = 1'b1;
    in_eop[0]  = 1'b1;
    #0;
    $display("XBAR combo in_ready=%04b out_vld=%04b dst0=%0d locked0=%0b",
             in_ready, out_vld, in_dst[0], u_xbar.locked[0]);
    @(posedge clk);
    $display("XBAR +1   in_ready=%04b out_vld=%04b out1=%h",
             in_ready, out_vld, out_data[1][639:480]);
    if (out_vld[1] && in_ready[0])
      $display("PASS tc_xbar_unit");
    else begin
      $display("FAIL tc_xbar_unit");
      $display("  stimulus : 1-beat in0 dest=1, all ready/up");
      $display("  expected : out_vld[1]=1 in_ready[0]=1");
      $display("  actual   : out_vld=%04b in_ready=%04b", out_vld, in_ready);
      $display("  hier     : u_xbar.in_dst / locked / out_ready");
      $display("  reproduce: iverilog + vvp tc_xbar_unit");
    end
    $finish;
  end
endmodule
