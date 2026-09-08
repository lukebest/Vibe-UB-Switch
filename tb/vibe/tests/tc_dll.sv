// DLL wrapper smoke (AS-0.1 §12). Children covered in units. RXBUF default 1024.
`timescale 1ns/1ps
module tc_dll;
  `include "vibe_tb_defs.svh"
  logic clk, rst_n, port_rst, device_rst, link_up, fec_fail;
  logic [511:0] nw_dll_data, dll_nw_data;
  logic [639:0] dll_pcs_data, pcs_dll_data, cfg0_data;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready;
  logic dll_pcs_vld, dll_pcs_ready, pcs_dll_vld, pcs_dll_ready;
  logic status_up, disabled, retrain_req, retry_error, proto_err, fc_ovf, rx_ovf, cfg0_hit;
  integer fail, i;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll #(.RETRY_WAIT_CYC(4)) u_d (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .link_up(link_up), .fec_fail(fec_fail),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .status_up(status_up), .disabled(disabled), .retrain_req(retrain_req),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; device_rst = 0; link_up = 0; fec_fail = 0;
    nw_dll_vld = 0; dll_nw_ready = 1; dll_pcs_ready = 1; pcs_dll_vld = 0;
    nw_dll_data = 0; pcs_dll_data = 0;
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
    nw_dll_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    for (i = 0; i < 8; i = i + 1) begin
      @(negedge clk);
      nw_dll_vld = nw_dll_ready;
      @(posedge clk);
    end
    nw_dll_vld = 0;
    pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd0, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    @(negedge clk);
    pcs_dll_vld = 1;
    @(posedge clk);
    @(negedge clk);
    pcs_dll_vld = 0;
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
