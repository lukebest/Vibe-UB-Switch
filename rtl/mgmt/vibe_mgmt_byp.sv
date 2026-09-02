// AS-0.1 §14: mgmt bypass FIFO 16×512b. Does not enter xbar.
module vibe_mgmt_byp #(
  parameter int DEPTH = 16
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [511:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [511:0] out_data,
  output logic         out_vld,
  input  logic         out_ready
);
  logic [511:0] mem [0:DEPTH-1];
  logic [4:0]   wptr, rptr;
  assign in_ready = ((wptr + 5'd1) != rptr);
  assign out_vld  = (wptr != rptr);
  assign out_data = mem[rptr[3:0]];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 5'd0;
      rptr <= 5'd0;
    end else begin
      if (in_vld && in_ready) begin
        mem[wptr[3:0]] <= in_data;
        wptr <= wptr + 5'd1;
      end
      if (out_vld && out_ready)
        rptr <= rptr + 5'd1;
    end
  end
endmodule
