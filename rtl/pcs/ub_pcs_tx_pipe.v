//-----------------------------------------------------------------------------
// Module: ub_pcs_tx_pipe
// PCS TX pipeline top module.
// DL clock domain: gearbox(640b->FEC->512b) -> per-lane scramble(4x128b)
//                  -> AMCTL insertion(4x128b)
// CDC crossing: per-lane async FIFO (DL 1.25GHz -> PCS 921.875MHz)
// PCS clock domain: gray coder -> SerDes output (4x128b)
//-----------------------------------------------------------------------------
module ub_pcs_tx_pipe (
    input  wire          dl_clk,
    input  wire          dl_rst_n,
    input  wire          pcs_clk,
    input  wire          pcs_rst_n,
    // 640-bit flit input (DL clock domain, from DLL TX engine)
    input  wire [639:0]  flit_in,
    input  wire          flit_valid,
    output wire          flit_ready,
    // SerDes output (PCS clock domain, 4 lanes x 128 bits)
    output wire [127:0]  serdes_lane0,
    output wire [127:0]  serdes_lane1,
    output wire [127:0]  serdes_lane2,
    output wire [127:0]  serdes_lane3,
    output wire          serdes_valid,
    // Control
    input  wire          training_mode,
    input  wire          en
);

    //=========================================================================
    // DL Clock Domain (1.25 GHz)
    //=========================================================================

    // --- TX Gearbox: 640b flit -> FEC -> 2x512b ---
    wire [511:0] gb_data;
    wire         gb_valid;
    wire         gb_ready;

    ub_pcs_tx_gearbox u_tx_gearbox (
        .clk           (dl_clk),
        .rst_n         (dl_rst_n),
        .flit_in       (flit_in),
        .flit_valid    (flit_valid),
        .flit_ready    (flit_ready),
        .data_out      (gb_data),
        .data_valid_out(gb_valid),
        .data_ready_in (gb_ready)
    );

    // --- Split 512b -> 4x128b for per-lane scramble ---
    wire [127:0] pre_scram_lane0 = gb_data[127:0];
    wire [127:0] pre_scram_lane1 = gb_data[255:128];
    wire [127:0] pre_scram_lane2 = gb_data[383:256];
    wire [127:0] pre_scram_lane3 = gb_data[511:384];

    // --- Per-lane scramblers ---
    wire [127:0] scram_lane0, scram_lane1, scram_lane2, scram_lane3;
    wire         scram_valid0, scram_valid1, scram_valid2, scram_valid3;

    ub_pcs_scrambler_lane u_scram0 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(pre_scram_lane0), .valid_in(gb_valid),
        .data_out(scram_lane0), .valid_out(scram_valid0)
    );
    ub_pcs_scrambler_lane u_scram1 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(pre_scram_lane1), .valid_in(gb_valid),
        .data_out(scram_lane1), .valid_out(scram_valid1)
    );
    ub_pcs_scrambler_lane u_scram2 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(pre_scram_lane2), .valid_in(gb_valid),
        .data_out(scram_lane2), .valid_out(scram_valid2)
    );
    ub_pcs_scrambler_lane u_scram3 (
        .clk(dl_clk), .rst_n(dl_rst_n),
        .data_in(pre_scram_lane3), .valid_in(gb_valid),
        .data_out(scram_lane3), .valid_out(scram_valid3)
    );

    // --- AMCTL insertion (per-lane, 128b each) ---
    wire [127:0] amctl_lane0, amctl_lane1, amctl_lane2, amctl_lane3;
    wire         amctl_valid;
    wire         amctl_ready;

    ub_pcs_amctl_gen_wide u_amctl (
        .clk           (dl_clk),
        .rst_n         (dl_rst_n),
        .en            (en),
        .training_mode (training_mode),
        .lane0_data_in (scram_lane0),
        .lane1_data_in (scram_lane1),
        .lane2_data_in (scram_lane2),
        .lane3_data_in (scram_lane3),
        .data_valid_in (scram_valid0),
        .lane0_data_out(amctl_lane0),
        .lane1_data_out(amctl_lane1),
        .lane2_data_out(amctl_lane2),
        .lane3_data_out(amctl_lane3),
        .data_valid_out(amctl_valid),
        .ready         (amctl_ready)
    );

    // Backpressure: gearbox ready when AMCTL is ready
    assign gb_ready = amctl_ready;

    //=========================================================================
    // CDC: Per-lane async FIFO (DL -> PCS)
    //=========================================================================
    wire [127:0] cdc_lane0, cdc_lane1, cdc_lane2, cdc_lane3;
    wire         cdc_empty0, cdc_empty1, cdc_empty2, cdc_empty3;
    wire         cdc_full0, cdc_full1, cdc_full2, cdc_full3;

    // Read enable: all lanes read together when none empty
    wire cdc_all_valid = !cdc_empty0 && !cdc_empty1 && !cdc_empty2 && !cdc_empty3;
    wire cdc_rd_en = cdc_all_valid;

    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_tx0 (
        .wr_clk(dl_clk), .wr_rst_n(dl_rst_n),
        .wr_data(amctl_lane0), .wr_en(amctl_valid && !cdc_full0), .wr_full(cdc_full0),
        .rd_clk(pcs_clk), .rd_rst_n(pcs_rst_n),
        .rd_data(cdc_lane0), .rd_en(cdc_rd_en), .rd_empty(cdc_empty0)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_tx1 (
        .wr_clk(dl_clk), .wr_rst_n(dl_rst_n),
        .wr_data(amctl_lane1), .wr_en(amctl_valid && !cdc_full1), .wr_full(cdc_full1),
        .rd_clk(pcs_clk), .rd_rst_n(pcs_rst_n),
        .rd_data(cdc_lane1), .rd_en(cdc_rd_en), .rd_empty(cdc_empty1)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_tx2 (
        .wr_clk(dl_clk), .wr_rst_n(dl_rst_n),
        .wr_data(amctl_lane2), .wr_en(amctl_valid && !cdc_full2), .wr_full(cdc_full2),
        .rd_clk(pcs_clk), .rd_rst_n(pcs_rst_n),
        .rd_data(cdc_lane2), .rd_en(cdc_rd_en), .rd_empty(cdc_empty2)
    );
    ub_cdc_async_fifo #(.DATA_WIDTH(128), .ADDR_WIDTH(4)) u_cdc_tx3 (
        .wr_clk(dl_clk), .wr_rst_n(dl_rst_n),
        .wr_data(amctl_lane3), .wr_en(amctl_valid && !cdc_full3), .wr_full(cdc_full3),
        .rd_clk(pcs_clk), .rd_rst_n(pcs_rst_n),
        .rd_data(cdc_lane3), .rd_en(cdc_rd_en), .rd_empty(cdc_empty3)
    );

    //=========================================================================
    // PCS Clock Domain (921.875 MHz)
    //=========================================================================

    // --- Gray coding (combinational, per-lane) ---
    ub_pcs_gray_coder_lane u_gray0 (.data_in(cdc_lane0), .data_out(serdes_lane0));
    ub_pcs_gray_coder_lane u_gray1 (.data_in(cdc_lane1), .data_out(serdes_lane1));
    ub_pcs_gray_coder_lane u_gray2 (.data_in(cdc_lane2), .data_out(serdes_lane2));
    ub_pcs_gray_coder_lane u_gray3 (.data_in(cdc_lane3), .data_out(serdes_lane3));

    assign serdes_valid = cdc_all_valid;

endmodule
