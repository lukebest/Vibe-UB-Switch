// TP-PHY-012: 100 distinct GOLDEN 512b NW packets → PMA loopback → RX === TX.
// Full 512-bit compare per packet, in order. No rtl/ edit.
`timescale 1ns/1ps
module tc_nw_pkt_pma_loopback;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw512.svh"

  localparam NPKT     = 100;
  localparam WAIT_MAX = 2000000;
  localparam BEAT_TO  = 4096;

  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [511:0] fab_tx_data, fab_rx_data, mgmt_tx_data;
  logic [639:0] cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, j, accepted, dump_hold;
  integer saw_afrv, saw_pcs_rx, saw_am, saw_txnz;
  integer saw_fab_rx, saw_fec_fail, saw_deskew;
  integer nw_w, dll_w, rx_w;
  integer tx_n, rx_n, pkt, wait_i, beat_w, hit_other;
  logic [511:0] golden_tx, last_rx;
  logic [511:0] exp_sop [0:NPKT-1];
  logic [511:0] exp_b2  [0:NPKT-1];

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
        // Selected pins only — not $dumpvars(0, tc). 100 pkts stay small.
        $dumpvars(0, clk_fab, txclk, rxclk, rst_n,
                  fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready,
                  fab_tx_data, fab_rx_data, golden_tx,
                  wav_tx_sop, wav_tx_pld, wav_rx_sop, wav_rx_pld,
                  wav_tx_cfg, wav_tx_rt, wav_tx_scna, wav_tx_dcna,
                  wav_rx_cfg, wav_rx_rt, wav_rx_scna, wav_rx_dcna,
                  wav_tx_nz, wav_rx_nz, wav_lb_eq, wav_lane0, wav_lane3,
                  wav_ptxv, wav_txlv, wav_am, wav_pcs_rx, wav_fec,
                  wav_rx_eq, txdata, rxdata, tx_n, rx_n);
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
  always @(*) begin
    if (fab_rx_vld && rx_n >= 0 && rx_n < NPKT)
      wav_rx_eq = (fab_rx_data === exp_sop[rx_n]) &&
                  ($bits(u_p.fab_rx_data) === 512);
    else
      wav_rx_eq = 1'b0;
  end
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
      // Enough cells for 100 × 4-flit packets (grain 8 → 1 cell each).
      force u_p.u_dll.u_crd.cells = 16'd512;
      @(posedge clk_fab);
      release u_p.u_dll.u_crd.cells;
      force u_p.u_lmsm.st = 5'd9;
      release u_p.u_lmsm.am_locked;
      release u_p.u_lmsm.lid_bad;
      @(posedge clk_fab);
    end
  endtask

  task automatic peek_rx;
    begin
      if (u_p.afrv0 & u_p.afrv1 & u_p.afrv2 & u_p.afrv3) saw_afrv = 1;
      if (u_p.pcs_rx_v) saw_pcs_rx = 1;
      if (|u_p.am_locked) saw_am = 1;
      if (txdata !== 512'd0) saw_txnz = 1;
      if (u_p.fec_fail) saw_fec_fail = 1;
      if (u_p.deskew_ok) saw_deskew = 1;
      if (!fab_rx_vld)
        ;
      else begin
        saw_fab_rx = 1;
        last_rx = fab_rx_data;
        if (rx_n >= NPKT)
          ;
        else if (fab_rx_data === exp_sop[rx_n]) begin
          if (vibe_tb_nw512_vec_fail(rx_w, exp_sop[rx_n], fab_rx_data) ||
              vibe_tb_nw512_sop_lph_fail(exp_sop[rx_n], fab_rx_data)) begin
            vibe_tb_nw512_fail_print_pkt(
                "tc_nw_pkt_pma_loopback", rx_n, NPKT,
                "RX fab_rx_data[511:0] === GOLDEN of this packet",
                exp_sop[rx_n], rx_w, fab_rx_data, "u_p.fab_rx_data");
            fail = 1;
          end else
            rx_n = rx_n + 1;
        end else begin
          // Remainder / non-SOP beats are not required to match injected b2
          // (DUT may re-pack the 16 B). Only a different packet's SOP is order-FAIL.
          hit_other = -1;
          for (j = 0; j < NPKT; j = j + 1)
            if (fab_rx_data === exp_sop[j] && j != rx_n)
              hit_other = j;
          if (hit_other >= 0) begin
            vibe_tb_nw512_fail_print_pkt(
                "tc_nw_pkt_pma_loopback", rx_n, NPKT,
                "RX order: packet i TX must match packet i RX",
                exp_sop[rx_n], rx_w, fab_rx_data, "u_p.fab_rx_data");
            $display("  note     : recovered SOP of packet %0d while waiting for %0d",
                     hit_other, rx_n);
            fail = 1;
          end
        end
      end
    end
  endtask

  task automatic send_beat;
    input [511:0] beat;
    input integer score_tx;
    input integer pkt_i;
    begin
      fab_tx_data = beat;
      if (score_tx)
        golden_tx = beat;
      accepted = 0;
      beat_w = 0;
      while (!accepted && !fail && beat_w < BEAT_TO) begin
        @(negedge clk_fab);
        peek_rx();
        if (fail)
          ;
        else begin
          fab_tx_vld = 1;
          if (fab_tx_ready) begin
            @(posedge clk_fab);
            if (score_tx) begin
              if (vibe_tb_nw512_vec_fail(dll_w, beat, u_p.dll_tx_d)) begin
                vibe_tb_nw512_fail_print_pkt(
                    "tc_nw_pkt_pma_loopback", pkt_i, NPKT,
                    "TX NW→DLL accepted beat === this packet GOLDEN",
                    beat, dll_w, u_p.dll_tx_d, "u_p.dll_tx_d");
                fail = 1;
              end else if (vibe_tb_nw512_sop_lph_fail(beat, u_p.dll_tx_d)) begin
                $display("FAIL tc_nw_pkt_pma_loopback");
                $display("  packet   : %0d / %0d", pkt_i, NPKT);
                vibe_tb_nw512_sop_lph_print(
                    "tc_nw_pkt_pma_loopback",
                    "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
                    beat, u_p.dll_tx_d, "u_p.dll_tx_d[511:352]");
                fail = 1;
              end else
                tx_n = tx_n + 1;
            end
            fab_tx_vld = 0;
            accepted = 1;
          end else
            @(posedge clk_fab);
        end
        beat_w = beat_w + 1;
      end
      fab_tx_vld = 0;
      if (!accepted && !fail) begin
        vibe_tb_nw512_fail_print_pkt(
            "tc_nw_pkt_pma_loopback", pkt_i, NPKT,
            "fab_tx handshake for this packet beat",
            beat, 1, {511'd0, fab_tx_ready}, "u_p.u_nw / u_p.u_dll.u_tx");
        $display("  note     : fab_tx_ready never rose (timeout %0d cycles)", BEAT_TO);
        fail = 1;
      end
    end
  endtask

  initial begin
    fail = 0; accepted = 0; dump_hold = 0;
    saw_afrv = 0; saw_pcs_rx = 0; saw_am = 0; saw_txnz = 0;
    saw_fab_rx = 0; saw_fec_fail = 0; saw_deskew = 0;
    last_rx = 512'd0;
    tx_n = 0; rx_n = 0;
    nw_w  = $bits(u_p.fab_tx_data);
    dll_w = $bits(u_p.dll_tx_d);
    rx_w  = $bits(u_p.fab_rx_data);

    for (i = 0; i < NPKT; i = i + 1) begin
      exp_sop[i] = vibe_tb_nw512_golden_tx_n(i);
      exp_b2[i]  = vibe_tb_nw512_golden_tx_b2_n(i);
      if (exp_sop[i] === 512'd0) begin
        fail_at("build 100 unique GOLDEN SOP beats",
                "data[511:0] nonzero",
                "GOLDEN all-zero",
                "vibe_tb_nw512_golden_tx_n");
      end
    end
    for (i = 0; i < NPKT; i = i + 1)
      for (j = i + 1; j < NPKT; j = j + 1)
        if (exp_sop[i] === exp_sop[j]) begin
          fail_at("build 100 unique GOLDEN SOP beats",
                  "each packet data[511:0] distinct",
                  "duplicate GOLDEN",
                  "vibe_tb_nw512_golden_tx_n");
        end
    golden_tx = exp_sop[0];
    if (fail) begin
      $finish;
    end

    bring_link();
    if (fail) begin
      $finish;
    end

    for (pkt = 0; pkt < NPKT; pkt = pkt + 1) begin
      if (fail)
        pkt = NPKT;
      else begin
        send_beat(exp_sop[pkt], 1, pkt);
        if (!fail)
          send_beat(exp_b2[pkt], 0, pkt);
        wait_i = 0;
        while (rx_n <= pkt && !fail && wait_i < WAIT_MAX) begin
          @(negedge clk_fab);
          peek_rx();
          wait_i = wait_i + 1;
        end
        if (!fail && rx_n <= pkt) begin
          $display("  detail   : vld=%0b last_rx=%h pcs_rx_v=%0b am_lock=%04b fec_fail=%0b deskew=%0b",
                   fab_rx_vld, last_rx, u_p.pcs_rx_v, u_p.am_locked, u_p.fec_fail,
                   u_p.deskew_ok);
          vibe_tb_nw512_fail_print_pkt(
              "tc_nw_pkt_pma_loopback", pkt, NPKT,
              "PMA loopback; recover this packet GOLDEN (timeout, not a pass)",
              exp_sop[pkt], rx_w, last_rx, "u_p.fab_rx_data");
          fail = 1;
        end
        if (!fail && ((pkt % 10) == 9))
          $display("  progress : tx_n=%0d rx_n=%0d (after packet %0d)",
                   tx_n, rx_n, pkt);
      end
    end

    if (fail) begin
      $finish;
    end
    if (saw_fec_fail) begin
      fail_at("supporting: fec_fail during 100-pkt GOLDEN loopback",
              "fec_fail=0",
              "fec_fail=1",
              "u_p.fec_fail");
      $finish;
    end
    if (rx_n !== NPKT) begin
      $display("  detail   : vld=%0b last_rx=%h pcs_rx_v=%0b am_lock=%04b fec_fail=%0b deskew=%0b afrv=%0b%0b%0b%0b",
               fab_rx_vld, last_rx, u_p.pcs_rx_v, u_p.am_locked, u_p.fec_fail,
               u_p.deskew_ok, u_p.afrv0, u_p.afrv1, u_p.afrv2, u_p.afrv3);
      $display("  peak     : tx_n=%0d rx_n=%0d saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d",
               tx_n, rx_n, saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew);
      vibe_tb_nw512_fail_print_pkt(
          "tc_nw_pkt_pma_loopback", rx_n, NPKT,
          "PMA loopback; recover each GOLDEN in order (timeout, not a pass)",
          (rx_n < NPKT) ? exp_sop[rx_n] : 512'd0, rx_w, last_rx,
          "u_p.fab_rx_data");
      $finish;
    end
    if (!saw_am) begin
      fail_at("supporting: am_locked during GOLDEN loopback",
              "am_locked nonzero",
              "am_locked stayed 0",
              "u_p.am_locked");
      $finish;
    end

    // +DUMP: hold a few cycles after the 100th match so the PNG window is visible.
    if ($test$plusargs("DUMP") || $test$plusargs("VCD")) begin
      for (dump_hold = 0; dump_hold < 32; dump_hold = dump_hold + 1)
        @(negedge clk_fab);
    end

    $display("PASS tc_nw_pkt_pma_loopback");
    $display("  scored : %0d / %0d packets; each TX GOLDEN and RX fab_rx_data[511:0] matched in order",
             rx_n, NPKT);
    $display("  peak     : tx_n=%0d rx_n=%0d saw_txnz=%0d saw_afrv=%0d saw_am=%0d saw_pcs_rx=%0d saw_fab_rx=%0d saw_fec_fail=%0d saw_deskew=%0d am_lock_end=%04b",
             tx_n, rx_n, saw_txnz, saw_afrv, saw_am, saw_pcs_rx, saw_fab_rx, saw_fec_fail, saw_deskew,
             u_p.am_locked);
    $finish;
  end
endmodule
