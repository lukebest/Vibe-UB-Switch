// AS-0.1 §4: per-port — pma_bnd, afifo_tx/rx×4, pcs_tx, pcs_rx, lmsm, dll, nw_adapt.
module vibe_port (
  input  logic         clk_fab,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         device_rst,
  input  logic         lmsm_go,
  input  logic         txclk,
  input  logic         rxclk,
  output logic [511:0] pcs_pma_txdata,
  input  logic [511:0] pma_pcs_rxdata,
  input  logic [511:0] fab_nw_data,
  input  logic         fab_nw_vld,
  output logic         fab_nw_ready,
  output logic [511:0] nw_fab_data,
  output logic         nw_fab_vld,
  input  logic         nw_fab_ready,
  input  logic [511:0] mgmt_nw_data,
  input  logic         mgmt_nw_vld,
  output logic         mgmt_nw_ready,
  output logic         status_up,
  output logic         disabled,
  output logic         retry_error,
  output logic         proto_err,
  output logic         fc_ovf,
  output logic         rx_ovf,
  output logic         afifo_ovf,
  output logic         cfg0_hit,
  output logic [639:0] cfg0_data
);
  `include "vibe_ub_params.vh"

  logic        txrst_n, rxrst_n;
  logic        link_up, link_ready, sdf_period;
  logic [4:0]  lmsm_st;
  logic        width_fail;
  logic [3:0]  am_locked;
  logic        lid_bad, deskew_ok, fec_fail, retrain_req;
  logic [511:0] nw_dll_data, dll_nw_data;
  logic [639:0] dll_pcs_data, pcs_dll_data;
  logic        nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready;
  logic        dll_pcs_vld, dll_pcs_ready, pcs_dll_vld, pcs_dll_ready;
  logic [159:0] pcs_afifo_lane0, pcs_afifo_lane1, pcs_afifo_lane2, pcs_afifo_lane3;
  logic        pcs_afifo_lane_vld;
  logic [159:0] afifo_pcs_lane0, afifo_pcs_lane1, afifo_pcs_lane2, afifo_pcs_lane3;
  logic        afrv0, afrv1, afrv2, afrv3;
  wire         afifo_pcs_lane_vld = afrv0 & afrv1 & afrv2 & afrv3;
  logic [127:0] afifo_pma_lane0, afifo_pma_lane1, afifo_pma_lane2, afifo_pma_lane3;
  logic        afifo_pma_lane_vld;
  logic [127:0] pma_afifo_lane0, pma_afifo_lane1, pma_afifo_lane2, pma_afifo_lane3;
  logic        pma_afifo_lane_vld;
  logic [3:0]  af_tx, af_rx;
  logic [2:0]  fec_mode;
  assign fec_mode = VIBE_FEC_T4;
  logic [3:0]  ovf_l;

  vibe_rst_sync u_txrst (.clk(txclk), .rst_n_in(rst_n && !port_rst), .rst_n_out(txrst_n));
  vibe_rst_sync u_rxrst (.clk(rxclk), .rst_n_in(rst_n && !port_rst), .rst_n_out(rxrst_n));

  vibe_lmsm u_lmsm (
    .clk(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .lmsm_go(lmsm_go),
    .am_locked(am_locked), .lid_bad(lid_bad), .lane0_fail(1'b0),
    .eq_negotiated(1'b0), .retrain_req(retrain_req),
    .link_up(link_up), .link_ready(link_ready), .sdf_period(sdf_period),
    .state(lmsm_st), .width_fail(width_fail)
  );

  vibe_nw_adapt u_nw (
    .clk(clk_fab), .rst_n(rst_n), .link_ready(link_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .mgmt_nw_data(mgmt_nw_data), .mgmt_nw_vld(mgmt_nw_vld), .mgmt_nw_ready(mgmt_nw_ready),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready)
  );

  vibe_dll u_dll (
    .clk(clk_fab), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .link_up(link_up), .fec_fail(fec_fail),
    .nw_dll_data(nw_dll_data), .nw_dll_vld(nw_dll_vld), .nw_dll_ready(nw_dll_ready),
    .dll_nw_data(dll_nw_data), .dll_nw_vld(dll_nw_vld), .dll_nw_ready(dll_nw_ready),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .status_up(status_up), .disabled(disabled), .retrain_req(retrain_req),
    .retry_error(retry_error), .proto_err(proto_err), .fc_ovf(fc_ovf),
    .rx_ovf(rx_ovf), .cfg0_hit(cfg0_hit), .cfg0_data(cfg0_data)
  );

  vibe_pcs_tx u_ptx (
    .clk(clk_fab), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .fec_mode(fec_mode), .afifo_afull(|af_tx),
    .dll_pcs_data(dll_pcs_data), .dll_pcs_vld(dll_pcs_vld), .dll_pcs_ready(dll_pcs_ready),
    .pcs_afifo_lane0(pcs_afifo_lane0), .pcs_afifo_lane1(pcs_afifo_lane1),
    .pcs_afifo_lane2(pcs_afifo_lane2), .pcs_afifo_lane3(pcs_afifo_lane3),
    .pcs_afifo_lane_vld(pcs_afifo_lane_vld)
  );

  vibe_pcs_rx u_prx (
    .clk(clk_fab), .rst_n(rst_n), .link_up(link_up), .fec_mode(fec_mode),
    .afifo_pcs_lane0(afifo_pcs_lane0), .afifo_pcs_lane1(afifo_pcs_lane1),
    .afifo_pcs_lane2(afifo_pcs_lane2), .afifo_pcs_lane3(afifo_pcs_lane3),
    .afifo_pcs_lane_vld(afifo_pcs_lane_vld),
    .pcs_dll_data(pcs_dll_data), .pcs_dll_vld(pcs_dll_vld), .pcs_dll_ready(pcs_dll_ready),
    .fec_fail(fec_fail), .am_locked(am_locked), .lid_bad(lid_bad),
    .deskew_ok(deskew_ok)
  );

  // TX AFIFO + 160→128 gearbox per lane (AS-0.1 §5 T6/T7)
  logic [159:0] tq0, tq1, tq2, tq3;
  logic         te0, te1, te2, te3;
  logic         tren0, tren1, tren2, tren3;
  logic         g0r, g1r, g2r, g3r;

  vibe_afifo #(.W(160), .DEPTH(VIBE_AFIFO_DEPTH)) u_at0 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(pcs_afifo_lane_vld), .wdata(pcs_afifo_lane0),
    .wfull(), .almost_full(af_tx[0]), .wocc(),
    .rclk(txclk), .rrst_n(txrst_n), .ren(tren0), .rdata(tq0), .rempty(te0)
  );
  vibe_afifo #(.W(160), .DEPTH(VIBE_AFIFO_DEPTH)) u_at1 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(pcs_afifo_lane_vld), .wdata(pcs_afifo_lane1),
    .wfull(), .almost_full(af_tx[1]), .wocc(),
    .rclk(txclk), .rrst_n(txrst_n), .ren(tren1), .rdata(tq1), .rempty(te1)
  );
  vibe_afifo #(.W(160), .DEPTH(VIBE_AFIFO_DEPTH)) u_at2 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(pcs_afifo_lane_vld), .wdata(pcs_afifo_lane2),
    .wfull(), .almost_full(af_tx[2]), .wocc(),
    .rclk(txclk), .rrst_n(txrst_n), .ren(tren2), .rdata(tq2), .rempty(te2)
  );
  vibe_afifo #(.W(160), .DEPTH(VIBE_AFIFO_DEPTH)) u_at3 (
    .wclk(clk_fab), .wrst_n(rst_n), .wen(pcs_afifo_lane_vld), .wdata(pcs_afifo_lane3),
    .wfull(), .almost_full(af_tx[3]), .wocc(),
    .rclk(txclk), .rrst_n(txrst_n), .ren(tren3), .rdata(tq3), .rempty(te3)
  );

  // All four 160→128 must fire as one 512. Using only lane0 out_vld
  // captured a new lane0 128 with stale lane1-3 (PMA has no per-lane valid).
  logic gv0, gv1, gv2, gv3;
  assign afifo_pma_lane_vld = gv0 & gv1 & gv2 & gv3;
  // A gear that is not yet holding must not eat the next 160 while a
  // sibling waits for afifo_pma_lane_vld. That would mix 512s the same as dropping.
  wire tx_hold_wait = (gv0 | gv1 | gv2 | gv3) && !afifo_pma_lane_vld;

  vibe_gear_160_128 u_g0 (
    .clk(txclk), .rst_n(txrst_n), .in_vld(!te0 && !tx_hold_wait), .in_ready(g0r), .in_data(tq0),
    .out_vld(gv0), .out_ready(afifo_pma_lane_vld), .out_data(afifo_pma_lane0)
  );
  assign tren0 = g0r && !te0 && !tx_hold_wait;
  vibe_gear_160_128 u_g1 (
    .clk(txclk), .rst_n(txrst_n), .in_vld(!te1 && !tx_hold_wait), .in_ready(g1r), .in_data(tq1),
    .out_vld(gv1), .out_ready(afifo_pma_lane_vld), .out_data(afifo_pma_lane1)
  );
  assign tren1 = g1r && !te1 && !tx_hold_wait;
  vibe_gear_160_128 u_g2 (
    .clk(txclk), .rst_n(txrst_n), .in_vld(!te2 && !tx_hold_wait), .in_ready(g2r), .in_data(tq2),
    .out_vld(gv2), .out_ready(afifo_pma_lane_vld), .out_data(afifo_pma_lane2)
  );
  assign tren2 = g2r && !te2 && !tx_hold_wait;
  vibe_gear_160_128 u_g3 (
    .clk(txclk), .rst_n(txrst_n), .in_vld(!te3 && !tx_hold_wait), .in_ready(g3r), .in_data(tq3),
    .out_vld(gv3), .out_ready(afifo_pma_lane_vld), .out_data(afifo_pma_lane3)
  );
  assign tren3 = g3r && !te3 && !tx_hold_wait;

  vibe_pma_bnd u_pma (
    .txclk(txclk), .rxclk(rxclk),
    .afifo_pma_lane0(afifo_pma_lane0), .afifo_pma_lane1(afifo_pma_lane1),
    .afifo_pma_lane2(afifo_pma_lane2), .afifo_pma_lane3(afifo_pma_lane3),
    .afifo_pma_lane_vld(afifo_pma_lane_vld),
    .pcs_pma_txdata(pcs_pma_txdata), .pma_pcs_rxdata(pma_pcs_rxdata),
    .pma_afifo_lane0(pma_afifo_lane0), .pma_afifo_lane1(pma_afifo_lane1),
    .pma_afifo_lane2(pma_afifo_lane2), .pma_afifo_lane3(pma_afifo_lane3),
    .pma_afifo_lane_vld(pma_afifo_lane_vld)
  );

  // RX AFIFO 128b write @rxclk, gearbox 128→160 @clk_fab (AS-0.1 §6/§7)
  logic [127:0] rq0, rq1, rq2, rq3;
  logic         re0, re1, re2, re3;
  logic         rren0, rren1, rren2, rren3;
  logic         wf0, wf1, wf2, wf3;

  // PMA has no valid: TX holds last pcs_pma_txdata when idle. Writing every rxclk
  // duplicates 128b beats and makes 128→160 unrestorable. Change-detect only.
  logic [127:0] rxh0, rxh1, rxh2, rxh3;
  logic [3:0]   rx_got;
  always @(posedge rxclk or negedge rxrst_n) begin
    if (!rxrst_n) begin
      // Prime hold=0 / got=1: do not write the power-on 0/X 128b. That extra
      // beat slips the 128→160 grouping by 32b and AMCTL never matches.
      rx_got <= 4'b1111;
      rxh0 <= 128'd0; rxh1 <= 128'd0; rxh2 <= 128'd0; rxh3 <= 128'd0;
    end else if (pma_afifo_lane_vld) begin
      rxh0 <= pma_afifo_lane0; rxh1 <= pma_afifo_lane1;
      rxh2 <= pma_afifo_lane2; rxh3 <= pma_afifo_lane3;
      rx_got <= 4'b1111;
    end
  end
  // Write all four lanes when any 128 changes. Per-lane compare desynchronized
  // the 128→160 gears when one lane repeated (structured packet) and the AND
  // of afifo_pcs_lane_vld dropped 160s; idle scramble almost never repeats a lane.
  wire want0 = pma_afifo_lane_vld && (pma_afifo_lane0 !== rxh0);
  wire want1 = pma_afifo_lane_vld && (pma_afifo_lane1 !== rxh1);
  wire want2 = pma_afifo_lane_vld && (pma_afifo_lane2 !== rxh2);
  wire want3 = pma_afifo_lane_vld && (pma_afifo_lane3 !== rxh3);
  wire any_chg = want0 | want1 | want2 | want3;
  wire wr0 = any_chg && !wf0;
  wire wr1 = any_chg && !wf1;
  wire wr2 = any_chg && !wf2;
  wire wr3 = any_chg && !wf3;

  vibe_afifo #(.W(128), .DEPTH(VIBE_AFIFO_DEPTH)) u_ar0 (
    .wclk(rxclk), .wrst_n(rxrst_n), .wen(wr0), .wdata(pma_afifo_lane0),
    .wfull(wf0), .almost_full(af_rx[0]), .wocc(),
    .rclk(clk_fab), .rrst_n(rst_n), .ren(rren0), .rdata(rq0), .rempty(re0)
  );
  vibe_afifo #(.W(128), .DEPTH(VIBE_AFIFO_DEPTH)) u_ar1 (
    .wclk(rxclk), .wrst_n(rxrst_n), .wen(wr1), .wdata(pma_afifo_lane1),
    .wfull(wf1), .almost_full(af_rx[1]), .wocc(),
    .rclk(clk_fab), .rrst_n(rst_n), .ren(rren1), .rdata(rq1), .rempty(re1)
  );
  vibe_afifo #(.W(128), .DEPTH(VIBE_AFIFO_DEPTH)) u_ar2 (
    .wclk(rxclk), .wrst_n(rxrst_n), .wen(wr2), .wdata(pma_afifo_lane2),
    .wfull(wf2), .almost_full(af_rx[2]), .wocc(),
    .rclk(clk_fab), .rrst_n(rst_n), .ren(rren2), .rdata(rq2), .rempty(re2)
  );
  vibe_afifo #(.W(128), .DEPTH(VIBE_AFIFO_DEPTH)) u_ar3 (
    .wclk(rxclk), .wrst_n(rxrst_n), .wen(wr3), .wdata(pma_afifo_lane3),
    .wfull(wf3), .almost_full(af_rx[3]), .wocc(),
    .rclk(clk_fab), .rrst_n(rst_n), .ren(rren3), .rdata(rq3), .rempty(re3)
  );

  // Overflow: drop beat, count, irq; no PMA ready (AS-0.1 §6)
  always @(posedge rxclk or negedge rxrst_n) begin
    if (!rxrst_n) ovf_l <= 4'd0;
    else begin
      ovf_l[0] <= any_chg && wf0;
      ovf_l[1] <= any_chg && wf1;
      ovf_l[2] <= any_chg && wf2;
      ovf_l[3] <= any_chg && wf3;
    end
  end

  logic ovf_s1, ovf_s2;
  always @(posedge clk_fab or negedge rst_n) begin
    if (!rst_n) begin
      ovf_s1 <= 1'b0;
      ovf_s2 <= 1'b0;
      afifo_ovf <= 1'b0;
    end else begin
      ovf_s1 <= |ovf_l;
      ovf_s2 <= ovf_s1;
      afifo_ovf <= ovf_s2;
    end
  end

  logic gr0, gr1, gr2, gr3;
  // Hold each 160 until all four gears have one. out_ready=1 dropped a
  // lane whose sibling was a cycle late; PCS AND of afifo_pcs_lane_vld then skipped
  // that beat and 128→160 grouping slipped (every later CW failed).
  // Also stall 128 ingress while any lane holds: a late gear must not
  // consume the next 128 before the current 160 quartet is taken.
  wire rx_hold_wait = (afrv0 | afrv1 | afrv2 | afrv3) && !afifo_pcs_lane_vld;
  vibe_gear_128_160 u_rg0 (
    .clk(clk_fab), .rst_n(rst_n), .in_vld(!re0 && !rx_hold_wait), .in_ready(gr0), .in_data(rq0),
    .out_vld(afrv0), .out_ready(afifo_pcs_lane_vld), .out_data(afifo_pcs_lane0)
  );
  assign rren0 = gr0 && !re0 && !rx_hold_wait;
  vibe_gear_128_160 u_rg1 (
    .clk(clk_fab), .rst_n(rst_n), .in_vld(!re1 && !rx_hold_wait), .in_ready(gr1), .in_data(rq1),
    .out_vld(afrv1), .out_ready(afifo_pcs_lane_vld), .out_data(afifo_pcs_lane1)
  );
  assign rren1 = gr1 && !re1 && !rx_hold_wait;
  vibe_gear_128_160 u_rg2 (
    .clk(clk_fab), .rst_n(rst_n), .in_vld(!re2 && !rx_hold_wait), .in_ready(gr2), .in_data(rq2),
    .out_vld(afrv2), .out_ready(afifo_pcs_lane_vld), .out_data(afifo_pcs_lane2)
  );
  assign rren2 = gr2 && !re2 && !rx_hold_wait;
  vibe_gear_128_160 u_rg3 (
    .clk(clk_fab), .rst_n(rst_n), .in_vld(!re3 && !rx_hold_wait), .in_ready(gr3), .in_data(rq3),
    .out_vld(afrv3), .out_ready(afifo_pcs_lane_vld), .out_data(afifo_pcs_lane3)
  );
  assign rren3 = gr3 && !re3 && !rx_hold_wait;
endmodule
