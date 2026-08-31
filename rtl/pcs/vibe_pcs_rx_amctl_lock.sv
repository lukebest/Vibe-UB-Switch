// AS-0.1 §6 / §14: AMCTL lock per lane. CONFIRM_N = UNLOCK_N = 3.
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
  output logic         sdf
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

  logic [1:0] conf;
  logic [1:0] unlk;
  logic [319:0] win;
  logic         have;

  wire [15:0] w_end = win[127:112];
  wire match_body = (win[319:304] == cw21) || (win[319:304] == cw28);
  wire match_end  = (w_end == cw22);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      locked  <= 1'b0;
      lid     <= 2'd0;
      lid_bad <= 1'b0;
      is_amctl<= 1'b0;
      sdf     <= 1'b0;
      conf    <= 2'd0;
      unlk    <= 2'd0;
      win     <= 320'd0;
      have    <= 1'b0;
    end else begin
      is_amctl <= 1'b0;
      if (in_vld) begin
        if (!have) begin
          win[319:160] <= in_data;
          have <= 1'b1;
        end else begin
          win[159:0] <= in_data;
          have <= 1'b0;
          if (match_body && (in_data[127:112] == cw22 || match_end)) begin
            is_amctl <= 1'b1;
            if (conf < VIBE_AMCTL_CONFIRM_N[1:0])
              conf <= conf + 2'd1;
            else
              locked <= 1'b1;
            unlk <= 2'd0;
            // LID in symbols 16-23 of 40: second word bits
            if (in_data[79:64] == cw3)
              lid <= 2'd0;
            else if (in_data[79:64] == cw8)
              lid <= 2'd1;
            else if (in_data[79:64] == cw9)
              lid <= 2'd2;
            else if (in_data[79:64] == cw10)
              lid <= 2'd3;
            else
              lid_bad <= 1'b1;
            sdf <= 1'b1;
          end else if (locked) begin
            if (unlk < VIBE_AMCTL_UNLOCK_N[1:0])
              unlk <= unlk + 2'd1;
            else begin
              locked <= 1'b0;
              conf   <= 2'd0;
            end
          end
        end
      end
    end
  end
endmodule
