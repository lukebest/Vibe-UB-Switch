// One vibe_port smoke (AS-0.1 §4). Not the 4-port top. May be heavy in Verilator.
`timescale 1ns/1ps
module tc_port_smoke;
  `include "vibe_tb_defs.svh"
  logic clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk;
  logic [511:0] txdata, rxdata;
  logic [639:0] fab_tx_data, fab_rx_data, mgmt_tx_data, cfg0_data;
  logic fab_tx_vld, fab_tx_ready, fab_rx_vld, fab_rx_ready;
  logic mgmt_tx_vld, mgmt_tx_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  integer fail;
  initial clk_fab = 0;
  always #1 clk_fab = ~clk_fab;
  initial txclk = 0;
  always #2 txclk = ~txclk;
  initial rxclk = 0;
  always #2 rxclk = ~rxclk;
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
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; device_rst = 0; lmsm_go = 0;
    rxdata = 0; fab_tx_vld = 0; fab_rx_ready = 1; mgmt_tx_vld = 0;
    fab_tx_data = 0; mgmt_tx_data = 0;
    repeat (8) @(posedge clk_fab);
    rst_n = 1;
    repeat (4) @(posedge clk_fab);
    lmsm_go = 1;
    @(posedge clk_fab);
    lmsm_go = 0;
    repeat (8) @(posedge clk_fab);
    fab_tx_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    fab_tx_vld = 1;
    repeat (4) @(posedge clk_fab);
    fab_tx_vld = 0;
    mgmt_tx_vld = 1;
    @(posedge clk_fab);
    mgmt_tx_vld = 0;
    port_rst = 1;
    @(posedge clk_fab);
    port_rst = 0;
    if (!fail) $display("PASS tc_port_smoke");
    $finish;
  end
endmodule
