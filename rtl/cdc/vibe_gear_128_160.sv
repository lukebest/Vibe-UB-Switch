// AS-0.1 §6/§7: RX 128→160 dual-residue gearbox. 5×128 = 4×160.
module vibe_gear_128_160 (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  output logic         in_ready,
  input  logic [127:0] in_data,
  output logic         out_vld,
  input  logic         out_ready,
  output logic [159:0] out_data
);
  logic [127:0] res_a;
  logic [127:0] res_b;
  logic [2:0]   phase; // 0..4 inputs in a 5-beat group
  logic [159:0] hold;
  logic         hold_vld;

  assign out_vld  = hold_vld;
  assign out_data = hold;
  assign in_ready = !hold_vld || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      res_a    <= 128'd0;
      res_b    <= 128'd0;
      phase    <= 3'd0;
      hold     <= 160'd0;
      hold_vld <= 1'b0;
    end else begin
      if (hold_vld && out_ready)
        hold_vld <= 1'b0;
      if (in_vld && in_ready) begin
        case (phase)
          3'd0: begin
            res_a <= in_data;
            phase <= 3'd1;
          end
          3'd1: begin
            hold     <= {in_data[31:0], res_a};
            res_b    <= {32'd0, in_data[127:32]};
            hold_vld <= 1'b1;
            phase    <= 3'd2;
          end
          3'd2: begin
            hold     <= {in_data[63:0], res_b[95:0]};
            res_a    <= {64'd0, in_data[127:64]};
            hold_vld <= 1'b1;
            phase    <= 3'd3;
          end
          3'd3: begin
            hold     <= {in_data[95:0], res_a[63:0]};
            res_b    <= {96'd0, in_data[127:96]};
            hold_vld <= 1'b1;
            phase    <= 3'd4;
          end
          default: begin
            hold     <= {in_data, res_b[31:0]};
            hold_vld <= 1'b1;
            res_a    <= 128'd0;
            res_b    <= 128'd0;
            phase    <= 3'd0;
          end
        endcase
      end
    end
  end
endmodule
