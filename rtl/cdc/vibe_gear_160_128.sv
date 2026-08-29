// AS-0.1 §5 T7: TX read-domain 160→128 residue gearbox. 4×160 = 5×128.
module vibe_gear_160_128 (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  output logic         in_ready,
  input  logic [159:0] in_data,
  output logic         out_vld,
  input  logic         out_ready,
  output logic [127:0] out_data
);
  logic [127:0] res;
  logic [2:0]   rbits; // 0,1,2,3,4 → 0/32/64/96/128 bits valid in res[127:0]
  logic [127:0] hold;
  logic         hold_vld;

  wire take_out = hold_vld && out_ready;
  wire can_load = !hold_vld || out_ready;

  // Need input unless residue already holds a full 128-bit beat (rbits==4).
  assign in_ready = can_load && (rbits != 3'd4);
  assign out_vld  = hold_vld;
  assign out_data = hold;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      res      <= 128'd0;
      rbits    <= 3'd0;
      hold     <= 128'd0;
      hold_vld <= 1'b0;
    end else begin
      if (take_out)
        hold_vld <= 1'b0;

      if (rbits == 3'd4 && can_load) begin
        hold     <= res;
        hold_vld <= 1'b1;
        res      <= 128'd0;
        rbits    <= 3'd0;
      end else if (in_vld && in_ready) begin
        case (rbits)
          3'd0: begin
            hold     <= in_data[127:0];
            res      <= {96'd0, in_data[159:128]};
            hold_vld <= 1'b1;
            rbits    <= 3'd1;
          end
          3'd1: begin
            hold     <= {in_data[95:0], res[31:0]};
            res      <= {64'd0, in_data[159:96]};
            hold_vld <= 1'b1;
            rbits    <= 3'd2;
          end
          3'd2: begin
            hold     <= {in_data[63:0], res[63:0]};
            res      <= {32'd0, in_data[159:64]};
            hold_vld <= 1'b1;
            rbits    <= 3'd3;
          end
          default: begin // 3
            hold     <= {in_data[31:0], res[95:0]};
            res      <= in_data[159:32];
            hold_vld <= 1'b1;
            rbits    <= 3'd4;
          end
        endcase
      end
    end
  end
endmodule
