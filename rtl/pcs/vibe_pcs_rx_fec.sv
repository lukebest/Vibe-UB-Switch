// AS-0.1 §6: 2×512 codeword → RS decode. fail → fec_fail (Go-Back-N). No hi_FEC_BER.
// One-cycle syndrome over the assembled 1024b so a later 512 cannot overwrite cw
// while a serial feed is in progress (idle zeros hid that bug).
module vibe_pcs_rx_fec (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [2:0]   fec_mode,
  input  logic [511:0] beat_data,
  input  logic         beat_vld,
  output logic         beat_ready,
  output logic [959:0] win_data,
  output logic         win_vld,
  input  logic         win_ready,
  input  logic         am_gap = 1'b0, // 1: drop half-CW so 1024b does not straddle AMCTL
  output logic         fec_fail
);
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  logic [511:0] hi;
  logic         have_hi;

  wire bypass = (fec_mode == VIBE_FEC_BYPASS);

  // Accept a beat only when the output window is free. have_hi leftover is
  // the first half of the next CW and must survive an AMCTL-sized gap in
  // the 512b stream (5 beats/group is odd). am_gap drops that leftover.
  assign beat_ready = !win_vld;

  function automatic [7:0] gf_mul2;
    input [7:0] a;
    begin
      gf_mul2 = a[7] ? {a[6:0], 1'b0} ^ 8'h1D : {a[6:0], 1'b0};
    end
  endfunction

  // Same recurrence as vibe_rs128_120_dec, all 128 symbols in one shot.
  function automatic [63:0] rs_syndromes;
    input [1023:0] cw;
    integer i;
    logic [7:0] s0, s1, s2, s3, s4, s5, s6, s7, sym;
    begin
      s0 = 8'd0; s1 = 8'd0; s2 = 8'd0; s3 = 8'd0;
      s4 = 8'd0; s5 = 8'd0; s6 = 8'd0; s7 = 8'd0;
      for (i = 0; i < 128; i = i + 1) begin
        sym = cw[1023-8*i -: 8];
        s0 = s0 ^ sym;
        s1 = gf_mul2(s1) ^ sym;
        s2 = vibe_gf256_mul(s2, 8'd4) ^ sym;
        s3 = vibe_gf256_mul(s3, 8'd8) ^ sym;
        s4 = vibe_gf256_mul(s4, 8'd16) ^ sym;
        s5 = vibe_gf256_mul(s5, 8'd32) ^ sym;
        s6 = vibe_gf256_mul(s6, 8'd64) ^ sym;
        s7 = vibe_gf256_mul(s7, 8'd128) ^ sym;
      end
      rs_syndromes = {s0, s1, s2, s3, s4, s5, s6, s7};
    end
  endfunction

  wire [1023:0] cw_now  = {hi, beat_data};
  wire [63:0]   syn_now = rs_syndromes(cw_now);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hi       <= 512'd0;
      have_hi  <= 1'b0;
      win_data <= 960'd0;
      win_vld  <= 1'b0;
      fec_fail <= 1'b0;
    end else begin
      fec_fail <= 1'b0;
      if (win_vld && win_ready)
        win_vld <= 1'b0;

      // AMCTL is outside FEC. Default wiring is 0: a leftover 512 after a
      // 5-beat pack group must pair with the next group's first 512.
      if (am_gap)
        have_hi <= 1'b0;

      if (beat_vld && beat_ready) begin
        if (!have_hi) begin
          hi      <= beat_data;
          have_hi <= 1'b1;
        end else begin
          have_hi  <= 1'b0;
          win_data <= {hi, beat_data[511:64]};
          win_vld  <= 1'b1;
          if (!bypass)
            fec_fail <= |syn_now;
        end
      end
    end
  end
endmodule
