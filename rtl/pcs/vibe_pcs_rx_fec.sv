// AS-0.1 §6: 2×512 codeword → RS decode. fail → fec_fail (Go-Back-N). No hi_FEC_BER.
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
  output logic         fec_fail
);
  `include "vibe_ub_params.vh"

  logic [1023:0] cw;
  logic          have_hi;
  logic          start;
  logic          din_vld;
  logic [7:0]    din;
  logic          din_rdy;
  logic          done;
  logic          fail;
  logic [959:0]  dout;
  logic [7:0]    scnt;
  logic          feeding;

  wire bypass = (fec_mode == VIBE_FEC_BYPASS);

  vibe_rs128_120_dec u_dec (
    .clk(clk), .rst_n(rst_n), .start(start),
    .in_vld(din_vld), .in_sym(din), .in_ready(din_rdy),
    .done(done), .fec_fail(fail), .data_out(dout)
  );

  assign beat_ready = !have_hi || (!feeding && !win_vld);
  assign fec_fail   = fail;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cw      <= 1024'd0;
      have_hi <= 1'b0;
      start   <= 1'b0;
      din_vld <= 1'b0;
      din     <= 8'd0;
      scnt    <= 8'd0;
      feeding <= 1'b0;
      win_data<= 960'd0;
      win_vld <= 1'b0;
    end else begin
      start <= 1'b0;
      if (win_vld && win_ready)
        win_vld <= 1'b0;

      if (beat_vld && beat_ready) begin
        if (!have_hi) begin
          cw[1023:512] <= beat_data;
          have_hi <= 1'b1;
        end else begin
          cw[511:0] <= beat_data;
          have_hi   <= 1'b0;
          if (bypass) begin
            win_data <= beat_data[511:0] != 512'd0 || 1'b1 ? cw[1023:64] : cw[1023:64];
            win_data <= {cw[1023:512], beat_data[511:64]};
            win_vld  <= 1'b1;
          end else begin
            start   <= 1'b1;
            feeding <= 1'b1;
            scnt    <= 8'd0;
          end
        end
      end

      if (feeding) begin
        din     <= cw[1023-8*scnt -: 8];
        din_vld <= 1'b1;
        if (din_rdy) begin
          if (scnt == 8'd127) begin
            feeding <= 1'b0;
            din_vld <= 1'b0;
          end else
            scnt <= scnt + 8'd1;
        end
      end else
        din_vld <= 1'b0;

      if (done) begin
        win_data <= dout;
        win_vld  <= 1'b1;
      end
    end
  end
endmodule
