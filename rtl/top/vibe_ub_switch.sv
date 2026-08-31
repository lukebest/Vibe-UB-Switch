// FS-0.2.3 + AS-0.1 §4/§17: top — 4-port PMA + clk_fab + rst_n + cfg_wr_* + irq_logic.
// G1 named signals: rt_shortest_unimpl (32-bit saturating), sticky irq_logic. No extra IRQ pins.
module vibe_ub_switch #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic         clk_fab,
  input  logic         rst_n,
  input  logic         txclk_0,
  input  logic         txclk_1,
  input  logic         txclk_2,
  input  logic         txclk_3,
  input  logic         rxclk_0,
  input  logic         rxclk_1,
  input  logic         rxclk_2,
  input  logic         rxclk_3,
  output logic [511:0] txdata_0,
  output logic [511:0] txdata_1,
  output logic [511:0] txdata_2,
  output logic [511:0] txdata_3,
  input  logic [511:0] rxdata_0,
  input  logic [511:0] rxdata_1,
  input  logic [511:0] rxdata_2,
  input  logic [511:0] rxdata_3,
  input  logic         cfg_wr_vld,
  output logic         cfg_wr_ready,
  input  logic [2:0]   cfg_wr_cmd,
  input  logic [15:0]  cfg_wr_idx,
  input  logic [31:0]  cfg_wr_data,
  output logic         irq_logic
);
  logic [3:0]   status_up, disabled;
  logic [3:0]   retry_error, proto_err, fc_ovf, rx_ovf, afifo_ovf;
  logic [3:0]   port_rst, lmsm_go;
  logic         device_rst;
  logic [3:0]   default_bm;
  logic         rt_wr_en;
  logic [15:0]  rt_wr_idx;
  logic [31:0]  rt_wr_data;
  logic [15:0]  cna;
  logic         cna_written;
  logic [639:0] fab_tx [0:3];
  logic [3:0]   fab_tx_v, fab_tx_r;
  logic [639:0] fab_rx [0:3];
  logic [3:0]   fab_rx_v, fab_rx_r;
  logic [639:0] mgmt_tx [0:3];
  logic [3:0]   mgmt_tx_v, mgmt_tx_r;
  logic [3:0]   len_err, deadlock_drop, cfg6_hit, cfg6_cons;
  logic         drop_g1;
  logic [31:0]  rt_shortest_unimpl, drop_down;
  logic [639:0] cfg6_d [0:3];
  logic [639:0] reply_d [0:3];
  logic [3:0]   reply_v, reply_r;
  logic [511:0] txd [0:3];
  logic [511:0] rxd [0:3];
  logic [3:0]   txclk, rxclk;

  assign txclk = {txclk_3, txclk_2, txclk_1, txclk_0};
  assign rxclk = {rxclk_3, rxclk_2, rxclk_1, rxclk_0};
  assign rxd[0] = rxdata_0;
  assign rxd[1] = rxdata_1;
  assign rxd[2] = rxdata_2;
  assign rxd[3] = rxdata_3;
  assign txdata_0 = txd[0];
  assign txdata_1 = txd[1];
  assign txdata_2 = txd[2];
  assign txdata_3 = txd[3];

  genvar gi;
  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_port
      vibe_port u_port (
        .clk_fab(clk_fab), .rst_n(rst_n),
        .port_rst(port_rst[gi]), .device_rst(device_rst),
        .lmsm_go(lmsm_go[gi]),
        .txclk(txclk[gi]), .rxclk(rxclk[gi]),
        .txdata(txd[gi]), .rxdata(rxd[gi]),
        .fab_tx_data(fab_tx[gi]), .fab_tx_vld(fab_tx_v[gi]), .fab_tx_ready(fab_tx_r[gi]),
        .fab_rx_data(fab_rx[gi]), .fab_rx_vld(fab_rx_v[gi]), .fab_rx_ready(fab_rx_r[gi]),
        .mgmt_tx_data(mgmt_tx[gi]), .mgmt_tx_vld(mgmt_tx_v[gi]), .mgmt_tx_ready(mgmt_tx_r[gi]),
        .status_up(status_up[gi]), .disabled(disabled[gi]),
        .retry_error(retry_error[gi]), .proto_err(proto_err[gi]),
        .fc_ovf(fc_ovf[gi]), .rx_ovf(rx_ovf[gi]), .afifo_ovf(afifo_ovf[gi]),
        .cfg0_hit(), .cfg0_data()
      );
    end
  endgenerate

  vibe_fabric #(.ROUTE_TABLE_DEPTH(ROUTE_TABLE_DEPTH)) u_fab (
    .clk(clk_fab), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .ing_data(fab_rx), .ing_vld(fab_rx_v), .ing_ready(fab_rx_r),
    .egr_data(fab_tx), .egr_vld(fab_tx_v), .egr_ready(fab_tx_r),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down),
    .deadlock_drop(deadlock_drop), .irq_rt(),
    .cna(cna), .cna_written(cna_written),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_d)
  );

  vibe_mgmt #(.ROUTE_TABLE_DEPTH(ROUTE_TABLE_DEPTH)) u_mgmt (
    .clk(clk_fab), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .cfg6_hit(cfg6_hit), .cfg6_data(cfg6_d),
    .cfg6_consume(cfg6_cons),
    .reply_data(reply_d), .reply_vld(reply_v), .reply_ready(reply_r),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .len_err(len_err),
    .deadlock_drop(deadlock_drop), .drop_g1(drop_g1),
    .afifo_ovf(afifo_ovf), .irq_logic(irq_logic)
  );

  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_byp
      vibe_mgmt_byp u_byp (
        .clk(clk_fab), .rst_n(rst_n),
        .in_data(reply_d[gi]), .in_vld(reply_v[gi]), .in_ready(reply_r[gi]),
        .out_data(mgmt_tx[gi]), .out_vld(mgmt_tx_v[gi]), .out_ready(mgmt_tx_r[gi])
      );
    end
  endgenerate
endmodule
