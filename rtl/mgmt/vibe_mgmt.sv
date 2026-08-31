// AS-0.1 §4/§10: mgmt — cfg_space, cna_ep, irq_agg, rst_ctl.
module vibe_mgmt #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         cfg_wr_vld,
  output logic         cfg_wr_ready,
  input  logic [2:0]   cfg_wr_cmd,
  input  logic [15:0]  cfg_wr_idx,
  input  logic [31:0]  cfg_wr_data,
  output logic [15:0]  cna,
  output logic         cna_written,
  output logic [3:0]   default_bm,
  output logic         rt_wr_en,
  output logic [15:0]  rt_wr_idx,
  output logic [31:0]  rt_wr_data,
  output logic [3:0]   port_rst,
  output logic         device_rst,
  output logic [3:0]   lmsm_go,
  input  logic [3:0]   cfg6_hit,
  input  logic [639:0] cfg6_data [0:3],
  output logic [3:0]   cfg6_consume,
  output logic [639:0] reply_data [0:3],
  output logic [3:0]   reply_vld,
  input  logic [3:0]   reply_ready,
  input  logic [3:0]   rx_ovf,
  input  logic [3:0]   fc_ovf,
  input  logic [3:0]   proto_err,
  input  logic [3:0]   retry_error,
  input  logic [3:0]   len_err,
  input  logic [3:0]   deadlock_drop,
  input  logic         drop_g1,
  input  logic [3:0]   afifo_ovf,
  output logic         irq_logic
);
  logic [3:0] port_rst_pulse;
  logic       device_rst_pulse;
  logic       irq_clr;
  logic       icrc_fail;

  vibe_cfg_space #(.ROUTE_TABLE_DEPTH(ROUTE_TABLE_DEPTH)) u_cfg (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst_pulse(port_rst_pulse), .device_rst_pulse(device_rst_pulse),
    .lmsm_go_pulse(lmsm_go), .irq_clr(irq_clr),
    .guid0(), .class_code(), .port_basic(), .port_cap()
  );

  vibe_rst_ctl u_rst (
    .clk(clk), .rst_n(rst_n),
    .device_rst_pulse(device_rst_pulse), .port_rst_pulse(port_rst_pulse),
    .device_rst(device_rst), .port_rst(port_rst)
  );

  vibe_cna_ep u_cna (
    .clk(clk), .rst_n(rst_n), .cna(cna), .cna_written(cna_written),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_data),
    .consume(cfg6_consume),
    .reply_data(reply_data), .reply_vld(reply_vld), .reply_ready(reply_ready),
    .icrc_fail(icrc_fail)
  );

  vibe_irq_agg u_irq (
    .clk(clk), .rst_n(rst_n), .irq_clr(irq_clr | device_rst),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .icrc_fail(icrc_fail),
    .len_err(len_err), .deadlock_drop(deadlock_drop),
    .drop_g1(drop_g1), .afifo_ovf(afifo_ovf),
    .irq_logic(irq_logic)
  );
endmodule
