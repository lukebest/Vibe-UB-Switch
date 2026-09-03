// Top: reset/CNA plus a real packet on PMA rxdata. Score irq_logic (G1) at top.
`timescale 1ns/1ps
module tc_top_smoke;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw_pma.svh"
  logic         clk_fab, rst_n;
  logic         txclk_0, txclk_1, txclk_2, txclk_3;
  logic         rxclk_0, rxclk_1, rxclk_2, rxclk_3;
  logic [511:0] txdata_0, txdata_1, txdata_2, txdata_3;
  logic [511:0] rxdata_0, rxdata_1, rxdata_2, rxdata_3;
  logic         cfg_wr_vld, cfg_wr_ready, irq_logic;
  logic [3:0]   cfg_wr_cmd;
  logic [15:0]  cfg_wr_idx;
  logic [31:0]  cfg_wr_data;
  integer       fail, i, accepted, saw_peer_tx;

  logic prst, pdrst, plgo, ptxc, prxc;
  logic [511:0] ptx, prx;
  logic [511:0] p_fab_tx, p_fab_rx, p_mgmt;
  logic [639:0] p_cfg0;
  logic p_ftv, p_ftr, p_frv, p_frr, p_mv, p_mr, p_up, p_dis;
  logic p_rty, p_pe, p_fc, p_rxo, p_afo, p_c0;

  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial begin
    txclk_0 = 0; txclk_1 = 0; txclk_2 = 0; txclk_3 = 0;
  end
  always #2 txclk_0 = ~txclk_0;
  always #2 txclk_1 = ~txclk_1;
  always #2 txclk_2 = ~txclk_2;
  always #2 txclk_3 = ~txclk_3;
  assign rxclk_0 = txclk_0;
  assign rxclk_1 = txclk_1;
  assign rxclk_2 = txclk_2;
  assign rxclk_3 = txclk_3;
  assign ptxc = txclk_0;
  assign prxc = txclk_0;
  assign rxdata_0 = ptx;
  assign rxdata_1 = 512'd0;
  assign rxdata_2 = 512'd0;
  assign rxdata_3 = 512'd0;
  assign prx = 512'd0;

  vibe_ub_switch dut (
    .clk_fab(clk_fab), .rst_n(rst_n),
    .txclk_0(txclk_0), .txclk_1(txclk_1), .txclk_2(txclk_2), .txclk_3(txclk_3),
    .rxclk_0(rxclk_0), .rxclk_1(rxclk_1), .rxclk_2(rxclk_2), .rxclk_3(rxclk_3),
    .txdata_0(txdata_0), .txdata_1(txdata_1), .txdata_2(txdata_2), .txdata_3(txdata_3),
    .rxdata_0(rxdata_0), .rxdata_1(rxdata_1), .rxdata_2(rxdata_2), .rxdata_3(rxdata_3),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .irq_logic(irq_logic)
  );

  vibe_port u_peer (
    .clk_fab(clk_fab), .rst_n(rst_n), .port_rst(prst), .device_rst(pdrst),
    .lmsm_go(plgo), .txclk(ptxc), .rxclk(prxc),
    .txdata(ptx), .rxdata(prx),
    .fab_tx_data(p_fab_tx), .fab_tx_vld(p_ftv), .fab_tx_ready(p_ftr),
    .fab_rx_data(p_fab_rx), .fab_rx_vld(p_frv), .fab_rx_ready(p_frr),
    .mgmt_tx_data(p_mgmt), .mgmt_tx_vld(p_mv), .mgmt_tx_ready(p_mr),
    .status_up(p_up), .disabled(p_dis),
    .retry_error(p_rty), .proto_err(p_pe), .fc_ovf(p_fc),
    .rx_ovf(p_rxo), .afifo_ovf(p_afo), .cfg0_hit(p_c0), .cfg0_data(p_cfg0)
  );

  task automatic fail_at;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail = 1;
      $display("FAIL tc_top_smoke");
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe top");
    end
  endtask

  task automatic cfgw;
    input [3:0] cmd;
    input [15:0] idx;
    input [31:0] data;
    begin
      @(negedge clk_fab);
      cfg_wr_cmd = cmd; cfg_wr_idx = idx; cfg_wr_data = data; cfg_wr_vld = 1;
      @(posedge clk_fab);
      @(negedge clk_fab);
      cfg_wr_vld = 0;
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_peer_tx = 0;
    rst_n = 0;
    cfg_wr_vld = 0; cfg_wr_cmd = 0; cfg_wr_idx = 0; cfg_wr_data = 0;
    prst = 0; pdrst = 0; plgo = 0; p_ftv = 0; p_frr = 1; p_mv = 0;
    p_fab_tx = 0; p_mgmt = 0;
    repeat (8) @(posedge clk_fab);
    rst_n = 1;
    repeat (8) @(posedge clk_fab);

    if ($bits(dut.cfg_wr_cmd) !== 4) begin
      fail_at("reset", "cfg_wr_cmd[3:0] (4 bits)", "width not 4", "dut.cfg_wr_cmd");
      $finish;
    end
    if (!cfg_wr_ready) begin
      fail_at("reset", "cfg_wr_ready=1", "0", "dut.cfg_wr_ready");
      $finish;
    end
    if (irq_logic !== 1'b0) begin
      fail_at("reset, idle PMA", "irq_logic=0", "1", "dut.irq_logic");
      $finish;
    end

    cfgw(4'd0, 16'd0, 32'h0000_0001);
    if (dut.u_mgmt.cna !== 16'd1) begin
      fail_at("cfg_wr CNA=1", "u_mgmt.cna=1", "CNA not written", "dut.u_mgmt.cna");
      $finish;
    end

    // Bring peer TX and DUT port 0 to ACTIVE (peer AM / credit substitutes).
    force u_peer.u_lmsm.am_locked = 4'b1111;
    force u_peer.u_lmsm.lid_bad   = 1'b0;
    force dut.g_port[0].u_port.u_lmsm.am_locked = 4'b1111;
    force dut.g_port[0].u_port.u_lmsm.lid_bad   = 1'b0;
    force dut.g_port[1].u_port.u_lmsm.am_locked = 4'b1111;
    force dut.g_port[1].u_port.u_lmsm.lid_bad   = 1'b0;
    @(negedge clk_fab);
    plgo = 1;
    cfgw(4'd5, 16'd0, 32'd0);
    cfgw(4'd5, 16'd1, 32'd0);
    @(posedge clk_fab);
    plgo = 0;
    i = 0;
    while (!(u_peer.link_ready && p_up) && i < 64) begin
      @(posedge clk_fab);
      i = i + 1;
    end
    if (!u_peer.link_ready || !p_up) begin
      fail_at("peer lmsm_go + am_locked",
              "peer link_ready && status_up",
              "peer did not reach ACTIVE",
              "u_peer.u_lmsm");
      $finish;
    end
    force u_peer.u_dll.u_crd.cells = 16'd64;
    force dut.g_port[0].u_port.u_dll.u_crd.cells = 16'd64;
    @(posedge clk_fab);
    release u_peer.u_dll.u_crd.cells;
    release dut.g_port[0].u_port.u_dll.u_crd.cells;
    force u_peer.u_lmsm.st = 5'd9;
    force dut.g_port[0].u_port.u_lmsm.st = 5'd9;
    force dut.g_port[1].u_port.u_lmsm.st = 5'd9;
    release u_peer.u_lmsm.am_locked;
    release u_peer.u_lmsm.lid_bad;
    release dut.g_port[0].u_port.u_lmsm.am_locked;
    release dut.g_port[0].u_port.u_lmsm.lid_bad;
    release dut.g_port[1].u_port.u_lmsm.am_locked;
    release dut.g_port[1].u_port.u_lmsm.lid_bad;
    @(posedge clk_fab);

    if (!dut.g_port[0].u_port.link_up) begin
      fail_at("DUT port0 lmsm_go + force ACTIVE",
              "link_up=1 so DLL RX can deliver to fabric",
              "link_up=0 — packet cannot be accepted",
              "dut.g_port[0].u_port.link_up");
      $finish;
    end

    // RT=10 packet through peer PMA TX onto dut.rxdata_0 → G1 irq_logic.
    p_fab_tx = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b10, 4'd0, 16'hA11A, 16'hB22B, vibe_tb_plen_nflit(1),
        16'hC33C, 8'h5A, 3'd0, 8'd0));
    for (i = 0; i < 32; i = i + 1) begin
      @(negedge clk_fab);
      p_ftv = 1;
      if (p_ftr) begin
        @(posedge clk_fab);
        accepted = 1;
        p_ftv = 0;
        i = 32;
      end else
        @(posedge clk_fab);
    end
    p_ftv = 0;
    if (!accepted) begin
      fail_at("peer fab_tx RT=10 after LinkReady",
              "peer fab_tx_ready handshake",
              "encoder did not accept packet",
              "u_peer.u_nw / u_peer.u_dll.u_tx");
      $finish;
    end

    for (i = 0; i < 20000; i = i + 1) begin
      @(posedge clk_fab);
      if (ptx !== 512'd0) saw_peer_tx = 1;
      if (irq_logic) i = 20000;
    end

    if (!saw_peer_tx) begin
      fail_at("peer accepted RT=10; watch peer txdata → dut.rxdata_0",
              "peer txdata nonzero (PMA encoded packet)",
              "peer txdata stayed 0",
              "u_peer.u_pma.txdata");
      $finish;
    end
    if (!irq_logic) begin
      fail_at("rxdata_0 = peer txdata (RT=10 LPH); wait 20000 clk_fab",
              "irq_logic=1 (G1 at top pin)",
              "irq_logic stayed 0",
              "dut.irq_logic / dut.u_fab.drop_g1 / dut.u_mgmt");
      $finish;
    end
    $display("PASS tc_top_smoke");
    $finish;
  end
endmodule
