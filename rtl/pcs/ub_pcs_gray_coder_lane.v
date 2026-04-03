//-----------------------------------------------------------------------------
// Module: ub_pcs_gray_coder_lane
// 128-bit per-lane Gray coder: 64 x 2-bit PAM4 symbol Gray encoding.
// Combinational — no clock or reset.
//-----------------------------------------------------------------------------
module ub_pcs_gray_coder_lane (
    input  wire [127:0] data_in,
    output wire [127:0] data_out
);

    genvar i;
    generate
        for (i = 0; i < 64; i = i + 1) begin : gen_gc
            ub_pcs_gray_coder u_gc (
                .bits    (data_in[i*2 +: 2]),
                .symbols (data_out[i*2 +: 2])
            );
        end
    endgenerate

endmodule
