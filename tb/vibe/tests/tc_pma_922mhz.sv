// PMA 512b @ 922 MHz product period (AS-0.1). Slice only; no PMA ready.
`timescale 1ps/1ps
module tc_pma_922mhz;
  // 922 MHz → T ≈ 1084.6 ps
  localparam integer T_PS = 1085;
  logic txclk, rxclk, tvl, rvl;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata;
  integer fail, edges;
  initial txclk = 0;
  always #(T_PS/2) txclk = ~txclk;
  initial rxclk = 0;
  always #(T_PS/2) rxclk = ~rxclk;
  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk),
    .afifo_pma_lane0(t0), .afifo_pma_lane1(t1), .afifo_pma_lane2(t2), .afifo_pma_lane3(t3),
    .afifo_pma_lane_vld(tvl), .pcs_pma_txdata(pcs_pma_txdata),
    .pma_pcs_rxdata(pma_pcs_rxdata),
    .pma_afifo_lane0(r0), .pma_afifo_lane1(r1), .pma_afifo_lane2(r2), .pma_afifo_lane3(r3),
    .pma_afifo_lane_vld(rvl)
  );
  initial begin
    fail = 0; edges = 0;
    t0 = 128'hA0; t1 = 128'hA1; t2 = 128'hA2; t3 = 128'hA3;
    tvl = 1; pma_pcs_rxdata = 512'd0;
    repeat (8) begin
      @(posedge txclk);
      edges = edges + 1;
    end
    if (pcs_pma_txdata[127:0] !== 128'hA0 || pcs_pma_txdata[511:384] !== 128'hA3) begin
      $display("FAIL tc_pma_922mhz");
      $display("  stimulus : 512b PMA at T=1085ps (~922 MHz), lanes A0..A3");
      $display("  expected : packed {A3,A2,A1,A0}");
      $display("  actual   : %h", pcs_pma_txdata);
      $display("  hier     : u_p.pcs_pma_txdata");
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
