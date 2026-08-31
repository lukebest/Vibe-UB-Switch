// PMA 512b @ 922 MHz product period (AS-0.1). Slice only; no PMA ready.
`timescale 1ps/1ps
module tc_pma_922mhz;
  // 922 MHz → T ≈ 1084.6 ps
  localparam integer T_PS = 1085;
  logic txclk, rxclk, tvl, rvl;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] txdata, rxdata;
  integer fail, edges;
  initial txclk = 0;
  always #(T_PS/2) txclk = ~txclk;
  initial rxclk = 0;
  always #(T_PS/2) rxclk = ~rxclk;
  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk),
    .tx_lane0(t0), .tx_lane1(t1), .tx_lane2(t2), .tx_lane3(t3),
    .tx_lane_vld(tvl), .txdata(txdata),
    .rxdata(rxdata),
    .rx_lane0(r0), .rx_lane1(r1), .rx_lane2(r2), .rx_lane3(r3),
    .rx_lane_vld(rvl)
  );
  initial begin
    fail = 0; edges = 0;
    t0 = 128'hA0; t1 = 128'hA1; t2 = 128'hA2; t3 = 128'hA3;
    tvl = 1; rxdata = 512'd0;
    repeat (8) begin
      @(posedge txclk);
      edges = edges + 1;
    end
    if (txdata[127:0] !== 128'hA0 || txdata[511:384] !== 128'hA3) begin
      $display("FAIL tc_pma_922mhz");
      $display("  stimulus : 512b PMA at T=1085ps (~922 MHz), lanes A0..A3");
      $display("  expected : packed {A3,A2,A1,A0}");
      $display("  actual   : %h", txdata);
      $display("  hier     : u_p.txdata");
      fail = 1;
    end
    if (edges < 8) begin
      $display("FAIL tc_pma_922mhz");
      $display("  stimulus : 8 posedges at 922 MHz period");
      $display("  expected : clocks advance");
      $display("  actual   : edges=%0d", edges);
      fail = 1;
    end
    if (!fail) $display("PASS tc_pma_922mhz");
    $finish;
  end
endmodule
