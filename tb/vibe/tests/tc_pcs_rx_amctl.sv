// AMCTL lock CONFIRM_N=UNLOCK_N=3. LID {0,1,2,3} else lid_bad (U24).
`timescale 1ns/1ps
module tc_pcs_rx_amctl;
  logic clk, rst_n, in_vld, locked, lid_bad, is_amctl, sdf;
  logic [159:0] in_data;
  logic [1:0] lid;
  logic [15:0] cw21, cw22, cw28, cw3, cw8, cw9, cw10;
  integer fail, n;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_ebch16 u21 (.cw_sel(5'd21), .cw(cw21));
  vibe_ebch16 u22 (.cw_sel(5'd22), .cw(cw22));
  vibe_ebch16 u28 (.cw_sel(5'd28), .cw(cw28));
  vibe_ebch16 u3  (.cw_sel(5'd3),  .cw(cw3));
  vibe_ebch16 u8  (.cw_sel(5'd8),  .cw(cw8));
  vibe_ebch16 u9  (.cw_sel(5'd9),  .cw(cw9));
  vibe_ebch16 u10 (.cw_sel(5'd10), .cw(cw10));
  vibe_pcs_rx_amctl_lock u_l (
    .clk(clk), .rst_n(rst_n), .in_vld(in_vld), .in_data(in_data),
    .locked(locked), .lid(lid), .lid_bad(lid_bad), .is_amctl(is_amctl), .sdf(sdf)
  );

  task automatic send_pair;
    input [15:0] body;
    input [15:0] lidw;
    input [15:0] endw;
    logic [159:0] w0, w1;
    begin
      w0 = 160'd0; w1 = 160'd0;
      w0[159:144] = body;
      w1[127:112] = endw;
      w1[79:64]   = lidw;
      @(negedge clk);
      in_data = w0; in_vld = 1;
      @(posedge clk);
      @(negedge clk);
      in_data = w1;
      @(posedge clk);
      @(negedge clk);
      in_vld = 0;
    end
  endtask

  initial begin
    fail = 0;
    rst_n = 0; in_vld = 0; in_data = 0;
    #1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // 4 confirm pairs (conf 0,1,2 then lock)
    for (n = 0; n < 4; n = n + 1)
      send_pair(cw21, cw3, cw22);
    if (!locked || lid !== 2'd0) begin
      $display("FAIL tc_pcs_rx_amctl");
      $display("  stimulus : 4× AMCTL LID0");
      $display("  expected : locked lid=0");
      $display("  actual   : lock=%0b lid=%0d", locked, lid);
      fail = 1;
    end
    // other LIDs
    send_pair(cw28, cw8, cw22);
    if (lid !== 2'd1) begin
      $display("FAIL tc_pcs_rx_amctl");
      $display("  stimulus : LID cw8");
      $display("  expected : lid=1");
      $display("  actual   : %0d", lid);
      fail = 1;
    end
    send_pair(cw21, cw9, cw22);
    send_pair(cw21, cw10, cw22);
    if (lid !== 2'd3) begin
      $display("FAIL tc_pcs_rx_amctl");
      $display("  stimulus : LID cw10");
      $display("  expected : lid=3");
      $display("  actual   : %0d", lid);
      fail = 1;
    end
    // unlock: 4 non-AM pairs
    for (n = 0; n < 4; n = n + 1)
      send_pair(16'h0000, 16'h0000, 16'h0000);
    if (locked) begin
      $display("FAIL tc_pcs_rx_amctl");
      $display("  stimulus : 4 non-AM while locked");
      $display("  expected : unlock");
      $display("  actual   : still locked");
      fail = 1;
    end
    // lid_bad
    rst_n = 0;
    @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    send_pair(cw21, 16'hFFFF, cw22);
    if (!lid_bad) begin
      $display("FAIL tc_pcs_rx_amctl");
      $display("  stimulus : AMCTL LID not {0,1,2,3}");
      $display("  expected : lid_bad (U24 no swap)");
      $display("  actual   : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_rx_amctl");
    $finish;
  end
endmodule
