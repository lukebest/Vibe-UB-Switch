// AS-0.1 §8: fabric — SAF, 8 stages, route_lu, port_sel, xbar, VOQ×16 VL, vl_rr, fecn_mark.
// Transit MUST NOT recompute ICRC. Mgmt bypass does not enter xbar.
module vibe_fabric #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         device_rst,
  input  logic [3:0]   status_up,
  input  logic [3:0]   default_bm,
  input  logic         rt_wr_en,
  input  logic [15:0]  rt_wr_idx,
  input  logic [31:0]  rt_wr_data,
  input  logic [639:0] ing_data [0:3],
  input  logic [3:0]   ing_vld,
  output logic [3:0]   ing_ready,
  output logic [639:0] egr_data [0:3],
  output logic [3:0]   egr_vld,
  input  logic [3:0]   egr_ready,
  output logic [3:0]   len_err,
  output logic         drop_g1,
  output logic [31:0]  rt_shortest_unimpl,
  output logic [31:0]  drop_down_cnt,
  output logic [3:0]   deadlock_drop,
  output logic         irq_rt,
  // AS-0.1 §9: mgmt CNA for CFG6 terminate vs forward
  input  logic [15:0]  cna,
  input  logic         cna_written,
  // to cna_ep: only terminate-class CFG6 (not all CFG6)
  output logic [3:0]   cfg6_hit,
  output logic [639:0] cfg6_data [0:3]
);
  `include "vibe_ub_fn.vh"
  `include "vibe_ub_params.vh"

  logic [639:0] saf_d [0:3];
  logic [3:0]   saf_v, saf_r, saf_sop, saf_eop;
  logic [15:0]  saf_b [0:3];
  logic [3:0]   bm;
  logic         g1;
  logic [1:0]   egr [0:3];
  logic [3:0]   pdrop;
  logic [639:0] xb_d [0:3];
  logic [3:0]   xb_v, xb_sop, xb_eop, xb_r;
  logic [15:0]  ne [0:3];
  logic [3:0]   vl_sel [0:3];
  logic [3:0]   vl_ok;
  logic [5:0]   occ0 [0:3];
  logic [15:0]  cci_m [0:3];
  integer       p;

  genvar gi;
  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_saf
      vibe_saf_ing #(.DEPTH(VIBE_SAF_PKT_DEPTH)) u_saf (
        .clk(clk), .rst_n(rst_n),
        .in_data(ing_data[gi]), .in_vld(ing_vld[gi]), .in_ready(ing_ready[gi]),
        .pkt_data(saf_d[gi]), .pkt_vld(saf_v[gi]), .pkt_ready(saf_r[gi]),
        .pkt_sop(saf_sop[gi]), .pkt_eop(saf_eop[gi]),
        .pkt_bytes(saf_b[gi]), .len_err(len_err[gi])
      );
    end
  endgenerate

  wire [159:0] f0 = saf_d[0][639:480];
  wire [3:0]   cfg0 = vibe_lph_cfg(f0);
  wire [1:0]   rt0  = vibe_lph_rt(f0);
  wire [15:0]  src0 = vibe_nth_scna(f0);
  wire [15:0]  dst0 = vibe_nth_dcna(f0);
  wire [3:0]   vl0  = vibe_lph_vl(f0);

  vibe_route_lu #(.DEPTH(ROUTE_TABLE_DEPTH)) u_rt (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .wr_en(rt_wr_en), .wr_idx(rt_wr_idx), .wr_data(rt_wr_data),
    .dest(dst0), .rt(rt0), .lu_vld(saf_v[0]),
    .bitmap(bm), .drop_g1(g1)
  );

  vibe_port_sel u_ps (
    .clk(clk), .rst_n(rst_n),
    .bitmap(bm), .status_up(status_up), .default_bm(default_bm),
    .rt(rt0), .drop_g1(g1), .sel_vld(saf_v[0]),
    .cfg(cfg0), .src(src0), .dest(dst0), .vl(vl0),
    .egr(egr[0]), .drop(pdrop[0]), .drop_down_cnt(drop_down_cnt)
  );

  // Per-ingress header parse + route for ports 1..3 (shared table via wr only on u_rt)
  logic [3:0] bm_p [1:3];
  logic       g1_p [1:3];
  generate
    for (gi = 1; gi < 4; gi = gi + 1) begin : g_rt
      vibe_route_lu #(.DEPTH(ROUTE_TABLE_DEPTH)) u_rti (
        .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
        .wr_en(rt_wr_en), .wr_idx(rt_wr_idx), .wr_data(rt_wr_data),
        .dest(vibe_nth_dcna(saf_d[gi][639:480])),
        .rt(vibe_lph_rt(saf_d[gi][639:480])),
        .lu_vld(saf_v[gi]),
        .bitmap(bm_p[gi]), .drop_g1(g1_p[gi])
      );
      vibe_port_sel u_psi (
        .clk(clk), .rst_n(rst_n),
        .bitmap(bm_p[gi]), .status_up(status_up), .default_bm(default_bm),
        .rt(vibe_lph_rt(saf_d[gi][639:480])), .drop_g1(g1_p[gi]),
        .sel_vld(saf_v[gi]),
        .cfg(vibe_lph_cfg(saf_d[gi][639:480])),
        .src(vibe_nth_scna(saf_d[gi][639:480])),
        .dest(vibe_nth_dcna(saf_d[gi][639:480])),
        .vl(vibe_lph_vl(saf_d[gi][639:480])),
        .egr(egr[gi]), .drop(pdrop[gi]), .drop_down_cnt()
      );
    end
  endgenerate

  // FS-0.2.3 + AS-0.1 G1 named signals (architecture-chosen):
  //   rt_shortest_unimpl : 32-bit saturating (does not wrap)
  //   drop_g1            : one-shot per RT=10/11 packet → sticky irq_logic
  // No extra IRQ pins. No Dijkstra / no treat-as-RT=00 / no RT rewrite.
  logic [3:0] g1_comb, g1_evt, g1_drain, g1_seen, xb_in_r;
  always @* begin
    for (p = 0; p < 4; p = p + 1) begin
      g1_comb[p] = saf_v[p] &&
                   ((vibe_lph_rt(saf_d[p][639:480]) == 2'b10) ||
                    (vibe_lph_rt(saf_d[p][639:480]) == 2'b11));
      g1_evt[p]  = g1_comb[p] && saf_sop[p] && !g1_seen[p];
    end
  end
  assign drop_g1 = |g1_evt;
  assign irq_rt  = drop_g1;

  wire [2:0] g1_inc = {2'b0, g1_evt[0]} + {2'b0, g1_evt[1]} +
                      {2'b0, g1_evt[2]} + {2'b0, g1_evt[3]};
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n || device_rst) begin
      rt_shortest_unimpl <= 32'd0;
      g1_drain           <= 4'd0;
      g1_seen            <= 4'd0;
    end else begin
      if (g1_inc != 3'd0) begin
        if (rt_shortest_unimpl >= (32'hFFFF_FFFF - {29'd0, g1_inc}))
          rt_shortest_unimpl <= 32'hFFFF_FFFF;
        else
          rt_shortest_unimpl <= rt_shortest_unimpl + {29'd0, g1_inc};
      end
      for (p = 0; p < 4; p = p + 1) begin
        if (g1_evt[p]) begin
          g1_seen[p]  <= 1'b1;
          g1_drain[p] <= 1'b1;
        end
        if (g1_drain[p] && saf_v[p] && saf_r[p] && saf_eop[p]) begin
          g1_seen[p]  <= 1'b0;
          g1_drain[p] <= 1'b0;
        end
      end
    end
  end

  // CFG6: terminate only if us / NLP=1 / opcode 0x10 targeting us (AS-0.1 §9).
  // Non-term CFG6 must take the xbar like CFG3/4/5/7/9. Do not flood.
  logic [3:0] cfg6_term, cfg6_drain, cfg6_seen;
  always @* begin
    for (p = 0; p < 4; p = p + 1) begin
      cfg6_term[p] = saf_v[p] &&
                     (vibe_lph_cfg(saf_d[p][639:480]) == 4'd6) &&
                     vibe_cfg6_should_term(cna_written, cna, saf_d[p][639:480]);
      cfg6_hit[p]  = cfg6_term[p] || cfg6_drain[p];
      cfg6_data[p] = saf_d[p];
      // Drain G1 drops and terminate-CFG6; non-term CFG6 uses xbar ready.
      saf_r[p]     = g1_evt[p] || g1_drain[p] || pdrop[p] ||
                     cfg6_term[p] || cfg6_drain[p] ||
                     (xb_in_r[p] && !g1_comb[p] && !cfg6_hit[p]);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n || device_rst) begin
      cfg6_drain <= 4'd0;
      cfg6_seen  <= 4'd0;
    end else begin
      for (p = 0; p < 4; p = p + 1) begin
        if (cfg6_drain[p] && saf_v[p] && saf_r[p] && saf_eop[p]) begin
          cfg6_seen[p]  <= 1'b0;
          cfg6_drain[p] <= 1'b0;
        end else if (cfg6_term[p] && saf_sop[p] && !cfg6_seen[p]) begin
          // Single-beat term: do not leave drain sticky (next pkt must be able to fwd).
          if (saf_r[p] && saf_eop[p]) begin
            cfg6_seen[p]  <= 1'b0;
            cfg6_drain[p] <= 1'b0;
          end else begin
            cfg6_seen[p]  <= 1'b1;
            cfg6_drain[p] <= 1'b1;
          end
        end
      end
    end
  end

  logic [3:0] x_in_v;
  always @* begin
    for (p = 0; p < 4; p = p + 1)
      x_in_v[p] = saf_v[p] && !pdrop[p] && !cfg6_hit[p] &&
                  !g1_comb[p] && !g1_drain[p];
  end

  vibe_xbar u_xbar (
    .clk(clk), .rst_n(rst_n), .status_up(status_up),
    .in_data(saf_d), .in_vld(x_in_v), .in_sop(saf_sop), .in_eop(saf_eop),
    .in_dst(egr), .in_ready(xb_in_r),
    .out_data(xb_d), .out_vld(xb_v), .out_sop(xb_sop), .out_eop(xb_eop),
    .out_ready(xb_r)
  );

  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_egr
      vibe_voq_egr #(.DEPTH(VIBE_VOQ_DEPTH)) u_voq (
        .clk(clk), .rst_n(rst_n),
        .wr_vl(vibe_lph_vl(xb_d[gi][639:480])),
        .wr_en(xb_v[gi]), .wr_data(xb_d[gi]),
        .wr_sop(xb_sop[gi]), .wr_eop(xb_eop[gi]), .wr_ready(xb_r[gi]),
        .rd_vl(vl_sel[gi]), .rd_en(egr_ready[gi] && vl_ok[gi]),
        .rd_data(egr_data[gi]), .rd_sop(), .rd_eop(),
        .nonempty(ne[gi]), .occ_vl0(occ0[gi]),
        .deadlock_drop(deadlock_drop[gi]), .deadlock_cnt()
      );
      vibe_vl_rr u_rr (
        .clk(clk), .rst_n(rst_n), .nonempty(ne[gi]),
        .grant(egr_ready[gi] && vl_ok[gi]),
        .vl_sel(vl_sel[gi]), .valid(vl_ok[gi])
      );
      vibe_fecn_mark #(.FECN_WM(VIBE_FECN_WM)) u_fecn (
        .cci_in(vibe_nth_cci(egr_data[gi][639:480])),
        .voq_occ(occ0[gi]),
        .cci_out(cci_m[gi]),
        .marked()
      );
      assign egr_vld[gi] = vl_ok[gi];
    end
  endgenerate
endmodule
