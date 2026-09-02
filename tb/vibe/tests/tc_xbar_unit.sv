// Unit probe of vibe_xbar (debug why fabric xb_in_r stays 0).
`timescale 1ns/1ps

module tc_xbar_unit;
  logic         clk, rst_n;
  logic [3:0]   status_up, in_vld, in_sop, in_eop, in_ready;
  logic [3:0]   out_vld, out_sop, out_eop, out_ready;
  logic [511:0] in_data [0:3];
  logic [511:0] out_data [0:3];
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
      in_data[i] = 512'd0;
      in_dst[i]  = 2'd0;
    end
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    in_data[0] = {160'hA, 352'd0};
    in_dst[0]  = 2'd1;
    in_vld[0]  = 1'b1;
    in_sop[0]  = 1'b1;
    in_eop[0]  = 1'b1;
    #0;
    $display("XBAR combo in_ready=%04b out_vld=%04b dst0=%0d locked0=%0b",
             in_ready, out_vld, in_dst[0], u_xbar.locked[0]);
    @(posedge clk);
    $display("XBAR +1   in_ready=%04b out_vld=%04b out1=%h",
             in_ready, out_vld, out_data[1][511:352]);
    if (!(out_vld[1] && in_ready[0])) begin
      $display("FAIL tc_xbar_unit");
      $display("  stimulus : 1-beat in0 dest=1, all ready/up");
      $display("  expected : out_vld[1]=1 in_ready[0]=1");
      $display("  actual   : out_vld=%04b in_ready=%04b", out_vld, in_ready);
      $display("  hier     : u_xbar.in_dst / locked / out_ready");
      $display("  reproduce: iverilog + vvp tc_xbar_unit");
      $finish;
    end
    in_vld = 0; in_sop = 0; in_eop = 0;
    repeat (2) @(posedge clk);
    // 2-beat locked grant (sop then eop)
    in_data[0] = {160'hB, 352'd0};
    in_dst[0]  = 2'd2;
    in_vld[0]  = 1; in_sop[0] = 1; in_eop[0] = 0;
    @(posedge clk);
    in_sop[0] = 0; in_eop[0] = 1; in_data[0] = {160'hC, 352'd0};
    @(posedge clk);
    in_vld[0] = 0; in_eop[0] = 0;
    repeat (2) @(posedge clk);
    // locked grant with out_ready=0 (else of locked if)
    in_data[0] = {160'hE, 352'd0};
    in_dst[0]  = 2'd1;
    in_vld[0]  = 1; in_sop[0] = 1; in_eop[0] = 0; out_ready = 4'b1111;
    @(posedge clk);
    out_ready[1] = 0; in_sop[0] = 0; in_eop[0] = 0;
    @(posedge clk);
    out_ready[1] = 1; in_eop[0] = 1; in_data[0] = {160'hF, 352'd0};
    @(posedge clk);
    in_vld[0] = 0; in_eop[0] = 0;
    repeat (2) @(posedge clk);
    // conflict: two ingress to dest 3
    in_data[0] = {160'h1, 352'd0}; in_dst[0] = 2'd3; in_vld[0] = 1; in_sop[0] = 1; in_eop[0] = 1;
    in_data[1] = {160'h2, 352'd0}; in_dst[1] = 2'd3; in_vld[1] = 1; in_sop[1] = 1; in_eop[1] = 1;
    #0;
    @(posedge clk);
    in_vld = 0;
    // down port: status_up[0]=0 gets no data
    status_up[0] = 1'b0;
    in_data[2] = {160'hD, 352'd0}; in_dst[2] = 2'd0; in_vld[2] = 1; in_sop[2] = 1; in_eop[2] = 1;
    #0;
    if (out_vld[0]) begin
      $display("FAIL tc_xbar_unit");
      $display("  stimulus : dest=0 status_up[0]=0");
      $display("  expected : out_vld[0]=0 (down, no DLLDP)");
      $display("  actual   : 1");
      $finish;
    end
    in_vld = 0;
    $display("PASS tc_xbar_unit");
    $finish;
  end
endmodule
