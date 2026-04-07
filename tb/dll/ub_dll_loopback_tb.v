//-----------------------------------------------------------------------------
// Testbench: ub_dll_loopback_tb
// DLL TX engine -> RX engine loopback test.
// Verifies: data integrity, SOP/EOP passthrough, null block filtering,
//           credit-based flow control with feedback loop.
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module ub_dll_loopback_tb;

    reg         clk, rst_n;

    // TX engine - network layer side
    reg  [639:0] tx_data;
    reg          tx_valid;
    wire         tx_ready;

    // Loopback: TX flit_out -> RX flit_in
    wire [639:0] lb_flit;
    wire         lb_valid;

    // RX engine - network layer side
    wire [639:0] rx_data;
    wire         rx_valid;
    wire         rx_sop, rx_eop;

    // Control feedback: RX -> TX (ack, credit return)
    wire         fb_ack;
    wire [7:0]   fb_ack_ptr;
    wire         fb_cr;
    wire [7:0]   fb_cr_amt;

    //-------------------------------------------------------------------------
    // DUT: TX engine -> loopback -> RX engine
    //-------------------------------------------------------------------------
    ub_dll_tx_engine u_tx (
        .clk               (clk),
        .rst_n             (rst_n),
        .link_ready        (1'b1),
        .nw_flit_in        (tx_data),
        .nw_flit_valid     (tx_valid),
        .nw_flit_sop       (1'b0),
        .nw_flit_eop       (1'b0),
        .nw_flit_ready     (tx_ready),
        .flit_out          (lb_flit),
        .flit_valid        (lb_valid),
        .flit_ready        (1'b1),
        .retry_req_received(1'b0),
        .retry_rcvptr      (8'd0),
        .ack_received      (fb_ack),
        .ack_ptr           (fb_ack_ptr),
        .credit_return     (fb_cr),
        .credit_return_amt (fb_cr_amt)
    );

    ub_dll_rx_engine u_rx (
        .clk                (clk),
        .rst_n              (rst_n),
        .flit_in            (lb_flit),
        .flit_valid         (lb_valid),
        .nw_flit_out        (rx_data),
        .nw_flit_valid      (rx_valid),
        .nw_flit_sop        (rx_sop),
        .nw_flit_eop        (rx_eop),
        .nw_flit_ready      (1'b1),
        .retry_req_to_send  (),
        .retry_rcvptr       (),
        .ack_to_send        (fb_ack),
        .ack_ptr            (fb_ack_ptr),
        .credit_return_to_send(fb_cr),
        .credit_return_amt  (fb_cr_amt)
    );

    //-------------------------------------------------------------------------
    // Clock: 1.25 GHz
    //-------------------------------------------------------------------------
    initial clk = 0;
    always #0.4 clk = ~clk;

    //-------------------------------------------------------------------------
    // Test data
    //-------------------------------------------------------------------------
    reg [639:0] test_flits [0:4];
    reg         test_sop   [0:4];
    reg         test_eop   [0:4];
    integer errors, rx_count, i;

    // Build a 640-bit test flit from a seed with SOP/EOP in bits 638/637.
    // Bits [636:0] are filled with incrementing 32-bit words from seed.
    // Bit 639 is left 0 (TX engine overwrites with 1 for data flits).
    function [639:0] make_flit;
        input [31:0] seed;
        input sop_bit, eop_bit;
        reg [639:0] f;
        integer j;
        begin
            f = 640'd0;
            f[638] = sop_bit;
            f[637] = eop_bit;
            for (j = 0; j < 19; j = j + 1)
                f[j*32 +: 32] = seed + j;
            f[636:608] = seed[28:0];
            make_flit = f;
        end
    endfunction

    initial begin
        $dumpfile("ub_dll_loopback_tb.vcd");
        $dumpvars(0, ub_dll_loopback_tb);
        //---------------------------------------------------------------------
        // Setup test data
        //---------------------------------------------------------------------
        test_flits[0] = make_flit(32'hDEAD0000, 1, 0);  // SOP only
        test_flits[1] = make_flit(32'hCAFEBABE, 0, 0);  // neither
        test_flits[2] = make_flit(32'h12345678, 0, 1);  // EOP only
        test_flits[3] = make_flit(32'h0BADF00D, 1, 1);  // SOP + EOP
        test_flits[4] = make_flit(32'h1337C0DE, 0, 0);  // neither

        test_sop[0] = 1; test_eop[0] = 0;
        test_sop[1] = 0; test_eop[1] = 0;
        test_sop[2] = 0; test_eop[2] = 1;
        test_sop[3] = 1; test_eop[3] = 1;
        test_sop[4] = 0; test_eop[4] = 0;

        errors   = 0;
        rx_count = 0;
        tx_data  = 640'd0;
        tx_valid = 1'b0;

        // Reset
        rst_n = 1'b0;
        repeat(10) @(posedge clk);
        rst_n = 1'b1;
        repeat(5) @(posedge clk);  // Wait for credit init

        $display("DLL Engine Loopback Test");

        //---------------------------------------------------------------------
        // Test 1: Send 5 data flits, verify loopback
        // Use fork-join to send and receive concurrently (2-cycle latency
        // means RX produces data while TX is still being fed).
        //---------------------------------------------------------------------
        $display("  Test 1: Basic data loopback (5 flits)");
        fork
            begin : tx_process
                for (i = 0; i < 5; i = i + 1) begin
                    tx_data  = test_flits[i];
                    tx_valid = 1'b1;
                    @(posedge clk);
                end
                tx_valid = 1'b0;
                tx_data  = 640'd0;
            end
            begin : rx_process
                while (rx_count < 5) begin
                    @(posedge clk);
                    if (rx_valid) begin
                        if (rx_data !== {1'b1, test_flits[rx_count][638:0]}) begin
                            $display("    FAIL flit %0d: data mismatch", rx_count);
                            $display("      expected: %h", {1'b1, test_flits[rx_count][638:0]});
                            $display("      got:      %h", rx_data);
                            errors = errors + 1;
                        end else if (rx_sop !== test_sop[rx_count] || rx_eop !== test_eop[rx_count]) begin
                            $display("    FAIL flit %0d: SOP/EOP mismatch (exp sop=%b eop=%b, got sop=%b eop=%b)",
                                     rx_count, test_sop[rx_count], test_eop[rx_count],
                                     rx_sop, rx_eop);
                            errors = errors + 1;
                        end else begin
                            $display("    PASS flit %0d: data + SOP/EOP match", rx_count);
                        end
                        rx_count = rx_count + 1;
                    end
                end
            end
        join

        //---------------------------------------------------------------------
        // Test 2: Null block filtering — no spurious output after data
        //---------------------------------------------------------------------
        $display("  Test 2: Null block filtering");
        begin : null_test
            reg spurious;
            spurious = 1'b0;
            repeat(20) @(posedge clk) begin
                if (rx_valid) spurious = 1'b1;
            end
            if (spurious) begin
                $display("    FAIL: spurious data received during null-block phase");
                errors = errors + 1;
            end else
                $display("    PASS: no spurious data (null blocks filtered)");
        end

        //---------------------------------------------------------------------
        // Report
        //---------------------------------------------------------------------
        repeat(5) @(posedge clk);
        if (errors == 0)
            $display("\nDLL LOOPBACK PASS: all tests passed.");
        else
            $display("\nDLL LOOPBACK FAIL: %0d error(s).", errors);
        $finish;
    end

    // Timeout
    initial begin
        #100000;
        $display("TIMEOUT: received %0d/5 flits", rx_count);
        $finish;
    end

endmodule
