//-----------------------------------------------------------------------------
// Module: ub_xbar_arbiter
// Per-output-port round-robin arbiter with packet-level atomicity.
// Once granted at SOP, holds grant until EOP.
//-----------------------------------------------------------------------------
module ub_xbar_arbiter (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [3:0]  req,
    input  wire [3:0]  req_sop,
    input  wire [3:0]  req_eop,
    output reg  [3:0]  grant,
    output wire [1:0]  grant_idx
);

    reg [1:0] rr_ptr;
    reg       locked;
    reg [1:0] locked_port;

    assign grant_idx = grant[0] ? 2'd0 :
                       grant[1] ? 2'd1 :
                       grant[2] ? 2'd2 : 2'd3;

    // Combinational: compute next grant based on round-robin
    reg [3:0] ng;
    reg [1:0] ng_idx;
    always @(*) begin
        ng = 4'b0000;
        ng_idx = rr_ptr;
        if (req[rr_ptr])
            ng = 4'b0001 << rr_ptr;
        else if (req[rr_ptr + 2'd1])
            ng = 4'b0001 << (rr_ptr + 2'd1);
        else if (req[rr_ptr + 2'd2])
            ng = 4'b0001 << (rr_ptr + 2'd2);
        else if (req[rr_ptr + 2'd3])
            ng = 4'b0001 << (rr_ptr + 2'd3);

        ng_idx = ng[0] ? 2'd0 : ng[1] ? 2'd1 : ng[2] ? 2'd2 : 2'd3;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant       <= 4'b0000;
            rr_ptr      <= 2'd0;
            locked      <= 1'b0;
            locked_port <= 2'd0;
        end else begin
            if (locked) begin
                if (req[locked_port]) begin
                    grant <= 4'b0001 << locked_port;
                    if (req_eop[locked_port]) begin
                        locked <= 1'b0;
                        rr_ptr <= locked_port + 1'b1;
                    end
                end else begin
                    grant  <= 4'b0000;
                    locked <= 1'b0;
                end
            end else begin
                if (req != 4'b0000) begin
                    grant <= ng;
                    if (|(ng & req_sop)) begin
                        locked      <= 1'b1;
                        locked_port <= ng_idx;
                    end else begin
                        rr_ptr <= ng_idx + 1'b1;
                    end
                end else begin
                    grant <= 4'b0000;
                end
            end
        end
    end

endmodule
