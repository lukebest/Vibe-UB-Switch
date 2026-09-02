// DLL wrapper smoke (AS-0.1 §12). Children covered in units. RXBUF default 1024.
`timescale 1ns/1ps
module tc_dll;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, port_rst, device_rst, link_up, fec_fail;
  logic [511:0] nw_tx_data, nw_rx_data;
  logic [639:0] pcs_tx_data, pcs_rx_data, cfg0_data;
  logic nw_tx_vld, nw_tx_ready, nw_rx_vld, nw_rx_ready;
  logic pcs_tx_vld, pcs_tx_ready, pcs_rx_vld, pcs_rx_ready;
  logic status_up, disabled, retrain_req, retry_error, proto_err, fc_ovf, rx_ovf, cfg0_hit;
  integer fail, i;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll #(.RETRY_WAIT_CYC(4)) u_d (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .link_up(link_up), .fec_fail(fec_fail),
    .nw_tx_data(nw_tx_data), .nw_tx_vld(nw_tx_vld), .nw_tx_ready(nw_tx_ready),
    .nw_rx_data(nw_rx_data), .nw_rx_vld(nw_rx_vld), .nw_rx_ready(nw_rx_ready),
    .pcs_tx_data(pcs_tx_data), .pcs_tx_vld(pcs_tx_vld), .pcs_tx_ready(pcs_tx_ready),
    .pcs_rx_data(pcs_rx_data), .pcs_rx_vld(pcs_rx_vld), .pcs_rx_ready(pcs_rx_ready),
    .status_up(status_up), .disabled(disabled), .retrain_req(retrain_req),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; device_rst = 0; link_up = 0; fec_fail = 0;
    nw_tx_vld = 0; nw_rx_ready = 1; pcs_tx_ready = 1; pcs_rx_vld = 0;
    nw_tx_data = 0; pcs_rx_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (!disabled) begin
      $display("FAIL tc_dll");
      $display("  stimulus : LinkUp=0");
      $display("  expected : disabled");
      fail = 1;
    end
    link_up = 1;
    repeat (8) @(posedge clk);
    nw_tx_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    for (i = 0; i < 8; i = i + 1) begin
      @(negedge clk);
      nw_tx_vld = nw_tx_ready;
      @(posedge clk);
    end
    nw_tx_vld = 0;
    pcs_rx_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd0, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    @(negedge clk);
    pcs_rx_vld = 1;
    @(posedge clk);
    @(negedge clk);
    pcs_rx_vld = 0;
    fec_fail = 1;
    @(posedge clk);
    fec_fail = 0;
    port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    if (!fail) $display("PASS tc_dll");
    $finish;
  end
endmodule
