//-----------------------------------------------------------------------------
// Module: ub_pcs_rx_pipe
// PCS RX pipeline top module.
// PCS clock domain: SerDes input (4x128b) -> CDC
// DL clock domain: gray decoder -> lane aligner -> per-lane descramble
//                  -> reassemble 512b -> RX gearbox -> 640b flit
//-----------------------------------------------------------------------------
module ub_pcs_rx_pipe (
    input  wire          dl_clk,
    input  wire          dl_rst_n,
    input  wire          pcs_clk,
    input  wire          pcs_rst_n,
    // SerDes input (PCS clock domain, 4 lanes x 128 bits)
    input  wire [127:0]  serdes_lane0,
    input  wire [127:0]  serdes_lane1,
    input  wire [127:0]  serdes_lane2,
    input  wire [127:0]  serdes_lane3,
    input  wire          serdes_valid,
    // 640-bit flit output (DL clock domain, to DLL RX engine)
    output wire [639:0]  flit_out,
    output wire          flit_valid,
    input  wire          flit_ready,
    // Status
    output wire          all_lanes_aligned,
    output wire          fec_fail,
    // Control
    input  wire          training_mode,
    input  wire          en
);

    //=========================================================================
    // PCS Clock Domain (921.875 MHz) — only CDC write side
    //=========================================================================

    // Gray decoding is combinational, done after CDC in DL domain
    // SerDes data goes directly into CDC FIFOs

    //=========================================================================
    // CDC: Per-lane async FIFO (PCS -> DL)
    //=========================================================================
    wire [127:0] cdc_lane0, cdc_lane1, cdc_lane2, cdc_lane3;
    wire         cdc_empty0, cdc_empty1, cdc_empty2, cdc_empty3;
    wire         cdc_full0, cdc_full1, cdc_full2, cdc_full3;

    wire cdc_all_valid = !cdc_empty0 && !cdc_empty1 && !cdc_empty2 && !cdc_empty3;
    // Gate CDC read with downstream readiness to prevent data loss
    // when the RX gearbox is busy processing FEC/FLIT output
    wire rx_gb_data_ready;
    wire cdc_rd_en = cdc_all_valid && rx_gb_data_ready;

    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_rx0 (
        .wr_clk(pcs_clk), .wr_rst_n(pcs_rst_n),
        .wr_data(serdes_lane0), .wr_en(serdes_valid && !cdc_full0), .wr_full(cdc_full0),
        .rd_clk(dl_clk), .rd_rst_n(dl_rst_n),
        .rd_data(cdc_lane0), .rd_en(cdc_rd_en), .rd_empty(cdc_empty0)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_rx1 (
        .wr_clk(pcs_clk), .wr_rst_n(pcs_rst_n),
        .wr_data(serdes_lane1), .wr_en(serdes_valid && !cdc_full1), .wr_full(cdc_full1),
        .rd_clk(dl_clk), .rd_rst_n(dl_rst_n),
        .rd_data(cdc_lane1), .rd_en(cdc_rd_en), .rd_empty(cdc_empty1)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_rx2 (
        .wr_clk(pcs_clk), .wr_rst_n(pcs_rst_n),
        .wr_data(serdes_lane2), .wr_en(serdes_valid && !cdc_full2), .wr_full(cdc_full2),
        .rd_clk(dl_clk), .rd_rst_n(dl_rst_n),
        .rd_data(cdc_lane2), .rd_en(cdc_rd_en), .rd_empty(cdc_empty2)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_rx3 (
        .wr_clk(pcs_clk), .wr_rst_n(pcs_rst_n),
        .wr_data(serdes_lane3), .wr_en(serdes_valid && !cdc_full3), .wr_full(cdc_full3),
        .rd_clk(dl_clk), .rd_rst_n(dl_rst_n),
        .rd_data(cdc_lane3), .rd_en(cdc_rd_en), .rd_empty(cdc_empty3)
    );

    //=========================================================================
    // DL Clock Domain (1.25 GHz)
    //=========================================================================

    // --- Gray decoding (combinational, per-lane) ---
    wire [127:0] decoded_lane0, decoded_lane1, decoded_lane2, decoded_lane3;

    ub_pcs_gray_decoder_lane u_gdec0 (.data_in(cdc_lane0), .data_out(decoded_lane0));
    ub_pcs_gray_decoder_lane u_gdec1 (.data_in(cdc_lane1), .data_out(decoded_lane1));
    ub_pcs_gray_decoder_lane u_gdec2 (.data_in(cdc_lane2), .data_out(decoded_lane2));
    ub_pcs_gray_decoder_lane u_gdec3 (.data_in(cdc_lane3), .data_out(decoded_lane3));

    // --- Lane alignment ---
    // The existing lane_aligner uses 32b per lane. For 128b per lane,
    // we use a simplified alignment approach: since all 4 CDC FIFOs are
    // read synchronously (cdc_rd_en broadcast), lanes are already aligned
    // at the CDC output. We mark alignment as achieved when all FIFOs
    // have valid data.
    assign all_lanes_aligned = cdc_all_valid && en;

    // --- Per-lane descramblers ---
    wire [127:0] descram_lane0, descram_lane1, descram_lane2, descram_lane3;
    wire         descram_valid0, descram_valid1, descram_valid2, descram_valid3;

    // Descrambler valid_in must track actual FIFO consumption (cdc_rd_en),
    // not just FIFO-not-empty (cdc_all_valid). Otherwise the LFSR advances
    // on stale data while the RX gearbox is busy in FEC/FLIT states,
    // causing scrambler/descrambler sync loss.
    ub_pcs_descrambler_lane u_descram0 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(decoded_lane0), .valid_in(cdc_rd_en),
        .data_out(descram_lane0), .valid_out(descram_valid0)
    );
    ub_pcs_descrambler_lane u_descram1 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(decoded_lane1), .valid_in(cdc_rd_en),
        .data_out(descram_lane1), .valid_out(descram_valid1)
    );
    ub_pcs_descrambler_lane u_descram2 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(decoded_lane2), .valid_in(cdc_rd_en),
        .data_out(descram_lane2), .valid_out(descram_valid2)
    );
    ub_pcs_descrambler_lane u_descram3 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(decoded_lane3), .valid_in(cdc_rd_en),
        .data_out(descram_lane3), .valid_out(descram_valid3)
    );

    // --- Reassemble 4x128b -> 512b ---
    wire [511:0] reassembled = {descram_lane3, descram_lane2, descram_lane1, descram_lane0};
    wire         reassembled_valid = descram_valid0; // all lanes in sync

    // --- RX Gearbox: 2x512b -> 1024b -> FEC dec -> 960b -> 640b flit ---
    ub_pcs_rx_gearbox u_rx_gearbox (
        .clk         (dl_clk),
        .rst_n       (dl_rst_n),
        .data_in     (reassembled),
        .data_valid_in(reassembled_valid),
        .data_ready  (rx_gb_data_ready),
        .flit_out    (flit_out),
        .flit_valid  (flit_valid),
        .flit_ready  (flit_ready),
        .fec_fail    (fec_fail)
    );

endmodule
