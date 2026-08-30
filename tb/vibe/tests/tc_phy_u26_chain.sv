// PHY/U26 width chain: 4×160 → 5×128 (TX gear) + PMA 512b slice + 5×128 → 4×160 (RX gear).
`timescale 1ns/1ps
module tc_phy_u26_chain;
  logic clk, rst_n;
  logic        g1_iv, g1_ir, g1_ov, g1_or;
  logic [159:0] g1_id;
  logic [127:0] g1_od;
  logic        g2_iv, g2_ir, g2_ov, g2_or;
  logic [127:0] g2_id;
  logic [159:0] g2_od;
  logic txclk, rxclk, tvl, rvl;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] txdata, rxdata;
  integer fail, n128, n160, sent;
  initial clk = 0;
  always #1 clk = ~clk;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  initial rxclk = 0;
  always #2 rxclk = ~rxclk;

  vibe_gear_160_128 u_txg (
    .clk(clk), .rst_n(rst_n), .in_vld(g1_iv), .in_ready(g1_ir),
    .in_data(g1_id), .out_vld(g1_ov), .out_ready(g1_or), .out_data(g1_od)
  );
  vibe_pma_bnd u_p (
    .txclk(txclk), .rxclk(rxclk),
    .tx_lane0(t0), .tx_lane1(t1), .tx_lane2(t2), .tx_lane3(t3),
    .tx_lane_vld(tvl), .txdata(txdata),
    .rxdata(rxdata),
    .rx_lane0(r0), .rx_lane1(r1), .rx_lane2(r2), .rx_lane3(r3),
    .rx_lane_vld(rvl)
  );
  vibe_gear_128_160 u_rxg (
    .clk(clk), .rst_n(rst_n), .in_vld(g2_iv), .in_ready(g2_ir),
    .in_data(g2_id), .out_vld(g2_ov), .out_ready(g2_or), .out_data(g2_od)
  );

  always @(posedge clk) begin
    if (g1_ov && g1_or) n128 <= n128 + 1;
    if (g2_ov && g2_or) n160 <= n160 + 1;
  end

  initial begin
    fail = 0; n128 = 0; n160 = 0; sent = 0;
    rst_n = 0; g1_iv = 0; g1_or = 1; g1_id = 0;
    g2_iv = 0; g2_or = 1; g2_id = 0;
    t0 = 0; t1 = 0; t2 = 0; t3 = 0; tvl = 0; rxdata = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    while (sent < 4) begin
      @(negedge clk);
      if (g1_ir) begin
        g1_id = {40'hA, 120'h1};
        g1_iv = 1;
        sent = sent + 1;
      end else
        g1_iv = 0;
      @(posedge clk);
    end
    @(negedge clk);
    g1_iv = 0;
    repeat (16) @(posedge clk);
    t0 = 128'h11; t1 = 128'h22; t2 = 128'h33; t3 = 128'h44;
    tvl = 1;
    @(posedge txclk);
    @(posedge txclk);
    rxdata = txdata;
    @(posedge rxclk);
    @(posedge rxclk);
    if (n128 < 5) begin
      $display("FAIL tc_phy_u26_chain");
      $display("  stimulus : 4x160 into TX gear");
      $display("  expected : >=5 x128 beats (U26 4*160=5*128)");
      $display("  actual   : %0d", n128);
      $display("  hier     : u_txg.rbits / hold_vld");
      fail = 1;
    end
    if (txdata[127:0] !== 128'h11 || r0 !== 128'h11) begin
      $display("FAIL tc_phy_u26_chain");
      $display("  stimulus : PMA lanes 11/22/33/44 looped rxdata=txdata");
      $display("  expected : [127:0]=lane0=11 both TX pack and RX slice");
      $display("  actual   : txdata[127:0]=%h r0=%h", txdata[127:0], r0);
      $display("  hier     : u_p.txdata / u_p.rx_lane0");
      fail = 1;
    end
    sent = 0;
    while (sent < 5) begin
      @(negedge clk);
      if (g2_ir) begin
        g2_id = 128'h55;
        g2_iv = 1;
        sent = sent + 1;
      end else
        g2_iv = 0;
      @(posedge clk);
    end
    @(negedge clk);
    g2_iv = 0;
    repeat (16) @(posedge clk);
    if (n160 < 4) begin
      $display("FAIL tc_phy_u26_chain");
      $display("  stimulus : 5x128 into RX gear");
      $display("  expected : >=4 x160 beats");
      $display("  actual   : %0d", n160);
      fail = 1;
    end
    if (!fail) $display("PASS tc_phy_u26_chain");
    $finish;
  end
endmodule
