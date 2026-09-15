// Leaf-unit UVM top: AS-locked blocks with dedicated interfaces.
`timescale 1ns/1ps

module vibe_unit_tb_top;
  import uvm_pkg::*;
  import vibe_uvm_pkg::*;
  `include "uvm_macros.svh"

  vibe_clk_rst_if clk_if();
  wire clk = clk_if.clk;

  vibe_credit_if       crd   (clk);
  vibe_lmsm_if         lmsm  (clk);
  vibe_cfg_space_if    cfgs  (clk);
  vibe_irq_if          irq   (clk);
  vibe_vlrr_if         vlrr  (clk);
  vibe_bcrc_if         bcrc  (clk);
  vibe_afifo_if        afifo();
  vibe_psel_if         psel  (clk);
  vibe_dll_sm_if       dsm   (clk);
  vibe_retry_buf_if    rbuf  (clk);
  vibe_retry_req_if    rreq  (clk);
  vibe_retry_ack_if    rack  (clk);
  vibe_voq_if          voq   (clk);
  vibe_dll_rx_if       drx   (clk);
  vibe_dll_wrap_if     dllw  (clk);
  vibe_rst_sync_if     rsyn  (clk);
  vibe_mgmt_byp_if     mbyp  (clk);
  vibe_fecn_if         fecn();
  vibe_nw_adapt_if     nwa   (clk);
  vibe_pma_bnd_if      pma();
  vibe_gear_tx_if      gtx   (clk);
  vibe_gear_rx_if      grx   (clk);
  vibe_cw2beat_if      cw2   (clk);
  vibe_pcs_fec_if      fec   (clk);
  vibe_pcs_scramble_if scr   (clk);
  vibe_pcs_amctl_if    amc   (clk);
  vibe_icrc_if         icrc  (clk);
  vibe_xbar_if         xbar  (clk);
  vibe_cna_if          cna   (clk);

  integer gi, xi;

  initial begin
    clk_if.rst_n = 1'b0;
    afifo.wclk = 0;
    afifo.rclk = 0;
    pma.txclk = 0;
    pma.rxclk = 0;
  end
  always #1 afifo.wclk = ~afifo.wclk;
  always #2 afifo.rclk = ~afifo.rclk;
  // ~922 MHz product PMA (T≈1085 ps). Slice tests ignore the exact period.
  always #542ps pma.txclk = ~pma.txclk;
  always #542ps pma.rxclk = ~pma.rxclk;

  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(crd.rst_n), .port_rst(crd.port_rst), .link_up(crd.link_up),
    .grain_n(crd.grain_n),
    .consume_vld(crd.consume_vld), .consume_flits(crd.consume_flits), .is_cfg0(crd.is_cfg0),
    .credit_ret(crd.credit_ret), .credit_ret_n(crd.credit_ret_n),
    .pending(crd.pending), .credit_low(crd.credit_low), .force_crd_ack(crd.force_crd_ack),
    .bp_nw(crd.bp_nw), .proto_err(crd.proto_err), .fc_ovf(crd.fc_ovf)
  );
  assign crd.cells = u_crd.cells;

  vibe_lmsm u_lmsm (
    .clk(clk), .rst_n(lmsm.rst_n), .port_rst(lmsm.port_rst), .lmsm_go(lmsm.lmsm_go),
    .am_locked(lmsm.am_locked), .lid_bad(lmsm.lid_bad), .lane0_fail(lmsm.lane0_fail),
    .eq_negotiated(lmsm.eq_negotiated), .retrain_req(lmsm.retrain_req),
    .link_up(lmsm.link_up), .link_ready(lmsm.link_ready), .sdf_period(lmsm.sdf_period),
    .state(lmsm.state), .width_fail(lmsm.width_fail)
  );

  vibe_cfg_space u_cfg (
    .clk(clk), .rst_n(cfgs.rst_n), .device_rst(cfgs.device_rst),
    .cfg_wr_vld(cfgs.cfg_wr_vld), .cfg_wr_ready(cfgs.cfg_wr_ready),
    .cfg_wr_cmd(cfgs.cfg_wr_cmd), .cfg_wr_idx(cfgs.cfg_wr_idx), .cfg_wr_data(cfgs.cfg_wr_data),
    .cna(cfgs.cna), .cna_written(cfgs.cna_written), .default_bm(cfgs.default_bm),
    .rt_wr_en(cfgs.rt_wr_en), .rt_wr_idx(cfgs.rt_wr_idx), .rt_wr_data(cfgs.rt_wr_data),
    .port_rst_pulse(cfgs.port_rst_pulse), .port_rst_hold(cfgs.port_rst_hold),
    .port_rst_rw1c(cfgs.port_rst_rw1c), .device_rst_pulse(cfgs.device_rst_pulse),
    .lmsm_go_pulse(cfgs.lmsm_go_pulse), .irq_clr(cfgs.irq_clr),
    .guid0(cfgs.guid0), .class_code(cfgs.class_code),
    .port_basic(cfgs.port_basic), .port_cap(cfgs.port_cap)
  );

  vibe_irq_agg u_irq (
    .clk(clk), .rst_n(irq.rst_n), .irq_clr(irq.irq_clr),
    .rx_ovf(irq.rx_ovf), .fc_ovf(irq.fc_ovf), .proto_err(irq.proto_err),
    .retry_error(irq.retry_error), .icrc_fail(irq.icrc_fail),
    .len_err(irq.len_err), .deadlock_drop(irq.deadlock_drop),
    .drop_g1(irq.drop_g1), .afifo_ovf(irq.afifo_ovf),
    .irq_logic(irq.irq_logic)
  );

  vibe_vl_rr u_vlrr (
    .clk(clk), .rst_n(vlrr.rst_n), .nonempty(vlrr.nonempty),
    .grant(vlrr.grant), .vl_sel(vlrr.vl_sel), .valid(vlrr.valid)
  );

  vibe_bcrc u_bcrc (
    .clk(clk), .rst_n(bcrc.rst_n), .start(bcrc.start), .in_vld(bcrc.in_vld),
    .in_flit(bcrc.in_flit), .last(bcrc.last), .error_flag(bcrc.error_flag),
    .crc_word(bcrc.crc_word), .done(bcrc.done)
  );

  vibe_afifo #(.W(160), .DEPTH(16)) u_afifo (
    .wclk(afifo.wclk), .wrst_n(afifo.wrst_n), .wen(afifo.wen), .wdata(afifo.wdata),
    .wfull(afifo.wfull), .almost_full(afifo.almost_full), .wocc(afifo.wocc),
    .rclk(afifo.rclk), .rrst_n(afifo.rrst_n), .ren(afifo.ren), .rdata(afifo.rdata),
    .rempty(afifo.rempty)
  );

  vibe_route_lu #(.DEPTH(256)) u_rt (
    .clk(clk), .rst_n(psel.rst_n), .device_rst(psel.device_rst),
    .wr_en(psel.wr_en), .wr_idx(psel.wr_idx), .wr_data(psel.wr_data),
    .dest(psel.dest), .rt(psel.rt), .lu_vld(psel.sel_vld),
    .bitmap(psel.bitmap), .drop_g1(psel.drop_g1)
  );
  vibe_port_sel u_ps (
    .clk(clk), .rst_n(psel.rst_n),
    .bitmap(psel.bitmap), .status_up(psel.status_up), .default_bm(psel.default_bm),
    .rt(psel.rt), .drop_g1(psel.drop_g1), .sel_vld(psel.sel_vld),
    .cfg(psel.cfg), .src(psel.src), .dest(psel.dest), .vl(psel.vl),
    .egr(psel.egr), .drop(psel.drop), .drop_down_cnt(psel.drop_down)
  );

  vibe_dll_sm u_dsm (
    .clk(clk), .rst_n(dsm.rst_n), .port_rst(dsm.port_rst), .link_up(dsm.link_up),
    .param_ok(dsm.param_ok), .credit_ok(dsm.credit_ok), .dll_error(dsm.dll_error),
    .state(dsm.state), .status_up(dsm.status_up), .disabled(dsm.disabled)
  );

  vibe_dll_retry_buf u_rbuf (
    .clk(clk), .rst_n(rbuf.rst_n), .port_rst(rbuf.port_rst), .link_up(rbuf.link_up),
    .wr_en(rbuf.wr_en), .is_null(rbuf.is_null), .is_retry(rbuf.is_retry), .wr_flit(rbuf.wr_flit),
    .send_size(rbuf.send_size), .ack_rel(rbuf.ack_rel), .rel_size(rbuf.rel_size),
    .rd_ptr_i(rbuf.rd_ptr_i),
    .rd_flit(rbuf.rd_flit), .wr_ptr(rbuf.wr_ptr), .tail_ptr(rbuf.tail_ptr), .rcv_ptr(rbuf.rcv_ptr),
    .num_free(rbuf.num_free), .proto_err(rbuf.proto_err), .can_send(rbuf.can_send)
  );

  vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(4)) u_rreq (
    .clk(clk), .rst_n(rreq.rst_n), .port_rst(rreq.port_rst), .device_rst(rreq.device_rst),
    .start_retry(rreq.start_retry), .phy_retrain(rreq.phy_retrain),
    .wait_done_ack(rreq.wait_done_ack),
    .state(rreq.state), .drop_data(rreq.drop_data), .retrain_req(rreq.retrain_req),
    .retry_error(rreq.retry_error), .send_idle(rreq.send_idle), .send_req(rreq.send_req),
    .send_cnt(rreq.send_cnt)
  );

  vibe_dll_retry_ack_sm u_rack (
    .clk(clk), .rst_n(rack.rst_n), .port_rst(rack.port_rst),
    .start_ack(rack.start_ack), .wr_ptr(rack.wr_ptr), .rcv_ptr(rack.rcv_ptr),
    .state(rack.state), .send_idle(rack.send_idle), .send_ack(rack.send_ack),
    .replay(rack.replay), .rd_ptr(rack.rd_ptr)
  );

  vibe_voq_egr #(.DEPTH(32)) u_voq (
    .clk(clk), .rst_n(voq.rst_n),
    .wr_vl(voq.wr_vl), .wr_en(voq.wr_en), .wr_data(voq.wr_data),
    .wr_sop(voq.wr_sop), .wr_eop(voq.wr_eop), .wr_ready(voq.wr_ready),
    .rd_vl(voq.rd_vl), .rd_en(voq.rd_en), .rd_data(voq.rd_data),
    .rd_sop(voq.rd_sop), .rd_eop(voq.rd_eop),
    .nonempty(voq.nonempty), .occ_vl0(voq.occ_vl0),
    .deadlock_drop(voq.deadlock_drop), .deadlock_cnt(voq.deadlock_cnt)
  );

  vibe_dll_rx #(.RXBUF(32)) u_drx (
    .clk(clk), .rst_n(drx.rst_n), .port_rst(drx.port_rst), .link_up(drx.link_up),
    .fec_fail(drx.fec_fail),
    .pcs_dll_data(drx.pcs_dll_data), .pcs_dll_vld(drx.pcs_dll_vld),
    .pcs_dll_ready(drx.pcs_dll_ready),
    .dll_nw_data(drx.dll_nw_data), .dll_nw_vld(drx.dll_nw_vld),
    .dll_nw_ready(drx.dll_nw_ready),
    .cfg0_hit(drx.cfg0_hit), .cfg0_data(drx.cfg0_data),
    .bcrc_fail(drx.bcrc_fail), .start_retry(drx.start_retry),
    .rx_ovf(drx.rx_ovf), .start_ack(drx.start_ack)
  );
  assign drx.have = u_drx.have;

  vibe_dll #(.RETRY_WAIT_CYC(4)) u_dll (
    .clk(clk), .rst_n(dllw.rst_n), .port_rst(dllw.port_rst),
    .device_rst(dllw.device_rst), .link_up(dllw.link_up), .fec_fail(dllw.fec_fail),
    .nw_dll_data(dllw.nw_dll_data), .nw_dll_vld(dllw.nw_dll_vld),
    .nw_dll_ready(dllw.nw_dll_ready),
    .dll_nw_data(dllw.dll_nw_data), .dll_nw_vld(dllw.dll_nw_vld),
    .dll_nw_ready(dllw.dll_nw_ready),
    .dll_pcs_data(dllw.dll_pcs_data), .dll_pcs_vld(dllw.dll_pcs_vld),
    .dll_pcs_ready(dllw.dll_pcs_ready),
    .pcs_dll_data(dllw.pcs_dll_data), .pcs_dll_vld(dllw.pcs_dll_vld),
    .pcs_dll_ready(dllw.pcs_dll_ready),
    .status_up(dllw.status_up), .disabled(dllw.disabled),
    .retrain_req(dllw.retrain_req), .retry_error(dllw.retry_error),
    .proto_err(dllw.proto_err), .fc_ovf(dllw.fc_ovf),
    .rx_ovf(dllw.rx_ovf), .cfg0_hit(dllw.cfg0_hit), .cfg0_data(dllw.cfg0_data)
  );

  vibe_rst_sync u_rsyn (.clk(clk), .rst_n_in(rsyn.rst_n_in), .rst_n_out(rsyn.rst_n_out));

  vibe_mgmt_byp u_mbyp (
    .clk(clk), .rst_n(mbyp.rst_n),
    .in_data(mbyp.in_data), .in_vld(mbyp.in_vld), .in_ready(mbyp.in_ready),
    .out_data(mbyp.out_data), .out_vld(mbyp.out_vld), .out_ready(mbyp.out_ready)
  );

  vibe_fecn_mark #(.FECN_WM(24)) u_fecn (
    .cci_in(fecn.cci_in), .voq_occ(fecn.voq_occ),
    .cci_out(fecn.cci_out), .marked(fecn.marked)
  );

  vibe_nw_adapt u_nwa (
    .clk(clk), .rst_n(nwa.rst_n), .link_ready(nwa.link_ready),
    .fab_nw_data(nwa.fab_nw_data), .fab_nw_vld(nwa.fab_nw_vld), .fab_nw_ready(nwa.fab_nw_ready),
    .mgmt_nw_data(nwa.mgmt_nw_data), .mgmt_nw_vld(nwa.mgmt_nw_vld),
    .mgmt_nw_ready(nwa.mgmt_nw_ready),
    .nw_dll_data(nwa.nw_dll_data), .nw_dll_vld(nwa.nw_dll_vld),
    .nw_dll_ready(nwa.nw_dll_ready),
    .dll_nw_data(nwa.dll_nw_data), .dll_nw_vld(nwa.dll_nw_vld),
    .dll_nw_ready(nwa.dll_nw_ready),
    .nw_fab_data(nwa.nw_fab_data), .nw_fab_vld(nwa.nw_fab_vld),
    .nw_fab_ready(nwa.nw_fab_ready)
  );

  vibe_pma_bnd u_pma (
    .txclk(pma.txclk), .rxclk(pma.rxclk),
    .afifo_pma_lane0(pma.t0), .afifo_pma_lane1(pma.t1),
    .afifo_pma_lane2(pma.t2), .afifo_pma_lane3(pma.t3),
    .afifo_pma_lane_vld(pma.afifo_pma_lane_vld), .pcs_pma_txdata(pma.pcs_pma_txdata),
    .pma_pcs_rxdata(pma.pma_pcs_rxdata),
    .pma_afifo_lane0(pma.r0), .pma_afifo_lane1(pma.r1),
    .pma_afifo_lane2(pma.r2), .pma_afifo_lane3(pma.r3),
    .pma_afifo_lane_vld(pma.pma_afifo_lane_vld)
  );

  vibe_gear_160_128 u_gtx (
    .clk(clk), .rst_n(gtx.rst_n), .in_vld(gtx.in_vld), .in_ready(gtx.in_ready),
    .in_data(gtx.in_data), .out_vld(gtx.out_vld), .out_ready(gtx.out_ready),
    .out_data(gtx.out_data)
  );
  vibe_gear_128_160 u_grx (
    .clk(clk), .rst_n(grx.rst_n), .in_vld(grx.in_vld), .in_ready(grx.in_ready),
    .in_data(grx.in_data), .out_vld(grx.out_vld), .out_ready(grx.out_ready),
    .out_data(grx.out_data)
  );

  vibe_pcs_tx_cw2beat u_cw2 (
    .clk(clk), .rst_n(cw2.rst_n), .cw_data(cw2.cw_data), .cw_vld(cw2.cw_vld),
    .cw_ready(cw2.cw_ready), .beat_data(cw2.beat_data), .beat_vld(cw2.beat_vld),
    .beat_ready(cw2.beat_ready)
  );

  vibe_pcs_tx_fec u_fec (
    .clk(clk), .rst_n(fec.rst_n), .fec_mode(fec.fec_mode),
    .win_data(fec.win_data), .win_vld(fec.win_vld), .win_ready(fec.win_ready),
    .cw_data(fec.cw_data), .cw_vld(fec.cw_vld), .cw_ready(fec.cw_ready)
  );
  assign fec.enc_a_start = u_fec.enc_a_start;
  assign fec.enc_b_start = u_fec.enc_b_start;

  always @* begin
    if (lmsm.zap_tmr) force u_lmsm.tmr = 27'd0;
    else release u_lmsm.tmr;
  end
  always @* begin
    if (rack.force_st7) force u_rack.st = 3'd7;
    else release u_rack.st;
  end

  vibe_pcs_scramble u_scr (
    .clk(clk), .rst_n(scr.rst_n), .lane_id(scr.lane_id), .seed_load(scr.seed_load),
    .en(scr.en), .in_vld(scr.in_vld), .in_data(scr.in_data),
    .out_vld(scr.out_vld), .out_data(scr.out_data)
  );

  vibe_pcs_tx_amctl u_amc (
    .clk(clk), .rst_n(amc.rst_n), .link_up(amc.link_up), .sdf_period(amc.sdf_period),
    .lane_id(amc.lane_id), .req(amc.req), .ack(amc.ack), .amctl_40B(amc.amctl_40B)
  );

  vibe_icrc u_icrc (
    .clk(clk), .rst_n(icrc.rst_n), .start(icrc.start), .in_vld(icrc.in_vld),
    .in_byte(icrc.in_byte), .last(icrc.last), .crc_out(icrc.crc_out), .done(icrc.done)
  );

  vibe_xbar u_xbar (
    .clk(clk), .rst_n(xbar.rst_n), .status_up(xbar.status_up),
    .in_data(xbar.in_data), .in_vld(xbar.in_vld), .in_sop(xbar.in_sop),
    .in_eop(xbar.in_eop), .in_dst(xbar.in_dst), .in_ready(xbar.in_ready),
    .out_data(xbar.out_data), .out_vld(xbar.out_vld), .out_sop(xbar.out_sop),
    .out_eop(xbar.out_eop), .out_ready(xbar.out_ready)
  );

  vibe_cna_ep u_cna (
    .clk(clk), .rst_n(cna.rst_n), .cna(cna.cna), .cna_written(cna.cna_written),
    .fab_mgmt_cfg6_hit(cna.hit), .fab_mgmt_cfg6_data(cna.data),
    .mgmt_fab_cfg6_consume(cna.cons), .mgmt_nw_data(cna.reply), .mgmt_nw_vld(cna.rvld),
    .mgmt_nw_ready(cna.rready), .icrc_fail(cna.icrc)
  );

  initial begin
    crd.rst_n = 0; lmsm.rst_n = 0; cfgs.rst_n = 0; irq.rst_n = 0;
    vlrr.rst_n = 0; bcrc.rst_n = 0; psel.rst_n = 0;
    crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.is_cfg0 = 0; crd.credit_ret = 0;
    lmsm.port_rst = 0; lmsm.lmsm_go = 0;
    irq.irq_clr = 0;
    lmsm.zap_tmr = 0;
    rack.force_st7 = 0;
    dsm.rst_n = 0; dsm.port_rst = 0; dsm.link_up = 0;
    dsm.param_ok = 0; dsm.credit_ok = 0; dsm.dll_error = 0;
    rbuf.rst_n = 0; rbuf.port_rst = 0; rbuf.link_up = 1;
    rbuf.wr_en = 0; rbuf.is_null = 0; rbuf.is_retry = 0; rbuf.ack_rel = 0;
    rbuf.send_size = 8'd1; rbuf.rel_size = 0; rbuf.rd_ptr_i = 0; rbuf.wr_flit = 0;
    rreq.rst_n = 0; rreq.port_rst = 0; rreq.device_rst = 0;
    rreq.start_retry = 0; rreq.phy_retrain = 0; rreq.wait_done_ack = 0;
    rack.rst_n = 0; rack.port_rst = 0; rack.start_ack = 0;
    rack.wr_ptr = 0; rack.rcv_ptr = 0;
    voq.rst_n = 0; voq.wr_en = 0; voq.rd_en = 0; voq.wr_vl = 0; voq.rd_vl = 0;
    voq.wr_data = 0; voq.wr_sop = 1; voq.wr_eop = 1;
    drx.rst_n = 0; drx.port_rst = 0; drx.link_up = 1; drx.fec_fail = 0;
    drx.pcs_dll_vld = 0; drx.pcs_dll_data = 0; drx.dll_nw_ready = 1;
    dllw.rst_n = 0; dllw.port_rst = 0; dllw.device_rst = 0; dllw.link_up = 0;
    dllw.fec_fail = 0; dllw.nw_dll_vld = 0; dllw.dll_nw_ready = 1;
    dllw.dll_pcs_ready = 1; dllw.pcs_dll_vld = 0;
    dllw.nw_dll_data = 0; dllw.pcs_dll_data = 0;
    rsyn.rst_n_in = 0;
    mbyp.rst_n = 0; mbyp.in_vld = 0; mbyp.out_ready = 0; mbyp.in_data = 0;
    fecn.cci_in = 0; fecn.voq_occ = 0;
    nwa.rst_n = 1; nwa.link_ready = 0;
    nwa.fab_nw_data = 0; nwa.mgmt_nw_data = 0; nwa.dll_nw_data = 0;
    nwa.fab_nw_vld = 0; nwa.mgmt_nw_vld = 0; nwa.nw_dll_ready = 1;
    nwa.dll_nw_vld = 0; nwa.nw_fab_ready = 1;
    pma.t0 = 0; pma.t1 = 0; pma.t2 = 0; pma.t3 = 0;
    pma.afifo_pma_lane_vld = 0; pma.pma_pcs_rxdata = 0;
    gtx.rst_n = 0; gtx.in_vld = 0; gtx.out_ready = 1; gtx.in_data = 0;
    grx.rst_n = 0; grx.in_vld = 0; grx.out_ready = 1; grx.in_data = 0;
    cw2.rst_n = 0; cw2.cw_vld = 0; cw2.beat_ready = 1; cw2.cw_data = 0;
    fec.rst_n = 0; fec.win_vld = 0; fec.cw_ready = 1; fec.win_data = 0;
    fec.fec_mode = 3'd0;
    scr.rst_n = 0; scr.lane_id = 0; scr.seed_load = 0; scr.en = 0;
    scr.in_vld = 0; scr.in_data = 0;
    amc.rst_n = 0; amc.link_up = 1; amc.sdf_period = 1; amc.lane_id = 0; amc.req = 0;
    icrc.rst_n = 0; icrc.start = 0; icrc.in_vld = 0; icrc.last = 0; icrc.in_byte = 0;
    xbar.rst_n = 0; xbar.status_up = 4'b1111;
    xbar.in_vld = 0; xbar.in_sop = 0; xbar.in_eop = 0; xbar.out_ready = 4'b1111;
    for (xi = 0; xi < 4; xi = xi + 1) begin
      xbar.in_data[xi] = 512'd0;
      xbar.in_dst[xi]  = 2'd0;
    end
    cna.rst_n = 0; cna.cna = 0; cna.cna_written = 0; cna.hit = 0;
    cna.rready = 4'b1111;
    for (gi = 0; gi < 4; gi = gi + 1) cna.data[gi] = 512'd0;

    uvm_config_db#(virtual vibe_clk_rst_if)::set(null, "*", "clk_vif", clk_if);
    uvm_config_db#(virtual vibe_credit_if)::set(null, "*", "crd", crd);
    uvm_config_db#(virtual vibe_lmsm_if)::set(null, "*", "lmsm", lmsm);
    uvm_config_db#(virtual vibe_cfg_space_if)::set(null, "*", "cfgs", cfgs);
    uvm_config_db#(virtual vibe_irq_if)::set(null, "*", "irq", irq);
    uvm_config_db#(virtual vibe_vlrr_if)::set(null, "*", "vlrr", vlrr);
    uvm_config_db#(virtual vibe_bcrc_if)::set(null, "*", "bcrc", bcrc);
    uvm_config_db#(virtual vibe_afifo_if)::set(null, "*", "afifo", afifo);
    uvm_config_db#(virtual vibe_psel_if)::set(null, "*", "psel", psel);
    uvm_config_db#(virtual vibe_dll_sm_if)::set(null, "*", "dsm", dsm);
    uvm_config_db#(virtual vibe_retry_buf_if)::set(null, "*", "rbuf", rbuf);
    uvm_config_db#(virtual vibe_retry_req_if)::set(null, "*", "rreq", rreq);
    uvm_config_db#(virtual vibe_retry_ack_if)::set(null, "*", "rack", rack);
    uvm_config_db#(virtual vibe_voq_if)::set(null, "*", "voq", voq);
    uvm_config_db#(virtual vibe_dll_rx_if)::set(null, "*", "drx", drx);
    uvm_config_db#(virtual vibe_dll_wrap_if)::set(null, "*", "dllw", dllw);
    uvm_config_db#(virtual vibe_rst_sync_if)::set(null, "*", "rsyn", rsyn);
    uvm_config_db#(virtual vibe_mgmt_byp_if)::set(null, "*", "mbyp", mbyp);
    uvm_config_db#(virtual vibe_fecn_if)::set(null, "*", "fecn", fecn);
    uvm_config_db#(virtual vibe_nw_adapt_if)::set(null, "*", "nwa", nwa);
    uvm_config_db#(virtual vibe_pma_bnd_if)::set(null, "*", "pma", pma);
    uvm_config_db#(virtual vibe_gear_tx_if)::set(null, "*", "gtx", gtx);
    uvm_config_db#(virtual vibe_gear_rx_if)::set(null, "*", "grx", grx);
    uvm_config_db#(virtual vibe_cw2beat_if)::set(null, "*", "cw2", cw2);
    uvm_config_db#(virtual vibe_pcs_fec_if)::set(null, "*", "fec", fec);
    uvm_config_db#(virtual vibe_pcs_scramble_if)::set(null, "*", "scr", scr);
    uvm_config_db#(virtual vibe_pcs_amctl_if)::set(null, "*", "amc", amc);
    uvm_config_db#(virtual vibe_icrc_if)::set(null, "*", "icrc", icrc);
    uvm_config_db#(virtual vibe_xbar_if)::set(null, "*", "xbar", xbar);
    uvm_config_db#(virtual vibe_cna_if)::set(null, "*", "cna", cna);
    run_test();
  end
endmodule
