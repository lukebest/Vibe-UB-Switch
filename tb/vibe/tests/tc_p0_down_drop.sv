// TP-NW-003 / TP-NW-006: bitmap AND Status_Up; port0 Down → drop+count, no flood.
`timescale 1ns/1ps
module tc_p0_down_drop;
  logic        clk, rst_n;
  logic [3:0]  bitmap, status_up, default_bm;
  logic [1:0]  rt;
  logic        drop_g1, sel_vld, drop;
  logic [3:0]  cfg, vl;
  logic [15:0] src, dest;
  logic [1:0]  egr;
  logic [31:0] drop_down;
  integer      fail, cnt_before;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bitmap), .status_up(status_up), .default_bm(default_bm),
    .rt(rt), .drop_g1(drop_g1), .sel_vld(sel_vld),
    .cfg(cfg), .src(src), .dest(dest), .vl(vl),
    .egr(egr), .drop(drop), .drop_down_cnt(drop_down)
  );

  initial begin
    fail = 0;
    rst_n = 0;
    bitmap = 4'd0; status_up = 4'b1111; default_bm = 4'd0;
    rt = 2'b00; drop_g1 = 0; sel_vld = 0;
    cfg = 4'd3; vl = 4'd0; src = 16'h0030; dest = 16'h00FF;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    // Port 0 up + empty bitmap + default all-0 → egr=0, no drop
    @(negedge clk);
    status_up = 4'b1111;
    bitmap = 4'd0;
    sel_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (drop || egr !== 2'd0) begin
      $display("FAIL tc_p0_down_drop");
      $display("  stimulus : RT=00 bitmap=0 default_bm=0 status_up=1111 dest=00FF");
      $display("  expected : drop=0 egr=0 (AS-0.1 §8 default → port 0)");
      $display("  actual   : drop=%0b egr=%0d", drop, egr);
      $display("  hier     : u_ps.use_bm / u_ps.drop");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    sel_vld = 0;
    @(posedge clk);

    cnt_before = drop_down;
    @(negedge clk);
    status_up = 4'b1110; // port 0 Down
    bitmap = 4'd0;
    sel_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!drop) begin
      $display("FAIL tc_p0_down_drop");
      $display("  stimulus : default all-0 → port 0; status_up[0]=0");
      $display("  expected : drop=1 (no flood)");
      $display("  actual   : drop=%0b egr=%0d", drop, egr);
      $display("  hier     : u_ps.avail / u_ps.drop");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end else if (drop_down !== cnt_before + 32'd1) begin
      $display("FAIL tc_p0_down_drop");
      $display("  stimulus : port 0 Down after empty bitmap filter");
      $display("  expected : drop_down_cnt += 1");
      $display("  actual   : before=%0d after=%0d", cnt_before, drop_down);
      $display("  hier     : u_ps.drop_down_cnt");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    sel_vld = 0;
    if (!fail) $display("PASS tc_p0_down_drop");
    $finish;
  end
endmodule
