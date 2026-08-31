// Tiny driver so Verilator can collect coverage on vibe_port_sel only.
`timescale 1ns/1ps
module tc_psel_cov;
  logic clk, rst_n, drop_g1, sel_vld, drop;
  logic [3:0] bitmap, status_up, default_bm, cfg, vl;
  logic [1:0] rt, egr;
  logic [15:0] src, dest;
  logic [31:0] drop_down;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(sel_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down)
  );

  integer k;
  initial begin
    rst_n = 0; bitmap = 4'b1111; status_up = 4'b1111; default_bm = 0;
    rt = 0; drop_g1 = 0; sel_vld = 0; cfg = 3; src = 1; dest = 2; vl = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    for (k = 0; k < 8; k = k + 1) begin
      @(negedge clk);
      rt = k[1:0]; vl = k[3:0]; drop_g1 = (k[1:0] >= 2);
      sel_vld = 1;
      @(posedge clk);
    end
    sel_vld = 0;
    // default_bm all-0 → port 0; port0 down → drop_down
    @(negedge clk);
    bitmap = 4'd0; status_up = 4'b1110; default_bm = 4'd0;
    rt = 2'b00; drop_g1 = 0; sel_vld = 1;
    @(posedge clk);
    @(negedge clk);
    status_up = 4'b0000;
    @(posedge clk);
    // default_bm nonempty
    @(negedge clk);
    default_bm = 4'b0100; status_up = 4'b1111; bitmap = 4'd0;
    @(posedge clk);
    // RT=00 sticky miss (use_bm bit not sticky)
    @(negedge clk);
    bitmap = 4'b0010; vl = 4'd3; rt = 2'b00;
    @(posedge clk);
    @(negedge clk);
    bitmap = 4'b1000;
    @(posedge clk);
    sel_vld = 0;
    repeat (4) @(posedge clk);
    $finish;
  end
endmodule
