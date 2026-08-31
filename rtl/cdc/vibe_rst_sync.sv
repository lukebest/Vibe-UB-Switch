// AS-0.1 §3: async assert, sync deassert into a destination clock.
module vibe_rst_sync (
  input  logic clk,
  input  logic rst_n_in,
  output logic rst_n_out
);
  logic r1;
  always @(posedge clk or negedge rst_n_in) begin
    if (!rst_n_in) begin
      r1        <= 1'b0;
      rst_n_out <= 1'b0;
    end else begin
      r1        <= 1'b1;
      rst_n_out <= r1;
    end
  end
endmodule
