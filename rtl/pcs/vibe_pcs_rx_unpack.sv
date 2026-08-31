// AS-0.1 §6: strip AMCTL, 4×160 → 512b beats (inverse G2).
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
  output logic [511:0] beat_data,
  output logic         beat_vld,
  input  logic         beat_ready
);
  logic [2559:0] acc;
  logic [2:0]    n;
  logic          have;

  wire skip = am0 | am1 | am2 | am3;
  assign beat_vld  = have;
  assign beat_data = acc[511:0];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc  <= 2560'd0;
      n    <= 3'd0;
      have <= 1'b0;
    end else begin
      if (have && beat_ready) begin
        acc  <= {512'd0, acc[2559:512]};
        have <= (n > 3'd1);
        if (n > 3'd0) n <= n - 3'd1;
      end
      if (lane_vld && !skip) begin
        acc[640*n +: 640] <= {lane3, lane2, lane1, lane0};
        if (n == 3'd3) begin
          n    <= 3'd4;
          have <= 1'b1;
        end else if (!have) begin
          n <= n + 3'd1;
        end
      end
    end
  end
endmodule
