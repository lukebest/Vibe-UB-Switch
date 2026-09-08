// LinkReady participates in ready. Mgmt inject priority over VOQ.
// Overlay B: 512-bit GOLDEN vector compare TX and RX. Width is a gate only.
`timescale 1ns/1ps
module tc_nw_adapt_linkready;
  `include "vibe_tb_nw512.svh"

  logic clk, rst_n, link_ready;
  logic [511:0] fab_nw_data, mgmt_nw_data, nw_dll_data, dll_nw_data, nw_fab_data;
  logic fab_nw_vld, fab_nw_ready, mgmt_nw_vld, mgmt_nw_ready;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready, nw_fab_vld, nw_fab_ready;
  logic [511:0] golden_tx, golden_rx;
  integer fail, nw_w, dll_w, rx_w;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_nw_adapt u_n (
    .clk(clk), .rst_n(rst_n), .link_ready(link_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld), .mgmt_nw_ready(mgmt_nw_ready),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready)
  );

  initial begin
    fail = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    golden_rx = vibe_tb_nw512_golden_rx();
    rst_n = 1; link_ready = 0;
    nw_w  = $bits(u_n.fab_nw_data);
    dll_w = $bits(u_n.nw_dll_data);
    rx_w  = $bits(u_n.nw_fab_data);
    if (nw_w !== 512) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : FS-0.2.7 Overlay B NW↔DLL data[511:0]");
      $display("  expected : $bits(fab_nw_data)=512");
      $display("  actual   : %0d", nw_w);
      $display("  hier     : u_n.fab_nw_data");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // Always attempt 512-bit content (do not PASS on a 640 low-slice).
    fab_nw_data = golden_tx; mgmt_nw_data = 0; dll_nw_data = golden_rx;
    fab_nw_vld = 1; mgmt_nw_vld = 0; nw_dll_ready = 1;
    dll_nw_vld = 1; nw_fab_ready = 1;
    #1;
    if (fab_nw_ready || nw_dll_vld) begin
      $display("FAIL tc_nw_adapt_linkready");
      $display("  stimulus : link_ready=0 fab_nw_vld GOLDEN_TX");
      $display("  expected : fab_nw_ready=0 nw_dll_vld=0");
      $display("  actual   : rdy=%0b vld=%0b", fab_nw_ready, nw_dll_vld);
      $display("  hier     : u_n.fab_nw_ready");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    link_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, nw_dll_data) ||
        !nw_dll_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "TX NW→DLL link_ready=1 fab only GOLDEN_TX",
          golden_tx, dll_w, nw_dll_data,
          "u_n.nw_dll_data");
      $display("  actual   : nw_dll_vld=%0b", nw_dll_vld);
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_tx, nw_dll_data)) begin
      vibe_tb_nw512_sop_lph_print(
          "tc_nw_adapt_linkready",
          "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
          golden_tx, nw_dll_data, "u_n.nw_dll_data[511:352]");
      fail = 1;
    end
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, nw_fab_data) ||
        !nw_fab_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "RX DLL→NW dll_rx=GOLDEN_RX",
          golden_rx, rx_w, nw_fab_data,
          "u_n.nw_fab_data");
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_rx, nw_fab_data)) begin
      vibe_tb_nw512_sop_lph_print(
          "tc_nw_adapt_linkready",
          "RX SOP LPH GOLDEN_RX[511:352] vs DUT[511:352]",
          golden_rx, nw_fab_data, "u_n.nw_fab_data[511:352]");
      fail = 1;
    end
    mgmt_nw_vld = 1;
    mgmt_nw_data = golden_rx;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_rx, nw_dll_data) ||
        fab_nw_ready) begin
      vibe_tb_nw512_fail_print(
          "tc_nw_adapt_linkready",
          "mgmt GOLDEN_RX priority over fab GOLDEN_TX",
          golden_rx, dll_w, nw_dll_data,
          "u_n.nw_dll_data");
      $display("  actual   : fab_nw_ready=%0b (must be 0)", fab_nw_ready);
      fail = 1;
    end
    if (!fail) $display("PASS tc_nw_adapt_linkready");
    $finish;
  end
endmodule
