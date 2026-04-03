//-----------------------------------------------------------------------------
// Module: ub_dll_flow_ctrl
// Simplified credit-based flow control for single VL.
// Tracks available TX credits; decrements on send, increments on return.
//-----------------------------------------------------------------------------
module ub_dll_flow_ctrl (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        credit_init,
    input  wire [7:0]  credit_init_val,
    input  wire        tx_flit_sent,
    output wire        tx_credit_avail,
    input  wire        credit_return,
    input  wire [7:0]  credit_return_amt,
    output reg  [7:0]  credit_count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            credit_count <= 8'd0;
        end else if (credit_init) begin
            credit_count <= credit_init_val;
        end else begin
            case ({tx_flit_sent, credit_return})
                2'b10:   credit_count <= (credit_count > 0) ? credit_count - 8'd1 : 8'd0;
                2'b01:   credit_count <= (credit_count + credit_return_amt > 8'd255) ?
                                         8'd255 : credit_count + credit_return_amt;
                2'b11:   credit_count <= credit_count + credit_return_amt - 8'd1;
                default: ;
            endcase
        end
    end

    assign tx_credit_avail = (credit_count > 8'd0);

endmodule
