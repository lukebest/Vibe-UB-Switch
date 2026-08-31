// TP-PHY-012: NW packet TX → PMA txdata looped to rxdata → fab_rx LPH/payload.
// Same DUT vibe_port. No rtl/ edit.
`timescale 1ns/1ps
module tc_nw_pkt_pma_loopback;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw_pma.svh"

  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [639:0] fab_tx_data, fab_rx_data, mgmt_tx_data, cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, k, accepted, saw_rx, payload_ok;
  integer saw_afrv, saw_pcs_rx, saw_am, saw_txnz;
  integer saw_amctl_idle, saw_am_word;
  integer saw_fab_rx, saw_fec_fail, saw_deskew;
  logic [159:0] last_flit0, first_flit0;
  logic [639:0] pkt;

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
      $display("FAIL tc_nw_pkt_pma_loopback");
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe units");
    end
  endtask

  task automatic bring_link;
    integer w;
    begin
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
      w = 0;
      while (!(u_p.link_ready && status_up) && w < 64) begin
        @(posedge clk_fab);
        w = w + 1;
      end
      if (!u_p.link_ready || !status_up) begin
        fail_at("lmsm_go + force am_locked/lid_bad",
                "link_ready=1 status_up=1",
                "LMSM/DLL did not reach ACTIVE/NRM",
                "u_p.u_lmsm / u_p.u_dll.u_sm");
      end
      force u_p.u_dll.u_crd.cells = 16'd64;
      @(posedge clk_fab);
      release u_p.u_dll.u_crd.cells;
      force u_p.u_lmsm.st = 5'd9;
      release u_p.u_lmsm.am_locked;
      release u_p.u_lmsm.lid_bad;
      @(posedge clk_fab);
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_rx = 0; payload_ok = 0;
    saw_afrv = 0; saw_pcs_rx = 0; saw_am = 0; saw_txnz = 0;
    saw_amctl_idle = 0; saw_am_word = 0;
    saw_fab_rx = 0; saw_fec_fail = 0; saw_deskew = 0;
    last_flit0 = 160'd0; first_flit0 = 160'd0;
    pkt = vibe_tb_nw_pma_pkt();
    bring_link();
    if (fail) begin
      $finish;
    end

    fab_tx_data = pkt;
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_tx_vld = 1;
      if (fab_tx_ready) begin
        @(posedge clk_fab);
        accepted = 1;
        fab_tx_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_tx_vld = 0;
    if (!accepted) begin
      fail_at("fab_tx legal RT=00 packet after LinkReady",
              "fab_tx_ready handshake",
              "not accepted",
              "u_p.u_nw / u_p.u_dll.u_tx");
      $finish;
    end

    // TX→PMA→RX inverse. Score LPH + payload (not merely vld).
    for (i = 0; i < 20000; i = i + 1) begin
      @(negedge clk_fab);
      if (u_p.afrv0 & u_p.afrv1 & u_p.afrv2 & u_p.afrv3) saw_afrv = 1;
      if (u_p.pcs_rx_v) saw_pcs_rx = 1;
      if (|u_p.am_locked) saw_am = 1;
      if (txdata !== 512'd0) saw_txnz = 1;
      if (u_p.fec_fail) saw_fec_fail = 1;
      if (u_p.deskew_ok) saw_deskew = 1;
      if (fab_rx_vld) begin
        if (!saw_fab_rx)
          first_flit0 = fab_rx_data[639:480];
        saw_fab_rx = 1;
        last_flit0 = fab_rx_data[639:480];
      end
      // Diagnostic only (does not change expected LPH). Idle = fab_tx_vld==0
      // after handshake. AMCTL-looking = 16b BODY/END CWs on held txdata.
      if (!fab_tx_vld) begin
        if (u_p.u_ptx.am_word) saw_am_word = 1;
        for (k = 0; k < 32; k = k + 1) begin
          if (txdata[k*16 +: 16] === 16'hAC8E ||
              txdata[k*16 +: 16] === 16'hB23C ||
              txdata[k*16 +: 16] === 16'hE14D)
            saw_amctl_idle = 1;
        end
      end
      if (fab_rx_vld && vibe_tb_nw_pma_lph_ok(fab_rx_data)) begin
        saw_rx = 1;
        // Payload flits 1..2 and [159:32] of flit3 (DLL TX may attach BCRC in [31:0]).
        if (fab_rx_data[479:320] === pkt[479:320] &&
            fab_rx_data[319:160] === pkt[319:160] &&
            fab_rx_data[159:32]  === pkt[159:32])
          payload_ok = 1;
      end
    end

    if (!saw_rx) begin
      $display("  detail   : vld=%0b flit0=%h first_flit0=%h last_flit0=%h pcs_rx_v=%0b am_lock=%04b fec_fail=%0b deskew=%0b afrv=%0b%0b%0b%0b txlv=%0b",
               fab_rx_vld, fab_rx_data[639:480], first_flit0, last_flit0,
               u_p.pcs_rx_v, u_p.am_locked, u_p.fec_fail, u_p.deskew_ok,
               u_p.afrv0, u_p.afrv1, u_p.afrv2, u_p.afrv3, u_p.txlv);
      $display("  first_lph: CFG=%0d RT=%02b SCNA=%04h DCNA=%04h (expected CFG=3 RT=00 SCNA=A11A DCNA=B22B)",
               vibe_lph_cfg(first_flit0), vibe_lph_rt(first_flit0),
               vibe_nth_scna(first_flit0), vibe_nth_dcna(first_flit0));
      $display("  peak     : saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d saw_amctl_idle=%0d (during wait)",
               saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew, saw_amctl_idle);
      fail_at("rxdata=txdata after accepted NW packet; wait 20000 clk_fab",
              "fab_rx_vld with CFG=3 RT=00 SCNA=A11A DCNA=B22B (TP-PHY-012)",
              "see detail line",
              "u_p.u_prx / u_p.u_dll.u_rx / u_p.u_nw.fab_rx");
      $finish;
    end
    if (!payload_ok) begin
      $display("  detail   : rx[479:160]=%h", fab_rx_data[479:160]);
      fail_at("fab_rx LPH matched; compare payload flits",
              "payload[479:32] matches injected beat (BCRC may occupy [31:0])",
              "see detail line",
              "u_p.fab_rx_data");
      $finish;
    end

    $display("PASS tc_nw_pkt_pma_loopback");
    $display("  scored : fab_rx LPH+payload after PMA loopback");
    $display("  peak     : saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d afrv_end=%0b%0b%0b%0b am_lock_end=%04b fab_rx_vld=%0b flit0=%h",
             saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew,
             u_p.afrv0, u_p.afrv1, u_p.afrv2, u_p.afrv3, u_p.am_locked, fab_rx_vld, last_flit0);
    $finish;
  end
endmodule
