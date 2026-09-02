// TP-PHY-001: full-duplex port. Overlay B: 512-bit GOLDEN TX NW→DLL and
// RX DLL→NW after PMA loopback. Width is a gate; content is the must.
`timescale 1ns/1ps
module tc_port_smoke;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw512.svh"
  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [511:0] fab_tx_data, fab_rx_data, mgmt_tx_data;
  logic [639:0] cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, accepted, saw_tx, pack_ok, saw_rx, last_v, nw_w, dll_w, rx_w;
  logic [511:0] last_pack;
  logic [511:0] golden_tx;

  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  assign rxclk  = txclk;
  assign rxdata = txdata;

  vibe_port u_p (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .lmsm_go(lmsm_go), .txclk(txclk), .rxclk(rxclk),
    .txdata(txdata), .rxdata(rxdata),
    .fab_tx_data(fab_tx_data), .fab_tx_vld(fab_tx_vld), .fab_tx_ready(fab_tx_ready),
    .fab_rx_data(fab_rx_data), .fab_rx_vld(fab_rx_vld), .fab_rx_ready(fab_rx_ready),
    .mgmt_tx_data(mgmt_tx_data), .mgmt_tx_vld(mgmt_tx_vld), .mgmt_tx_ready(mgmt_tx_ready),
    .status_up(status_up), .disabled(disabled),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .afifo_ovf(afifo_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );

  task automatic fail_at;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail = 1;
      $display("FAIL tc_port_smoke");
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe units");
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_tx = 0; pack_ok = 1; saw_rx = 0; last_v = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    nw_w  = $bits(u_p.fab_tx_data);
    dll_w = $bits(u_p.dll_tx_d);
    rx_w  = $bits(u_p.fab_rx_data);
    rst_n = 0; port_rst = 0; device_rst = 0; lmsm_go = 0;
    fab_tx_vld = 0; fab_rx_ready = 1; mgmt_tx_vld = 0;
    fab_tx_data = 0; mgmt_tx_data = 0;
    repeat (8) @(posedge clk_fab);
    rst_n = 1;
    repeat (8) @(posedge clk_fab);
    force u_p.u_lmsm.am_locked = 4'b1111;
    force u_p.u_lmsm.lid_bad   = 1'b0;
    @(negedge clk_fab);
    lmsm_go = 1;
    @(posedge clk_fab);
    lmsm_go = 0;
    i = 0;
    while (!(u_p.link_ready && status_up) && i < 64) begin
      @(posedge clk_fab);
      i = i + 1;
    end
    if (!u_p.link_ready || !status_up) begin
      fail_at("lmsm_go + force am_locked=1111 lid_bad=0",
              "link_ready=1 status_up=1 (TX and RX domains up)",
              "LMSM/DLL did not reach ACTIVE/NRM",
              "u_p.u_lmsm / u_p.u_dll.u_sm");
      $finish;
    end
    force u_p.u_dll.u_crd.cells = 16'd64;
    @(posedge clk_fab);
    release u_p.u_dll.u_crd.cells;
    force u_p.u_lmsm.st = 5'd9;
    release u_p.u_lmsm.am_locked;
    release u_p.u_lmsm.lid_bad;
    @(posedge clk_fab);

    fab_tx_data = golden_tx;
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_tx_vld = 1;
      if (fab_tx_ready) begin
        @(posedge clk_fab);
        accepted = 1;
        if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, u_p.dll_tx_d)) begin
          vibe_tb_nw512_fail_print(
              "tc_port_smoke",
              "TX NW→DLL accepted beat GOLDEN_TX",
              golden_tx, dll_w, u_p.dll_tx_d,
              "u_p.dll_tx_d");
          $finish;
        end
        fab_tx_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_tx_vld = 0;
    if (!accepted) begin
      fail_at("fab_tx_vld GOLDEN_TX after LinkReady+cells=64",
              "fab_tx_ready handshake (packet accepted)",
              "not accepted",
              "u_p.u_nw.fab_tx_ready / u_p.u_dll.u_tx.nw_ready");
      $finish;
    end

    for (i = 0; i < 20000; i = i + 1) begin
      @(posedge txclk);
      if (last_v) begin
        saw_tx = 1;
        if (txdata === 512'd0)
          pack_ok = 0;
        if (txdata !== last_pack)
          pack_ok = 0;
      end
      last_v    = u_p.p_txv;
      last_pack = {u_p.p_tx3, u_p.p_tx2, u_p.p_tx1, u_p.p_tx0};
      @(negedge clk_fab);
      if (fab_rx_vld) begin
        if (!vibe_tb_nw512_vec_fail(rx_w, golden_tx, fab_rx_data))
          saw_rx = 1;
      end
    end

    if (!saw_tx) begin
      fail_at("legal NW beat accepted; watch PMA txdata",
              "txdata[511:0] nonzero (full-duplex TX)",
              "txdata stayed 0 or p_txv never rose",
              "u_p.u_pma.txdata / u_p.p_txv");
      $finish;
    end
    if (!pack_ok) begin
      fail_at("p_txv beats after accept",
              "txdata[127:0]=lane0 .. [511:384]=lane3 (TP-PHY-001/018)",
              "lane pack mismatch or zero beat",
              "u_p.u_pma / u_p.p_tx0..3");
      $finish;
    end
    if (!saw_rx) begin
      vibe_tb_nw512_fail_print(
          "tc_port_smoke",
          "PMA loopback; recover NW RX data[511:0] === GOLDEN_TX",
          golden_tx, rx_w, fab_rx_data,
          "u_p.fab_rx_data");
      $display("  actual   : fab_rx_vld=%0b fec_fail=%0b am_locked=%04b",
               fab_rx_vld, u_p.fec_fail, u_p.am_locked);
      $finish;
    end
    $display("PASS tc_port_smoke");
    $finish;
  end
endmodule
