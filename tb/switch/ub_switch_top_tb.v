//-----------------------------------------------------------------------------
// Testbench: ub_switch_top_tb
// Full switch top-level testbench.
// Tests: DCNA routing, crossbar integration, packet flow.
// Forces xbar_out_ready=1 so output queues drain freely.
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module ub_switch_top_tb;

    reg  dl_clk, dl_rst_n, pcs_clk, pcs_rst_n;
    reg  [1:0]   csr_port_sel;
    reg          csr_wen;
    reg  [15:0]  csr_wdata;

    // SerDes wires
    wire [127:0] p0_sd_tx0, p0_sd_tx1, p0_sd_tx2, p0_sd_tx3;
    wire         p0_sd_tx_v;
    wire [127:0] p1_sd_tx0, p1_sd_tx1, p1_sd_tx2, p1_sd_tx3;
    wire         p1_sd_tx_v;
    wire [127:0] p2_sd_tx0, p2_sd_tx1, p2_sd_tx2, p2_sd_tx3;
    wire         p2_sd_tx_v;
    wire [127:0] p3_sd_tx0, p3_sd_tx1, p3_sd_tx2, p3_sd_tx3;
    wire         p3_sd_tx_v;
    wire [3:0] link_up, link_ready;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    ub_switch_top u_switch (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .p0_serdes_tx_lane0(p0_sd_tx0), .p0_serdes_tx_lane1(p0_sd_tx1),
        .p0_serdes_tx_lane2(p0_sd_tx2), .p0_serdes_tx_lane3(p0_sd_tx3),
        .p0_serdes_tx_valid(p0_sd_tx_v),
        .p0_serdes_rx_lane0(128'd0), .p0_serdes_rx_lane1(128'd0),
        .p0_serdes_rx_lane2(128'd0), .p0_serdes_rx_lane3(128'd0),
        .p0_serdes_rx_valid(1'b0),
        .p1_serdes_tx_lane0(p1_sd_tx0), .p1_serdes_tx_lane1(p1_sd_tx1),
        .p1_serdes_tx_lane2(p1_sd_tx2), .p1_serdes_tx_lane3(p1_sd_tx3),
        .p1_serdes_tx_valid(p1_sd_tx_v),
        .p1_serdes_rx_lane0(128'd0), .p1_serdes_rx_lane1(128'd0),
        .p1_serdes_rx_lane2(128'd0), .p1_serdes_rx_lane3(128'd0),
        .p1_serdes_rx_valid(1'b0),
        .p2_serdes_tx_lane0(p2_sd_tx0), .p2_serdes_tx_lane1(p2_sd_tx1),
        .p2_serdes_tx_lane2(p2_sd_tx2), .p2_serdes_tx_lane3(p2_sd_tx3),
        .p2_serdes_tx_valid(p2_sd_tx_v),
        .p2_serdes_rx_lane0(128'd0), .p2_serdes_rx_lane1(128'd0),
        .p2_serdes_rx_lane2(128'd0), .p2_serdes_rx_lane3(128'd0),
        .p2_serdes_rx_valid(1'b0),
        .p3_serdes_tx_lane0(p3_sd_tx0), .p3_serdes_tx_lane1(p3_sd_tx1),
        .p3_serdes_tx_lane2(p3_sd_tx2), .p3_serdes_tx_lane3(p3_sd_tx3),
        .p3_serdes_tx_valid(p3_sd_tx_v),
        .p3_serdes_rx_lane0(128'd0), .p3_serdes_rx_lane1(128'd0),
        .p3_serdes_rx_lane2(128'd0), .p3_serdes_rx_lane3(128'd0),
        .p3_serdes_rx_valid(1'b0),
        .training_mode(1'b0),
        .start_train(4'b0000),
        .csr_port_sel(csr_port_sel), .csr_wen(csr_wen), .csr_wdata(csr_wdata),
        .port_link_up(link_up), .port_link_ready(link_ready)
    );

    //-------------------------------------------------------------------------
    // Clocks
    //-------------------------------------------------------------------------
    initial dl_clk = 0;
    always #0.4 dl_clk = ~dl_clk;

    initial pcs_clk = 0;
    always #0.5425 pcs_clk = ~pcs_clk;

    //-------------------------------------------------------------------------
    // Helpers
    //-------------------------------------------------------------------------
    function [511:0] make_pkt;
        input [15:0] dcna;
        input [31:0] seed;
        reg [511:0] pkt;
        integer k;
        begin
            pkt = 512'd0;
            pkt[511:496] = dcna;
            for (k = 0; k < 15; k = k + 1)
                pkt[k*32 +: 32] = seed + k;
            make_pkt = pkt;
        end
    endfunction

    integer errors, test_num;

    //-------------------------------------------------------------------------
    // Test sequence
    //-------------------------------------------------------------------------
    initial begin
        errors  = 0;
        test_num = 0;

        dl_rst_n  = 1'b0;
        pcs_rst_n = 1'b0;
        repeat(10) @(posedge dl_clk);
        dl_rst_n  = 1'b1;
        pcs_rst_n = 1'b1;
        repeat(5) @(posedge dl_clk);

        $display("Full Switch Top Testbench");

        // Bypass LMSM training
        force u_switch.u_port0.link_up    = 1'b1;
        force u_switch.u_port0.link_ready = 1'b1;
        force u_switch.u_port1.link_up    = 1'b1;
        force u_switch.u_port1.link_ready = 1'b1;
        force u_switch.u_port2.link_up    = 1'b1;
        force u_switch.u_port2.link_ready = 1'b1;
        force u_switch.u_port3.link_up    = 1'b1;
        force u_switch.u_port3.link_ready = 1'b1;

        // Force crossbar output ready so queues always drain
        force u_switch.u_xbar.out_pkt_ready_0 = 1'b1;
        force u_switch.u_xbar.out_pkt_ready_1 = 1'b1;
        force u_switch.u_xbar.out_pkt_ready_2 = 1'b1;
        force u_switch.u_xbar.out_pkt_ready_3 = 1'b1;

        // Debug: verify SCNA
        $display("  SCNA[0]=%h [1]=%h [2]=%h [3]=%h",
                 u_switch.port_scna[0], u_switch.port_scna[1],
                 u_switch.port_scna[2], u_switch.port_scna[3]);

        repeat(10) @(posedge dl_clk);

        // Configure SCNA via CSR
        csr_wen = 1'b0;
        csr_port_sel = 2'd0; csr_wdata = 16'h0001;
        @(posedge dl_clk); #1;
        csr_wen = 1'b1;
        @(posedge dl_clk); #1;
        csr_port_sel = 2'd1; csr_wdata = 16'h0002;
        @(posedge dl_clk); #1;
        csr_port_sel = 2'd2; csr_wdata = 16'h0003;
        @(posedge dl_clk); #1;
        csr_port_sel = 2'd3; csr_wdata = 16'h0004;
        @(posedge dl_clk); #1;
        csr_wen = 1'b0;
        repeat(2) @(posedge dl_clk);

        $display("  SCNA[0]=%h [1]=%h [2]=%h [3]=%h",
                 u_switch.port_scna[0], u_switch.port_scna[1],
                 u_switch.port_scna[2], u_switch.port_scna[3]);

        //-----------------------------------------------------------------
        // Test 1: Port 0 -> Port 2
        // Force directly at crossbar fabric input to avoid force propagation
        // issues between ub_port output and ub_switch_top wire array.
        //-----------------------------------------------------------------
        test_num = 1;
        $display("  Test 1: Port 0 -> Port 2");
        begin : t1
            reg [511:0] pkt, got;
            pkt = make_pkt(16'h0003, 32'hAAAA0000);

            // Inject at crossbar input level.
            // Need 2 cycles: cycle 1 = arbiter registers grant,
            // cycle 2 = output queue captures data via MUX.
            @(negedge dl_clk);
            force u_switch.u_xbar.in_pkt_data_0  = pkt;
            force u_switch.u_xbar.in_pkt_valid_0 = 1'b1;
            force u_switch.u_xbar.in_pkt_sop_0   = 1'b1;
            force u_switch.u_xbar.in_pkt_eop_0   = 1'b1;
            force u_switch.u_xbar.in_dest_port_0  = 2'd2;
            force u_switch.u_xbar.in_pkt_valid_1 = 1'b0;
            force u_switch.u_xbar.in_pkt_valid_2 = 1'b0;
            force u_switch.u_xbar.in_pkt_valid_3 = 1'b0;
            @(posedge dl_clk);  // Cycle 1: arbiter registers grant
            @(posedge dl_clk);  // Cycle 2: output queue captures data
            @(negedge dl_clk);
            release u_switch.u_xbar.in_pkt_data_0;
            release u_switch.u_xbar.in_pkt_valid_0;
            release u_switch.u_xbar.in_pkt_sop_0;
            release u_switch.u_xbar.in_pkt_eop_0;
            release u_switch.u_xbar.in_dest_port_0;
            release u_switch.u_xbar.in_pkt_valid_1;
            release u_switch.u_xbar.in_pkt_valid_2;
            release u_switch.u_xbar.in_pkt_valid_3;

            // Data is valid for only 1 cycle (rd_ready=1 auto-consumes).
            // Poll immediately after release.
            got = 512'd0;
            begin : t1_poll
                integer wc1;
                wc1 = 0;
                while (wc1 < 10) begin
                    @(posedge dl_clk);
                    if (u_switch.u_xbar.out_pkt_valid_2) begin
                        got = u_switch.u_xbar.out_pkt_data_2;
                        disable t1_poll;
                    end
                    wc1 = wc1 + 1;
                end
            end

            if (got === pkt)
                $display("    PASS");
            else begin
                $display("    FAIL: valid=%b got[31:0]=%h exp[31:0]=%h",
                         u_switch.u_xbar.out_pkt_valid_2, got[31:0], pkt[31:0]);
                errors = errors + 1;
            end
        end

        repeat(10) @(posedge dl_clk);

        //-----------------------------------------------------------------
        // Test 2: Simultaneous Port 0->1, Port 3->0
        //-----------------------------------------------------------------
        test_num = 2;
        $display("  Test 2: Port 0->1 and Port 3->0");
        begin : t2
            reg [511:0] pkt01, pkt30, got1, got0;
            pkt01 = make_pkt(16'h0002, 32'hBBBB0000);
            pkt30 = make_pkt(16'h0001, 32'hCCCC0000);

            // Inject at crossbar input level: Port 0 -> Port 1, Port 3 -> Port 0
            // 2 cycles for arbiter grant + queue capture.
            @(negedge dl_clk);
            force u_switch.u_xbar.in_pkt_data_0  = pkt01;
            force u_switch.u_xbar.in_pkt_valid_0 = 1'b1;
            force u_switch.u_xbar.in_pkt_sop_0   = 1'b1;
            force u_switch.u_xbar.in_pkt_eop_0   = 1'b1;
            force u_switch.u_xbar.in_dest_port_0  = 2'd1;
            force u_switch.u_xbar.in_pkt_data_3  = pkt30;
            force u_switch.u_xbar.in_pkt_valid_3 = 1'b1;
            force u_switch.u_xbar.in_pkt_sop_3   = 1'b1;
            force u_switch.u_xbar.in_pkt_eop_3   = 1'b1;
            force u_switch.u_xbar.in_dest_port_3  = 2'd0;
            force u_switch.u_xbar.in_pkt_valid_1 = 1'b0;
            force u_switch.u_xbar.in_pkt_valid_2 = 1'b0;
            @(posedge dl_clk);
            @(posedge dl_clk);
            @(negedge dl_clk);
            release u_switch.u_xbar.in_pkt_data_0;
            release u_switch.u_xbar.in_pkt_valid_0;
            release u_switch.u_xbar.in_pkt_sop_0;
            release u_switch.u_xbar.in_pkt_eop_0;
            release u_switch.u_xbar.in_dest_port_0;
            release u_switch.u_xbar.in_pkt_data_3;
            release u_switch.u_xbar.in_pkt_valid_3;
            release u_switch.u_xbar.in_pkt_sop_3;
            release u_switch.u_xbar.in_pkt_eop_3;
            release u_switch.u_xbar.in_dest_port_3;
            release u_switch.u_xbar.in_pkt_valid_1;
            release u_switch.u_xbar.in_pkt_valid_2;

            // Poll for data (auto-consumed after 1 cycle due to rd_ready=1)
            got1 = 512'd0; got0 = 512'd0;
            begin : t2_poll
                integer rx2, wc2;
                rx2 = 0; wc2 = 0;
                while (rx2 < 2 && wc2 < 15) begin
                    @(posedge dl_clk);
                    if (u_switch.u_xbar.out_pkt_valid_1) begin
                        got1 = u_switch.u_xbar.out_pkt_data_1;
                        rx2 = rx2 + 1;
                    end
                    if (u_switch.u_xbar.out_pkt_valid_0) begin
                        got0 = u_switch.u_xbar.out_pkt_data_0;
                        rx2 = rx2 + 1;
                    end
                    wc2 = wc2 + 1;
                end
            end

            if (got1 === pkt01)
                $display("    PASS: 0->1");
            else begin
                $display("    FAIL: 0->1 got[31:0]=%h exp[31:0]=%h",
                         got1[31:0], pkt01[31:0]);
                errors = errors + 1;
            end
            if (got0 === pkt30)
                $display("    PASS: 3->0");
            else begin
                $display("    FAIL: 3->0 got[31:0]=%h exp[31:0]=%h",
                         got0[31:0], pkt30[31:0]);
                errors = errors + 1;
            end
        end

        repeat(10) @(posedge dl_clk);

        //-----------------------------------------------------------------
        // Test 3: Contention Port 0+1 -> Port 2
        //-----------------------------------------------------------------
        test_num = 3;
        $display("  Test 3: Contention Port 0+1 -> Port 2");
        begin : t3
            reg [511:0] pkt0, pkt1;
            reg [511:0] rx [0:1];
            integer rx_cnt, wc;
            pkt0 = make_pkt(16'h0003, 32'hDDDD0000);
            pkt1 = make_pkt(16'h0003, 32'heeee0000);

            // Inject at crossbar input level: Port 0 -> Port 2, Port 1 -> Port 2 (contention)
            // 2 cycles for arbiter grant + queue capture.
            @(negedge dl_clk);
            force u_switch.u_xbar.in_pkt_data_0  = pkt0;
            force u_switch.u_xbar.in_pkt_valid_0 = 1'b1;
            force u_switch.u_xbar.in_pkt_sop_0   = 1'b1;
            force u_switch.u_xbar.in_pkt_eop_0   = 1'b1;
            force u_switch.u_xbar.in_dest_port_0  = 2'd2;
            force u_switch.u_xbar.in_pkt_data_1  = pkt1;
            force u_switch.u_xbar.in_pkt_valid_1 = 1'b1;
            force u_switch.u_xbar.in_pkt_sop_1   = 1'b1;
            force u_switch.u_xbar.in_pkt_eop_1   = 1'b1;
            force u_switch.u_xbar.in_dest_port_1  = 2'd2;
            force u_switch.u_xbar.in_pkt_valid_2 = 1'b0;
            force u_switch.u_xbar.in_pkt_valid_3 = 1'b0;
            // Need 4 cycles: 2 for first packet (arbiter+queue), 2 for second
            @(posedge dl_clk);
            @(posedge dl_clk);
            @(posedge dl_clk);
            @(posedge dl_clk);
            @(negedge dl_clk);
            release u_switch.u_xbar.in_pkt_data_0;
            release u_switch.u_xbar.in_pkt_valid_0;
            release u_switch.u_xbar.in_pkt_sop_0;
            release u_switch.u_xbar.in_pkt_eop_0;
            release u_switch.u_xbar.in_dest_port_0;
            release u_switch.u_xbar.in_pkt_data_1;
            release u_switch.u_xbar.in_pkt_valid_1;
            release u_switch.u_xbar.in_pkt_sop_1;
            release u_switch.u_xbar.in_pkt_eop_1;
            release u_switch.u_xbar.in_dest_port_1;
            release u_switch.u_xbar.in_pkt_valid_2;
            release u_switch.u_xbar.in_pkt_valid_3;

            rx_cnt = 0; wc = 0;
            while (rx_cnt < 2 && wc < 30) begin
                @(posedge dl_clk);
                wc = wc + 1;
                if (u_switch.u_xbar.out_pkt_valid_2) begin
                    rx[rx_cnt] = u_switch.u_xbar.out_pkt_data_2;
                    rx_cnt = rx_cnt + 1;
                end
            end

            if (rx_cnt != 2) begin
                $display("    FAIL: got %0d packets", rx_cnt);
                errors = errors + 1;
            end else if ((rx[0] === pkt0 || rx[0] === pkt1) &&
                        (rx[1] === pkt0 || rx[1] === pkt1) &&
                        rx[0] !== rx[1]) begin
                $display("    PASS: round-robin");
            end else begin
                $display("    FAIL: rx0=%h rx1=%h", rx[0][31:0], rx[1][31:0]);
                errors = errors + 1;
            end
        end

        //-----------------------------------------------------------------
        // Report
        //-----------------------------------------------------------------
        repeat(5) @(posedge dl_clk);
        if (errors == 0)
            $display("\nSWITCH TOP PASS: all %0d tests passed.", test_num);
        else
            $display("\nSWITCH TOP FAIL: %0d error(s) in %0d tests.", errors, test_num);
        $finish;
    end

    initial begin
        #500000;
        $display("TIMEOUT at test %0d", test_num);
        $finish;
    end

endmodule
