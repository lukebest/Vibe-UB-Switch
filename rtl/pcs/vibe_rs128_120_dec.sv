// AS-0.1 §6: RS(128,120) syndrome check. Nonzero syndrome → fec_fail (Go-Back-N).
module vibe_rs128_120_dec (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_sym,
  output logic         in_ready,
  output logic         done,
  output logic         fec_fail,
  output logic [959:0] data_out
);
  `include "vibe_ub_fn.vh"

  logic [7:0]   s0, s1, s2, s3, s4, s5, s6, s7;
  logic [7:0]   cnt;
  logic         busy;
  logic [7:0]   msg [0:119];

  assign in_ready = busy && (cnt < 8'd128);

  function automatic [7:0] gf_mul2;
    input [7:0] a;
    begin
      gf_mul2 = a[7] ? {a[6:0], 1'b0} ^ 8'h1D : {a[6:0], 1'b0};
    end
  endfunction

  // Next syndromes (combo) so the last symbol is included before fec_fail.
  wire [7:0] ns0 = s0 ^ in_sym;
  wire [7:0] ns1 = gf_mul2(s1) ^ in_sym;
  wire [7:0] ns2 = vibe_gf256_mul(s2, 8'd4) ^ in_sym;
  wire [7:0] ns3 = vibe_gf256_mul(s3, 8'd8) ^ in_sym;
  wire [7:0] ns4 = vibe_gf256_mul(s4, 8'd16) ^ in_sym;
  wire [7:0] ns5 = vibe_gf256_mul(s5, 8'd32) ^ in_sym;
  wire [7:0] ns6 = vibe_gf256_mul(s6, 8'd64) ^ in_sym;
  wire [7:0] ns7 = vibe_gf256_mul(s7, 8'd128) ^ in_sym;

  integer i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
      s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
      cnt      <= 8'd0;
      busy     <= 1'b0;
      done     <= 1'b0;
      fec_fail <= 1'b0;
      data_out <= 960'd0;
      for (i = 0; i < 120; i = i + 1) msg[i] <= 8'd0;
    end else begin
      done <= 1'b0;
      if (start) begin
        s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
        s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
        cnt      <= 8'd0;
        busy     <= 1'b1;
        fec_fail <= 1'b0;
      end else if (busy && in_vld && in_ready) begin
        s0 <= ns0;
        s1 <= ns1;
        s2 <= ns2;
        s3 <= ns3;
        s4 <= ns4;
        s5 <= ns5;
        s6 <= ns6;
        s7 <= ns7;
        if (cnt < 8'd120)
          msg[cnt] <= in_sym;
        if (cnt == 8'd127) begin
          busy     <= 1'b0;
          done     <= 1'b1;
          fec_fail <= |{ns0, ns1, ns2, ns3, ns4, ns5, ns6, ns7};
          // pack msg[0] as first symbol (MSB of data_out)
          for (i = 0; i < 120; i = i + 1)
            data_out[959-8*i -: 8] <= msg[i];
        end else begin
          cnt <= cnt + 8'd1;
        end
      end
    end
  end
endmodule
