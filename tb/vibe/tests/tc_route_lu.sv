// Route table dest→bitmap. Default all-0. RT=10/11 drop_g1 (AS-0.1 G1).
`timescale 1ns/1ps
module tc_route_lu;
  logic clk, rst_n, device_rst, wr_en, lu_vld, drop_g1;
  logic [15:0] wr_idx, dest;
  logic [31:0] wr_data;
  logic [1:0] rt;
  logic [3:0] bitmap;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(wr_en), .wr_idx(wr_idx), .wr_data(wr_data),
    .dest(dest), .rt(rt), .lu_vld(lu_vld),
    .bitmap(bitmap), .drop_g1(drop_g1)
  );
  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; wr_en = 0; lu_vld = 0;
    wr_idx = 0; wr_data = 0; dest = 16'd1; rt = 2'b00;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    @(negedge clk);
    lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    lu_vld = 0;
    if (bitmap !== 4'd0 || drop_g1) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : lu dest=1 empty table");
      $display("  expected : bitmap=0 drop_g1=0");
      $display("  actual   : bm=%04b g1=%0b", bitmap, drop_g1);
      fail = 1;
    end
    @(negedge clk);
    wr_en = 1; wr_idx = 16'd1; wr_data = 32'h0000_000F;
    @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    dest = 16'd1; rt = 2'b00; lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    lu_vld = 0;
    if (bitmap !== 4'b1111) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : wr dest=1 data=F, lu RT=00");
      $display("  expected : bitmap=1111");
      $display("  actual   : %04b tbl1=%h", bitmap, u_rt.tbl[1]);
      fail = 1;
    end
    @(negedge clk);
    rt = 2'b10; lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!drop_g1 || bitmap !== 4'd0) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : RT=10");
      $display("  expected : drop_g1=1 bitmap=0 (not alias 00)");
      $display("  actual   : g1=%0b bm=%04b", drop_g1, bitmap);
      fail = 1;
    end
    lu_vld = 0;
    @(negedge clk);
    rt = 2'b11; lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!drop_g1) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : RT=11");
      $display("  expected : drop_g1");
      fail = 1;
    end
    lu_vld = 0;
    @(negedge clk);
    rt = 2'b01; lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (drop_g1 || bitmap !== 4'b1111) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : RT=01 after write");
      $display("  expected : forward bitmap=F");
      $display("  actual   : g1=%0b bm=%04b", drop_g1, bitmap);
      fail = 1;
    end
    lu_vld = 0;
    @(negedge clk);
    device_rst = 1;
    @(posedge clk);
    @(negedge clk);
    device_rst = 0;
    dest = 16'd1; rt = 2'b00; lu_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (bitmap !== 4'd0) begin
      $display("FAIL tc_route_lu");
      $display("  stimulus : device_rst then lu");
      $display("  expected : table all-0");
      $display("  actual   : %04b", bitmap);
      fail = 1;
    end
    if (!fail) $display("PASS tc_route_lu");
    $finish;
  end
endmodule
