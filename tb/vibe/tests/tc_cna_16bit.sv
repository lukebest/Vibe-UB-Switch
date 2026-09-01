// TP-CFG-007: mgmt CNA is 16-bit, not 24-bit.
`timescale 1ns/1ps
module tc_cna_16bit;
  `include "vibe_ub_params.vh"
  logic        clk, rst_n, device_rst;
  logic        cfg_wr_vld, cfg_wr_ready, cna_written, rt_wr_en, irq_clr;
  logic        device_rst_pulse;
  logic [2:0]  cfg_wr_cmd;
  logic [15:0] cfg_wr_idx, cna, rt_wr_idx;
  logic [31:0] cfg_wr_data, rt_wr_data;
  logic [3:0]  default_bm, port_rst_pulse, lmsm_go_pulse;
  logic [31:0] guid0, class_code, port_basic, port_cap;
  integer      fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_cfg_space u_cfg (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst_pulse(port_rst_pulse), .device_rst_pulse(device_rst_pulse),
    .lmsm_go_pulse(lmsm_go_pulse), .irq_clr(irq_clr),
    .guid0(guid0), .class_code(class_code),
    .port_basic(port_basic), .port_cap(port_cap)
  );

  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; cfg_wr_vld = 0;
    cfg_wr_cmd = 0; cfg_wr_idx = 0; cfg_wr_data = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    @(negedge clk);
    cfg_wr_cmd = 3'd0;
    cfg_wr_data = 32'h00AB_CDEF; // 24-bit-looking payload
    cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cfg_wr_vld = 0;
    repeat (2) @(posedge clk);
    if (cna !== 16'hCDEF) begin
      $display("FAIL tc_cna_16bit");
      $display("  stimulus : cfg_wr_cmd=0 data=00ABCDEF");
      $display("  expected : cna=16'hCDEF (low 16 only; not 24-bit)");
      $display("  actual   : cna=%h written=%0b", cna, cna_written);
      $display("  hier     : u_cfg.cna");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if ($bits(cna) !== 16) begin
      $display("FAIL tc_cna_16bit");
      $display("  stimulus : $bits(cna)");
      $display("  expected : 16");
      $display("  actual   : %0d", $bits(cna));
      fail = 1;
    end
    if (!fail) $display("PASS tc_cna_16bit");
    $finish;
  end
endmodule
