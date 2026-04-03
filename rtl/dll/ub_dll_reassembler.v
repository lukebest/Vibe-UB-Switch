module ub_dll_reassembler (
    input clk, rst_n,
    input [159:0] flit_in,
    input flit_valid,
    output reg [159:0] net_data,
    output reg net_valid, net_sop, net_eop,
    input net_ready
);
    reg [1:0] state;
    localparam IDLE = 0, WAIT_DATA1 = 1, WAIT_DATA2 = 2;
    
    reg [127:0] data_hold;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            net_data <= 0;
            net_valid <= 0;
            net_sop <= 0;
            net_eop <= 0;
            data_hold <= 0;
        end else begin
            net_valid <= 0;
            net_sop <= 0;
            net_eop <= 0;
            
            case (state)
                IDLE: begin
                    if (flit_valid && flit_in[159:128] == 32'h80000000) begin
                        // Flit 0: LPH(32b) + N0[159:32](128b)
                        data_hold <= flit_in[127:0];
                        state <= WAIT_DATA1;
                    end
                end
                WAIT_DATA1: begin
                    if (flit_valid) begin
                        // Flit 1: N0[31:0](32b) + N1[159:32](128b)
                        net_data <= {data_hold, flit_in[159:128]};
                        net_valid <= 1;
                        net_sop <= 1;
                        data_hold <= flit_in[127:0];
                        state <= WAIT_DATA2;
                    end
                end
                WAIT_DATA2: begin
                    if (flit_valid) begin
                        // Flit 2: N1[31:0](32b) + Padding(128b)
                        net_data <= {data_hold, flit_in[159:128]};
                        net_valid <= 1;
                        net_eop <= 1;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
