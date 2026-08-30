// BCRC CRC30 init all-1, no invert. bit31 reserved 0, bit30 ERROR_FLAG.
`timescale 1ns/1ps
module tc_bcrc_crc30;
  logic clk, rst_n, start, in_vld, last, error_flag, done;
  logic [159:0] in_flit;
  logic [31:0] crc_word;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_bcrc u_b (
    .clk(clk), .rst_n(rst_n), .start(start), .in_vld(in_vld),
    .in_flit(in_flit), .last(last), .error_flag(error_flag),
    .crc_word(crc_word), .done(done)
  );
  initial begin
    fail = 0;
    rst_n = 0; start = 0; in_vld = 0; last = 0; error_flag = 1; in_flit = 160'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    start = 1;
    @(posedge clk);
    start = 0;
    in_vld = 1; last = 1; in_flit = 160'hA5A5_A5A5_A5A5_A5A5_A5A5;
    @(posedge clk);
    // done is a 1-cycle pulse on the last-flit NBA
    if (!done) begin
      $display("FAIL tc_bcrc_crc30");
      $display("  stimulus : start + one flit last error_flag=1");
      $display("  expected : done=1");
      $display("  actual   : done=0 crc=%h", crc_word);
      $display("  hier     : u_b.crc / crc_word");
      fail = 1;
    end else if (crc_word[31] !== 1'b0 || crc_word[30] !== 1'b1) begin
      $display("FAIL tc_bcrc_crc30");
      $display("  stimulus : error_flag=1");
      $display("  expected : bit31=0 reserved, bit30=ERROR_FLAG=1");
      $display("  actual   : crc_word=%h", crc_word);
      fail = 1;
    end
    if (!fail) $display("PASS tc_bcrc_crc30");
    $finish;
  end
endmodule
