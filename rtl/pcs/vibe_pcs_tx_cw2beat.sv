// AS-0.1 §5 T4: 1024b codeword as two 512b beats.
module vibe_pcs_tx_cw2beat (
  input  logic          clk,
  input  logic          rst_n,
  input  logic [1023:0] cw_data,
  input  logic          cw_vld,
  output logic          cw_ready,
  output logic [511:0]  beat_data,
  output logic          beat_vld,
  input  logic          beat_ready
);
  logic [511:0] hi, lo;
  logic         have_hi, have_lo;

  assign cw_ready  = !have_hi && !have_lo;
  assign beat_vld  = have_hi || have_lo;
  assign beat_data = have_hi ? hi : lo;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hi      <= 512'd0;
      lo      <= 512'd0;
      have_hi <= 1'b0;
      have_lo <= 1'b0;
    end else begin
      if (cw_vld && cw_ready) begin
        hi      <= cw_data[1023:512];
        lo      <= cw_data[511:0];
        have_hi <= 1'b1;
        have_lo <= 1'b1;
      end
      if (beat_vld && beat_ready) begin
        if (have_hi) have_hi <= 1'b0;
        else         have_lo <= 1'b0;
      end
    end
  end
endmodule
