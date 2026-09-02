// --cc: LinkUp==0 while have → pad 0 + ERROR_FLAG (AS-0.1 §6/§12).
// have lives exactly one cycle (set, then have&&!nw_vld consumes it).
// Drop link_up on the negedge after the capturing posedge — no extra clock.
`timescale 1ns/1ps
module tc_dll_rx_errflag;
  `include "vibe_tb_defs.svh"
  logic         clk, rst_n, port_rst, link_up, fec_fail;
  logic [639:0] pcs_data, cfg0_data;
  logic [511:0] nw_data;
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
    pcs_vld = 0; pcs_data = 640'd0; nw_ready = 0;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    @(negedge clk);
    pcs_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    pcs_vld = 1;
    nw_ready = 0;
    @(posedge clk);   // have <= 1 (NBA)
    @(negedge clk);
    pcs_vld = 0;
    link_up = 0;      // next posedge: !link_up && have
    @(posedge clk);
    @(negedge clk);
    $display("INFO tc_dll_rx_errflag nw_vld=%0b have=%0b nw=%h",
             nw_vld, u_rx.have, nw_data);
    if (!nw_vld) begin
      $display("FAIL tc_dll_rx_errflag");
      $display("  stimulus : drop link_up on negedge after have");
      $display("  expected : nw_vld + pad0/ERROR_FLAG (dll_rx :61)");
      $display("  actual   : nw_vld=0 have=%0b", u_rx.have);
      fail = 1;
    end
    link_up = 1;
    nw_ready = 1;
    if (!fail) $display("PASS tc_dll_rx_errflag");
    $finish;
  end
endmodule
