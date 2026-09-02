// TP-PHY-015: FEC decode >T fail → DLL start_retry (Go-Back-N). TP-RTY-001 maps to tc_retry_req_gbn.
`timescale 1ns/1ps
module tc_fec_fail_gbn;
  `include "vibe_tb_defs.svh"
  logic         clk, rst_n, port_rst, link_up, fec_fail;
  logic [639:0] pcs_data, nw_data, cfg0_data;
  logic         pcs_vld, pcs_ready, nw_vld, nw_ready;
  logic         cfg0_hit, bcrc_fail, start_retry, rx_ovf, start_ack;
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

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; fec_fail = 0;
    pcs_vld = 0; pcs_data = 640'd0; nw_ready = 1;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    if (start_retry !== 1'b0) begin
      $display("FAIL tc_fec_fail_gbn");
      $display("  stimulus : reset fec_fail=0");
      $display("  expected : start_retry=0");
      $display("  actual   : start_retry=%0b", start_retry);
      $display("  hier     : u_rx.start_retry");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    @(negedge clk);
    fec_fail = 1;
    #0;
    if (start_retry !== 1'b1) begin
      $display("FAIL tc_fec_fail_gbn");
      $display("  stimulus : pulse fec_fail=1 (RS decode fail)");
      $display("  expected : start_retry=1 (Go-Back-N; AS-0.1 §6/§12)");
      $display("  actual   : start_retry=%0b bcrc_fail=%0b", start_retry, bcrc_fail);
      $display("  hier     : u_rx.start_retry = fec_fail || bcrc_fail");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    @(negedge clk);
    fec_fail = 0;
    #0;
    if (start_retry !== 1'b0) begin
      $display("FAIL tc_fec_fail_gbn");
      $display("  stimulus : fec_fail deassert");
      $display("  expected : start_retry=0 (combo follows fec_fail)");
      $display("  actual   : start_retry=%0b", start_retry);
      $display("  hier     : u_rx.start_retry");
      fail = 1;
    end
    if (!fail) $display("PASS tc_fec_fail_gbn");
    $finish;
  end
endmodule
