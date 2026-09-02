// TP-PHY-008 / FS-0.2.7 Overlay B: NW↔DLL data[511:0] @ 1.25 GHz + vld/ready.
// Beat-by-beat 512-bit vector compare, both directions. Width is a gate only.
// Do not invent LPH slices. Do not PASS on [511:0] of a 640-bit DUT pin.
`timescale 1ns/1ps
module tc_phy_nw_dll_512b;
  `include "vibe_tb_nw512.svh"

  logic clk, rst_n, link_ready;
  logic [511:0] fab_tx_data, mgmt_tx_data, dll_tx_data, dll_rx_data, fab_rx_data;
  logic fab_tx_vld, fab_tx_ready, mgmt_tx_vld, mgmt_tx_ready;
  logic dll_tx_vld, dll_tx_ready, dll_rx_vld, dll_rx_ready, fab_rx_vld, fab_rx_ready;
  logic [511:0] golden_tx, golden_rx;
  integer fail, nw_w, dll_w, rx_w, dll_rx_w;

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
    rst_n = 1; link_ready = 1;
    fab_tx_data = 0; mgmt_tx_data = 0; dll_rx_data = 0;
    fab_tx_vld = 0; mgmt_tx_vld = 0; dll_tx_ready = 1;
    dll_rx_vld = 0; fab_rx_ready = 1;
    #1;
    nw_w     = $bits(u_n.fab_tx_data);
    dll_w    = $bits(u_n.dll_tx_data);
    rx_w     = $bits(u_n.fab_rx_data);
    dll_rx_w = $bits(u_n.dll_rx_data);
    if (nw_w !== 512 || rx_w !== 512) begin
      $display("FAIL tc_phy_nw_dll_512b");
      $display("  stimulus : FS-0.2.7 Overlay B — NW↔DLL data[511:0] @1.25GHz");
      $display("  expected : $bits(fab_tx_data)=512 $bits(fab_rx_data)=512");
      $display("  actual   : NW fab_tx_data=%0d fab_rx_data=%0d", nw_w, rx_w);
      $display("  hier     : u_n.fab_tx_data / vibe_nw_adapt");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // TX NW→DLL: drive GOLDEN, handshake, score dll_tx === GOLDEN.
    link_ready = 1; dll_tx_ready = 1; mgmt_tx_vld = 0;
    fab_tx_data = golden_tx;
    fab_tx_vld = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, dll_tx_data) ||
        !fab_tx_ready || !dll_tx_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_phy_nw_dll_512b",
          "TX NW→DLL: fab_tx_data=GOLDEN_TX vld/ready",
          golden_tx, dll_w, dll_tx_data,
          "u_n.dll_tx_data");
      $display("  actual   : ready=%0b dll_tx_vld=%0b (must handshake + 512b match)",
               fab_tx_ready, dll_tx_vld);
      fail = 1;
    end
    fab_tx_vld = 0;

    // RX DLL→NW: drive GOLDEN_RX, score fab_rx === GOLDEN_RX.
    dll_rx_data = golden_rx;
    dll_rx_vld = 1; fab_rx_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, fab_rx_data) ||
        !fab_rx_vld) begin
      vibe_tb_nw512_fail_print(
          "tc_phy_nw_dll_512b",
          "RX DLL→NW: dll_rx_data=GOLDEN_RX vld/ready",
          golden_rx, rx_w, fab_rx_data,
          "u_n.fab_rx_data");
      $display("  actual   : fab_rx_vld=%0b", fab_rx_vld);
      fail = 1;
    end
    dll_rx_vld = 0;

    // Supporting: LinkReady gates ready/vld (only if Overlay B width already holds).
    if (!fail) begin
      link_ready = 0; fab_tx_vld = 1; #1;
      if (fab_tx_ready || dll_tx_vld) begin
        $display("FAIL tc_phy_nw_dll_512b");
        $display("  stimulus : link_ready=0 fab_tx_vld=1");
        $display("  expected : ready=0 vld=0");
        $display("  actual   : rdy=%0b vld=%0b", fab_tx_ready, dll_tx_vld);
        $display("  hier     : u_n.fab_tx_ready");
        $display("  reproduce: make -C tb/vibe units");
        fail = 1;
      end
    end

    if (!fail)
      $display("PASS tc_phy_nw_dll_512b");
    $finish;
  end
endmodule
