//-----------------------------------------------------------------------------
// Testbench: ub_pcs_tx_rx_loopback_tb
// Full PCS TX→RX loopback: feed 640b flits into TX pipe, loopback serdes
// lanes to RX pipe, verify output flits match input data.
// AMCTL disabled (en=0) for clean data pass-through.
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module ub_pcs_tx_rx_loopback_tb;

    localparam DL_CLK_PERIOD  = 0.8;    // 1.25 GHz
    localparam PCS_CLK_PERIOD = 1.143;  // 875 MHz

    reg dl_clk, pcs_clk;
    reg dl_rst_n, pcs_rst_n;

    // TX pipe interface
    reg  [639:0] tx_flit_in;
    reg          tx_flit_valid;
    wire         tx_flit_ready;

    // Serdes loopback wires
    wire [127:0] tx_lane0, tx_lane1, tx_lane2, tx_lane3;
    wire         tx_serdes_valid;

    // RX pipe interface
    wire [639:0] rx_flit_out;
    wire         rx_flit_valid;
    reg          rx_flit_ready;

    // Status
    wire all_lanes_aligned;
    wire fec_fail;

    //-------------------------------------------------------------------------
    // DUT: TX pipe -> loopback -> RX pipe
    //-------------------------------------------------------------------------
    ub_pcs_tx_pipe u_tx_pipe (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .flit_in(tx_flit_in),
        .flit_valid(tx_flit_valid),
        .flit_ready(tx_flit_ready),
        .serdes_lane0(tx_lane0),
        .serdes_lane1(tx_lane1),
        .serdes_lane2(tx_lane2),
        .serdes_lane3(tx_lane3),
        .serdes_valid(tx_serdes_valid),
        .training_mode(1'b0),
        .en(1'b0)
    );

    ub_pcs_rx_pipe u_rx_pipe (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .serdes_lane0(tx_lane0),
        .serdes_lane1(tx_lane1),
        .serdes_lane2(tx_lane2),
        .serdes_lane3(tx_lane3),
        .serdes_valid(tx_serdes_valid),
        .flit_out(rx_flit_out),
        .flit_valid(rx_flit_valid),
        .flit_ready(rx_flit_ready),
        .all_lanes_aligned(all_lanes_aligned),
        .fec_fail(fec_fail),
        .training_mode(1'b0),
        .en(1'b1)
    );

    //-------------------------------------------------------------------------
    // Clock generation
    //-------------------------------------------------------------------------
    initial dl_clk = 0;
    always #(DL_CLK_PERIOD/2) dl_clk = ~dl_clk;

    initial pcs_clk = 0;
    always #(PCS_CLK_PERIOD/2) pcs_clk = ~pcs_clk;

    //-------------------------------------------------------------------------
    // Test data and scoreboard
    //-------------------------------------------------------------------------
    reg [639:0] test_flits [0:2];
    integer errors;
    integer rx_count;

    initial begin
        // Test flit patterns (full 640-bit)
        test_flits[0] = 640'hAAAA_BBBB_CCCC_DDDD_EEEE_1111_2222_3332_2222_1111_EEEE_DDDD_CCCC_BBBB_AAAA_0000_5555_6666_7777_8888_9999_AAAA_BBBB_CCCC_1234_5678_9ABC_DEF0_0FED_CBA9_8765_4321_DEAD_BEEF_CAFE_BABA_55AA_CC33_33CC_AA55;
        test_flits[1] = 640'h1234_5678_9ABC_DEF0_0FED_CBA9_8765_4321_1234_5678_9ABC_DEF0_0FED_CBA9_8765_4321_AAAA_BBBB_CCCC_DDDD_EEEE_FFFF_0000_1111_2222_3333_4444_5555_6666_7777_8888_9999_CAFE_BABE_DEAD_BEEF_1234_5678_9ABC_DEF0;
        test_flits[2] = 640'hDEAD_BEEF_CAFE_BABA_0BAD_F00D_1CE0_B00B_1337_C0DE_600D_F00B_A555_1234_5678_9AB0_F00F_E00E_D00D_C00C_B00B_A00A_9009_8008_7007_6006_5005_4004_3003_2002_1001_0000_FFFF_EEEE_DDDD_CCCC_BBBB_AAAA_9999_8888;

        // Initialize
        tx_flit_in    = 640'd0;
        tx_flit_valid = 1'b0;
        rx_flit_ready = 1'b1;
        errors   = 0;
        rx_count = 0;

        // Reset
        dl_rst_n  = 1'b0;
        pcs_rst_n = 1'b0;
        repeat(10) @(posedge dl_clk);
        dl_rst_n  = 1'b1;
        pcs_rst_n = 1'b1;
        repeat(5) @(posedge dl_clk);

        $display("PCS TX->RX Loopback Test");

        // Flit 0
        tx_flit_in    = test_flits[0];
        tx_flit_valid = 1'b1;
        @(posedge dl_clk);

        // Flit 1
        tx_flit_in    = test_flits[1];
        @(posedge dl_clk);
        tx_flit_valid = 1'b0;

        // Wait for ACC2
        while (!tx_flit_ready) @(posedge dl_clk);

        // Flit 2
        tx_flit_in    = test_flits[2];
        tx_flit_valid = 1'b1;
        @(posedge dl_clk);
        tx_flit_valid = 1'b0;

        //-------------------------------------------------------------
        // Receive and check 3 flits
        //-------------------------------------------------------------
        while (rx_count < 3) begin
            @(posedge dl_clk);
            if (rx_flit_valid && rx_flit_ready) begin
                if (rx_flit_out !== test_flits[rx_count]) begin
                    $display("  FAIL flit %0d:", rx_count);
                    $display("    expected: %h", test_flits[rx_count]);
                    $display("    got:      %h", rx_flit_out);
                    errors = errors + 1;
                end else begin
                    $display("  PASS flit %0d: data matches", rx_count);
                end
                rx_count = rx_count + 1;
            end
        end

        repeat(5) @(posedge dl_clk);
        if (errors == 0 && !fec_fail)
            $display("\nPCS LOOPBACK PASS: all 3 flits matched, no FEC errors.");
        else if (fec_fail)
            $display("\nPCS LOOPBACK FAIL: FEC error detected.");
        else
            $display("\nPCS LOOPBACK FAIL: %0d flit mismatch(es).", errors);
        $finish;
    end

    // Timeout
    initial begin
        #200000;
        $display("TIMEOUT: only received %0d/3 flits", rx_count);
        $finish;
    end

endmodule
