// CFG0 terminate in per-port DLL — never enters fabric (AS-0.1 §9 / §6).
`timescale 1ns/1ps

module tc_cfg0_term_not_fabric;
  `include "vibe_tb_defs.svh"

  logic         clk, rst_n, port_rst, link_up, fec_fail;
  logic [639:0] pcs_data, nw_data, cfg0_data;
  logic         pcs_vld, pcs_ready, nw_vld, nw_ready;
  logic         cfg0_hit, bcrc_fail, start_retry, rx_ovf, start_ack;
  logic         saw_cfg0, saw_nw, saw_nw_during_cfg0;
  integer       fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_dll_rx #(.RXBUF(32)) u_rx (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .fec_fail(fec_fail),
    .pcs_data(pcs_data), .pcs_vld(pcs_vld), .pcs_ready(pcs_ready),
    .nw_data(nw_data), .nw_vld(nw_vld), .nw_ready(nw_ready),
    .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data),
    .bcrc_fail(bcrc_fail), .start_retry(start_retry),
    .rx_ovf(rx_ovf), .start_ack(start_ack)
  );

  task automatic send_beat;
    input [3:0] cfg;
    begin
      @(negedge clk);
      pcs_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
          cfg, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
          16'd0, 8'd0, 3'd0, 8'd0));
      pcs_vld = 1'b1;
      @(posedge clk);
      @(negedge clk);
      pcs_vld = 1'b0;
    end
  endtask

  always @(posedge clk) begin
    if (cfg0_hit) saw_cfg0 <= 1'b1;
    if (nw_vld)   saw_nw   <= 1'b1;
    if (nw_vld && saw_cfg0 && !saw_nw) saw_nw_during_cfg0 <= 1'b1;
  end

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; fec_fail = 0;
    pcs_vld = 0; pcs_data = 640'd0; nw_ready = 1;
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
      $display("  expected : nw_vld never rises (does not enter fabric)");
      $display("  actual   : nw_vld pulsed");
      $display("  hier     : u_rx.nw_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    saw_nw = 1'b0;
    send_beat(4'd3);
    repeat (8) @(posedge clk);
    if (!saw_nw) begin
      $display("FAIL tc_cfg0_term_not_fabric");
      $display("  stimulus : CFG=3 beat (must reach NW/fabric)");
      $display("  expected : nw_vld pulse");
      $display("  actual   : no nw_vld");
      $display("  hier     : u_rx.have / nw_vld");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // rx_ovf: RXBUF=32, each beat +4, 9 beats without consume
    begin : ovf
      integer k;
      for (k = 0; k < 10; k = k + 1) send_beat(4'd3);
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
    pcs_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    pcs_vld = 1'b1;
    nw_ready = 1'b0;
    @(posedge clk);
    @(negedge clk);
    pcs_vld = 1'b0;
    repeat (1) @(posedge clk); // have registered
    @(negedge clk);
    link_up = 0;
    repeat (3) @(posedge clk);
    link_up = 1;
    nw_ready = 1;
    port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    if (!fail) $display("PASS tc_cfg0_term_not_fabric");
    $finish;
  end
endmodule
