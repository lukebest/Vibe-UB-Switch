// AS-0.1 §6: PCS RX — AMCTL lock x4, unpack, descramble, FEC decode, deskew.
module vibe_pcs_rx (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [2:0]   fec_mode,
  input  logic [159:0] lane0,
  input  logic [159:0] lane1,
  input  logic [159:0] lane2,
  input  logic [159:0] lane3,
  input  logic         lane_vld,
  output logic [639:0] dll_data,
  output logic         dll_vld,
  input  logic         dll_ready,
  output logic         fec_fail,
  output logic [3:0]   am_locked,
  output logic         lid_bad,
  output logic         deskew_ok
);
  logic [159:0] d0, d1, d2, d3;
  logic         dv;
  logic         am0, am1, am2, am3;
  logic         sdf0;
  logic [1:0]   lid0, lid1, lid2, lid3;
  logic         bad0, bad1, bad2, bad3;
  logic [159:0] u0, u1, u2, u3;
  logic         uv, aligned;
  logic [511:0] beat;
  logic         bv, br;
  logic [959:0] win;
  logic         wv, wr;
  logic [319:0] rem;
  logic         remv;

  vibe_pcs_scramble u_d0 (.clk(clk), .rst_n(rst_n), .lane_id(2'd0), .seed_load(1'b0),
    .en(1'b1), .in_vld(lane_vld), .in_data(lane0), .out_vld(dv), .out_data(d0));
  vibe_pcs_scramble u_d1 (.clk(clk), .rst_n(rst_n), .lane_id(2'd1), .seed_load(1'b0),
    .en(1'b1), .in_vld(lane_vld), .in_data(lane1), .out_vld(), .out_data(d1));
  vibe_pcs_scramble u_d2 (.clk(clk), .rst_n(rst_n), .lane_id(2'd2), .seed_load(1'b0),
    .en(1'b1), .in_vld(lane_vld), .in_data(lane2), .out_vld(), .out_data(d2));
  vibe_pcs_scramble u_d3 (.clk(clk), .rst_n(rst_n), .lane_id(2'd3), .seed_load(1'b0),
    .en(1'b1), .in_vld(lane_vld), .in_data(lane3), .out_vld(), .out_data(d3));

  vibe_pcs_rx_amctl_lock u_l0 (.clk(clk), .rst_n(rst_n), .in_vld(dv), .in_data(d0),
    .locked(am_locked[0]), .lid(lid0), .lid_bad(bad0), .is_amctl(am0), .sdf(sdf0));
  vibe_pcs_rx_amctl_lock u_l1 (.clk(clk), .rst_n(rst_n), .in_vld(dv), .in_data(d1),
    .locked(am_locked[1]), .lid(lid1), .lid_bad(bad1), .is_amctl(am1), .sdf());
  vibe_pcs_rx_amctl_lock u_l2 (.clk(clk), .rst_n(rst_n), .in_vld(dv), .in_data(d2),
    .locked(am_locked[2]), .lid(lid2), .lid_bad(bad2), .is_amctl(am2), .sdf());
  vibe_pcs_rx_amctl_lock u_l3 (.clk(clk), .rst_n(rst_n), .in_vld(dv), .in_data(d3),
    .locked(am_locked[3]), .lid(lid3), .lid_bad(bad3), .is_amctl(am3), .sdf());

  assign lid_bad = bad0 | bad1 | bad2 | bad3 |
                   (am_locked[0] && lid0 != 2'd0) |
                   (am_locked[1] && lid1 != 2'd1) |
                   (am_locked[2] && lid2 != 2'd2) |
                   (am_locked[3] && lid3 != 2'd3);

  vibe_pcs_rx_deskew u_dsk (
    .clk(clk), .rst_n(rst_n),
    .in0(d0), .in1(d1), .in2(d2), .in3(d3), .in_vld(dv),
    .am0(am0), .am1(am1), .am2(am2), .am3(am3),
    .out0(u0), .out1(u1), .out2(u2), .out3(u3),
    .out_vld(uv), .aligned(aligned)
  );
  assign deskew_ok = aligned;

  vibe_pcs_rx_unpack u_un (
    .clk(clk), .rst_n(rst_n),
    .lane0(u0), .lane1(u1), .lane2(u2), .lane3(u3), .lane_vld(uv),
    .am0(1'b0), .am1(1'b0), .am2(1'b0), .am3(1'b0),
    .beat_data(beat), .beat_vld(bv), .beat_ready(br)
  );

  vibe_pcs_rx_fec u_fec (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .beat_data(beat), .beat_vld(bv), .beat_ready(br),
    .win_data(win), .win_vld(wv), .win_ready(wr),
    .fec_fail(fec_fail)
  );

  // 960b (6 flits) → 640b beats (4 flits) with 320b remainder (AS-0.1 inverse T2)
  assign wr = dll_ready;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rem     <= 320'd0;
      remv    <= 1'b0;
      dll_data<= 640'd0;
      dll_vld <= 1'b0;
    end else begin
      if (dll_vld && dll_ready)
        dll_vld <= 1'b0;
      if (wv && wr && !dll_vld) begin
        if (!remv) begin
          dll_data <= win[959:320];
          rem      <= win[319:0];
          remv     <= 1'b1;
          dll_vld  <= 1'b1;
        end else begin
          dll_data <= {rem, win[959:640]};
          rem      <= win[639:320];
          dll_vld  <= 1'b1;
          // leftover 320 of this window kept
        end
      end
    end
  end
endmodule
