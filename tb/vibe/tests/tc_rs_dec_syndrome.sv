// RS(128,120) decoder: start + 128 zero symbols → done (syndrome path).
`timescale 1ns/1ps
module tc_rs_dec_syndrome;
  logic clk, rst_n, start, in_vld, in_ready, done, fec_fail;
  logic [7:0] in_sym;
  logic [959:0] data_out;
  integer fail, i, saw_done;
  initial clk = 0;
  always #1 clk = ~clk;
  always @(posedge clk) if (done) saw_done <= 1;
  vibe_rs128_120_dec u_d (
    .clk(clk), .rst_n(rst_n), .start(start), .in_vld(in_vld), .in_sym(in_sym),
    .in_ready(in_ready), .done(done), .fec_fail(fec_fail), .data_out(data_out)
  );
  initial begin
    fail = 0; saw_done = 0;
    rst_n = 0; start = 0; in_vld = 0; in_sym = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    start = 1;
    @(posedge clk);
    @(negedge clk);
    start = 0;
    for (i = 0; i < 128; i = i + 1) begin
      @(negedge clk);
      while (!in_ready) @(posedge clk);
      in_sym = 8'd0;
      in_vld = 1;
      @(posedge clk);
    end
    @(negedge clk);
    in_vld = 0;
    repeat (8) @(posedge clk);
    if (!saw_done) begin
      $display("FAIL tc_rs_dec_syndrome");
      $display("  stimulus : start + 128 zero symbols");
      $display("  expected : done pulse");
      $display("  actual   : no done fail=%0b", fec_fail);
      $display("  hier     : u_d.busy / cnt / s0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_rs_dec_syndrome");
    $finish;
  end
endmodule
