`timescale 1ns/1ps

module ub_nw_rx_tb;
    reg clk, rst_n;
    reg [159:0] flit_in;
    reg flit_valid, flit_sop, flit_eop;
    wire [127:0] pkt_out;
    wire pkt_valid, pkt_sop, pkt_eop, pkt_err;
    reg [15:0] local_scna;

    ub_nw_rx uut (
        .clk(clk), .rst_n(rst_n),
        .flit_in(flit_in), .flit_valid(flit_valid), .flit_sop(flit_sop), .flit_eop(flit_eop),
        .pkt_out(pkt_out), .pkt_valid(pkt_valid), .pkt_sop(pkt_sop), .pkt_eop(pkt_eop),
        .pkt_err(pkt_err),
        .local_scna(local_scna)
    );

    // ICRC helper for testbench
    reg [159:0] icrc_tb_data;
    reg icrc_tb_valid;
    reg icrc_tb_sop;
    wire [31:0] icrc_tb_out;
    ub_nw_icrc i_icrc_tb (
        .clk(clk), .rst_n(rst_n),
        .data_in(icrc_tb_data), .data_valid(icrc_tb_valid), .is_sop(icrc_tb_sop),
        .icrc_out(icrc_tb_out)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("ub_nw_rx_tb.vcd");
        $dumpvars(0, ub_nw_rx_tb);
        clk = 0; rst_n = 0;
        flit_in = 0; flit_valid = 0; flit_sop = 0; flit_eop = 0;
        local_scna = 16'hBBBB;
        icrc_tb_data = 0; icrc_tb_valid = 0; icrc_tb_sop = 0;
        #20 rst_n = 1;

        #10;
        @(posedge clk);
        #1;
        flit_valid = 1; flit_sop = 1; flit_eop = 0;
        flit_in[159:158] = 2'b01;
        flit_in[157:142] = 16'hAAAA;
        flit_in[141:126] = 16'hBBBB;
        flit_in[125:110] = 16'hCCCC;
        flit_in[109:102] = 8'hDD;
        flit_in[101:98]  = 4'hE;
        flit_in[97]      = 1'b1;
        flit_in[96:94]   = 3'b001;
        flit_in[93:64]   = 30'h0;
        flit_in[63:0]    = 64'h0123456789ABCDEF;

        icrc_tb_data = flit_in;
        icrc_tb_valid = 1;
        icrc_tb_sop = 1;
        
        @(posedge clk);
        #1;
        flit_sop = 0; flit_eop = 1;
        flit_in[159:96] = 64'hFEDCBA9876543210;
        flit_in[63:0] = 64'h0;
        
        icrc_tb_data = {flit_in[159:96], 32'h0, flit_in[63:0]};
        icrc_tb_sop = 0;

        #1; // Allow combinational logic to settle
        flit_in[95:64] = icrc_tb_out;
        $display("Generated ICRC: %h", icrc_tb_out);
        
        @(posedge clk);
        #1;
        flit_valid = 0; flit_eop = 0;
        icrc_tb_valid = 0;

        @(posedge pkt_valid);
        #1;
        $display("Pkt Out: %h", pkt_out);
        if (pkt_out !== 128'h0123456789ABCDEF_FEDCBA9876543210) $display("ERROR: Pkt data mismatch");
        if (pkt_err) $display("ERROR: Unexpected pkt_err");
        else $display("SUCCESS: Valid packet received correctly");

        #100;
        $finish;
    end
endmodule
