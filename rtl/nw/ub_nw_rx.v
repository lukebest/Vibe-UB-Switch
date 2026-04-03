module ub_nw_rx (
    input clk, rst_n,
    // Flit Input (160-bit flits)
    input [159:0] flit_in,
    input flit_valid, flit_sop, flit_eop,
    // Pkt Output (128-bit segments)
    output reg [127:0] pkt_out,
    output reg pkt_valid, pkt_sop, pkt_eop,
    output reg pkt_err,
    // Configuration
    input [15:0] local_scna
);

    // State Machine
    reg state;
    localparam IDLE = 0, WAIT_FLIT2 = 1;

    reg [63:0] pkt_high_reg;
    reg [15:0] dcna_reg;
    reg [31:0] icrc_received;

    // ICRC Verification
    // The ICRC module expects flits. We zero out the ICRC field in the last flit.
    // Flit 2: Pkt[63:0] (159:96), ICRC[31:0] (95:64), Padding[63:0] (63:0)
    wire [159:0] icrc_data_in;
    assign icrc_data_in = (flit_valid && flit_eop) ? {flit_in[159:96], 32'h0, flit_in[63:0]} : flit_in;

    wire [31:0] icrc_computed;
    ub_nw_icrc i_icrc (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(icrc_data_in),
        .data_valid(flit_valid),
        .is_sop(flit_sop),
        .icrc_out(icrc_computed)
    );

    reg pkt_valid_q;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) pkt_valid_q <= 0;
        else pkt_valid_q <= pkt_valid;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            pkt_out <= 0;
            pkt_valid <= 0;
            pkt_sop <= 0;
            pkt_eop <= 0;
            pkt_err <= 0;
            pkt_high_reg <= 0;
            dcna_reg <= 0;
            icrc_received <= 0;
        end else begin
            pkt_valid <= 0;
            pkt_sop <= 0;
            pkt_eop <= 0;
            // Note: pkt_err is sticky for the duration of pkt_valid_q to capture the error
            if (!pkt_valid_q) pkt_err <= 0;

            case (state)
                IDLE: begin
                    if (flit_valid && flit_sop) begin
                        $display("NW RX IDLE -> WAIT_FLIT2, flit_in=%h", flit_in);
                        pkt_high_reg <= flit_in[63:0];
                        dcna_reg <= flit_in[141:126];
                        state <= WAIT_FLIT2;
                    end
                end
                WAIT_FLIT2: begin
                    if (flit_valid) begin
                        $display("NW RX WAIT_FLIT2 -> IDLE, flit_in=%h, eop=%b", flit_in, flit_eop);
                        pkt_out <= {pkt_high_reg, flit_in[159:96]};
                        icrc_received <= flit_in[95:64];
                        
                        if (dcna_reg != local_scna) begin
                            pkt_err <= 1;
                        end
                        
                        pkt_valid <= 1;
                        pkt_sop <= 1;
                        pkt_eop <= 1;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
            
            // Delayed ICRC check
            if (pkt_valid_q) begin
                if (icrc_computed != icrc_received) begin
                    pkt_err <= 1;
                end
            end
        end
    end
endmodule
