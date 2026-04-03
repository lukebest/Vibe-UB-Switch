//-----------------------------------------------------------------------------
// Module: ub_xbar_outq
// Per-output-port store-and-forward queue.
// Stores {data[511:0], sop, eop} per entry.
//-----------------------------------------------------------------------------
module ub_xbar_outq #(
    parameter DEPTH = 8
)(
    input  wire         clk,
    input  wire         rst_n,
    input  wire [511:0] wr_data,
    input  wire         wr_valid,
    input  wire         wr_sop,
    input  wire         wr_eop,
    output wire         wr_ready,
    output wire [511:0] rd_data,
    output wire         rd_valid,
    output wire         rd_sop,
    output wire         rd_eop,
    input  wire         rd_ready
);

    localparam ENTRY_W = 514; // 512 data + sop + eop
    localparam ADDR_W  = $clog2(DEPTH);

    reg [ENTRY_W-1:0] mem [0:DEPTH-1];
    reg [ADDR_W:0]    wr_ptr, rd_ptr;
    reg [ADDR_W:0]    pkt_boundary_ptr; // points to start of complete packet

    wire [ADDR_W:0] count = wr_ptr - rd_ptr;
    wire full  = (count == DEPTH);
    wire empty = (rd_ptr == pkt_boundary_ptr); // only read complete packets

    assign wr_ready = !full;

    // Write
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr           <= 0;
            pkt_boundary_ptr <= 0;
        end else if (wr_valid && !full) begin
            mem[wr_ptr[ADDR_W-1:0]] <= {wr_eop, wr_sop, wr_data};
            wr_ptr <= wr_ptr + 1;
            if (wr_eop)
                pkt_boundary_ptr <= wr_ptr + 1;
        end
    end

    // Read
    wire [ENTRY_W-1:0] rd_entry = mem[rd_ptr[ADDR_W-1:0]];
    assign rd_data  = rd_entry[511:0];
    assign rd_sop   = rd_entry[512];
    assign rd_eop   = rd_entry[513];
    assign rd_valid  = !empty;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= 0;
        end else if (rd_valid && rd_ready) begin
            rd_ptr <= rd_ptr + 1;
        end
    end

endmodule
