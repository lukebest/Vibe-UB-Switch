`timescale 1ns/1ps

module ub_nw_tx_tb;
    reg clk, rst_n;
    // Pkt Input
    reg [127:0] pkt_data;
    reg pkt_valid, pkt_sop, pkt_eop;
    wire pkt_ready;
    // NTH Fields
    reg [1:0] rt;
    reg [15:0] scna, dcna, cci;
    reg [7:0] lbf;
    reg [3:0] sl;
    reg mgmt;
    reg [2:0] nlp;
    // Flit Output
    wire [159:0] flit_out;
    wire flit_valid;

    ub_nw_tx uut (
        .clk(clk), .rst_n(rst_n),
        .pkt_data(pkt_data), .pkt_valid(pkt_valid), .pkt_sop(pkt_sop), .pkt_eop(pkt_eop),
        .pkt_ready(pkt_ready),
        .rt(rt), .scna(scna), .dcna(dcna), .cci(cci), .lbf(lbf), .sl(sl), .mgmt(mgmt), .nlp(nlp),
        .flit_out(flit_out), .flit_valid(flit_valid)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("ub_nw_tx_tb.vcd");
        $dumpvars(0, ub_nw_tx_tb);
        clk = 0; rst_n = 0;
        pkt_data = 0; pkt_valid = 0; pkt_sop = 0; pkt_eop = 0;
        rt = 2'b01; scna = 16'hAAAA; dcna = 16'hBBBB; cci = 16'hCCCC;
        lbf = 8'hDD; sl = 4'hE; mgmt = 1'b1; nlp = 3'b001;
        #20 rst_n = 1;

        // Step 1: Write failing test (128-bit Pkt -> 160-bit Flit)
        // Verify that the first flit contains the NTH (12B) and first 8 bytes of payload.
        #10;
        pkt_valid = 1; pkt_sop = 1; pkt_eop = 1;
        pkt_data = 128'h0123456789ABCDEF_FEDCBA9876543210;
        
        // Expected NTH (96 bits = 12B):
        // [159:158] RT = 01
        // [157:142] SCNA = AAAA
        // [141:126] DCNA = BBBB
        // [125:110] CCI = CCCC
        // [109:102] LBF = DD
        // [101:98] SL = E
        // [97] Mgmt = 1
        // [96:94] NLP = 001
        // [93:64] RSVD = 00...0 (30 bits)
        // Expected Flit 1 (160 bits):
        // [159:64] = NTH
        // [63:0] = pkt_data[127:64] = 0123456789ABCDEF
        
        @(posedge flit_valid);
        #1;
        $display("Flit 1: %h", flit_out);
        
        // Check RT, SCNA, DCNA, etc.
        if (flit_out[159:158] !== 2'b01) $display("ERROR: RT mismatch");
        if (flit_out[157:142] !== 16'hAAAA) $display("ERROR: SCNA mismatch");
        if (flit_out[141:126] !== 16'hBBBB) $display("ERROR: DCNA mismatch");
        if (flit_out[125:110] !== 16'hCCCC) $display("ERROR: CCI mismatch");
        if (flit_out[109:102] !== 8'hDD) $display("ERROR: LBF mismatch");
        if (flit_out[101:98] !== 4'hE) $display("ERROR: SL mismatch");
        if (flit_out[97] !== 1'b1) $display("ERROR: Mgmt mismatch");
        if (flit_out[96:94] !== 3'b001) $display("ERROR: NLP mismatch");
        
        if (flit_out[63:0] !== 64'h0123456789ABCDEF) $display("ERROR: First 8 bytes of payload mismatch");
        
        @(posedge clk);
        #1;
        // Second flit should contain remaining 8 bytes of payload
        $display("Flit 2: %h", flit_out);
        if (flit_out[159:96] !== 64'hFEDCBA9876543210) $display("ERROR: Last 8 bytes of payload mismatch");
        
        $display("Test complete");
        $finish;
    end
endmodule
