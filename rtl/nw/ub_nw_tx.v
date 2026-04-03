module ub_nw_tx (
    input clk, rst_n,
    // Pkt Input (128-bit segments)
    input [127:0] pkt_data,
    input pkt_valid, pkt_sop, pkt_eop,
    output reg pkt_ready,
    // NTH Fields
    input [1:0] rt,
    input [15:0] scna, dcna, cci,
    input [7:0] lbf,
    input [3:0] sl,
    input mgmt,
    input [2:0] nlp,
    // Flit Output (160-bit flits)
    output reg [159:0] flit_out,
    output reg flit_valid,
    output reg flit_sop, flit_eop,
    input flit_ready
);

    // State Machine for Gearbox (128 bits -> 160 bits)
    // Packet = 96-bit NTH + 128-bit Data = 224 bits
    // Flit 1: 160 bits (NTH + Data[127:64])
    // Flit 2: 64 bits (Data[63:0] + Padding/Next)
    
    reg [1:0] state;
    localparam IDLE = 0, FLIT1 = 1, FLIT2 = 2;
    
    reg [127:0] data_reg;
    reg [95:0] nth_reg;
    reg eop_reg;

    wire [95:0] nth_comb = {rt, scna, dcna, cci, lbf, sl, mgmt, nlp, 30'h0};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            pkt_ready <= 1;
            flit_out <= 0;
            flit_valid <= 0;
            flit_sop <= 0;
            flit_eop <= 0;
            data_reg <= 0;
            nth_reg <= 0;
            eop_reg <= 0;
        end else begin
            case (state)
                IDLE: begin
                    flit_valid <= 0;
                    flit_sop <= 0;
                    flit_eop <= 0;
                    if (pkt_valid && pkt_sop) begin
                        $display("NW TX IDLE -> FLIT1, pkt_data=%h", pkt_data);
                        // Start of packet
                        nth_reg <= nth_comb;
                        data_reg <= pkt_data;
                        eop_reg <= pkt_eop;
                        pkt_ready <= 0;
                        state <= FLIT1;
                    end
                end
                FLIT1: begin
                    if (flit_ready) begin
                        $display("NW TX FLIT1 -> FLIT2");
                        // Flit 1: NTH (96 bits) + Pkt[127:64] (64 bits)
                        flit_out <= {nth_reg, data_reg[127:64]};
                        flit_valid <= 1;
                        flit_sop <= 1;
                        flit_eop <= 0;
                        state <= FLIT2;
                    end
                end
                FLIT2: begin
                    if (flit_ready) begin
                        $display("NW TX FLIT2 -> IDLE");
                        // Flit 2: Pkt[63:0] (64 bits) + Padding (96 bits)
                        flit_out <= {data_reg[63:0], 96'h0};
                        flit_valid <= 1;
                        flit_sop <= 0;
                        flit_eop <= 1; // Assuming 128-bit packet for now
                        pkt_ready <= 1;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
