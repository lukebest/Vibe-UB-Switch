//-----------------------------------------------------------------------------
// Module: ub_pcs_descrambler_lane
// Per-lane 128-bit descrambler. Same LFSR as scrambler_lane.
//-----------------------------------------------------------------------------
module ub_pcs_descrambler_lane (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [127:0] data_in,
    input  wire         valid_in,
    output reg  [127:0] data_out,
    output reg          valid_out
);

    reg [57:0] lfsr;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lfsr      <= 58'h3FFFFFFFFFFFFFF;
            data_out  <= 128'd0;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            for (i = 0; i < 128; i = i + 1) begin
                data_out[i] <= data_in[i] ^ lfsr[57];
                lfsr <= {lfsr[56:0], lfsr[57] ^ lfsr[38]};
            end
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end

endmodule
