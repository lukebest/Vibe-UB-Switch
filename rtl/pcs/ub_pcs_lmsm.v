module ub_pcs_lmsm (
    input clk, rst_n,
    input start_train,
    input [159:0] rx_flit_in,
    input rx_flit_valid,
    output reg [159:0] tx_flit_out,
    output reg link_up,
    output reg link_ready,
    output [2:0] state_dbg
);
    localparam LINK_IDLE = 3'd0;
    localparam PROBE_WAIT = 3'd1;
    localparam DISC_ACTIVE = 3'd2;
    localparam DISC_CONFIRM = 3'd3;
    localparam CONFIG_ACTIVE = 3'd4;
    localparam CONFIG_CHECK = 3'd5;
    localparam LINK_ACTIVE = 3'd6;

    reg [2:0] state;
    reg [3:0] probe_cnt;
    reg [3:0] dltb_cnt;
    reg [3:0] cltb_cnt;

    assign state_dbg = state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= LINK_IDLE;
            probe_cnt <= 4'd0;
            dltb_cnt <= 4'd0;
            cltb_cnt <= 4'd0;
            tx_flit_out <= 160'd0;
            link_up <= 1'b0;
            link_ready <= 1'b0;
        end else begin
            case (state)
                LINK_IDLE: begin
                    link_up <= 1'b0;
                    link_ready <= 1'b0;
                    if (start_train) begin
                        state <= PROBE_WAIT;
                        probe_cnt <= 4'd0;
                    end
                end
                PROBE_WAIT: begin
                    if (probe_cnt == 4'd9) begin
                        state <= DISC_ACTIVE;
                        dltb_cnt <= 4'd0;
                    end else begin
                        probe_cnt <= probe_cnt + 4'd1;
                    end
                end
                DISC_ACTIVE: begin
                    tx_flit_out <= {8'h01, 152'h0}; // DLTB Type 8'h01
                    if (rx_flit_valid && rx_flit_in[159:152] == 8'h01) begin
                        if (dltb_cnt == 4'd7) begin
                            state <= DISC_CONFIRM;
                            dltb_cnt <= 4'd0;
                        end else begin
                            dltb_cnt <= dltb_cnt + 4'd1;
                        end
                    end
                end
                DISC_CONFIRM: begin
                    tx_flit_out <= {8'h02, 152'h0}; // DLTB Type 8'h02
                    if (rx_flit_valid && rx_flit_in[159:152] == 8'h02) begin
                        if (dltb_cnt == 4'd7) begin
                            state <= CONFIG_ACTIVE;
                            dltb_cnt <= 4'd0;
                        end else begin
                            dltb_cnt <= dltb_cnt + 4'd1;
                        end
                    end
                end
                CONFIG_ACTIVE: begin
                    tx_flit_out <= {8'h03, 152'h0}; // CLTB Type 8'h03
                    if (rx_flit_valid && rx_flit_in[159:152] == 8'h03) begin
                        if (cltb_cnt == 4'd1) begin
                            state <= CONFIG_CHECK;
                            cltb_cnt <= 4'd0;
                        end else begin
                            cltb_cnt <= cltb_cnt + 4'd1;
                        end
                    end
                end
                CONFIG_CHECK: begin
                    tx_flit_out <= {8'h04, 152'h0}; // CLTB Type 8'h04
                    if (rx_flit_valid && rx_flit_in[159:152] == 8'h04) begin
                        if (cltb_cnt == 4'd1) begin
                            state <= LINK_ACTIVE;
                            cltb_cnt <= 4'd0;
                        end else begin
                            cltb_cnt <= cltb_cnt + 4'd1;
                        end
                    end
                end
                LINK_ACTIVE: begin
                    link_up <= 1'b1;
                    link_ready <= 1'b1;
                    tx_flit_out <= 160'h0;
                end
                default: state <= LINK_IDLE;
            endcase
        end
    end
endmodule
