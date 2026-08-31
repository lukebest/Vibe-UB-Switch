// Unit harness: vibe_route_lu + vibe_port_sel (AS-0.1 §2/§8).
// Used when iverilog X on 640b unpacked xbar ports blocks fabric egress.

`timescale 1ns/1ps

module vibe_psel_harness;
  logic        clk, rst_n, device_rst;
  logic [3:0]  bitmap, status_up, default_bm;
  logic [1:0]  rt;
  logic        drop_g1, sel_vld, drop;
  logic [3:0]  cfg, vl;
  logic [15:0] src, dest;
  logic [1:0]  egr;
  logic [31:0] drop_down;
  logic        wr_en;
  logic [15:0] wr_idx;
  logic [31:0] wr_data;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(wr_en), .wr_idx(wr_idx), .wr_data(wr_data),
    .dest(dest), .rt(rt), .lu_vld(sel_vld),
    .bitmap(bitmap), .drop_g1(drop_g1)
  );

  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(sel_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down)
  );

  task automatic cycles;
    input integer n;
    integer i;
    begin
      for (i = 0; i < n; i = i + 1) @(posedge clk);
    end
  endtask

  task automatic reset;
    begin
      rst_n = 0; device_rst = 0; status_up = 4'b1111; default_bm = 4'd0;
      rt = 2'b00; sel_vld = 0; cfg = 4'd3; vl = 4'd0;
      src = 16'd0; dest = 16'd0; wr_en = 0; wr_idx = 0; wr_data = 0;
      cycles(3);
      rst_n = 1;
      cycles(2);
    end
  endtask

  task automatic wr_route;
    input [15:0] d;
    input [3:0]  bm;
    begin
      @(negedge clk);
      wr_en = 1; wr_idx = d; wr_data = {28'd0, bm};
      @(posedge clk);
      @(negedge clk);
      wr_en = 0;
      cycles(1);
    end
  endtask

  // Pulse sel_vld for 2 cycles so route_lu bitmap (registered) is visible
  // to port_sel on the second cycle.
  task automatic select;
    input [1:0]  rt_i;
    input [3:0]  vl_i;
    input [15:0] src_i;
    input [15:0] dst_i;
    begin
      @(negedge clk);
      rt = rt_i; vl = vl_i; src = src_i; dest = dst_i;
      sel_vld = 1;
      @(posedge clk);
      @(posedge clk);
      @(negedge clk);
      sel_vld = 0;
      cycles(1);
    end
  endtask
endmodule
