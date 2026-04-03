// UB PCS Deskew FIFO Buffer
//
// This module implements a per-lane deskew FIFO buffer.
// It performs two main functions:
// 1. Bit-alignment: Uses the 'marker_pos' from the AMCTL lock module to 
//    barrel-shift the incoming 32-bit data into word-aligned chunks.
// 2. Lane deskewing: Buffers the aligned data and identifies the start 
//    of the Alignment Marker Control (AMCTL) block.
//
// The master Lane Aligner will wait for all lanes to report 'fifo_ready',
// then assert 'fifo_read_en' to all FIFOs simultaneously to release
// synchronized data starting from the AMCTL boundary.

module ub_pcs_deskew_fifo (
    input  wire        clk,
    input  wire        rst_n,
    
    // Incoming data from PMA/Descrambler
    input  wire [31:0] data_in,
    input  wire        data_valid,
    
    // Alignment info from ub_pcs_amctl_lock
    input  wire        lane_locked,
    input  wire [4:0]  marker_pos,
    
    // Control from master Lane Aligner
    input  wire        fifo_read_en,
    input  wire        training_mode,
    
    // Aligned and deskewed output
    output reg  [31:0] data_out,
    output reg         data_out_valid,
    output reg         fifo_ready
);

    // FIFO Depth of 128 words (512 bytes) is sufficient to handle
    // maximum expected skew (20ns) and AMCTL buffering.
    localparam DEPTH = 128;
    localparam ADDR_WIDTH = 7;

    reg [31:0] mem [0:DEPTH-1];
    reg [ADDR_WIDTH-1:0] wr_ptr;
    reg [ADDR_WIDTH-1:0] rd_ptr;
    
    // --- Bit Alignment (Barrel Shifter) ---
    reg [31:0] data_prev;
    wire [63:0] sliding_window = {data_in, data_prev};
    wire [31:0] aligned_data = sliding_window[marker_pos +: 32];
    
    // --- AMCTL Tracking ---
    localparam [31:0] AMCTL_END_PATTERN = 32'h9C789C78;
    reg [ADDR_WIDTH-1:0] first_amctl_ptr;
    reg [1:0]            amctl_count;
    
    // --- FIFO Control ---
    reg reading;
    reg [5:0] skip_timer;
    wire [5:0] data_interval = training_mode ? 6'd32 : 6'd40;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            data_prev <= 32'h0;
            first_amctl_ptr <= 0;
            amctl_count <= 2'd0;
            fifo_ready <= 1'b0;
            data_out <= 32'h0;
            data_out_valid <= 1'b0;
            reading <= 1'b0;
            skip_timer <= 0;
        end else begin
            // Write Path: Buffer bit-aligned data
            if (data_valid) begin
                data_prev <= data_in;
                mem[wr_ptr] <= aligned_data;
                
                // Identify AMCTL start position
                if (aligned_data == AMCTL_END_PATTERN) begin
                    if (amctl_count == 0) begin
                        first_amctl_ptr <= wr_ptr - 7'd4;
                    end
                    if (amctl_count < 2'd3)
                        amctl_count <= amctl_count + 1'b1;
                end
                
                wr_ptr <= wr_ptr + 1'b1;
            end
            
            // Status signaling to Lane Aligner
            if (lane_locked && amctl_count >= 2'd2) begin
                fifo_ready <= 1'b1;
            end else if (!lane_locked) begin
                fifo_ready <= 1'b0;
                amctl_count <= 2'd0;
            end
            
            // Read Path: Synchronized release with AMCTL stripping
            if (fifo_read_en) begin
                if (!reading) begin
                    rd_ptr <= first_amctl_ptr + 7'd10;
                    reading <= 1'b1;
                    skip_timer <= 0;
                    data_out_valid <= 1'b0;
                end else begin
                    if (skip_timer < data_interval) begin
                        data_out <= mem[rd_ptr];
                        data_out_valid <= 1'b1;
                        rd_ptr <= rd_ptr + 1'b1;
                        skip_timer <= skip_timer + 1;
                    end else if (skip_timer < data_interval + 9) begin
                        data_out_valid <= 1'b0;
                        rd_ptr <= rd_ptr + 1'b1;
                        skip_timer <= skip_timer + 1;
                    end else begin
                        data_out_valid <= 1'b0;
                        rd_ptr <= rd_ptr + 1'b1;
                        skip_timer <= 0;
                    end
                end
            end else begin
                reading <= 1'b0;
                data_out_valid <= 1'b0;
                skip_timer <= 0;
            end
        end
    end

endmodule
