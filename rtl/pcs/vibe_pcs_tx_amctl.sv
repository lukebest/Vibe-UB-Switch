// AS-0.1 §5: AMCTL 40 symbol/lane, eBCH-16. After FEC, before G2.
// Data period 640 symbols after SDF; other LMSM states 512 symbols.
module vibe_pcs_tx_amctl (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         sdf_period, // 1 = 640-symbol data period
  input  logic [1:0]   lane_id,
  input  logic         req,
  output logic         ack,
  output logic [319:0] amctl_40B // 40 symbols
);
  logic [15:0] cw3, cw8, cw9, cw10, cw21, cw22, cw28;
  vibe_ebch16 u3  (.cw_sel(5'd3),  .cw(cw3));
  vibe_ebch16 u8  (.cw_sel(5'd8),  .cw(cw8));
  vibe_ebch16 u9  (.cw_sel(5'd9),  .cw(cw9));
  vibe_ebch16 u10 (.cw_sel(5'd10), .cw(cw10));
  vibe_ebch16 u21 (.cw_sel(5'd21), .cw(cw21));
  vibe_ebch16 u22 (.cw_sel(5'd22), .cw(cw22));
  vibe_ebch16 u28 (.cw_sel(5'd28), .cw(cw28));

  logic [15:0] lid1, lid0;
  always @* begin
    case (lane_id)
      2'd0: begin lid1 = cw3;  lid0 = cw3;  end
      2'd1: begin lid1 = cw3;  lid0 = cw8;  end
      2'd2: begin lid1 = cw3;  lid0 = cw9;  end
      default: begin lid1 = cw3; lid0 = cw10; end
    endcase
  end

  // BODY CW21/CW28, END CW22, LID, CTRL_TYPE=Link Width x4 (SDF), CTRL_DETAIL x4
  assign amctl_40B = {
    {3{cw21, cw28}},          // BODY 12 symbols
    cw22, cw22,               // END 4
    lid1, lid0, lid1, lid0,   // LID 8
    cw8, cw9, cw8, cw9,       // CTRL_TYPE Link Width Switch
    cw10, cw22, cw10, cw22    // CTRL_DETAIL x4 SDF
  };

  assign ack = req && link_up;
endmodule
