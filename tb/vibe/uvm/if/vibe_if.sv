// AS-0.1 §3/§10/§18 product and overlay-B interfaces for the UVM env.
// Clocks/resets are exempt from {src}_{dst}_{meaning}. Handshake is _vld/_ready.
`timescale 1ns/1ps

interface vibe_clk_rst_if;
  logic clk;
  logic rst_n;

  initial clk = 1'b0;
  always #1 clk = ~clk;
endinterface

// AS-0.1 §10/§18: static write, clk_fab, vld/ready. irq_logic is the single sticky pin.
interface vibe_cfg_if (input logic clk, input logic rst_n);
  logic        vld;
  logic        ready;
  logic [3:0]  cmd;
  logic [15:0] idx;
  logic [31:0] data;
  logic        irq_logic;

  task automatic idle;
    begin
      vld  = 1'b0;
      cmd  = 4'd0;
      idx  = 16'd0;
      data = 32'd0;
    end
  endtask

  task automatic write(input logic [3:0] c, input logic [15:0] i, input logic [31:0] d);
    begin
      @(negedge clk);
      cmd  = c;
      idx  = i;
      data = d;
      vld  = 1'b1;
      @(posedge clk);
      while (!ready) @(posedge clk);
      @(negedge clk);
      vld = 1'b0;
      repeat (3) @(posedge clk);
    end
  endtask
endinterface

// AS-0.1 §3/§18: product PMA, no extra handshake, no PMA ready.
// Slice: [127:0]=lane0 … [511:384]=lane3.
interface vibe_pma_if (input logic txclk, input logic rxclk);
  logic [511:0] pcs_pma_txdata;
  logic [511:0] pma_pcs_rxdata;

  task automatic idle_rx;
    pma_pcs_rxdata = 512'd0;
  endtask
endinterface

// Overlay B 512b @ clk_fab: nw_fab_* / fab_nw_* (AS-0.1 §3). Four ports.
interface vibe_nw4_if (input logic clk, input logic rst_n);
  logic [511:0] data  [0:3];
  logic [3:0]   vld;
  logic [3:0]   ready;

  task automatic idle_master;
    integer p;
    begin
      vld = 4'd0;
      for (p = 0; p < 4; p = p + 1) data[p] = 512'd0;
    end
  endtask

  task automatic idle_slave_ready;
    ready = 4'b1111;
  endtask
endinterface

// DLL↔PCS 640b window @ clk_fab (AS-0.1 §3). Not used on fabric/NW pins.
interface vibe_pcs4_if (input logic clk, input logic rst_n);
  logic [639:0] data  [0:3];
  logic [3:0]   vld;
  logic [3:0]   ready;
endinterface

// Hierarchical fabric/mgmt probes (not product pins). AS §2 G1 counter is hier-only.
interface vibe_fab_probe_if (input logic clk, input logic rst_n);
  logic         drop_g1;
  logic         irq_logic;
  logic         irq_rt;
  logic [31:0]  rt_shortest_unimpl;
  logic [31:0]  drop_down_cnt;
  logic [3:0]   len_err;
  logic [3:0]   deadlock_drop;
  logic [3:0]   fab_mgmt_cfg6_hit;
  logic [3:0]   mgmt_fab_cfg6_consume;
  logic [3:0]   x_in_v;
  logic [3:0]   saf_v;
  logic [3:0]   g1_comb;
  logic [3:0]   g1_evt;
  logic [3:0]   pdrop;
  logic [15:0]  cna;
  logic         cna_written;
  logic [3:0]   port_rst;
  logic         device_rst;
  logic [3:0]   lmsm_go;
  logic [3:0]   status_up;
  logic [3:0]   default_bm;
  logic [31:0]  guid0;
  logic [31:0]  class_code;
  logic [31:0]  port_basic;
  logic [31:0]  port_cap;
  logic [3:0]   port_rst_rw1c;
  logic [511:0] saf_d [0:3];
  logic [511:0] egr_last [0:3];
  logic [1:0]   last_rt_egr [0:3];
  logic [3:0]   saw_egr;
  logic [3:0]   saw_xin;
  logic [3:0]   saw_len_err;
  logic         saw_drop_g1;
  integer       egr_cnt [0:3];

  logic         preload_req;
  logic         preload_done;
  logic [31:0]  preload_val;

  task automatic clr_mon;
    integer p;
    begin
      saw_drop_g1 = 1'b0;
      saw_len_err = 4'd0;
      saw_egr     = 4'd0;
      saw_xin     = 4'd0;
      for (p = 0; p < 4; p = p + 1) begin
        egr_cnt[p]     = 0;
        egr_last[p]    = 512'd0;
        last_rt_egr[p] = 2'd0;
      end
    end
  endtask
endinterface

// vibe_route_lu + vibe_port_sel (AS-0.1 §2/§8) for RT-00/01 sticky/RR unit checks.
interface vibe_psel_if (input logic clk);
  logic        rst_n;
  logic        device_rst;
  logic        wr_en;
  logic        sel_vld;
  logic        drop_g1;
  logic        drop;
  logic [3:0]  bitmap;
  logic [3:0]  status_up;
  logic [3:0]  default_bm;
  logic [3:0]  cfg;
  logic [3:0]  vl;
  logic [1:0]  rt;
  logic [1:0]  egr;
  logic [15:0] wr_idx;
  logic [15:0] src;
  logic [15:0] dest;
  logic [31:0] wr_data;
  logic [31:0] drop_down;

  task automatic reset;
    begin
      rst_n = 1'b0; device_rst = 1'b0; status_up = 4'b1111; default_bm = 4'd0;
      rt = 2'b00; sel_vld = 1'b0; cfg = 4'd3; vl = 4'd0;
      src = 16'd0; dest = 16'd0; wr_en = 1'b0; wr_idx = 16'd0; wr_data = 32'd0;
      repeat (3) @(posedge clk);
      rst_n = 1'b1;
      repeat (2) @(posedge clk);
    end
  endtask

  task automatic wr_route(input logic [15:0] d, input logic [3:0] bm);
    begin
      @(negedge clk);
      wr_en = 1'b1; wr_idx = d; wr_data = {28'd0, bm};
      @(posedge clk);
      @(negedge clk);
      wr_en = 1'b0;
      @(posedge clk);
    end
  endtask

  task automatic select(
      input logic [1:0]  rt_i,
      input logic [3:0]  vl_i,
      input logic [15:0] src_i,
      input logic [15:0] dst_i);
    begin
      @(negedge clk);
      rt = rt_i; vl = vl_i; src = src_i; dest = dst_i;
      sel_vld = 1'b1;
      @(posedge clk);
      @(posedge clk);
      @(negedge clk);
      sel_vld = 1'b0;
      @(posedge clk);
    end
  endtask
endinterface

// Standalone vibe_cna_ep for AS-0.1 §9 CFG6 term vs forward pulses.
interface vibe_cna_if (input logic clk);
  logic         rst_n;
  logic         cna_written;
  logic         icrc;
  logic [15:0]  cna;
  logic [3:0]   hit;
  logic [3:0]   cons;
  logic [3:0]   rready;
  logic [3:0]   rvld;
  logic [511:0] data  [0:3];
  logic [511:0] reply [0:3];
endinterface

// ----- leaf unit interfaces (AS-locked blocks) -----

interface vibe_credit_if (input logic clk);
  logic        rst_n, port_rst, link_up;
  logic        consume_vld, is_cfg0, credit_ret;
  logic [7:0]  grain_n;
  logic [9:0]  consume_flits;
  logic [15:0] credit_ret_n, pending, cells;
  logic        credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf;
endinterface

interface vibe_lmsm_if (input logic clk);
  logic        rst_n, port_rst, lmsm_go, lid_bad, lane0_fail, eq_negotiated, retrain_req;
  logic [3:0]  am_locked;
  logic        link_up, link_ready, sdf_period, width_fail;
  logic [4:0]  state;
  logic        zap_tmr;
endinterface

interface vibe_cfg_space_if (input logic clk);
  logic        rst_n, device_rst;
  logic        cfg_wr_vld, cfg_wr_ready, cna_written, rt_wr_en, irq_clr;
  logic        device_rst_pulse;
  logic [3:0]  cfg_wr_cmd;
  logic [15:0] cfg_wr_idx, cna, rt_wr_idx;
  logic [31:0] cfg_wr_data, rt_wr_data;
  logic [3:0]  default_bm, port_rst_pulse, port_rst_hold, port_rst_rw1c, lmsm_go_pulse;
  logic [31:0] guid0, class_code, port_basic, port_cap;
endinterface

interface vibe_irq_if (input logic clk);
  logic        rst_n, irq_clr, icrc_fail, drop_g1, irq_logic;
  logic [3:0]  rx_ovf, fc_ovf, proto_err, retry_error, len_err, deadlock_drop, afifo_ovf;
endinterface

interface vibe_vlrr_if (input logic clk);
  logic        rst_n, grant, valid;
  logic [15:0] nonempty;
  logic [3:0]  vl_sel;
endinterface

interface vibe_bcrc_if (input logic clk);
  logic         rst_n, start, in_vld, last, error_flag, done;
  logic [159:0] in_flit;
  logic [31:0]  crc_word;
endinterface

interface vibe_afifo_if;
  logic         wclk, rclk, wrst_n, rrst_n, wen, ren, wfull, almost_full, rempty;
  logic [159:0] wdata, rdata;
  logic [4:0]   wocc;
endinterface

interface vibe_dll_sm_if (input logic clk);
  logic rst_n, port_rst, link_up, param_ok, credit_ok, dll_error;
  logic [1:0] state;
  logic status_up, disabled;
endinterface

interface vibe_retry_buf_if (input logic clk);
  logic rst_n, port_rst, link_up, wr_en, is_null, is_retry, ack_rel, proto_err, can_send;
  logic [159:0] wr_flit, rd_flit;
  logic [7:0] send_size, rel_size, rd_ptr_i, wr_ptr, tail_ptr, rcv_ptr;
  logic [8:0] num_free;
endinterface

interface vibe_retry_req_if (input logic clk);
  logic rst_n, port_rst, device_rst, start_retry, phy_retrain, wait_done_ack;
  logic [2:0] state;
  logic drop_data, retrain_req, retry_error, send_idle, send_req;
  logic [4:0] send_cnt;
endinterface

interface vibe_retry_ack_if (input logic clk);
  logic rst_n, port_rst, start_ack, send_idle, send_ack, replay;
  logic [7:0] wr_ptr, rcv_ptr, rd_ptr;
  logic [2:0] state;
  logic force_st7;
endinterface

interface vibe_voq_if (input logic clk);
  logic rst_n, wr_en, wr_sop, wr_eop, wr_ready, rd_en, rd_sop, rd_eop;
  logic [3:0] wr_vl, rd_vl;
  logic [511:0] wr_data, rd_data;
  logic [15:0] nonempty;
  logic [5:0] occ_vl0;
  logic deadlock_drop;
  logic [31:0] deadlock_cnt;
endinterface

interface vibe_dll_rx_if (input logic clk);
  logic rst_n, port_rst, link_up, fec_fail;
  logic [639:0] pcs_dll_data, cfg0_data;
  logic [511:0] dll_nw_data;
  logic pcs_dll_vld, pcs_dll_ready, dll_nw_vld, dll_nw_ready;
  logic cfg0_hit, bcrc_fail, start_retry, rx_ovf, start_ack;
  logic have;
endinterface

interface vibe_dll_wrap_if (input logic clk);
  logic rst_n, port_rst, device_rst, link_up, fec_fail;
  logic [511:0] nw_dll_data, dll_nw_data;
  logic [639:0] dll_pcs_data, pcs_dll_data, cfg0_data;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready;
  logic dll_pcs_vld, dll_pcs_ready, pcs_dll_vld, pcs_dll_ready;
  logic status_up, disabled, retrain_req, retry_error, proto_err, fc_ovf, rx_ovf, cfg0_hit;
endinterface

interface vibe_rst_sync_if (input logic clk);
  logic rst_n_in, rst_n_out;
endinterface

interface vibe_mgmt_byp_if (input logic clk);
  logic rst_n, in_vld, in_ready, out_vld, out_ready;
  logic [511:0] in_data, out_data;
endinterface

interface vibe_fecn_if;
  logic [15:0] cci_in, cci_out;
  logic [5:0] voq_occ;
  logic marked;
endinterface

interface vibe_nw_adapt_if (input logic clk);
  logic rst_n, link_ready;
  logic [511:0] fab_nw_data, mgmt_nw_data, nw_dll_data, dll_nw_data, nw_fab_data;
  logic fab_nw_vld, fab_nw_ready, mgmt_nw_vld, mgmt_nw_ready;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready, nw_fab_vld, nw_fab_ready;
endinterface

interface vibe_pma_bnd_if;
  logic txclk, rxclk, afifo_pma_lane_vld, pma_afifo_lane_vld;
  logic [127:0] t0, t1, t2, t3, r0, r1, r2, r3;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata;
endinterface

interface vibe_gear_tx_if (input logic clk);
  logic rst_n, in_vld, in_ready, out_vld, out_ready;
  logic [159:0] in_data;
  logic [127:0] out_data;
endinterface

interface vibe_gear_rx_if (input logic clk);
  logic rst_n, in_vld, in_ready, out_vld, out_ready;
  logic [127:0] in_data;
  logic [159:0] out_data;
endinterface

interface vibe_cw2beat_if (input logic clk);
  logic rst_n, cw_vld, cw_ready, beat_vld, beat_ready;
  logic [1023:0] cw_data;
  logic [511:0] beat_data;
endinterface

interface vibe_pcs_fec_if (input logic clk);
  logic rst_n, win_vld, win_ready, cw_vld, cw_ready;
  logic [2:0] fec_mode;
  logic [959:0] win_data;
  logic [1023:0] cw_data;
  logic enc_a_start, enc_b_start;
endinterface

interface vibe_pcs_scramble_if (input logic clk);
  logic rst_n, seed_load, en, in_vld, out_vld;
  logic [1:0] lane_id;
  logic [159:0] in_data, out_data;
endinterface

interface vibe_pcs_amctl_if (input logic clk);
  logic rst_n, link_up, sdf_period, req, ack;
  logic [1:0] lane_id;
  logic [319:0] amctl_40B;
endinterface

interface vibe_icrc_if (input logic clk);
  logic rst_n, start, in_vld, last, done;
  logic [7:0] in_byte;
  logic [31:0] crc_out;
endinterface

interface vibe_xbar_if (input logic clk);
  logic rst_n;
  logic [3:0] status_up, in_vld, in_sop, in_eop, in_ready;
  logic [3:0] out_vld, out_sop, out_eop, out_ready;
  logic [511:0] in_data [0:3];
  logic [511:0] out_data [0:3];
  logic [1:0] in_dst [0:3];
endinterface

// Product vibe_port (AS-0.1 §4) plus Overlay-B / PMA probes.
interface vibe_port_if (input logic clk_fab, input logic txclk, input logic rxclk);
  logic rst_n, port_rst, device_rst, lmsm_go, loop_en;
  logic [511:0] pcs_pma_txdata, pma_pcs_rxdata;
  logic [511:0] fab_nw_data, nw_fab_data, mgmt_nw_data;
  logic [639:0] cfg0_data;
  logic fab_nw_vld, fab_nw_ready, nw_fab_vld, nw_fab_ready;
  logic mgmt_nw_vld, mgmt_nw_ready, status_up, disabled, retry_error;
  logic proto_err, fc_ovf, rx_ovf, afifo_ovf, cfg0_hit;
  logic link_ready, fec_fail, deskew_ok;
  logic [4:0] lmsm_st;
  logic [3:0] am_locked;
  logic [511:0] nw_dll_data, dll_nw_data;
  logic nw_dll_vld, nw_dll_ready, dll_nw_vld, dll_nw_ready;
  logic [639:0] dll_pcs_data, pcs_dll_data;
  logic dll_pcs_vld, dll_pcs_ready, pcs_dll_vld, pcs_dll_ready;
  logic [159:0] pcs_afifo_lane0, pcs_afifo_lane1, pcs_afifo_lane2, pcs_afifo_lane3;
  logic pcs_afifo_lane_vld;
  logic [127:0] afifo_pma_lane0, afifo_pma_lane1, afifo_pma_lane2, afifo_pma_lane3;
  logic afifo_pma_lane_vld;
  logic afrv0, afrv1, afrv2, afrv3;
  logic [15:0] crd_cells, crd_pend;
  logic credit_low, bp_nw, can_send;
  logic [1:0] dll_sm_st;
  logic force_am_lock, force_lid_ok, force_st_active;
  logic force_crd64, force_crd512, force_pend0;
endinterface
