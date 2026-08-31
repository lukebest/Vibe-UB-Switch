// AS-0.1 §5: PCS TX — G1, dual RS FEC, scramble, AMCTL insert, G2 pack.
module vibe_pcs_tx (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         sdf_period,
  input  logic [2:0]   fec_mode,
  input  logic         afifo_afull,
  input  logic [639:0] dll_data,
  input  logic         dll_vld,
  output logic         dll_ready,
  output logic [159:0] lane0,
  output logic [159:0] lane1,
  output logic [159:0] lane2,
  output logic [159:0] lane3,
  output logic         lane_vld
);
  logic [959:0]  win;
  logic          win_vld, win_rdy;
  logic [1023:0] cw;
  logic          cw_vld, cw_rdy;
  logic [511:0]  beat;
  logic          beat_vld, beat_rdy;
  logic [159:0]  p0, p1, p2, p3;
  logic          p_vld, p_rdy;
  logic [159:0]  s0, s1, s2, s3;
  logic          s_vld;
  logic          am_word;

  vibe_pcs_tx_g1 u_g1 (
    .clk(clk), .rst_n(rst_n), .link_up(link_up),
    .in_data(dll_data), .in_vld(dll_vld), .in_ready(dll_ready),
    .win_data(win), .win_vld(win_vld), .win_ready(win_rdy)
  );
  vibe_pcs_tx_fec u_fec (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .win_data(win), .win_vld(win_vld), .win_ready(win_rdy),
    .cw_data(cw), .cw_vld(cw_vld), .cw_ready(cw_rdy)
  );
  vibe_pcs_tx_cw2beat u_cw (
    .clk(clk), .rst_n(rst_n),
    .cw_data(cw), .cw_vld(cw_vld), .cw_ready(cw_rdy),
    .beat_data(beat), .beat_vld(beat_vld), .beat_ready(beat_rdy)
  );
  vibe_pcs_tx_pack u_pack (
    .clk(clk), .rst_n(rst_n), .sdf_period(sdf_period),
    .afifo_afull(afifo_afull),
    .beat_data(beat), .beat_vld(beat_vld), .beat_ready(beat_rdy),
    .lane0(p0), .lane1(p1), .lane2(p2), .lane3(p3),
    .lane_vld(p_vld), .lane_ready(p_rdy), .am_word(am_word)
  );

  // AS-0.1 §5: scramble LTB, not AMCTL/EEIB. Pack emits AMCTL on am_word.
  assign p_rdy = 1'b1;

  vibe_pcs_scramble u_s0 (.clk(clk), .rst_n(rst_n), .lane_id(2'd0), .seed_load(!link_up),
    .en(!am_word), .in_vld(p_vld), .in_data(p0), .out_vld(s_vld), .out_data(s0));
  vibe_pcs_scramble u_s1 (.clk(clk), .rst_n(rst_n), .lane_id(2'd1), .seed_load(!link_up),
    .en(!am_word), .in_vld(p_vld), .in_data(p1), .out_vld(), .out_data(s1));
  vibe_pcs_scramble u_s2 (.clk(clk), .rst_n(rst_n), .lane_id(2'd2), .seed_load(!link_up),
    .en(!am_word), .in_vld(p_vld), .in_data(p2), .out_vld(), .out_data(s2));
  vibe_pcs_scramble u_s3 (.clk(clk), .rst_n(rst_n), .lane_id(2'd3), .seed_load(!link_up),
    .en(!am_word), .in_vld(p_vld), .in_data(p3), .out_vld(), .out_data(s3));

  assign lane0 = s0;
  assign lane1 = s1;
  assign lane2 = s2;
  assign lane3 = s3;
  assign lane_vld = s_vld;
endmodule
