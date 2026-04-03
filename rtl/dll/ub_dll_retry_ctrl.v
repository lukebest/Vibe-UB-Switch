//-----------------------------------------------------------------------------
// Module: ub_dll_retry_ctrl
// Simplified Go-Back-N retry controller with circular retry buffer.
//-----------------------------------------------------------------------------
module ub_dll_retry_ctrl (
    input  wire         clk,
    input  wire         rst_n,
    // Flit backup
    input  wire [639:0] tx_flit_in,
    input  wire         tx_flit_valid,
    input  wire         is_null_block,
    // Retry request from peer
    input  wire         retry_req_received,
    input  wire [7:0]   retry_rcvptr,
    // ACK processing
    input  wire         ack_received,
    input  wire [7:0]   ack_ptr,
    // Retransmit output
    output reg  [639:0] retry_flit_out,
    output reg          retry_flit_valid,
    output wire         retry_active
);

    localparam BUF_DEPTH = 256;
    localparam ADDR_W    = 8;

    // Retry buffer
    reg [639:0] buf_mem [0:BUF_DEPTH-1];

    // Pointers
    reg [ADDR_W-1:0] wr_ptr;    // next write position
    reg [ADDR_W-1:0] tail_ptr;  // oldest unACKed entry
    reg [ADDR_W-1:0] rd_ptr;    // current retransmit read position

    // State
    localparam ST_NORMAL     = 2'd0;
    localparam ST_RETRANSMIT = 2'd1;

    reg [1:0] state;

    assign retry_active = (state == ST_RETRANSMIT);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr          <= 8'd0;
            tail_ptr        <= 8'd0;
            rd_ptr          <= 8'd0;
            state           <= ST_NORMAL;
            retry_flit_out  <= 640'd0;
            retry_flit_valid <= 1'b0;
        end else begin
            retry_flit_valid <= 1'b0;

            case (state)
                ST_NORMAL: begin
                    // Backup sent flits (skip null blocks)
                    if (tx_flit_valid && !is_null_block) begin
                        buf_mem[wr_ptr] <= tx_flit_in;
                        wr_ptr <= wr_ptr + 1'b1;
                    end
                    // Release buffer on ACK
                    if (ack_received) begin
                        tail_ptr <= ack_ptr;
                    end
                    // Enter retransmit on retry request
                    if (retry_req_received) begin
                        rd_ptr <= retry_rcvptr;
                        state  <= ST_RETRANSMIT;
                    end
                end

                ST_RETRANSMIT: begin
                    if (rd_ptr != wr_ptr) begin
                        retry_flit_out   <= buf_mem[rd_ptr];
                        retry_flit_valid <= 1'b1;
                        rd_ptr           <= rd_ptr + 1'b1;
                    end else begin
                        state <= ST_NORMAL;
                    end
                end

                default: state <= ST_NORMAL;
            endcase
        end
    end

endmodule
