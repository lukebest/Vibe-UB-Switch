// Integrated Lane Aligner (RX)
//
// This module integrates 4 instances of ub_pcs_amctl_lock and 
// ub_pcs_deskew_fifo to perform multi-lane deskewing and alignment.
//
// Alignment Process:
// 1. Each lane independently locks onto its AMCTL sequence.
// 2. Each lane's FIFO buffers the bit-aligned data and identifies the AMCTL start.
// 3. The aligner waits for all lanes to assert 'fifo_ready'.
// 4. Once all lanes are ready, 'fifo_read_en' is asserted to all FIFOs 
//    simultaneously, ensuring the synchronized output of data starting
//    from the AMCTL boundary.

module ub_pcs_lane_aligner (
    input  wire        clk,
    input  wire        rst_n,
    
    // 4 lanes of incoming data from PMA/Descrambler
    input  wire [31:0] lane0_data_in,
    input  wire        lane0_data_valid,
    input  wire [31:0] lane1_data_in,
    input  wire        lane1_data_valid,
    input  wire [31:0] lane2_data_in,
    input  wire        lane2_data_valid,
    input  wire [31:0] lane3_data_in,
    input  wire        lane3_data_valid,
    
    // Control
    input  wire        en,
    input  wire        training_mode,
    
    // Aligned outputs
    output wire [31:0] lane0_data_out,
    output wire        lane0_data_out_valid,
    output wire [31:0] lane1_data_out,
    output wire        lane1_data_out_valid,
    output wire [31:0] lane2_data_out,
    output wire        lane2_data_out_valid,
    output wire [31:0] lane3_data_out,
    output wire        lane3_data_out_valid,
    
    output wire        all_lanes_aligned
);

    // Internal signals for Lane 0
    wire [4:0] lane0_marker_pos;
    wire       lane0_locked;
    wire       lane0_fifo_ready;
    
    // Internal signals for Lane 1
    wire [4:0] lane1_marker_pos;
    wire       lane1_locked;
    wire       lane1_fifo_ready;
    
    // Internal signals for Lane 2
    wire [4:0] lane2_marker_pos;
    wire       lane2_locked;
    wire       lane2_fifo_ready;
    
    // Internal signals for Lane 3
    wire [4:0] lane3_marker_pos;
    wire       lane3_locked;
    wire       lane3_fifo_ready;
    
    reg fifo_read_en;
    
    // Master Alignment Logic
    // Wait for all lanes to report fifo_ready
    assign all_lanes_aligned = lane0_fifo_ready && lane1_fifo_ready && 
                               lane2_fifo_ready && lane3_fifo_ready;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fifo_read_en <= 1'b0;
        end else if (en) begin
            if (all_lanes_aligned) begin
                fifo_read_en <= 1'b1;
            end else begin
                // Optional: We could keep it high once triggered, 
                // but the FIFO 'reading' state handles persistence.
                // If any lane loses lock, we might want to drop read_en.
                fifo_read_en <= 1'b0;
            end
        end else begin
            fifo_read_en <= 1'b0;
        end
    end

    // Lane 0 Instantiation
    ub_pcs_amctl_lock i_lock0 (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .training_mode(training_mode),
        .data_in(lane0_data_in),
        .data_valid(lane0_data_valid),
        .lane_locked(lane0_locked),
        .marker_pos(lane0_marker_pos)
    );
    
    ub_pcs_deskew_fifo i_fifo0 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(lane0_data_in),
        .data_valid(lane0_data_valid),
        .lane_locked(lane0_locked),
        .marker_pos(lane0_marker_pos),
        .fifo_read_en(fifo_read_en),
        .training_mode(training_mode),
        .data_out(lane0_data_out),
        .data_out_valid(lane0_data_out_valid),
        .fifo_ready(lane0_fifo_ready)
    );

    // Lane 1 Instantiation
    ub_pcs_amctl_lock i_lock1 (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .training_mode(training_mode),
        .data_in(lane1_data_in),
        .data_valid(lane1_data_valid),
        .lane_locked(lane1_locked),
        .marker_pos(lane1_marker_pos)
    );
    
    ub_pcs_deskew_fifo i_fifo1 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(lane1_data_in),
        .data_valid(lane1_data_valid),
        .lane_locked(lane1_locked),
        .marker_pos(lane1_marker_pos),
        .fifo_read_en(fifo_read_en),
        .training_mode(training_mode),
        .data_out(lane1_data_out),
        .data_out_valid(lane1_data_out_valid),
        .fifo_ready(lane1_fifo_ready)
    );

    // Lane 2 Instantiation
    ub_pcs_amctl_lock i_lock2 (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .training_mode(training_mode),
        .data_in(lane2_data_in),
        .data_valid(lane2_data_valid),
        .lane_locked(lane2_locked),
        .marker_pos(lane2_marker_pos)
    );
    
    ub_pcs_deskew_fifo i_fifo2 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(lane2_data_in),
        .data_valid(lane2_data_valid),
        .lane_locked(lane2_locked),
        .marker_pos(lane2_marker_pos),
        .fifo_read_en(fifo_read_en),
        .training_mode(training_mode),
        .data_out(lane2_data_out),
        .data_out_valid(lane2_data_out_valid),
        .fifo_ready(lane2_fifo_ready)
    );

    // Lane 3 Instantiation
    ub_pcs_amctl_lock i_lock3 (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .training_mode(training_mode),
        .data_in(lane3_data_in),
        .data_valid(lane3_data_valid),
        .lane_locked(lane3_locked),
        .marker_pos(lane3_marker_pos)
    );
    
    ub_pcs_deskew_fifo i_fifo3 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(lane3_data_in),
        .data_valid(lane3_data_valid),
        .lane_locked(lane3_locked),
        .marker_pos(lane3_marker_pos),
        .fifo_read_en(fifo_read_en),
        .training_mode(training_mode),
        .data_out(lane3_data_out),
        .data_out_valid(lane3_data_out_valid),
        .fifo_ready(lane3_fifo_ready)
    );

endmodule
