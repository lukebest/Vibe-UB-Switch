// TP-PHY-008 / FS-0.2.7 Overlay B: NW↔DLL is ONLY data[511:0] @ 1.25 GHz
// with vld/ready. 640b is the DLL↔PCS window, not the NW pin.
// Compiles against current 640-bit DUT pins; FAIL if NW width is not 512.
`timescale 1ns/1ps
module tc_phy_nw_dll_512b;
  logic clk, rst_n, link_ready;
  logic [639:0] fab_tx_data, mgmt_tx_data, dll_tx_data, dll_rx_data, fab_rx_data;
  logic fab_tx_vld, fab_tx_ready, mgmt_tx_vld, mgmt_tx_ready;
  logic dll_tx_vld, dll_tx_ready, dll_rx_vld, dll_rx_ready, fab_rx_vld, fab_rx_ready;
  integer fail, nw_w, dll_pcs_w;

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
    rst_n = 1; link_ready = 1;
    fab_tx_data = 0; mgmt_tx_data = 0; dll_rx_data = 0;
    fab_tx_vld = 0; mgmt_tx_vld = 0; dll_tx_ready = 1;
    dll_rx_vld = 0; fab_rx_ready = 1;
    #1;
    nw_w = $bits(u_n.fab_tx_data);
    dll_pcs_w = $bits(u_n.dll_tx_data);
    if (nw_w !== 512) begin
      $display("FAIL tc_phy_nw_dll_512b");
      $display("  stimulus : FS-0.2.7 Overlay B — NW↔DLL data[511:0] @1.25GHz");
      $display("  expected : $bits(fab_tx_data)=512 (and fab_rx_data=512)");
      $display("  actual   : NW fab_tx_data=%0d fab_rx_data=%0d",
               nw_w, $bits(u_n.fab_rx_data));
      $display("  hier     : u_n.fab_tx_data / vibe_nw_adapt / vibe_port");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    // DLL↔PCS 640 is allowed (old U26 window). Do not require it on this pin
    // until 设计 splits the buses; only FAIL the NW 512 rule above.
    if (!fail && (dll_pcs_w !== 512) && (dll_pcs_w !== 640)) begin
      $display("FAIL tc_phy_nw_dll_512b");
      $display("  stimulus : Overlay B — DLL side of nw_adapt");
      $display("  expected : 512 (NW↔DLL) or 640 (unsplit DUT)");
      $display("  actual   : dll_tx_data=%0d", dll_pcs_w);
      $display("  hier     : u_n.dll_tx_data");
      fail = 1;
    end
    if (!fail) begin
      // Ready handshake still required at fab clock.
      link_ready = 0; fab_tx_vld = 1; #1;
      if (fab_tx_ready || dll_tx_vld) begin
        $display("FAIL tc_phy_nw_dll_512b");
        $display("  stimulus : link_ready=0 fab_tx_vld=1");
        $display("  expected : ready=0 vld=0");
        $display("  actual   : rdy=%0b vld=%0b", fab_tx_ready, dll_tx_vld);
        $display("  hier     : u_n.fab_tx_ready");
        fail = 1;
      end
    end
    if (!fail)
      $display("PASS tc_phy_nw_dll_512b");
    $finish;
  end
endmodule
