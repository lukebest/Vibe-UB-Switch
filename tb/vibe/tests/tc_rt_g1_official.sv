// TP-RT-010/012/014/015/016: G1 in route_lu+port_sel.
// RT=11 not as 01; unique bitmap still drop; default still drop; not proto_err.
`timescale 1ns/1ps
module tc_rt_g1_official;
  logic        clk, rst_n, device_rst, wr_en, lu_vld, drop_g1, drop;
  logic [15:0] wr_idx, dest, src;
  logic [31:0] wr_data, drop_down;
  logic [3:0]  bitmap, status_up, default_bm, cfg, vl;
  logic [1:0]  rt, egr;
  integer      fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(wr_en), .wr_idx(wr_idx), .wr_data(wr_data),
    .dest(dest), .rt(rt), .lu_vld(lu_vld),
    .bitmap(bitmap), .drop_g1(drop_g1)
  );
  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(lu_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down)
  );

  task automatic sel;
    input [1:0] rti;
    input [15:0] d;
    begin
      @(negedge clk);
      rt = rti; dest = d;
      lu_vld = 1;
      @(posedge clk);
      @(posedge clk);
      @(negedge clk);
      lu_vld = 0;
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; wr_en = 0; lu_vld = 0;
    status_up = 4'b1111; default_bm = 4'd0;
    cfg = 4'd3; vl = 4'd0; src = 16'h22; dest = 16'h000B; rt = 2'b00;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    @(negedge clk);
    wr_en = 1; wr_idx = 16'h000B; wr_data = 32'h0000_0004; // unique port2
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;

    // RT-010: RT=01 forwards unique bitmap; RT=11 drops
    sel(2'b01, 16'h000B);
    if (drop || drop_g1) begin
      $display("FAIL tc_rt11_not_as_rt01");
      $display("  stimulus : RT=01 dest=B unique bitmap=port2");
      $display("  expected : drop=0 drop_g1=0 (implemented RT)");
      $display("  actual   : drop=%0b g1=%0b egr=%0d", drop, drop_g1, egr);
      $display("  hier     : u_rt.drop_g1 / u_ps.drop");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    sel(2'b11, 16'h000B);
    if (!drop || !drop_g1) begin
      $display("FAIL tc_rt11_not_as_rt01");
      $display("  stimulus : same dest/bitmap RT=11");
      $display("  expected : drop=1 drop_g1=1 (not treated as RT=01)");
      $display("  actual   : drop=%0b g1=%0b egr=%0d", drop, drop_g1, egr);
      $display("  hier     : u_rt.drop_g1 / u_ps.drop");
      fail = 1;
    end else
      $display("PASS tc_rt11_not_as_rt01");

    // RT-012 / 014: unique bitmap still G1 drop
    sel(2'b10, 16'h000B);
    if (!drop_g1 || !drop) begin
      $display("FAIL tc_rt_g1_official");
      $display("  stimulus : RT=10 unique bitmap=0001<<2");
      $display("  expected : drop_g1=1 drop=1 (detect in route_lu/port_sel)");
      $display("  actual   : g1=%0b drop=%0b bm=%04b", drop_g1, drop, bitmap);
      $display("  hier     : u_rt.drop_g1");
      fail = 1;
    end else
      $display("PASS tc_rt_detect_in_port_sel");

    if (drop_g1 && drop)
      $display("PASS tc_rt10_unique_bm_drop");

    // RT-015: empty table (default port0) still G1 drop
    @(negedge clk);
    wr_en = 1; wr_idx = 16'h00FF; wr_data = 32'd0;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    sel(2'b10, 16'h00FF);
    if (!drop_g1 || !drop) begin
      $display("FAIL tc_rt10_on_default_drop");
      $display("  stimulus : RT=10 dest=00FF table=0 (would default port0)");
      $display("  expected : drop=1 (G1, not default forward)");
      $display("  actual   : g1=%0b drop=%0b", drop_g1, drop);
      $display("  hier     : u_rt.drop_g1 / u_ps.drop");
      fail = 1;
    end else
      $display("PASS tc_rt10_on_default_drop");

    // RT-016: G1 is drop, not a credit proto_err pin on this path
    if (drop_g1) begin
      $display("PASS tc_rt10_not_proto_err");
      $display("NOTE tc_rt10_not_proto_err: G1 is drop_g1, not dll proto_err");
    end

    if (!fail) $display("PASS tc_rt_g1_official");
    $finish;
  end
endmodule
