// PMA 512b slice + pin-idle PRBS31 (SPEC §4.4 / CR-PMA-IDLE-PRBS31).
// [127:0]=lane0 … [511:384]=lane3. No PMA ready. No PMA_IDLE_MARK.
`timescale 1ns/1ps
module tc_pma_512b_slice;
  `include "vibe_prbs31.svh"
  logic txclk, rxclk, txrst_n, rxrst_n, afifo_pma_lane_vld, pma_afifo_lane_vld;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata, idle0, idle1, gold0, gold1;
  logic [30:0] s0, s1, s2, s3;
  integer fail;

  initial txclk = 0;
  always #2 txclk = ~txclk;
  initial rxclk = 0;
  always #2 rxclk = ~rxclk;

  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk), .txrst_n(txrst_n), .rxrst_n(rxrst_n),
    .afifo_pma_lane0(t0), .afifo_pma_lane1(t1), .afifo_pma_lane2(t2), .afifo_pma_lane3(t3),
    .afifo_pma_lane_vld(afifo_pma_lane_vld), .pcs_pma_txdata(pcs_pma_txdata),
    .pma_pcs_rxdata(pma_pcs_rxdata),
    .pma_afifo_lane0(r0), .pma_afifo_lane1(r1), .pma_afifo_lane2(r2), .pma_afifo_lane3(r3),
    .pma_afifo_lane_vld(pma_afifo_lane_vld)
  );

  initial begin
    fail = 0;
    txrst_n = 0; rxrst_n = 0;
    t0 = 128'h11; t1 = 128'h22; t2 = 128'h33; t3 = 128'h44;
    afifo_pma_lane_vld = 0; pma_pcs_rxdata = 512'd0;
    s0 = vibe_tb_prbs31_seed(2'd0);
    s1 = vibe_tb_prbs31_seed(2'd1);
    s2 = vibe_tb_prbs31_seed(2'd2);
    s3 = vibe_tb_prbs31_seed(2'd3);
    gold0 = vibe_tb_prbs31_pack4(s0, s1, s2, s3);
    gold1 = vibe_tb_prbs31_pack4(vibe_tb_prbs31_adv128(s0),
                                vibe_tb_prbs31_adv128(s1),
                                vibe_tb_prbs31_adv128(s2),
                                vibe_tb_prbs31_adv128(s3));
    repeat (2) @(posedge txclk);
    txrst_n = 1; rxrst_n = 1;
    @(posedge txclk);
    if (pcs_pma_txdata !== gold0 || !vibe_tb_prbs31_pack_ok(pcs_pma_txdata)) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : afifo_pma_lane_vld=0 after rst");
      $display("  expected : pcs_pma_txdata PRBS31 seed pack (poly x^31+x^28+1)");
      $display("  actual   : %h", pcs_pma_txdata);
      fail = 1;
    end
    idle0 = pcs_pma_txdata;
    @(posedge txclk);
    if (pcs_pma_txdata === 512'd0 || pcs_pma_txdata === idle0 ||
        pcs_pma_txdata !== gold1 || !vibe_tb_prbs31_pack_ok(pcs_pma_txdata)) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : second idle txclk");
      $display("  expected : new PRBS31 beat (must change every clock)");
      $display("  actual   : %h", pcs_pma_txdata);
      fail = 1;
    end
    idle1 = pcs_pma_txdata;
    @(posedge txclk);
    if (pcs_pma_txdata === idle1 || !vibe_tb_prbs31_pack_ok(pcs_pma_txdata)) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : third idle txclk");
      $display("  expected : another new PRBS31 beat");
      $display("  actual   : %h", pcs_pma_txdata);
      fail = 1;
    end
    afifo_pma_lane_vld = 1;
    @(posedge txclk);
    @(posedge txclk);
    if (pcs_pma_txdata[127:0] !== 128'h11 || pcs_pma_txdata[255:128] !== 128'h22 ||
        pcs_pma_txdata[383:256] !== 128'h33 || pcs_pma_txdata[511:384] !== 128'h44) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : tx lanes 11/22/33/44 vld");
      $display("  expected : pcs_pma_txdata slices lane0..3 (business beat)");
      $display("  actual   : %h", pcs_pma_txdata);
      fail = 1;
    end
    pma_pcs_rxdata = {128'hAA, 128'hBB, 128'hCC, 128'hDD};
    @(posedge rxclk);
    @(posedge rxclk);
    if (r0 !== 128'hDD || r3 !== 128'hAA || !pma_afifo_lane_vld) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : pma_pcs_rxdata {AA,BB,CC,DD} (not PRBS31)");
      $display("  expected : lane0=DD lane3=AA vld=1");
      $display("  actual   : r0=%h r3=%h vld=%0b", r0, r3, pma_afifo_lane_vld);
      fail = 1;
    end
    pma_pcs_rxdata = gold0;
    @(posedge rxclk);
    @(posedge rxclk);
    if (pma_afifo_lane_vld) begin
      $display("FAIL tc_pma_512b_slice");
      $display("  stimulus : pma_pcs_rxdata = PRBS31 seed pack");
      $display("  expected : pma_afifo_lane_vld=0 (pin-idle drop, no mark)");
      $display("  actual   : vld=1");
      fail = 1;
    end
    afifo_pma_lane_vld = 0;
    @(posedge txclk);
    if (!fail) $display("PASS tc_pma_512b_slice");
    $finish;
  end
endmodule
