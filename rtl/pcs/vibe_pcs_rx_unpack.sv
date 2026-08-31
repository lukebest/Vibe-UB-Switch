// AS-0.1 §6: strip AMCTL, 4×160 → 512b beats (inverse G2).
// 4×640 = 2560b = 5×512. Dual-buffer the 2560: accept the next 4×640
// while emitting 5×512. A single acc that dropped ingress while `have`
// permanently slipped 512 pairing vs TX vibe_pcs_tx_pack (5×512 ↔ 4×640).
module vibe_pcs_rx_unpack (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [159:0] lane0,
  input  logic [159:0] lane1,
  input  logic [159:0] lane2,
  input  logic [159:0] lane3,
  input  logic         lane_vld,
  input  logic         am0,
  input  logic         am1,
  input  logic         am2,
  input  logic         am3,
  input  logic         am_gap = 1'b0,
  output logic [511:0] beat_data,
  output logic         beat_vld,
  input  logic         beat_ready
);
  logic [2559:0] acc;      // group being emitted as 5×512
  logic [2559:0] nxt;      // group being filled as 4×640
  logic [2:0]    n;        // 640s collected in nxt (0..3)
  logic [2:0]    e;        // 512s left in acc after the one on beat_data
  logic          have;     // acc holds a group
  logic          nxt_full; // nxt holds a complete 2560 waiting for acc

  wire skip = am0 | am1 | am2 | am3;
  wire [639:0] din = {lane3, lane2, lane1, lane0};
  // Accept unless the fill buffer is already a complete group.
  wire take = lane_vld && !skip && !am_gap && !nxt_full;

  assign beat_vld  = have;
  assign beat_data = acc[511:0];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc      <= 2560'd0;
      nxt      <= 2560'd0;
      n        <= 3'd0;
      e        <= 3'd0;
      have     <= 1'b0;
      nxt_full <= 1'b0;
    end else begin
      // One-cycle AMCTL-gap reset: next 4×640 starts at n=0. Keep an
      // in-flight emit (have/acc) so draining 5×512 is not wiped.
      if (am_gap)
        n <= 3'd0;

      // Emit one 512. Last beat (e==0) frees acc, or swaps in nxt.
      if (have && beat_ready) begin
        if (e != 3'd0) begin
          acc <= {512'd0, acc[2559:512]};
          e   <= e - 3'd1;
        end else if (nxt_full) begin
          acc      <= nxt;
          e        <= 3'd4;
          have     <= 1'b1;
          nxt_full <= 1'b0;
        end else begin
          have <= 1'b0;
        end
      end

      // Fill nxt (or acc if it is free this cycle). n=0..2 write slices;
      // n==3 completes the 2560 as {4th 640, first 3×640}.
      if (take) begin
        if (n == 3'd3) begin
          if (!have || (have && beat_ready && e == 3'd0 && !nxt_full)) begin
            acc  <= {din, nxt[1919:0]};
            e    <= 3'd4;
            have <= 1'b1;
            n    <= 3'd0;
          end else begin
            nxt      <= {din, nxt[1919:0]};
            nxt_full <= 1'b1;
            n        <= 3'd0;
          end
        end else begin
          nxt[640*n +: 640] <= din;
          n                 <= n + 3'd1;
        end
      end
    end
  end
endmodule
