// TP-PHY-009/010/018 + Overlay B: GOLDEN 512b NW→DLL, then PMA pcs_pma_txdata pack.
// DUT vibe_port. Hierarchical LMSM/credit bring-up (no rtl/ edit).
`timescale 1ns/1ps
module tc_nw_pkt_to_pma_tx;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw512.svh"

  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata;
  logic [511:0] fab_nw_data, nw_fab_data, mgmt_nw_data;
  logic [639:0] cfg0_data;
  logic fab_nw_vld, fab_nw_ready, nw_fab_vld, nw_fab_ready;
  logic mgmt_nw_vld, mgmt_nw_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, accepted, saw_dll, saw_pma, pack_ok, gold_ok, gold_n, pack_n;
  integer lane_n, lane_mis, last_v, last_gv, nw_w, dll_w;
  logic [511:0] last_pack, last_gold;
  logic [511:0] golden_tx;
  logic [511:0] gold_tx;

  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  initial rxclk = 0;
  always #2 rxclk = ~rxclk;

  initial begin
    if ($test$plusargs("DUMP") || $test$plusargs("VCD")) begin
      begin : dump_open
        reg [8*256-1:0] dump_fn;
        dump_fn = "nw_pkt_to_pma_tx.vcd";
        if ($value$plusargs("DUMPFILE=%s", dump_fn)) ;
        $dumpfile(dump_fn);
        $dumpvars(0, clk_fab, txclk, rst_n, lmsm_go, status_up,
                  fab_nw_vld, fab_nw_ready, pcs_pma_txdata, gold_tx);
      end
    end
  end

  vibe_port u_p (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .lmsm_go(lmsm_go), .txclk(txclk), .rxclk(rxclk),
    .pcs_pma_txdata(pcs_pma_txdata), .pma_pcs_rxdata(pma_pcs_rxdata),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld), .mgmt_nw_ready(mgmt_nw_ready),
    .status_up(status_up), .disabled(disabled),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .afifo_ovf(afifo_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );

  // TB-only golden PCS (same DLL stream as DUT) + 4×160→128 + PMA pack.
  logic [159:0] gl0, gl1, gl2, gl3;
  logic         glv, g_dll_r;
  logic [127:0] gp0, gp1, gp2, gp3;
  logic         gpv, g0r, g1r, g2r, g3r;
  logic         gte0, gte1, gte2, gte3;
  logic [159:0] gq0, gq1, gq2, gq3;

  vibe_pcs_tx u_gold_pcs (
    .clk(clk_fab), .rst_n(rst_n),
    .link_up(u_p.link_up), .sdf_period(u_p.sdf_period),
    .fec_mode(VIBE_FEC_T4), .afifo_afull(1'b0),
    .dll_pcs_data(u_p.dll_pcs_data), .dll_pcs_vld(u_p.dll_pcs_vld), .dll_pcs_ready(g_dll_r),
    .pcs_afifo_lane0(gl0), .pcs_afifo_lane1(gl1),
    .pcs_afifo_lane2(gl2), .pcs_afifo_lane3(gl3), .pcs_afifo_lane_vld(glv)
  );

  vibe_afifo #(.W(160), .DEPTH(16)) u_ga0 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(glv), .wdata(gl0),
    .wfull(), .almost_full(), .wocc(),
    .rclk(txclk), .rrst_n(u_p.txrst_n), .ren(g0r && !gte0), .rdata(gq0), .rempty(gte0)
  );
  vibe_afifo #(.W(160), .DEPTH(16)) u_ga1 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(glv), .wdata(gl1),
    .wfull(), .almost_full(), .wocc(),
    .rclk(txclk), .rrst_n(u_p.txrst_n), .ren(g1r && !gte1), .rdata(gq1), .rempty(gte1)
  );
  vibe_afifo #(.W(160), .DEPTH(16)) u_ga2 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(glv), .wdata(gl2),
    .wfull(), .almost_full(), .wocc(),
    .rclk(txclk), .rrst_n(u_p.txrst_n), .ren(g2r && !gte2), .rdata(gq2), .rempty(gte2)
  );
  vibe_afifo #(.W(160), .DEPTH(16)) u_ga3 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(glv), .wdata(gl3),
    .wfull(), .almost_full(), .wocc(),
    .rclk(txclk), .rrst_n(u_p.txrst_n), .ren(g3r && !gte3), .rdata(gq3), .rempty(gte3)
  );

  vibe_gear_160_128 u_gg0 (
    .clk(txclk), .rst_n(u_p.txrst_n), .in_vld(!gte0), .in_ready(g0r), .in_data(gq0),
    .out_vld(gpv), .out_ready(1'b1), .out_data(gp0)
  );
  vibe_gear_160_128 u_gg1 (
    .clk(txclk), .rst_n(u_p.txrst_n), .in_vld(!gte1), .in_ready(g1r), .in_data(gq1),
    .out_vld(), .out_ready(1'b1), .out_data(gp1)
  );
  vibe_gear_160_128 u_gg2 (
    .clk(txclk), .rst_n(u_p.txrst_n), .in_vld(!gte2), .in_ready(g2r), .in_data(gq2),
    .out_vld(), .out_ready(1'b1), .out_data(gp2)
  );
  vibe_gear_160_128 u_gg3 (
    .clk(txclk), .rst_n(u_p.txrst_n), .in_vld(!gte3), .in_ready(g3r), .in_data(gq3),
    .out_vld(), .out_ready(1'b1), .out_data(gp3)
  );

  always @(posedge txclk)
    gold_tx <= {gp3, gp2, gp1, gp0};

  task automatic fail_at;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail = 1;
      $display("FAIL tc_nw_pkt_to_pma_tx");
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
      pma_pcs_rxdata = 0; fab_nw_vld = 0; nw_fab_ready = 1; mgmt_nw_vld = 0;
      fab_nw_data = 0; mgmt_nw_data = 0;
      repeat (8) @(posedge clk_fab);
      rst_n = 1;
      repeat (8) @(posedge clk_fab);
      // Peer substitutes (no RTL edit): AM lock + no LID bad so LMSM can walk.
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
        $display("  detail   : ready=%0b up=%0b lmsm=%0d dllst=%0d",
                 u_p.link_ready, status_up, u_p.lmsm_st, u_p.u_dll.sm_st);
        fail_at("lmsm_go + force am_locked=1111 lid_bad=0, wait 64",
                "link_ready=1 and DLL status_up (ACTIVE + ST_NRM)",
                "see detail line",
                "u_p.u_lmsm / u_p.u_dll.u_sm");
      end
      // Peer credit: cells power-on 0 → credit_low blocks nw_ready (not a non-goal).
      force u_p.u_dll.u_crd.cells = 16'd64;
      @(posedge clk_fab);
      release u_p.u_dll.u_crd.cells;
      // Hold ACTIVE without back-driving PCS RX am_locked net.
      force u_p.u_lmsm.st = 5'd9;
      release u_p.u_lmsm.am_locked;
      release u_p.u_lmsm.lid_bad;
      @(posedge clk_fab);
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_dll = 0; saw_pma = 0;
    pack_ok = 1; gold_ok = 1; gold_n = 0; pack_n = 0;
    lane_n = 0; lane_mis = 0; last_v = 0; last_gv = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    nw_w  = $bits(u_p.fab_nw_data);
    dll_w = $bits(u_p.nw_dll_data);
    bring_link();
    if (fail) begin
      $finish;
    end

    // Inject unique 512-bit GOLDEN (not a 640 slice); wait handshake.
    fab_nw_data = golden_tx;
    accepted = 0;
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_nw_vld = 1;
      if (fab_nw_ready) begin
        @(posedge clk_fab);
        accepted = 1;
        if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, u_p.nw_dll_data)) begin
          vibe_tb_nw512_fail_print(
              "tc_nw_pkt_to_pma_tx",
              "TX NW→DLL accepted beat GOLDEN_TX",
              golden_tx, dll_w, u_p.nw_dll_data,
              "u_p.nw_dll_data / u_p.u_nw.nw_dll_data");
          $finish;
        end
        if (vibe_tb_nw512_sop_lph_fail(golden_tx, u_p.nw_dll_data)) begin
          vibe_tb_nw512_sop_lph_print(
              "tc_nw_pkt_to_pma_tx",
              "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
              golden_tx, u_p.nw_dll_data, "u_p.nw_dll_data[511:352]");
          $finish;
        end
        fab_nw_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_nw_vld = 0;
    if (!accepted) begin
      $display("  detail   : ready=%0b link_r=%0b status_up=%0b crd_low=%0b can=%0b",
               fab_nw_ready, u_p.link_ready, status_up,
               u_p.u_dll.u_crd.credit_low, u_p.u_dll.can_send);
      fail_at("fab_nw_vld GOLDEN_TX 1-beat after LinkReady+cells=64",
              "fab_nw_ready handshake (packet accepted)",
              "see detail line",
              "u_p.u_nw.fab_nw_ready / u_p.u_dll.u_tx.nw_dll_ready");
      $finish;
    end

    saw_dll = 1;

    // Second beat completes the 80 B / 4-flit packet (DLL emits 640b to PCS).
    fab_nw_data = vibe_tb_nw512_golden_tx_b2();
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      fab_nw_vld = 1;
      if (fab_nw_ready) begin
        @(posedge clk_fab);
        fab_nw_vld = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    fab_nw_vld = 0;

    // PMA pcs_pma_txdata is registered: compare to the previous txclk's p_tx / golden.
    for (i = 0; i < 4000; i = i + 1) begin
      @(posedge clk_fab);
      if (glv && u_p.pcs_afifo_lane_vld) begin
        lane_n = lane_n + 1;
        if (gl0 !== u_p.pcs_afifo_lane0 || gl1 !== u_p.pcs_afifo_lane1 ||
            gl2 !== u_p.pcs_afifo_lane2 || gl3 !== u_p.pcs_afifo_lane3)
          lane_mis = lane_mis + 1;
      end
      @(posedge txclk);
      if (last_v) begin
        saw_pma = 1;
        pack_n = pack_n + 1;
        if (pcs_pma_txdata !== last_pack)
          pack_ok = 0;
      end
      if (last_gv) begin
        gold_n = gold_n + 1;
        if (pcs_pma_txdata !== last_gold)
          gold_ok = 0;
      end
      last_v    = u_p.afifo_pma_lane_vld;
      last_pack = {u_p.afifo_pma_lane3, u_p.afifo_pma_lane2, u_p.afifo_pma_lane1, u_p.afifo_pma_lane0};
      last_gv   = gpv;
      last_gold = {gp3, gp2, gp1, gp0};
    end

    if (!saw_pma || pcs_pma_txdata === 512'd0) begin
      $display("  detail   : afifo_pma_lane_vld=%0b pcs_pma_txdata=%h", u_p.afifo_pma_lane_vld, pcs_pma_txdata);
      fail_at("packet accepted; wait 4000 txclk",
              "afifo_pma_lane_vld and pcs_pma_txdata[511:0] nonzero (PMA product boundary)",
              "see detail line",
              "u_p.u_pma.pcs_pma_txdata / u_p.afifo_pma_lane_vld");
      $finish;
    end
    if (!pack_ok) begin
      $display("  detail   : pcs_pma_txdata=%h afifo_pma_lane0=%h", pcs_pma_txdata, u_p.afifo_pma_lane0);
      fail_at("afifo_pma_lane_vld beats after accept",
              "pcs_pma_txdata[127:0]=lane0 .. [511:384]=lane3 (AS-0.1 / TP-PHY-018)",
              "see detail line",
              "u_p.u_pma / u_p.afifo_pma_lane0..3");
      $finish;
    end
    if (lane_n == 0 || lane_mis != 0) begin
      $display("  detail   : lane_n=%0d lane_mis=%0d", lane_n, lane_mis);
      fail_at("TB golden vibe_pcs_tx (T=4, same dll_pcs_data stream, AMCTL in both)",
              "DUT lane0..3 match golden lanes whenever both lane_vld",
              "see detail line",
              "u_gold_pcs.pcs_afifo_lane* vs u_p.pcs_afifo_lane*");
      $finish;
    end
    if (gold_n == 0 || !gold_ok) begin
      $display("  detail   : gold_n=%0d gold_ok=%0b (lane golden already matched)",
               gold_n, gold_ok);
      fail_at("TB golden AFIFO+gear+pack vs DUT pcs_pma_txdata",
              "PMA beats match golden 4x160->4x128 pack",
              "see detail line",
              "u_gg0..3 vs u_p.u_pma.pcs_pma_txdata");
      $finish;
    end

    $display("PASS tc_nw_pkt_to_pma_tx");
    $display("  scored : dll_tx===GOLDEN_TX; %0d PMA pack; %0d PCS-lane golden; %0d gear golden",
             pack_n, lane_n, gold_n);
    $finish;
  end
endmodule
