//-----------------------------------------------------------------------------
// Module: ub_cdc_async_fifo
// Asynchronous FIFO with gray-code pointer synchronization for CDC.
// Parameterized data width and depth (depth must be power of 2).
//-----------------------------------------------------------------------------
module ub_cdc_async_fifo #(
    parameter DATA_WIDTH = 128,
    parameter ADDR_WIDTH = 4           // depth = 2^ADDR_WIDTH = 16
)(
    // Write port (source clock domain)
    input  wire                    wr_clk,
    input  wire                    wr_rst_n,
    input  wire [DATA_WIDTH-1:0]   wr_data,
    input  wire                    wr_en,
    output wire                    wr_full,

    // Read port (destination clock domain)
    input  wire                    rd_clk,
    input  wire                    rd_rst_n,
    output wire [DATA_WIDTH-1:0]   rd_data,
    input  wire                    rd_en,
    output wire                    rd_empty
);

    localparam DEPTH = 1 << ADDR_WIDTH;
    localparam PTR_WIDTH = ADDR_WIDTH + 1; // extra MSB for full/empty

    // Dual-port RAM
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // Write domain pointers
    reg  [PTR_WIDTH-1:0] wr_ptr_bin;
    wire [PTR_WIDTH-1:0] wr_ptr_gray;
    wire [ADDR_WIDTH-1:0] wr_addr;

    // Read domain pointers
    reg  [PTR_WIDTH-1:0] rd_ptr_bin;
    wire [PTR_WIDTH-1:0] rd_ptr_gray;
    wire [ADDR_WIDTH-1:0] rd_addr;

    // Synchronized pointers
    wire [PTR_WIDTH-1:0] wr_ptr_gray_sync; // wr_ptr synced to rd_clk
    wire [PTR_WIDTH-1:0] rd_ptr_gray_sync; // rd_ptr synced to wr_clk

    //-------------------------------------------------------------------------
    // Binary to Gray conversion
    //-------------------------------------------------------------------------
    assign wr_ptr_gray = wr_ptr_bin ^ (wr_ptr_bin >> 1);
    assign rd_ptr_gray = rd_ptr_bin ^ (rd_ptr_bin >> 1);

    //-------------------------------------------------------------------------
    // Address extraction
    //-------------------------------------------------------------------------
    assign wr_addr = wr_ptr_bin[ADDR_WIDTH-1:0];
    assign rd_addr = rd_ptr_bin[ADDR_WIDTH-1:0];

    //-------------------------------------------------------------------------
    // Gray-code pointer synchronizers
    //-------------------------------------------------------------------------
    ub_cdc_gray_sync #(.WIDTH(PTR_WIDTH)) u_wr2rd_sync (
        .clk      (rd_clk),
        .rst_n    (rd_rst_n),
        .data_in  (wr_ptr_gray),
        .data_out (wr_ptr_gray_sync)
    );

    ub_cdc_gray_sync #(.WIDTH(PTR_WIDTH)) u_rd2wr_sync (
        .clk      (wr_clk),
        .rst_n    (wr_rst_n),
        .data_in  (rd_ptr_gray),
        .data_out (rd_ptr_gray_sync)
    );

    //-------------------------------------------------------------------------
    // Full flag (write domain): gray pointers match except top 2 bits inverted
    //-------------------------------------------------------------------------
    wire [PTR_WIDTH-1:0] wr_full_cmp;
    assign wr_full_cmp = {~rd_ptr_gray_sync[PTR_WIDTH-1:PTR_WIDTH-2],
                           rd_ptr_gray_sync[PTR_WIDTH-3:0]};
    assign wr_full = (wr_ptr_gray == wr_full_cmp);

    //-------------------------------------------------------------------------
    // Empty flag (read domain): empty when pointers are equal
    //-------------------------------------------------------------------------
    assign rd_empty = (rd_ptr_gray == wr_ptr_gray_sync);

    //-------------------------------------------------------------------------
    // Write logic
    //-------------------------------------------------------------------------
    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_ptr_bin <= {PTR_WIDTH{1'b0}};
        end else if (wr_en && !wr_full) begin
            mem[wr_addr] <= wr_data;
            wr_ptr_bin   <= wr_ptr_bin + 1'b1;
        end
    end

    //-------------------------------------------------------------------------
    // Read logic
    //-------------------------------------------------------------------------
    assign rd_data = mem[rd_addr];

    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_ptr_bin <= {PTR_WIDTH{1'b0}};
        end else if (rd_en && !rd_empty) begin
            rd_ptr_bin <= rd_ptr_bin + 1'b1;
        end
    end

endmodule
