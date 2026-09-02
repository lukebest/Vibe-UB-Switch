// LinkReady participates in ready. Mgmt inject priority over VOQ.
`timescale 1ns/1ps
module tc_nw_adapt_linkready;
  logic clk, rst_n, link_ready;
  logic [639:0] fab_tx_data, mgmt_tx_data, dll_tx_data, dll_rx_data, fab_rx_data;
  logic fab_tx_vld, fab_tx_ready, mgmt_tx_vld, mgmt_tx_ready;
  logic dll_tx_vld, dll_tx_ready, dll_rx_vld, dll_rx_ready, fab_rx_vld, fab_rx_ready;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_nw_adapt u_n (
    .clk(clk), .rst_n(rst_n), .link_ready(link_ready),
    .fab_tx_data(fab_tx_data), .fab_tx_vld(fab_tx_vld), .fab_tx_ready(fab_tx_ready),
    .mgmt_tx_data(mgmt_tx_data), .mgmt_tx_vld(mgmt_tx_vld), .mgmt_tx_ready(mgmt_tx_ready),
    .dll_tx_data(dll_tx_data), .dll_tx_vld(dll_tx_vld), .dll_tx_ready(dll_tx_ready),
    .dll_rx_data(dll_rx_data), .dll_rx_vld(dll_rx_vld), .dll_rx_ready(dll_rx_ready),
    .fab_rx_data(fab_rx_data), .fab_rx_vld(fab_rx_vld), .fab_rx_ready(fab_rx_ready)
  );
  initial begin
    fail = 0;
    rst_n = 1; link_ready = 0;
    if ($bits(u_n.fab_tx_data) !== 512) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : FS-0.2.7 Overlay B NW↔DLL data[511:0]");
      $display("  expected : $bits(fab_tx_data)=512");
      $display("  actual   : %0d", $bits(u_n.fab_tx_data));
      $display("  hier     : u_n.fab_tx_data");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
      $finish;
    end
    fab_tx_data = 640'h1; mgmt_tx_data = 640'h2; dll_rx_data = 640'h3;
    fab_tx_vld = 1; mgmt_tx_vld = 0; dll_tx_ready = 1; dll_rx_vld = 1; fab_rx_ready = 1;
    #1;
    if (fab_tx_ready || dll_tx_vld) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : link_ready=0 fab_tx_vld");
      $display("  expected : fab_tx_ready=0 dll_tx_vld=0");
      $display("  actual   : rdy=%0b vld=%0b", fab_tx_ready, dll_tx_vld);
      fail = 1;
    end
    link_ready = 1;
    #1;
    if (!dll_tx_vld || dll_tx_data !== 640'h1) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : link_ready=1 fab only");
      $display("  expected : dll_tx = fab");
      fail = 1;
    end
    mgmt_tx_vld = 1;
    #1;
    if (dll_tx_data !== 640'h2 || fab_tx_ready) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : mgmt_tx_vld with fab");
      $display("  expected : mgmt priority, fab_tx_ready=0");
      $display("  actual   : data=%h fab_rdy=%0b", dll_tx_data, fab_tx_ready);
      fail = 1;
    end
    if (!fail) $display("PASS tc_nw_adapt_linkready");
    $finish;
  end
endmodule
