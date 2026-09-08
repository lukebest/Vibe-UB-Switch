// PMA 512b slice: [127:0]=lane0 … [511:384]=lane3. No PMA ready.
`timescale 1ns/1ps
module tc_pma_512b_slice;
  logic txclk, rxclk, afifo_pma_lane_vld, pma_afifo_lane_vld;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata;
  integer fail;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  initial rxclk = 0;
  always #2 rxclk = ~rxclk;
  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk),
    .afifo_pma_lane0(t0), .afifo_pma_lane1(t1), .afifo_pma_lane2(t2), .afifo_pma_lane3(t3),
    .afifo_pma_lane_vld(afifo_pma_lane_vld), .pcs_pma_txdata(pcs_pma_txdata),
    .pma_pcs_rxdata(pma_pcs_rxdata),
    .pma_afifo_lane0(r0), .pma_afifo_lane1(r1), .pma_afifo_lane2(r2), .pma_afifo_lane3(r3),
    .pma_afifo_lane_vld(pma_afifo_lane_vld)
  );
  initial begin
    fail = 0;
    t0 = 128'h11; t1 = 128'h22; t2 = 128'h33; t3 = 128'h44;
    afifo_pma_lane_vld = 0; pma_pcs_rxdata = 512'd0;
    repeat (2) @(posedge txclk);
    afifo_pma_lane_vld = 1;
    @(posedge txclk);
    @(posedge txclk);
    if (pcs_pma_txdata[127:0] !== 128'h11 || pcs_pma_txdata[255:128] !== 128'h22 ||
        pcs_pma_txdata[383:256] !== 128'h33 || pcs_pma_txdata[511:384] !== 128'h44) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : tx lanes 11/22/33/44 vld");
      $display("  expected : pcs_pma_txdata slices lane0..3");
      $display("  actual   : %h", pcs_pma_txdata);
      fail = 1;
    end
    pma_pcs_rxdata = {128'hAA, 128'hBB, 128'hCC, 128'hDD};
    @(posedge rxclk);
    @(posedge rxclk);
    if (r0 !== 128'hDD || r3 !== 128'hAA) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : pma_pcs_rxdata {AA,BB,CC,DD}");
      $display("  expected : lane0=DD lane3=AA");
      $display("  actual   : r0=%h r3=%h", r0, r3);
      fail = 1;
    end
    afifo_pma_lane_vld = 0;
    @(posedge txclk);
    if (!fail) $display("PASS tc_pma_512b_slice");
    $finish;
  end
endmodule
