// AS-0.1 §6 / §14: AMCTL lock per lane. CONFIRM_N = UNLOCK_N = 3.
// Lock on RAW 160b (AMCTL is not scrambled). Hunt with 1-beat slip.
// TX amctl_40B: BODY {3{cw21,cw28}} at [319:224] so [319:304]=cw21;
// END cw22,cw22 at [223:192] = first 160b [63:32]; LID at [191:128].
// If LID not {0,1,2,3} → fail (U24: do not swap lanes).
module vibe_pcs_rx_amctl_lock (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  input  logic [159:0] in_data,
  output logic         locked,
  output logic [1:0]   lid,
  output logic         lid_bad,
  output logic         is_amctl,
  output logic         sdf,
  output logic         edf
);
  `include "vibe_ub_params.vh"

  logic [15:0] cw21, cw22, cw28, cw3, cw8, cw9, cw10;
  vibe_ebch16 u21 (.cw_sel(5'd21), .cw(cw21));
  vibe_ebch16 u22 (.cw_sel(5'd22), .cw(cw22));
  vibe_ebch16 u28 (.cw_sel(5'd28), .cw(cw28));
  vibe_ebch16 u3  (.cw_sel(5'd3),  .cw(cw3));
  vibe_ebch16 u8  (.cw_sel(5'd8),  .cw(cw8));
  vibe_ebch16 u9  (.cw_sel(5'd9),  .cw(cw9));
  vibe_ebch16 u10 (.cw_sel(5'd10), .cw(cw10));

  logic [1:0]   conf;
  logic [1:0]   unlk;
  logic [159:0] prev;
  logic         have;
  logic         via_leg;

  // Word0 of TX AMCTL (am[319:160]): BODY at [159:144], END at [63:32].
  wire match_w0 = ((in_data[159:144] == cw21) || (in_data[159:144] == cw28)) &&
                  (in_data[63:32] == {cw22, cw22});
  wire match_body = (prev[159:144] == cw21) || (prev[159:144] == cw28);
  wire match_end_tx  = (prev[63:32] == {cw22, cw22});
  wire match_end_leg = (in_data[127:112] == cw22);
  wire match_pair = have && match_body && (match_end_tx || match_end_leg);

  // Word1 of TX AMCTL (am[159:0]): CTRL_TYPE Link-Width + CTRL_DETAIL SDF.
  // Hunt slip can present this word without a pair-match; LFSR must still
  // skip it the same way TX skips both am_phase words.
  wire match_w1 = (in_data[127:64] == {cw8, cw9, cw8, cw9}) &&
                  (in_data[63:0]   == {cw10, cw22, cw10, cw22});

  // Combo so descramble en=!is_amctl sees the same beat (pass-through AMCTL).
  assign is_amctl = in_vld && (match_pair || match_w0 || match_w1);

  function automatic [1:0] dec_lid;
    input [15:0] s;
    begin
      if (s == cw3)       dec_lid = 2'd0;
      else if (s == cw8)  dec_lid = 2'd1;
      else if (s == cw9)  dec_lid = 2'd2;
      else if (s == cw10) dec_lid = 2'd3;
      else                dec_lid = 2'd0;
    end
  endfunction

  wire [15:0] lid_sym = match_end_tx ? prev[15:0] : in_data[79:64];
  wire        lid_ok  = (lid_sym == cw3) || (lid_sym == cw8) ||
                        (lid_sym == cw9) || (lid_sym == cw10);
  // TX CTRL_DETAIL x4 SDF = {cw10,cw22,cw10,cw22} in second 160b [63:0].
  wire        detail_sdf = (in_data[63:0] == {cw10, cw22, cw10, cw22});

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      locked  <= 1'b0;
      lid     <= 2'd0;
      lid_bad <= 1'b0;
      sdf     <= 1'b0;
      edf     <= 1'b0;
      conf    <= 2'd0;
      unlk    <= 2'd0;
      prev    <= 160'd0;
      have    <= 1'b0;
      via_leg <= 1'b0;
    end else begin
      sdf <= 1'b0;
      edf <= 1'b0;
      if (in_vld) begin
        if (match_pair) begin
          sdf <= detail_sdf;
          edf <= !detail_sdf;
          if (lid_ok)
            lid <= dec_lid(lid_sym);
          else
            lid_bad <= 1'b1;
          // 3 AMCTL detections then locked. TX-layout lock is sticky through data.
          if (conf >= (VIBE_AMCTL_CONFIRM_N[1:0] - 2'd1))
            locked <= 1'b1;
          else
            conf <= conf + 2'd1;
          via_leg <= match_end_leg && !match_end_tx;
          unlk    <= 2'd0;
          have    <= 1'b0;
        end else if (!have) begin
          prev <= in_data;
          have <= 1'b1;
        end else begin
          // Slip one 160b (AS Slip) instead of committing a bad pair.
          prev <= in_data;
          have <= 1'b1;
          // UNLOCK_N only for legacy pair-slot hunt (unit TB); not TX-layout data.
          if (locked && via_leg) begin
            if (unlk >= (VIBE_AMCTL_UNLOCK_N[1:0] - 2'd1)) begin
              locked  <= 1'b0;
              conf    <= 2'd0;
              unlk    <= 2'd0;
              via_leg <= 1'b0;
            end else
              unlk <= unlk + 2'd1;
          end
        end
      end
    end
  end
endmodule
