//-----------------------------------------------------------------------------
// Module: ub_dll_tx_engine
// DLL TX engine: multiplexes data flits, null blocks, and retry flits.
// 640-bit flit interface. Integrates flow control and retry controller.
//-----------------------------------------------------------------------------
module ub_dll_tx_engine (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         link_ready,
    // Network layer input (640-bit flits)
    input  wire [639:0] nw_flit_in,
    input  wire         nw_flit_valid,
    input  wire         nw_flit_sop,
    input  wire         nw_flit_eop,
    output wire         nw_flit_ready,
    // Flit output to PCS TX pipe
    output reg  [639:0] flit_out,
    output reg          flit_valid,
    input  wire         flit_ready,
    // Retry/flow control from RX engine
    input  wire         retry_req_received,
    input  wire [7:0]   retry_rcvptr,
    input  wire         ack_received,
    input  wire [7:0]   ack_ptr,
    input  wire         credit_return,
    input  wire [7:0]   credit_return_amt
);

    // Null block: all zeros with control indicator (bit 639 = 0)
    localparam [639:0] NULL_BLOCK = 640'd0;

    //-------------------------------------------------------------------------
    // Flow control
    //-------------------------------------------------------------------------
    wire        tx_credit_avail;
    reg         tx_flit_sent;
    wire [7:0]  credit_count;

    ub_dll_flow_ctrl u_flow_ctrl (
        .clk              (clk),
        .rst_n            (rst_n),
        .credit_init      (link_ready && !credit_count_init_done),
        .credit_init_val  (8'd32),
        .tx_flit_sent     (tx_flit_sent),
        .tx_credit_avail  (tx_credit_avail),
        .credit_return    (credit_return),
        .credit_return_amt(credit_return_amt),
        .credit_count     (credit_count)
    );

    reg credit_count_init_done;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            credit_count_init_done <= 1'b0;
        else if (link_ready)
            credit_count_init_done <= 1'b1;
    end

    //-------------------------------------------------------------------------
    // Retry controller
    //-------------------------------------------------------------------------
    wire [639:0] retry_flit;
    wire         retry_flit_valid_w;
    wire         retry_active;

    ub_dll_retry_ctrl u_retry_ctrl (
        .clk               (clk),
        .rst_n             (rst_n),
        .tx_flit_in        (flit_out),
        .tx_flit_valid     (flit_valid && flit_ready),
        .is_null_block     (flit_out == NULL_BLOCK),
        .retry_req_received(retry_req_received),
        .retry_rcvptr      (retry_rcvptr),
        .ack_received      (ack_received),
        .ack_ptr           (ack_ptr),
        .retry_flit_out    (retry_flit),
        .retry_flit_valid  (retry_flit_valid_w),
        .retry_active      (retry_active)
    );

    //-------------------------------------------------------------------------
    // Output MUX (priority: retry > data > null)
    //-------------------------------------------------------------------------
    // NW ready: accept data when link ready, credit available, not retrying, downstream ready
    assign nw_flit_ready = link_ready && tx_credit_avail && !retry_active && flit_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            flit_out     <= NULL_BLOCK;
            flit_valid   <= 1'b0;
            tx_flit_sent <= 1'b0;
        end else if (!link_ready) begin
            flit_out     <= NULL_BLOCK;
            flit_valid   <= 1'b0;
            tx_flit_sent <= 1'b0;
        end else if (flit_ready || !flit_valid) begin
            tx_flit_sent <= 1'b0;
            if (retry_active && retry_flit_valid_w) begin
                // Priority 1: retransmit flit
                flit_out     <= retry_flit;
                flit_valid   <= 1'b1;
            end else if (nw_flit_valid && tx_credit_avail && !retry_active) begin
                // Priority 2: data flit (mark bit 639 = 1 for data)
                flit_out     <= {1'b1, nw_flit_in[638:0]};
                flit_valid   <= 1'b1;
                tx_flit_sent <= 1'b1;
            end else begin
                // Priority 3: null block
                flit_out     <= NULL_BLOCK;
                flit_valid   <= 1'b1;
            end
        end
    end

endmodule
