// AS-0.1 §6: deskew on AMCTL. Factory physical=logical; no lane swap (U24).
module vibe_pcs_rx_deskew (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [159:0] in0,
  input  logic [159:0] in1,
  input  logic [159:0] in2,
  input  logic [159:0] in3,
  input  logic         in_vld,
  input  logic         am0,
  input  logic         am1,
  input  logic         am2,
  input  logic         am3,
  output logic [159:0] out0,
  output logic [159:0] out1,
  output logic [159:0] out2,
  output logic [159:0] out3,
  output logic         out_vld,
  output logic         aligned
);
  logic [159:0] f0[0:7];
  logic [159:0] f1[0:7];
  logic [159:0] f2[0:7];
  logic [159:0] f3[0:7];
  logic [2:0]   wptr;
  logic [2:0]   a0, a1, a2, a3;
  logic         saw0, saw1, saw2, saw3;
  logic         am0_r, am1_r, am2_r, am3_r;

  assign aligned = saw0 & saw1 & saw2 & saw3;
  assign out_vld = in_vld && aligned && !(am0|am1|am2|am3);
  // Factory physical=logical (U24): no delay once aligned. FIFO pointers
  // only record first-AMCTL lock; feeding them as out would leak the second
  // AMCTL 160b into the 512b stream after each marker.
  assign out0 = in0;
  assign out1 = in1;
  assign out2 = in2;
  assign out3 = in3;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 3'd0;
      a0 <= 3'd0; a1 <= 3'd0; a2 <= 3'd0; a3 <= 3'd0;
      saw0 <= 1'b0; saw1 <= 1'b0; saw2 <= 1'b0; saw3 <= 1'b0;
      am0_r <= 1'b0; am1_r <= 1'b0; am2_r <= 1'b0; am3_r <= 1'b0;
    end else if (in_vld) begin
      f0[wptr] <= in0;
      f1[wptr] <= in1;
      f2[wptr] <= in2;
      f3[wptr] <= in3;
      // Latch delay on the first AMCTL 160b only. The second word would
      // shift the pointer so the next data beat reads AMCTL out of the FIFO.
      if (am0 && !am0_r) begin a0 <= wptr; saw0 <= 1'b1; end
      if (am1 && !am1_r) begin a1 <= wptr; saw1 <= 1'b1; end
      if (am2 && !am2_r) begin a2 <= wptr; saw2 <= 1'b1; end
      if (am3 && !am3_r) begin a3 <= wptr; saw3 <= 1'b1; end
      am0_r <= am0; am1_r <= am1; am2_r <= am2; am3_r <= am3;
      wptr <= wptr + 3'd1;
    end
  end
endmodule
