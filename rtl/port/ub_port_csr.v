//-----------------------------------------------------------------------------
// Module: ub_port_csr
// Per-port CSR block wrapping ub_nw_csr with port-level status registers.
//-----------------------------------------------------------------------------
module ub_port_csr (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        csr_wen,
    input  wire [15:0] csr_wdata,
    output wire [15:0] local_scna,
    // Status inputs
    input  wire        link_up,
    input  wire        link_ready,
    input  wire        all_lanes_aligned,
    input  wire        fec_fail,
    // Status output (read-only)
    output wire [15:0] port_status
);

    ub_nw_csr u_nw_csr (
        .clk        (clk),
        .rst_n      (rst_n),
        .reg_wen    (csr_wen),
        .reg_wdata  (csr_wdata),
        .local_scna (local_scna)
    );

    assign port_status = {12'd0, fec_fail, all_lanes_aligned, link_ready, link_up};

endmodule
