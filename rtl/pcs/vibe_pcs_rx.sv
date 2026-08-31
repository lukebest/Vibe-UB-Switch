// AS-0.1 §6: PCS RX — AMCTL lock x4, unpack, descramble, FEC decode, deskew.
module vibe_pcs_rx (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up = 1'b0,  // 1 = Send_NullBlock / Link_Active
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
  logic         am0_d, am1_d, am2_d, am3_d;
  logic         sdf0, edf0, edf1, edf2, edf3;
  logic [1:0]   lid0, lid1, lid2, lid3;
  logic         bad0, bad1, bad2, bad3;
  logic [3:0]   lid_seeded;
  logic [159:0] u0, u1, u2, u3;
  logic         uv, aligned;
  logic [511:0] beat;
  logic         bv, br;
  logic [959:0] win;
  logic         wv, wr;
  logic [319:0] rem;
  logic         remv;

  // Lock on RAW 160b (AMCTL is not scrambled). AS-0.1 §5/§6.
  vibe_pcs_rx_amctl_lock u_l0 (.clk(clk), .rst_n(rst_n), .in_vld(lane_vld), .in_data(lane0),
    .locked(am_locked[0]), .lid(lid0), .lid_bad(bad0), .is_amctl(am0), .sdf(sdf0), .edf(edf0));
  vibe_pcs_rx_amctl_lock u_l1 (.clk(clk), .rst_n(rst_n), .in_vld(lane_vld), .in_data(lane1),
    .locked(am_locked[1]), .lid(lid1), .lid_bad(bad1), .is_amctl(am1), .sdf(), .edf(edf1));
  vibe_pcs_rx_amctl_lock u_l2 (.clk(clk), .rst_n(rst_n), .in_vld(lane_vld), .in_data(lane2),
    .locked(am_locked[2]), .lid(lid2), .lid_bad(bad2), .is_amctl(am2), .sdf(), .edf(edf2));
  vibe_pcs_rx_amctl_lock u_l3 (.clk(clk), .rst_n(rst_n), .in_vld(lane_vld), .in_data(lane3),
    .locked(am_locked[3]), .lid(lid3), .lid_bad(bad3), .is_amctl(am3), .sdf(), .edf(edf3));

  // UB 3.2.2.4: hold seed while LMSM not Send_NullBlock/Link_Active (!link_up),
  // same as TX. Reload from AMCTL.LID on first lock. AMCTL+EDF while !link_up
  // also reloads. Do not reset on SDF while link_up.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      lid_seeded <= 4'd0;
    else if (!link_up)
      lid_seeded <= 4'd0;
    else begin
      if (am_locked[0]) lid_seeded[0] <= 1'b1;
      if (am_locked[1]) lid_seeded[1] <= 1'b1;
      if (am_locked[2]) lid_seeded[2] <= 1'b1;
      if (am_locked[3]) lid_seeded[3] <= 1'b1;
    end
  end
  wire sl0 = !link_up || (edf0 && !link_up) || (am_locked[0] && !lid_seeded[0]);
  wire sl1 = !link_up || (edf1 && !link_up) || (am_locked[1] && !lid_seeded[1]);
  wire sl2 = !link_up || (edf2 && !link_up) || (am_locked[2] && !lid_seeded[2]);
  wire sl3 = !link_up || (edf3 && !link_up) || (am_locked[3] && !lid_seeded[3]);

  // Descramble LTB only; pass-through AMCTL (do not advance LFSR). Seed = AMCTL.LID.
  vibe_pcs_scramble u_d0 (.clk(clk), .rst_n(rst_n),
    .lane_id(am_locked[0] ? lid0 : 2'd0), .seed_load(sl0),
    .en(lane_vld && !am0), .in_vld(lane_vld), .in_data(lane0), .out_vld(dv), .out_data(d0));
  vibe_pcs_scramble u_d1 (.clk(clk), .rst_n(rst_n),
    .lane_id(am_locked[1] ? lid1 : 2'd1), .seed_load(sl1),
    .en(lane_vld && !am1), .in_vld(lane_vld), .in_data(lane1), .out_vld(), .out_data(d1));
  vibe_pcs_scramble u_d2 (.clk(clk), .rst_n(rst_n),
    .lane_id(am_locked[2] ? lid2 : 2'd2), .seed_load(sl2),
    .en(lane_vld && !am2), .in_vld(lane_vld), .in_data(lane2), .out_vld(), .out_data(d2));
  vibe_pcs_scramble u_d3 (.clk(clk), .rst_n(rst_n),
    .lane_id(am_locked[3] ? lid3 : 2'd3), .seed_load(sl3),
    .en(lane_vld && !am3), .in_vld(lane_vld), .in_data(lane3), .out_vld(), .out_data(d3));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      am0_d <= 1'b0; am1_d <= 1'b0; am2_d <= 1'b0; am3_d <= 1'b0;
    end else begin
      am0_d <= am0; am1_d <= am1; am2_d <= am2; am3_d <= am3;
    end
  end

  assign lid_bad = bad0 | bad1 | bad2 | bad3 |
                   (am_locked[0] && lid0 != 2'd0) |
                   (am_locked[1] && lid1 != 2'd1) |
                   (am_locked[2] && lid2 != 2'd2) |
                   (am_locked[3] && lid3 != 2'd3);

  vibe_pcs_rx_deskew u_dsk (
    .clk(clk), .rst_n(rst_n),
    .in0(d0), .in1(d1), .in2(d2), .in3(d3), .in_vld(dv),
    .am0(am0_d), .am1(am1_d), .am2(am2_d), .am3(am3_d),
    .out0(u0), .out1(u1), .out2(u2), .out3(u3),
    .out_vld(uv), .aligned(aligned)
  );
  assign deskew_ok = aligned;

  vibe_pcs_rx_unpack u_un (
    .clk(clk), .rst_n(rst_n),
    .lane0(u0), .lane1(u1), .lane2(u2), .lane3(u3), .lane_vld(uv),
    .am0(1'b0), .am1(1'b0), .am2(1'b0), .am3(1'b0), // deskew already drops AMCTL
    .beat_data(beat), .beat_vld(bv), .beat_ready(br)
  );

  vibe_pcs_rx_fec u_fec (
    .clk(clk), .rst_n(rst_n), .fec_mode(fec_mode),
    .beat_data(beat), .beat_vld(bv), .beat_ready(br),
    .win_data(win), .win_vld(wv), .win_ready(wr),
    .am_gap(am0_d | am1_d | am2_d | am3_d),
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
