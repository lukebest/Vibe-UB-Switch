// TP-PHY-012: GOLDEN 512b NW TX → PMA loopback → recovered NW RX === GOLDEN.
// Full 512-bit compare (not LPH fields). No rtl/ edit.
`timescale 1ns/1ps
module tc_nw_pkt_pma_loopback;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw512.svh"

  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [511:0] fab_tx_data, fab_rx_data, mgmt_tx_data;
  logic [639:0] cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, accepted, saw_rx, dump_hold;
  integer saw_afrv, saw_pcs_rx, saw_am, saw_txnz;
  integer saw_fab_rx, saw_fec_fail, saw_deskew;
  integer nw_w, dll_w, rx_w;
  logic [511:0] golden_tx, last_rx;

  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  assign rxclk  = txclk;
  assign rxdata = txdata;

  logic        wav_tx_nz, wav_rx_nz, wav_lb_eq, wav_pcs_rx, wav_fec;
  logic        wav_ptxv, wav_txlv, wav_rx_eq;
  logic [3:0]  wav_am;
  logic [31:0] wav_lane0, wav_lane3;
  logic [159:0] wav_tx_sop, wav_rx_sop;
  logic [351:0] wav_tx_pld, wav_rx_pld;
  logic [3:0]   wav_tx_cfg, wav_rx_cfg;
  logic [1:0]   wav_tx_rt, wav_rx_rt;
  logic [15:0]  wav_tx_scna, wav_tx_dcna, wav_rx_scna, wav_rx_dcna;

  initial begin
    if ($test$plusargs("DUMP") || $test$plusargs("VCD")) begin
      begin : dump_open
        reg [8*256-1:0] dump_fn;
        dump_fn = "nw_pkt_pma_loopback_data512.vcd";
        if ($value$plusargs("DUMPFILE=%s", dump_fn)) ;
        $dumpfile(dump_fn);
        $dumpvars(0, clk_fab, txclk, rxclk, rst_n,
                  fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready,
                  fab_tx_data, fab_rx_data, golden_tx,
                  wav_tx_sop, wav_tx_pld, wav_rx_sop, wav_rx_pld,
                  wav_tx_cfg, wav_tx_rt, wav_tx_scna, wav_tx_dcna,
                  wav_rx_cfg, wav_rx_rt, wav_rx_scna, wav_rx_dcna,
                  wav_tx_nz, wav_rx_nz, wav_lb_eq, wav_lane0, wav_lane3,
                  wav_ptxv, wav_txlv, wav_am, wav_pcs_rx, wav_fec,
                  wav_rx_eq, txdata, rxdata);
      end
    end
  end

  vibe_port u_p (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .lmsm_go(lmsm_go), .txclk(txclk), .rxclk(rxclk),
    .txdata(txdata), .rxdata(rxdata),
    .fab_tx_data(fab_tx_data), .fab_tx_vld(fab_tx_vld), .fab_tx_ready(fab_tx_ready),
    .fab_rx_data(fab_rx_data), .fab_rx_vld(fab_rx_vld), .fab_rx_ready(fab_rx_ready),
    .mgmt_tx_data(mgmt_tx_data), .mgmt_tx_vld(mgmt_tx_vld), .mgmt_tx_ready(mgmt_tx_ready),
    .status_up(status_up), .disabled(disabled),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .afifo_ovf(afifo_ovf),     .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );

  assign wav_tx_nz   = |txdata;
  assign wav_rx_nz   = |rxdata;
  assign wav_lb_eq   = (rxdata === txdata);
  assign wav_lane0   = txdata[31:0];
  assign wav_lane3   = txdata[511:480];
  assign wav_am      = u_p.am_locked;
  assign wav_pcs_rx  = u_p.pcs_rx_v;
  assign wav_fec     = u_p.fec_fail;
  assign wav_ptxv    = u_p.p_txv;
  assign wav_txlv    = u_p.txlv;
  assign wav_rx_eq   = fab_rx_vld && (fab_rx_data === golden_tx) &&
                       ($bits(u_p.fab_rx_data) === 512);
  // 设计: SOP LPH is [511:352] (160b); [351:0] is payload. Not [511:496].
  assign wav_tx_sop  = fab_tx_data[511:352];
  assign wav_tx_pld  = fab_tx_data[351:0];
  assign wav_rx_sop  = fab_rx_data[511:352];
  assign wav_rx_pld  = fab_rx_data[351:0];
  assign wav_tx_cfg  = wav_tx_sop[11:8];
  assign wav_tx_rt   = wav_tx_sop[23:22];
  assign wav_tx_scna = wav_tx_sop[47:32];
  assign wav_tx_dcna = wav_tx_sop[63:48];
  assign wav_rx_cfg  = wav_rx_sop[11:8];
  assign wav_rx_rt   = wav_rx_sop[23:22];
  assign wav_rx_scna = wav_rx_sop[47:32];
  assign wav_rx_dcna = wav_rx_sop[63:48];

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
    fail = 0; accepted = 0; saw_rx = 0; dump_hold = 0;
    saw_afrv = 0; saw_pcs_rx = 0; saw_am = 0; saw_txnz = 0;
    saw_fab_rx = 0; saw_fec_fail = 0; saw_deskew = 0;
    last_rx = 512'd0;
    golden_tx = vibe_tb_nw512_golden_tx();
    nw_w  = $bits(u_p.fab_tx_data);
    dll_w = $bits(u_p.dll_tx_d);
    rx_w  = $bits(u_p.fab_rx_data);
    bring_link();
    if (fail) begin
      $finish;
    end

    fab_tx_data = golden_tx;
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_tx_vld = 1;
      if (fab_tx_ready) begin
        @(posedge clk_fab);
        accepted = 1;
        if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, u_p.dll_tx_d)) begin
          vibe_tb_nw512_fail_print(
              "tc_nw_pkt_pma_loopback",
              "TX NW→DLL accepted beat GOLDEN_TX",
              golden_tx, dll_w, u_p.dll_tx_d,
              "u_p.dll_tx_d");
          $finish;
        end
        if (vibe_tb_nw512_sop_lph_fail(golden_tx, u_p.dll_tx_d)) begin
          vibe_tb_nw512_sop_lph_print(
              "tc_nw_pkt_pma_loopback",
              "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
              golden_tx, u_p.dll_tx_d, "u_p.dll_tx_d[511:352]");
          $finish;
        end
        fab_tx_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_tx_vld = 0;
    fab_tx_data = vibe_tb_nw512_golden_tx_b2();
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_tx_vld = 1;
      if (fab_tx_ready) begin
        @(posedge clk_fab);
        fab_tx_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_tx_vld = 0;
    if (!accepted) begin
      fail_at("fab_tx GOLDEN_TX after LinkReady",
              "fab_tx_ready handshake",
              "not accepted",
              "u_p.u_nw / u_p.u_dll.u_tx");
      $finish;
    end

    for (i = 0; i < 20000; i = i + 1) begin
      @(negedge clk_fab);
      if (u_p.afrv0 & u_p.afrv1 & u_p.afrv2 & u_p.afrv3) saw_afrv = 1;
      if (u_p.pcs_rx_v) saw_pcs_rx = 1;
      if (|u_p.am_locked) saw_am = 1;
      if (txdata !== 512'd0) saw_txnz = 1;
      if (u_p.fec_fail) saw_fec_fail = 1;
      if (u_p.deskew_ok) saw_deskew = 1;
      if (fab_rx_vld) begin
        saw_fab_rx = 1;
        last_rx = fab_rx_data;
        if (!vibe_tb_nw512_vec_fail(rx_w, golden_tx, fab_rx_data) &&
            !vibe_tb_nw512_sop_lph_fail(golden_tx, fab_rx_data))
          saw_rx = 1;
      end
      // +DUMP: keep the window until GOLDEN match AND am_locked (supporting).
      // Exiting on saw_rx alone finishes before PCS lock and falsely FAILs.
      if (saw_rx && saw_am && ($test$plusargs("DUMP") || $test$plusargs("VCD"))) begin
        dump_hold = dump_hold + 1;
        if (dump_hold >= 32)
          i = 20000;
      end
    end

    if (!saw_rx) begin
      $display("  detail   : vld=%0b last_rx=%h pcs_rx_v=%0b am_lock=%04b fec_fail=%0b deskew=%0b afrv=%0b%0b%0b%0b",
               fab_rx_vld, last_rx, u_p.pcs_rx_v, u_p.am_locked, u_p.fec_fail,
               u_p.deskew_ok, u_p.afrv0, u_p.afrv1, u_p.afrv2, u_p.afrv3);
      $display("  peak     : saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d",
               saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew);
      vibe_tb_nw512_fail_print(
          "tc_nw_pkt_pma_loopback",
          "PMA loopback; recover NW RX data[511:0] === GOLDEN_TX",
          golden_tx, rx_w, last_rx,
          "u_p.fab_rx_data");
      $finish;
    end
    if (saw_fec_fail) begin
      fail_at("supporting: fec_fail during GOLDEN loopback",
              "fec_fail=0",
              "fec_fail=1",
              "u_p.fec_fail");
      $finish;
    end
    if (!saw_am) begin
      fail_at("supporting: am_locked during GOLDEN loopback",
              "am_locked nonzero",
              "am_locked stayed 0",
              "u_p.am_locked");
      $finish;
    end

    $display("PASS tc_nw_pkt_pma_loopback");
    $display("  scored : fab_rx_data[511:0] === GOLDEN_TX after PMA loopback");
    $display("  peak     : saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d am_lock_end=%04b",
             saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew,
             u_p.am_locked);
    $finish;
  end
endmodule
