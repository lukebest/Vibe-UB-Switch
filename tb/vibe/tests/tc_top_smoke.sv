// Top smoke + hierarchical probe of u_fab.rt_shortest_unimpl (not a top port).
`timescale 1ns/1ps

module tc_top_smoke;
  logic         clk_fab, rst_n;
  logic         txclk_0, txclk_1, txclk_2, txclk_3;
  logic         rxclk_0, rxclk_1, rxclk_2, rxclk_3;
  logic [511:0] txdata_0, txdata_1, txdata_2, txdata_3;
  logic [511:0] rxdata_0, rxdata_1, rxdata_2, rxdata_3;
  logic         cfg_wr_vld, cfg_wr_ready, irq_logic;
  logic [2:0]   cfg_wr_cmd;
  logic [15:0]  cfg_wr_idx;
  logic [31:0]  cfg_wr_data;
  integer       fail;

  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial begin
    txclk_0 = 0; txclk_1 = 0; txclk_2 = 0; txclk_3 = 0;
    rxclk_0 = 0; rxclk_1 = 0; rxclk_2 = 0; rxclk_3 = 0;
  end
  always #2 txclk_0 = ~txclk_0;
  always #2 txclk_1 = ~txclk_1;
  always #2 txclk_2 = ~txclk_2;
  always #2 txclk_3 = ~txclk_3;
  always #2 rxclk_0 = ~rxclk_0;
  always #2 rxclk_1 = ~rxclk_1;
  always #2 rxclk_2 = ~rxclk_2;
  always #2 rxclk_3 = ~rxclk_3;

  vibe_ub_switch dut (
    .clk_fab(clk_fab), .rst_n(rst_n),
    .txclk_0(txclk_0), .txclk_1(txclk_1), .txclk_2(txclk_2), .txclk_3(txclk_3),
    .rxclk_0(rxclk_0), .rxclk_1(rxclk_1), .rxclk_2(rxclk_2), .rxclk_3(rxclk_3),
    .txdata_0(txdata_0), .txdata_1(txdata_1), .txdata_2(txdata_2), .txdata_3(txdata_3),
    .rxdata_0(rxdata_0), .rxdata_1(rxdata_1), .rxdata_2(rxdata_2), .rxdata_3(rxdata_3),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .irq_logic(irq_logic)
  );

  initial begin
    fail = 0;
    rst_n = 0;
    rxdata_0 = 512'd0; rxdata_1 = 512'd0; rxdata_2 = 512'd0; rxdata_3 = 512'd0;
    cfg_wr_vld = 0; cfg_wr_cmd = 0; cfg_wr_idx = 0; cfg_wr_data = 0;
    repeat (8) @(posedge clk_fab);
    rst_n = 1;
    repeat (8) @(posedge clk_fab);

    if (!cfg_wr_ready) begin
      $display("FAIL tc_top_smoke");
      $display("  stimulus : reset");
      $display("  expected : cfg_wr_ready=1");
      $display("  actual   : 0");
      fail = 1;
    end
    if (irq_logic !== 1'b0) begin
      $display("FAIL tc_top_smoke");
      $display("  stimulus : reset, idle PMA");
      $display("  expected : irq_logic=0");
      $display("  actual   : 1");
      fail = 1;
    end
    if (dut.u_fab.rt_shortest_unimpl !== 32'd0) begin
      $display("FAIL tc_top_smoke");
      $display("  stimulus : hierarchical probe dut.u_fab.rt_shortest_unimpl");
      $display("  expected : 0 after reset (internal; not a top port)");
      $display("  actual   : %h", dut.u_fab.rt_shortest_unimpl);
      $display("  hier     : vibe_ub_switch.u_fab.rt_shortest_unimpl");
      fail = 1;
    end

    @(negedge clk_fab);
    cfg_wr_cmd = 3'd0; cfg_wr_data = 32'h0000_0001; cfg_wr_vld = 1;
    @(posedge clk_fab);
    @(negedge clk_fab);
    cfg_wr_vld = 0;
    repeat (4) @(posedge clk_fab);
    if (dut.u_mgmt.cna !== 16'd1) begin
      $display("FAIL tc_top_smoke");
      $display("  stimulus : cfg_wr CNA=1");
      $display("  expected : u_mgmt.cna=1");
      $display("  actual   : %h", dut.u_mgmt.cna);
      fail = 1;
    end

    $display("NOTE tc_top_smoke: PMA 512b loopback not driven (no packet BFM); G1 is fabric-harness");
    if (!fail) $display("PASS tc_top_smoke");
    $finish;
  end
endmodule
