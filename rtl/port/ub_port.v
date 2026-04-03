//-----------------------------------------------------------------------------
// Module: ub_port
// Single UB port: NW + DLL engines + PCS TX/RX pipes (with CDC) + LMSM.
// Dual clock domain: dl_clk (1.25 GHz) and pcs_clk (921.875 MHz).
//-----------------------------------------------------------------------------
module ub_port #(
    parameter [15:0] DEFAULT_SCNA = 16'h0001
)(
    // Clocks
    input  wire          dl_clk,
    input  wire          dl_rst_n,
    input  wire          pcs_clk,
    input  wire          pcs_rst_n,
    // Packet interface to/from crossbar (DL clock domain, 512-bit)
    input  wire [511:0]  tx_pkt_data,
    input  wire          tx_pkt_valid,
    input  wire          tx_pkt_sop,
    input  wire          tx_pkt_eop,
    output wire          tx_pkt_ready,
    output wire [511:0]  rx_pkt_data,
    output wire          rx_pkt_valid,
    output wire          rx_pkt_sop,
    output wire          rx_pkt_eop,
    // SerDes interface (PCS clock domain, 4 x 128-bit lanes)
    output wire [127:0]  serdes_tx_lane0,
    output wire [127:0]  serdes_tx_lane1,
    output wire [127:0]  serdes_tx_lane2,
    output wire [127:0]  serdes_tx_lane3,
    output wire          serdes_tx_valid,
    input  wire [127:0]  serdes_rx_lane0,
    input  wire [127:0]  serdes_rx_lane1,
    input  wire [127:0]  serdes_rx_lane2,
    input  wire [127:0]  serdes_rx_lane3,
    input  wire          serdes_rx_valid,
    // CSR
    input  wire          csr_wen,
    input  wire [15:0]   csr_wdata,
    output wire [15:0]   local_scna,
    // Status
    output wire          link_up,
    output wire          link_ready,
    output wire          all_lanes_aligned,
    output wire          fec_fail,
    // Control
    input  wire          training_mode,
    input  wire          start_train
);

    //=========================================================================
    // CSR
    //=========================================================================
    wire [15:0] port_status;

    ub_port_csr u_csr (
        .clk              (dl_clk),
        .rst_n            (dl_rst_n),
        .csr_wen          (csr_wen),
        .csr_wdata        (csr_wdata),
        .local_scna       (local_scna),
        .link_up          (link_up),
        .link_ready       (link_ready),
        .all_lanes_aligned(all_lanes_aligned),
        .fec_fail         (fec_fail),
        .port_status      (port_status)
    );

    //=========================================================================
    // LMSM (DL clock domain)
    //=========================================================================
    wire [159:0] lmsm_tx_flit;
    wire         lmsm_link_up;
    wire         lmsm_link_ready;

    ub_pcs_lmsm u_lmsm (
        .clk          (dl_clk),
        .rst_n        (dl_rst_n),
        .start_train  (start_train),
        .rx_flit_in   (160'd0),    // simplified: no LMSM RX feedback in this version
        .rx_flit_valid(1'b0),
        .tx_flit_out  (lmsm_tx_flit),
        .link_up      (lmsm_link_up),
        .link_ready   (lmsm_link_ready),
        .state_dbg    ()
    );

    assign link_up    = lmsm_link_up;
    assign link_ready = lmsm_link_ready;

    //=========================================================================
    // TX Path (DL clock domain -> PCS clock domain)
    //=========================================================================

    // --- NW TX: 512b pkt -> 640b flit ---
    // Simplified: pack 512b packet data into 640b flit with header
    // Flit format: {NTH[127:0], pkt_data[511:0]} = 640b
    // NTH is simplified: {16'd0, local_scna, 96'd0} = 128b placeholder
    wire [639:0] nw_tx_flit = {16'd0, local_scna, 96'd0, tx_pkt_data};
    wire         nw_tx_flit_valid = tx_pkt_valid && link_ready;
    wire         nw_tx_flit_sop   = tx_pkt_sop;
    wire         nw_tx_flit_eop   = tx_pkt_eop;
    wire         nw_tx_flit_ready;

    assign tx_pkt_ready = nw_tx_flit_ready && link_ready;

    // --- DLL TX Engine ---
    wire [639:0] dll_tx_flit;
    wire         dll_tx_flit_valid;
    wire         dll_tx_flit_ready;

    // Retry/flow control signals from RX engine
    wire         retry_req_from_rx;
    wire [7:0]   retry_rcvptr_from_rx;
    wire         ack_from_rx;
    wire [7:0]   ack_ptr_from_rx;
    wire         credit_return_from_rx;
    wire [7:0]   credit_return_amt_from_rx;

    ub_dll_tx_engine u_dll_tx (
        .clk               (dl_clk),
        .rst_n             (dl_rst_n),
        .link_ready        (link_ready),
        .nw_flit_in        (nw_tx_flit),
        .nw_flit_valid     (nw_tx_flit_valid),
        .nw_flit_sop       (nw_tx_flit_sop),
        .nw_flit_eop       (nw_tx_flit_eop),
        .nw_flit_ready     (nw_tx_flit_ready),
        .flit_out          (dll_tx_flit),
        .flit_valid        (dll_tx_flit_valid),
        .flit_ready        (dll_tx_flit_ready),
        .retry_req_received(retry_req_from_rx),
        .retry_rcvptr      (retry_rcvptr_from_rx),
        .ack_received      (ack_from_rx),
        .ack_ptr           (ack_ptr_from_rx),
        .credit_return     (credit_return_from_rx),
        .credit_return_amt (credit_return_amt_from_rx)
    );

    // --- PCS TX Pipe ---
    ub_pcs_tx_pipe u_pcs_tx (
        .dl_clk       (dl_clk),
        .dl_rst_n     (dl_rst_n),
        .pcs_clk      (pcs_clk),
        .pcs_rst_n    (pcs_rst_n),
        .flit_in      (dll_tx_flit),
        .flit_valid   (dll_tx_flit_valid),
        .flit_ready   (dll_tx_flit_ready),
        .serdes_lane0 (serdes_tx_lane0),
        .serdes_lane1 (serdes_tx_lane1),
        .serdes_lane2 (serdes_tx_lane2),
        .serdes_lane3 (serdes_tx_lane3),
        .serdes_valid (serdes_tx_valid),
        .training_mode(training_mode),
        .en           (link_ready)
    );

    //=========================================================================
    // RX Path (PCS clock domain -> DL clock domain)
    //=========================================================================

    // --- PCS RX Pipe ---
    wire [639:0] pcs_rx_flit;
    wire         pcs_rx_flit_valid;

    ub_pcs_rx_pipe u_pcs_rx (
        .dl_clk          (dl_clk),
        .dl_rst_n        (dl_rst_n),
        .pcs_clk         (pcs_clk),
        .pcs_rst_n       (pcs_rst_n),
        .serdes_lane0    (serdes_rx_lane0),
        .serdes_lane1    (serdes_rx_lane1),
        .serdes_lane2    (serdes_rx_lane2),
        .serdes_lane3    (serdes_rx_lane3),
        .serdes_valid    (serdes_rx_valid),
        .flit_out        (pcs_rx_flit),
        .flit_valid      (pcs_rx_flit_valid),
        .flit_ready      (1'b1),
        .all_lanes_aligned(all_lanes_aligned),
        .fec_fail        (fec_fail),
        .training_mode   (training_mode),
        .en              (1'b1)
    );

    // --- DLL RX Engine ---
    wire [639:0] dll_rx_nw_flit;
    wire         dll_rx_nw_flit_valid;
    wire         dll_rx_nw_flit_sop;
    wire         dll_rx_nw_flit_eop;

    ub_dll_rx_engine u_dll_rx (
        .clk                  (dl_clk),
        .rst_n                (dl_rst_n),
        .flit_in              (pcs_rx_flit),
        .flit_valid           (pcs_rx_flit_valid),
        .nw_flit_out          (dll_rx_nw_flit),
        .nw_flit_valid        (dll_rx_nw_flit_valid),
        .nw_flit_sop          (dll_rx_nw_flit_sop),
        .nw_flit_eop          (dll_rx_nw_flit_eop),
        .nw_flit_ready        (1'b1),
        .retry_req_to_send    (retry_req_from_rx),
        .retry_rcvptr         (retry_rcvptr_from_rx),
        .ack_to_send          (ack_from_rx),
        .ack_ptr              (ack_ptr_from_rx),
        .credit_return_to_send(credit_return_from_rx),
        .credit_return_amt    (credit_return_amt_from_rx)
    );

    // --- NW RX: extract 512b packet from 640b flit ---
    assign rx_pkt_data  = dll_rx_nw_flit[511:0];
    assign rx_pkt_valid = dll_rx_nw_flit_valid;
    assign rx_pkt_sop   = dll_rx_nw_flit_sop;
    assign rx_pkt_eop   = dll_rx_nw_flit_eop;

endmodule
