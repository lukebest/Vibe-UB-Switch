// TP-PHY-008 / FS-0.2.7 Overlay B: NW↔DLL data[511:0] @ 1.25 GHz + vld/ready.
// Beat-by-beat 512-bit vector compare, both directions. Width is a gate only.
// Do not invent LPH slices. Do not PASS on [511:0] of a 640-bit DUT pin.
`timescale 1ns/1ps
module tc_phy_nw_dll_512b;
  `include "vibe_tb_nw512.svh"

  logic clk, rst_n, link_ready;
  logic [511:0] fab_nw_data, mgmt_nw_data, nw_dll_data, dll_nw_data, nw_fab_data;
  logic fab_nw_vld, fab_nw_ready, mgmt_nw_vld, mgmt_nw_ready;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready, nw_fab_vld, nw_fab_ready;
  logic [511:0] golden_tx, golden_rx;
  integer fail, nw_w, dll_w, rx_w, dll_rx_w;

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
    rst_n = 1; link_ready = 1;
    fab_nw_data = 0; mgmt_nw_data = 0; dll_nw_data = 0;
    fab_nw_vld = 0; mgmt_nw_vld = 0; nw_dll_ready = 1;
    dll_nw_vld = 0; nw_fab_ready = 1;
    #1;
    nw_w     = $bits(u_n.fab_nw_data);
    dll_w    = $bits(u_n.nw_dll_data);
    rx_w     = $bits(u_n.nw_fab_data);
    dll_rx_w = $bits(u_n.dll_nw_data);
    if (nw_w !== 512 || rx_w !== 512) begin
      $display("FAIL tc_phy_nw_dll_512b");
      $display("  stimulus : FS-0.2.7 Overlay B — NW↔DLL data[511:0] @1.25GHz");
      $display("  expected : $bits(fab_nw_data)=512 $bits(nw_fab_data)=512");
      $display("  actual   : NW fab_nw_data=%0d nw_fab_data=%0d", nw_w, rx_w);
      $display("  hier     : u_n.fab_nw_data / vibe_nw_adapt");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // TX NW→DLL: drive GOLDEN, handshake, score dll_tx === GOLDEN.
    link_ready = 1; nw_dll_ready = 1; mgmt_nw_vld = 0;
    fab_nw_data = golden_tx;
    fab_nw_vld = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, nw_dll_data) ||
        !fab_nw_ready || !nw_dll_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_phy_nw_dll_512b",
          "TX NW→DLL: fab_nw_data=GOLDEN_TX vld/ready",
          golden_tx, dll_w, nw_dll_data,
          "u_n.nw_dll_data");
      $display("  actual   : ready=%0b nw_dll_vld=%0b (must handshake + 512b match)",
               fab_nw_ready, nw_dll_vld);
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_tx, nw_dll_data)) begin
      vibe_tb_nw512_sop_lph_print(
          "tc_phy_nw_dll_512b",
          "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
          golden_tx, nw_dll_data, "u_n.nw_dll_data[511:352]");
      fail = 1;
    end
    fab_nw_vld = 0;

    // RX DLL→NW: drive GOLDEN_RX, score fab_rx === GOLDEN_RX + SOP LPH.
    dll_nw_data = golden_rx;
    dll_nw_vld = 1; nw_fab_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, nw_fab_data) ||
        !nw_fab_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_phy_nw_dll_512b",
          "RX DLL→NW: dll_nw_data=GOLDEN_RX vld/ready",
          golden_rx, rx_w, nw_fab_data,
          "u_n.nw_fab_data");
      $display("  actual   : nw_fab_vld=%0b", nw_fab_vld);
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_rx, nw_fab_data)) begin
      vibe_tb_nw512_sop_lph_print(
          "tc_phy_nw_dll_512b",
          "RX SOP LPH GOLDEN_RX[511:352] vs DUT[511:352]",
          golden_rx, nw_fab_data, "u_n.nw_fab_data[511:352]");
      fail = 1;
    end
    dll_nw_vld = 0;

    // Supporting: LinkReady gates ready/vld (only if Overlay B width already holds).
    if (!fail) begin
      link_ready = 0; fab_nw_vld = 1; #1;
      if (fab_nw_ready || nw_dll_vld) begin
        $display("FAIL tc_phy_nw_dll_512b");
        $display("  stimulus : link_ready=0 fab_nw_vld=1");
        $display("  expected : ready=0 vld=0");
        $display("  actual   : rdy=%0b vld=%0b", fab_nw_ready, nw_dll_vld);
        $display("  hier     : u_n.fab_nw_ready");
        $display("  reproduce: make -C tb/vibe units");
        fail = 1;
      end
    end

    if (!fail)
      $display("PASS tc_phy_nw_dll_512b");
    $finish;
  end
endmodule
