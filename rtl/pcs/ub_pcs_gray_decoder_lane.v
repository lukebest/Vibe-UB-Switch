//-----------------------------------------------------------------------------
// Module: ub_pcs_gray_decoder_lane
// 128-bit per-lane Gray decoder: 64 x 2-bit PAM4 symbol Gray decoding.
// Combinational — no clock or reset.
//-----------------------------------------------------------------------------
module ub_pcs_gray_decoder_lane (
    input  wire [127:0] data_in,
    output wire [127:0] data_out
);

    genvar i;
    generate
        for (i = 0; i < 64; i = i + 1) begin : gen_gd
            ub_pcs_gray_decoder u_gd (
                .symbols (data_in[i*2 +: 2]),
                .bits    (data_out[i*2 +: 2])
            );
        end
    endgenerate

endmodule
