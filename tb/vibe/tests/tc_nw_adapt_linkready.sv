// LinkReady participates in ready. Mgmt inject priority over VOQ.
// Overlay B: 512-bit GOLDEN vector compare TX and RX. Width is a gate only.
`timescale 1ns/1ps
module tc_nw_adapt_linkready;
  `include "vibe_tb_nw512.svh"

  logic clk, rst_n, link_ready;
  logic [511:0] fab_tx_data, mgmt_tx_data, dll_tx_data, dll_rx_data, fab_rx_data;
  logic fab_tx_vld, fab_tx_ready, mgmt_tx_vld, mgmt_tx_ready;
  logic dll_tx_vld, dll_tx_ready, dll_rx_vld, dll_rx_ready, fab_rx_vld, fab_rx_ready;
  logic [511:0] golden_tx, golden_rx;
  integer fail, nw_w, dll_w, rx_w;

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
    golden_tx = vibe_tb_nw512_golden_tx();
    golden_rx = vibe_tb_nw512_golden_rx();
    rst_n = 1; link_ready = 0;
    nw_w  = $bits(u_n.fab_tx_data);
    dll_w = $bits(u_n.dll_tx_data);
    rx_w  = $bits(u_n.fab_rx_data);
    if (nw_w !== 512) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : FS-0.2.7 Overlay B NW↔DLL data[511:0]");
      $display("  expected : $bits(fab_tx_data)=512");
      $display("  actual   : %0d", nw_w);
      $display("  hier     : u_n.fab_tx_data");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // Always attempt 512-bit content (do not PASS on a 640 low-slice).
    fab_tx_data = golden_tx; mgmt_tx_data = 0; dll_rx_data = golden_rx;
    fab_tx_vld = 1; mgmt_tx_vld = 0; dll_tx_ready = 1;
    dll_rx_vld = 1; fab_rx_ready = 1;
    #1;
    if (fab_tx_ready || dll_tx_vld) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : link_ready=0 fab_tx_vld GOLDEN_TX");
      $display("  expected : fab_tx_ready=0 dll_tx_vld=0");
      $display("  actual   : rdy=%0b vld=%0b", fab_tx_ready, dll_tx_vld);
      $display("  hier     : u_n.fab_tx_ready");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    link_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, dll_tx_data) ||
        !dll_tx_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "TX NW→DLL link_ready=1 fab only GOLDEN_TX",
          golden_tx, dll_w, dll_tx_data,
          "u_n.dll_tx_data");
      $display("  actual   : dll_tx_vld=%0b", dll_tx_vld);
      fail = 1;
    end
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, fab_rx_data) ||
        !fab_rx_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "RX DLL→NW dll_rx=GOLDEN_RX",
          golden_rx, rx_w, fab_rx_data,
          "u_n.fab_rx_data");
      fail = 1;
    end
    mgmt_tx_vld = 1;
    mgmt_tx_data = golden_rx;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_rx, dll_tx_data) ||
        fab_tx_ready) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "mgmt GOLDEN_RX priority over fab GOLDEN_TX",
          golden_rx, dll_w, dll_tx_data,
          "u_n.dll_tx_data");
      $display("  actual   : fab_tx_ready=%0b (must be 0)", fab_tx_ready);
      fail = 1;
    end
    if (!fail) $display("PASS tc_nw_adapt_linkready");
    $finish;
  end
endmodule
