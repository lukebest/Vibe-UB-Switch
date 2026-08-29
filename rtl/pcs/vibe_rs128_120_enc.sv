// AS-0.1 §5 T3 / UB 2.0 §3.2.2: systematic RS(128,120) encoder, GF(256).
// Generator coefficients Table 3-2. T=2 encoding produces the same 8 parity symbols.
module vibe_rs128_120_enc (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        start,
  input  logic        in_vld,
  input  logic [7:0]  in_sym,
  output logic        in_ready,
  output logic        done,
  output logic [63:0] parity // p7..p0, p7 = p[63:56]
);
  `include "vibe_ub_fn.vh"

  localparam logic [7:0] G0 = 8'd24;
  localparam logic [7:0] G1 = 8'd200;
  localparam logic [7:0] G2 = 8'd173;
  localparam logic [7:0] G3 = 8'd239;
  localparam logic [7:0] G4 = 8'd54;
  localparam logic [7:0] G5 = 8'd81;
  localparam logic [7:0] G6 = 8'd11;
  localparam logic [7:0] G7 = 8'd255;

  logic [7:0] r0, r1, r2, r3, r4, r5, r6, r7;
  logic [7:0] cnt;
  logic       busy;

  assign in_ready = busy && (cnt < 8'd120);
  assign parity   = {r7, r6, r5, r4, r3, r2, r1, r0};

  wire [7:0] fb = in_sym ^ r7;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      r0 <= 8'd0; r1 <= 8'd0; r2 <= 8'd0; r3 <= 8'd0;
      r4 <= 8'd0; r5 <= 8'd0; r6 <= 8'd0; r7 <= 8'd0;
      cnt  <= 8'd0;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start) begin
        r0 <= 8'd0; r1 <= 8'd0; r2 <= 8'd0; r3 <= 8'd0;
        r4 <= 8'd0; r5 <= 8'd0; r6 <= 8'd0; r7 <= 8'd0;
        cnt  <= 8'd0;
        busy <= 1'b1;
      end else if (busy && in_vld && in_ready) begin
        r0 <= vibe_gf256_mul(fb, G0);
        r1 <= r0 ^ vibe_gf256_mul(fb, G1);
        r2 <= r1 ^ vibe_gf256_mul(fb, G2);
        r3 <= r2 ^ vibe_gf256_mul(fb, G3);
        r4 <= r3 ^ vibe_gf256_mul(fb, G4);
        r5 <= r4 ^ vibe_gf256_mul(fb, G5);
        r6 <= r5 ^ vibe_gf256_mul(fb, G6);
        r7 <= r6 ^ vibe_gf256_mul(fb, G7);
        cnt <= cnt + 8'd1;
        if (cnt == 8'd119) begin
          busy <= 1'b0;
          done <= 1'b1;
        end
      end
    end
  end
endmodule
