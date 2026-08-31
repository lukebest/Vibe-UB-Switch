// RX gearbox 128→160. 5×128 = 4×160.
`timescale 1ns/1ps
module tc_gear_128_160;
  logic clk, rst_n, in_vld, in_ready, out_vld, out_ready;
  logic [127:0] in_data;
  logic [159:0] out_data;
  integer fail, nout, sent;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_gear_128_160 u_g (
    .clk(clk), .rst_n(rst_n), .in_vld(in_vld), .in_ready(in_ready),
    .in_data(in_data), .out_vld(out_vld), .out_ready(out_ready), .out_data(out_data)
  );
  always @(posedge clk) begin
    if (out_vld && out_ready) nout <= nout + 1;
  end
  initial begin
    fail = 0; nout = 0; sent = 0;
    rst_n = 0; in_vld = 0; out_ready = 1; in_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    while (sent < 5) begin
      @(negedge clk);
      if (in_ready) begin
        in_data = 128'h55;
        in_vld = 1;
        sent = sent + 1;
      end else
        in_vld = 0;
      @(posedge clk);
    end
    @(negedge clk);
    in_vld = 0;
    repeat (16) @(posedge clk);
    if (nout < 4) begin
      $display("FAIL tc_gear_128_160");
      $display("  stimulus : 5×128b in");
      $display("  expected : 4×160b out");
      $display("  actual   : %0d", nout);
      $display("  hier     : u_g.phase / hold_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_gear_128_160");
    $finish;
  end
endmodule
