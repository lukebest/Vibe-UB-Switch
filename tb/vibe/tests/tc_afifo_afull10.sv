// AFIFO depth 16, gray ptr, almost_full at occ>=10.
`timescale 1ns/1ps
module tc_afifo_afull10;
  logic wclk, rclk, wrst_n, rrst_n, wen, ren, wfull, almost_full, rempty;
  logic [159:0] wdata, rdata;
  logic [4:0] wocc;
  integer fail, i;
  initial wclk = 0;
  always #1 wclk = ~wclk;
  initial rclk = 0;
  always #2 rclk = ~rclk;
  vibe_afifo #(.W(160), .DEPTH(16)) u_f (
    .wclk(wclk), .wrst_n(wrst_n), .wen(wen), .wdata(wdata),
    .wfull(wfull), .almost_full(almost_full), .wocc(wocc),
    .rclk(rclk), .rrst_n(rrst_n), .ren(ren), .rdata(rdata), .rempty(rempty)
  );
  initial begin
    fail = 0;
    wrst_n = 0; rrst_n = 0; wen = 0; ren = 0; wdata = 0;
    repeat (4) @(posedge wclk);
    wrst_n = 1; rrst_n = 1;
    repeat (4) @(posedge wclk);
    for (i = 0; i < 10; i = i + 1) begin
      @(negedge wclk);
      wdata = i[159:0];
      wen = 1;
      @(posedge wclk);
    end
    @(negedge wclk);
    wen = 0;
    @(posedge wclk);
    if (!almost_full) begin
      $display("FAIL tc_afifo_afull10");
      $display("  stimulus : 10 writes, no reads");
      $display("  expected : almost_full=1 (occ>=10)");
      $display("  actual   : afull=%0b wocc=%0d", almost_full, wocc);
      $display("  hier     : u_f.wocc");
      fail = 1;
    end
    // fill to full (depth 16)
    for (i = 10; i < 16; i = i + 1) begin
      @(negedge wclk);
      wdata = i[159:0];
      wen = 1;
      @(posedge wclk);
    end
    @(negedge wclk);
    wen = 0;
    @(posedge wclk);
    if (!wfull) begin
      $display("FAIL tc_afifo_afull10");
      $display("  stimulus : 16 writes");
      $display("  expected : wfull=1");
      $display("  actual   : 0 wocc=%0d", wocc);
      fail = 1;
    end
    // write while full must not increment
    @(negedge wclk);
    wen = 1; wdata = 160'hDEAD;
    @(posedge wclk);
    @(negedge wclk);
    wen = 0;
    // drain
    repeat (4) @(posedge rclk);
    for (i = 0; i < 16; i = i + 1) begin
      @(negedge rclk);
      if (!rempty) ren = 1;
      @(posedge rclk);
    end
    @(negedge rclk);
    ren = 0;
    repeat (4) @(posedge rclk);
    if (!rempty) begin
      $display("FAIL tc_afifo_afull10");
      $display("  stimulus : 16 reads after full");
      $display("  expected : rempty=1");
      $display("  actual   : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_afifo_afull10");
    $finish;
  end
endmodule
