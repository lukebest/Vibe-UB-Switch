// TP-PHY-009/010/018: legal NW/LPH packet → PMA txdata[511:0] content checker.
// DUT vibe_port. Hierarchical LMSM/credit bring-up (no rtl/ edit).
`timescale 1ns/1ps
module tc_nw_pkt_to_pma_tx;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw_pma.svh"

  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [639:0] fab_tx_data, fab_rx_data, mgmt_tx_data, cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail, i, accepted, saw_dll, saw_pma, pack_ok, gold_ok, gold_n, pack_n;
  logic [639:0] pkt;
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
                  fab_tx_vld, fab_tx_ready, txdata, gold_tx);
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
    .dll_data(u_p.pcs_tx_d), .dll_vld(u_p.pcs_tx_v), .dll_ready(g_dll_r),
    .lane0(gl0), .lane1(gl1), .lane2(gl2), .lane3(gl3), .lane_vld(glv)
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
      rxdata = 0; fab_tx_vld = 0; fab_rx_ready = 1; mgmt_tx_vld = 0;
      fab_tx_data = 0; mgmt_tx_data = 0;
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
        fail_at("lmsm_go + force am_locked=1111 lid_bad=0, wait 64",
                "link_ready=1 and DLL status_up (ACTIVE + ST_NRM)",
                $sformatf("ready=%0b up=%0b st=%0d dllst=%0d",
                          u_p.link_ready, status_up, u_p.lmsm_st, u_p.u_dll.sm_st),
                "u_p.u_lmsm / u_p.u_dll.u_sm");
      end
      // Peer credit: cells power-on 0 → credit_low blocks nw_ready (not a non-goal).
      force u_p.u_dll.u_crd.cells = 16'd64;
      @(posedge clk_fab);
      release u_p.u_dll.u_crd.cells;
      @(posedge clk_fab);
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_dll = 0; saw_pma = 0;
    pack_ok = 1; gold_ok = 1; gold_n = 0; pack_n = 0;
    pkt = vibe_tb_nw_pma_pkt();
    bring_link();
    if (fail) begin
      $finish;
    end

    // Inject one legal RT=00 beat; wait handshake.
    fab_tx_data = pkt;
    accepted = 0;
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
      fail_at("fab_tx_vld legal RT=00 1-beat after LinkReady+cells=64",
              "fab_tx_ready handshake (packet accepted)",
              $sformatf("ready=%0b link_r=%0b status_up=%0b crd_low=%0b can=%0b",
                        fab_tx_ready, u_p.link_ready, status_up,
                        u_p.u_dll.u_crd.credit_low, u_p.u_dll.can_send),
              "u_p.u_nw.fab_tx_ready / u_p.u_dll.u_tx.nw_ready");
      $finish;
    end

    // Score DLL wrap: injected LPH (and payload[639:32]) appears on pcs_tx.
    for (i = 0; i < 64; i = i + 1) begin
      @(negedge clk_fab);
      if (u_p.pcs_tx_v && vibe_tb_nw_pma_lph_ok(u_p.pcs_tx_d))
        saw_dll = 1;
    end
    if (!saw_dll) begin
      fail_at("packet accepted; watch u_p.pcs_tx_v/d",
              "DLL emits beat with CFG=3 RT=00 SCNA=A11A DCNA=B22B (BCRC may replace [31:0])",
              $sformatf("never matched pcs_tx_d[639:480]=%h vld=%0b",
                        u_p.pcs_tx_d[639:480], u_p.pcs_tx_v),
              "u_p.u_dll.u_tx.pcs_data");
      $finish;
    end

    // PMA: txdata must become valid and match DUT lane pack + TB golden chain.
    for (i = 0; i < 4000; i = i + 1) begin
      @(posedge txclk);
      if (u_p.p_txv) begin
        saw_pma = 1;
        pack_n = pack_n + 1;
        if (txdata !== {u_p.p_tx3, u_p.p_tx2, u_p.p_tx1, u_p.p_tx0})
          pack_ok = 0;
      end
      if (gpv) begin
        gold_n = gold_n + 1;
        if (txdata !== {gp3, gp2, gp1, gp0})
          gold_ok = 0;
      end
    end

    if (!saw_pma || txdata === 512'd0) begin
      fail_at("packet accepted; wait 4000 txclk",
              "tx_lane_vld and txdata[511:0] nonzero (PMA product boundary)",
              $sformatf("p_txv=%0b txdata=%h", u_p.p_txv, txdata),
              "u_p.u_pma.txdata / u_p.p_txv");
      $finish;
    end
    if (!pack_ok) begin
      fail_at("p_txv beats after accept",
              "txdata[127:0]=lane0 … [511:384]=lane3 (AS-0.1 / TP-PHY-018)",
              $sformatf("txdata=%h p_tx0=%h", txdata, u_p.p_tx0),
              "u_p.u_pma / u_p.p_tx0..3");
      $finish;
    end
    if (gold_n == 0 || !gold_ok) begin
      fail_at("TB golden PCS(T=4)+AFIFO+gear+pack vs DUT txdata (AMCTL in both)",
              "captured PMA beats match golden 4x160→4x128 pack",
              $sformatf("gold_n=%0d gold_ok=%0b txdata=%h gold=%h",
                        gold_n, gold_ok, txdata, {gp3, gp2, gp1, gp0}),
              "u_gold_pcs / u_gg0..3 vs u_p.u_pma.txdata");
      $finish;
    end

    $display("PASS tc_nw_pkt_to_pma_tx");
    $display("  scored : DLL LPH on pcs_tx_d; %0d PMA pack beats; %0d golden matches",
             pack_n, gold_n);
    $finish;
  end
endmodule
