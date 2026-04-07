//-----------------------------------------------------------------------------
// Testbench: ub_xbar_fabric_tb
// Tests 4x4 crossbar: routing, round-robin arbitration, contention
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module ub_xbar_fabric_tb;

    localparam CLK_PERIOD = 0.8; // 1.25 GHz

    reg         clk, rst_n;
    integer     errors;
    integer     i;

    // Input port signals
    reg  [511:0] in_data  [0:3];
    reg          in_valid [0:3];
    reg          in_sop   [0:3];
    reg          in_eop   [0:3];
    reg  [1:0]   in_dest  [0:3];
    wire         in_ready [0:3];

    // Output port signals
    wire [511:0] out_data  [0:3];
    wire         out_valid [0:3];
    wire         out_sop   [0:3];
    wire         out_eop   [0:3];
    reg          out_ready [0:3];

    // Packet counters per output port
    integer pkt_count [0:3];

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    ub_xbar_fabric dut (
        .clk(clk), .rst_n(rst_n),
        .in_pkt_data_0(in_data[0]),  .in_pkt_valid_0(in_valid[0]),
        .in_pkt_sop_0(in_sop[0]),    .in_pkt_eop_0(in_eop[0]),
        .in_dest_port_0(in_dest[0]), .in_pkt_ready_0(in_ready[0]),
        .in_pkt_data_1(in_data[1]),  .in_pkt_valid_1(in_valid[1]),
        .in_pkt_sop_1(in_sop[1]),    .in_pkt_eop_1(in_eop[1]),
        .in_dest_port_1(in_dest[1]), .in_pkt_ready_1(in_ready[1]),
        .in_pkt_data_2(in_data[2]),  .in_pkt_valid_2(in_valid[2]),
        .in_pkt_sop_2(in_sop[2]),    .in_pkt_eop_2(in_eop[2]),
        .in_dest_port_2(in_dest[2]), .in_pkt_ready_2(in_ready[2]),
        .in_pkt_data_3(in_data[3]),  .in_pkt_valid_3(in_valid[3]),
        .in_pkt_sop_3(in_sop[3]),    .in_pkt_eop_3(in_eop[3]),
        .in_dest_port_3(in_dest[3]), .in_pkt_ready_3(in_ready[3]),
        .out_pkt_data_0(out_data[0]),  .out_pkt_valid_0(out_valid[0]),
        .out_pkt_sop_0(out_sop[0]),    .out_pkt_eop_0(out_eop[0]),
        .out_pkt_ready_0(out_ready[0]),
        .out_pkt_data_1(out_data[1]),  .out_pkt_valid_1(out_valid[1]),
        .out_pkt_sop_1(out_sop[1]),    .out_pkt_eop_1(out_eop[1]),
        .out_pkt_ready_1(out_ready[1]),
        .out_pkt_data_2(out_data[2]),  .out_pkt_valid_2(out_valid[2]),
        .out_pkt_sop_2(out_sop[2]),    .out_pkt_eop_2(out_eop[2]),
        .out_pkt_ready_2(out_ready[2]),
        .out_pkt_data_3(out_data[3]),  .out_pkt_valid_3(out_valid[3]),
        .out_pkt_sop_3(out_sop[3]),    .out_pkt_eop_3(out_eop[3]),
        .out_pkt_ready_3(out_ready[3])
    );

    // Clock
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // Output monitor: count received packets per port
    always @(posedge clk) begin
        if (out_valid[0] && out_eop[0] && out_ready[0]) pkt_count[0] = pkt_count[0] + 1;
        if (out_valid[1] && out_eop[1] && out_ready[1]) pkt_count[1] = pkt_count[1] + 1;
        if (out_valid[2] && out_eop[2] && out_ready[2]) pkt_count[2] = pkt_count[2] + 1;
        if (out_valid[3] && out_eop[3] && out_ready[3]) pkt_count[3] = pkt_count[3] + 1;
    end

    // Task: send a single-beat packet (SOP+EOP same cycle)
    // Hold valid until in_ready asserted (handshake completion)
    // Must be automatic for fork-join re-entrancy
    task automatic send_pkt;
        input integer src;
        input [1:0]   dst;
        input [511:0] payload;
        begin
            @(posedge clk); #0.1;
            in_data[src]  = payload;
            in_valid[src] = 1;
            in_sop[src]   = 1;
            in_eop[src]   = 1;
            in_dest[src]  = dst;
            while (!in_ready[src]) begin
                @(posedge clk); #0.1;
            end
            @(posedge clk); #0.1;
            in_valid[src] = 0;
            in_sop[src]   = 0;
            in_eop[src]   = 0;
        end
    endtask

    //-------------------------------------------------------------------------
    // Main test
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("ub_xbar_fabric_tb.vcd");
        $dumpvars(0, ub_xbar_fabric_tb);
        errors = 0;
        for (i = 0; i < 4; i = i + 1) begin
            in_valid[i] = 0; in_sop[i] = 0; in_eop[i] = 0;
            in_data[i]  = 0; in_dest[i] = 0;
            out_ready[i] = 1;
            pkt_count[i] = 0;
        end
        rst_n = 0;
        repeat(10) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);

        //--- Test 1: Basic routing — port 0->2, port 1->3 simultaneously
        $display("TEST 1: Basic routing port0->2, port1->3");
        fork
            send_pkt(0, 2, {480'd0, 32'hABCD0002});
            send_pkt(1, 3, {480'd0, 32'hABCD0013});
        join
        repeat(20) @(posedge clk);
        if (pkt_count[2] == 1 && pkt_count[3] == 1)
            $display("  PASS: port2 got %0d pkt, port3 got %0d pkt", pkt_count[2], pkt_count[3]);
        else begin
            $display("  FAIL: port2=%0d (exp 1), port3=%0d (exp 1)", pkt_count[2], pkt_count[3]);
            errors = errors + 1;
        end

        //--- Test 2: Contention — ports 0,1,2,3 all send to port 0
        $display("TEST 2: Contention — all 4 ports -> port 0 (round-robin)");
        for (i = 0; i < 4; i = i + 1) pkt_count[i] = 0;
        fork
            begin send_pkt(0, 0, {480'd0, 32'hDEAD0000}); end
            begin send_pkt(1, 0, {480'd0, 32'hDEAD0100}); end
            begin send_pkt(2, 0, {480'd0, 32'hDEAD0200}); end
            begin send_pkt(3, 0, {480'd0, 32'hDEAD0300}); end
        join
        repeat(60) @(posedge clk);
        if (pkt_count[0] == 4)
            $display("  PASS: port0 received all 4 packets");
        else begin
            $display("  FAIL: port0 received %0d packets (expected 4)", pkt_count[0]);
            errors = errors + 1;
        end

        //--- Test 3: All-to-all (port i -> port (i+1)%4)
        $display("TEST 3: All-to-all rotation");
        for (i = 0; i < 4; i = i + 1) pkt_count[i] = 0;
        fork
            send_pkt(0, 1, {480'd0, 32'hCC000001});
            send_pkt(1, 2, {480'd0, 32'hCC000102});
            send_pkt(2, 3, {480'd0, 32'hCC000203});
            send_pkt(3, 0, {480'd0, 32'hCC000300});
        join
        repeat(40) @(posedge clk);
        if (pkt_count[0]==1 && pkt_count[1]==1 && pkt_count[2]==1 && pkt_count[3]==1)
            $display("  PASS: all ports received exactly 1 packet");
        else begin
            $display("  FAIL: counts p0=%0d p1=%0d p2=%0d p3=%0d (all exp 1)",
                     pkt_count[0], pkt_count[1], pkt_count[2], pkt_count[3]);
            errors = errors + 1;
        end

        repeat(10) @(posedge clk);
        if (errors == 0)
            $display("\nXBAR PASS: all tests passed.");
        else
            $display("\nXBAR FAIL: %0d test(s) failed.", errors);
        $finish;
    end

    initial begin
        #5000;
        $display("TIMEOUT");
        $finish;
    end

endmodule
