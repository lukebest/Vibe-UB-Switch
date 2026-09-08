// CFG0 terminate in per-port DLL — never enters fabric (AS-0.1 §9 / §6).
`timescale 1ns/1ps

module tc_cfg0_term_not_fabric;
  `include "vibe_tb_defs.svh"

  logic         clk, rst_n, port_rst, link_up, fec_fail;
  logic [639:0] pcs_dll_data, cfg0_data;
  logic [511:0] dll_nw_data;
  logic         pcs_dll_vld, pcs_dll_ready, dll_nw_vld, dll_nw_ready;
  logic         cfg0_hit, bcrc_fail, start_retry, rx_ovf, start_ack;
  logic         saw_cfg0, saw_nw, saw_nw_during_cfg0;
  integer       fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_dll_rx #(.RXBUF(32)) u_rx (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .fec_fail(fec_fail),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data),
    .bcrc_fail(bcrc_fail), .start_retry(start_retry),
    .rx_ovf(rx_ovf), .start_ack(start_ack)
  );

  task automatic send_beat;
    input [3:0] cfg;
    begin
      @(negedge clk);
      pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
          cfg, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
          16'd0, 8'd0, 3'd0, 8'd0));
      pcs_dll_vld = 1'b1;
      @(posedge clk);
      @(negedge clk);
      pcs_dll_vld = 1'b0;
    end
  endtask

  always @(posedge clk) begin
    if (cfg0_hit) saw_cfg0 <= 1'b1;
    if (dll_nw_vld)   saw_nw   <= 1'b1;
    if (dll_nw_vld && saw_cfg0 && !saw_nw) saw_nw_during_cfg0 <= 1'b1;
  end

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; fec_fail = 0;
    pcs_dll_vld = 0; pcs_dll_data = 640'd0; dll_nw_ready = 1;
    saw_cfg0 = 0; saw_nw = 0; saw_nw_during_cfg0 = 0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    send_beat(4'd0);
    repeat (6) @(posedge clk);
    if (!saw_cfg0) begin
      $display("FAIL tc_cfg0_term_not_fabric");
      $display("  stimulus : CFG=0 beat on dll_rx pcs_* (link_up=1)");
      $display("  expected : cfg0_hit pulse (terminate in DLL)");
      $display("  actual   : no cfg0_hit");
      $display("  hier     : u_rx.is_cfg0 / u_rx.cfg0_hit");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (saw_nw) begin
      $display("FAIL tc_cfg0_term_not_fabric");
      $display("  stimulus : CFG0 beat");
      $display("  expected : dll_nw_vld never rises (does not enter fabric)");
      $display("  actual   : dll_nw_vld pulsed");
      $display("  hier     : u_rx.dll_nw_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    saw_nw = 1'b0;
    send_beat(4'd3);
    repeat (8) @(posedge clk);
    if (!saw_nw) begin
      $display("FAIL tc_cfg0_term_not_fabric");
      $display("  stimulus : CFG=3 beat (must reach NW/fabric)");
      $display("  expected : dll_nw_vld pulse");
      $display("  actual   : no dll_nw_vld");
      $display("  hier     : u_rx.have / dll_nw_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // 5-flit declared length on one 640b beat: left=100, emit 64, leftover
    // (dll_rx :118 else). port_rst after so by_n/pkt_act do not stick.
    begin : leftover
      integer w;
      w = 0;
      @(negedge clk);
      while (!pcs_dll_ready && w < 40) begin @(posedge clk); w = w + 1; end
      pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
          4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(5),
          16'd0, 8'd0, 3'd0, 8'd0));
      pcs_dll_vld = 1'b1;
      @(posedge clk);
      @(negedge clk);
      pcs_dll_vld = 1'b0;
      repeat (4) @(posedge clk);
      port_rst = 1;
      @(posedge clk);
      port_rst = 0;
    end

    // need_hdr :128 — dll_nw_ready=0 before the first emit so dll_nw_vld sticks,
    // then a second SOP unpacks with can_emit=0.
    begin : needhdr
      integer w;
      dll_nw_ready = 1'b0;
      w = 0;
      @(negedge clk);
      while (!pcs_dll_ready && w < 40) begin @(posedge clk); w = w + 1; end
      pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
          4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
          16'd0, 8'd0, 3'd0, 8'd0));
      pcs_dll_vld = 1'b1;
      @(posedge clk);
      @(negedge clk);
      pcs_dll_vld = 1'b0;
      repeat (6) @(posedge clk);
      w = 0;
      @(negedge clk);
      while (!pcs_dll_ready && w < 40) begin @(posedge clk); w = w + 1; end
      pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
          4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
          16'd0, 8'd0, 3'd0, 8'd0));
      pcs_dll_vld = 1'b1;
      @(posedge clk);
      @(negedge clk);
      pcs_dll_vld = 1'b0;
      repeat (6) @(posedge clk);
      dll_nw_ready = 1'b1;
      port_rst = 1;
      @(posedge clk);
      port_rst = 0;
    end

    // rx_ovf :100 — RXBUF=32, +4 wptr/accept, rptr never pops. Drain
    // each 1-flit so pcs_dll_ready returns. wptr is not cleared by port_rst.
    begin : ovf
      integer k, w;
      dll_nw_ready = 1'b1;
      for (k = 0; k < 12; k = k + 1) begin
        w = 0;
        @(negedge clk);
        while (!pcs_dll_ready && w < 40) begin @(posedge clk); w = w + 1; end
        pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
            4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
            16'd0, 8'd0, 3'd0, 8'd0));
        pcs_dll_vld = 1'b1;
        @(posedge clk);
        @(negedge clk);
        pcs_dll_vld = 1'b0;
        repeat (6) @(posedge clk);
      end
      if (!rx_ovf) begin
        $display("FAIL tc_cfg0_term_not_fabric");
        $display("  stimulus : 12 ready-gated CFG3 beats, RXBUF=32");
        $display("  expected : rx_ovf (wptr-rptr >= 32)");
        $display("  actual   : rx_ovf=0 wptr0=%0d", u_rx.wptr[0]);
        $display("  hier     : u_rx.rx_ovf");
        $display("  reproduce: make -C tb/vibe units");
        fail = 1;
      end
    end
    repeat (4) @(posedge clk);
    // fec_fail → start_retry
    fec_fail = 1;
    @(posedge clk);
    if (!start_retry) begin
      $display("FAIL tc_cfg0_term_not_fabric");
      $display("  stimulus : fec_fail");
      $display("  expected : start_retry=1");
      $display("  actual   : 0");
      fail = 1;
    end
    fec_fail = 0;
    // !link_up while have: pad ERROR_FLAG. have is set on the send posedge
    // and consumed on the next posedge if link_up stays 1 — drop link_up
    // on the intervening negedge (no extra cycle).
    @(negedge clk);
    pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    pcs_dll_vld = 1'b1;
    dll_nw_ready = 1'b0;
    @(posedge clk);
    @(negedge clk);
    pcs_dll_vld = 1'b0;
    // have is live this cycle only — drop link_up now (no extra posedge).
    link_up = 0;
    repeat (3) @(posedge clk);
    link_up = 1;
    dll_nw_ready = 1;
    port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    if (!fail) $display("PASS tc_cfg0_term_not_fabric");
    $finish;
  end
endmodule
