module ub_dll_segmenter (
    input clk, rst_n,
    input link_ready,
    input [159:0] net_data,
    input net_valid, net_sop, net_eop,
    output wire net_ready,
    output reg [159:0] flit_out,
    output reg flit_valid
);
    reg [1:0] state;
    localparam IDLE = 0, SOP_LPH = 1, DATA = 2;
    
    reg [159:0] data_hold;

    // The segmenter is ready if it's IDLE (for SOP) or if it's in SOP_LPH (waiting for remaining data flits)
    // AND the link is ready.
    assign net_ready = link_ready && ((state == IDLE) || (state == SOP_LPH));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            flit_out <= 0;
            flit_valid <= 0;
            data_hold <= 0;
        end else begin
            case (state)
                IDLE: begin
                    flit_valid <= 0;
                    if (link_ready && net_valid && net_sop) begin
                        $display("DLL SEG: IDLE -> SOP_LPH, net_data=%h", net_data);
                        // Send LPH (4 bytes) + first 16 bytes of net_data
                        flit_out <= {32'h80000000, net_data[159:32]};
                        flit_valid <= 1;
                        data_hold <= {net_data[31:0], 128'h0};
                        state <= SOP_LPH;
                    end
                end
                SOP_LPH: begin
                    // Flit 2: data_hold[159:128] + net_data[159:32]
                    if (net_valid) begin
                        $display("DLL SEG: SOP_LPH -> DATA, net_data=%h", net_data);
                        flit_out <= {data_hold[159:128], net_data[159:32]};
                        flit_valid <= 1;
                        data_hold <= {net_data[31:0], 128'h0};
                        if (net_eop) state <= DATA;
                    end else begin
                        flit_valid <= 0;
                    end
                end
                DATA: begin
                    $display("DLL SEG: DATA -> IDLE");
                    // Flit 3 (DLL): Final bits of last network flit + padding
                    flit_out <= data_hold;
                    flit_valid <= 1;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
