// Per-Lane AMCTL Lock FSM
// Implements the state machine for locking onto Alignment Marker and Control (AMCTL)
// based on Figure 3-9 of the UB specification.
//
// States:
// 1. LOCK_INIT: Reset state, wait for enable.
// 2. SLIP: Search for the END field (CW22, CW22) in the bitstream.
// 3. ALIGN: Found first END, wait for the next periodic appearance.
// 4. CONFIRM: Verify multiple consecutive AMCTLs.
// 5. LOCK: Lane is locked, periodically validate.

module ub_pcs_amctl_lock (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,             // AMCTL_Lock_EN
    input  wire        training_mode,  // 1 for 32 cycle data interval, 0 for 40 cycle
    input  wire [31:0] data_in,
    input  wire        data_valid,
    
    output reg         lane_locked,
    output reg  [4:0]  marker_pos      // Bit offset (0-31) of the END field start
);

    // FSM States
    localparam ST_LOCK_INIT = 3'd0;
    localparam ST_SLIP      = 3'd1;
    localparam ST_ALIGN     = 3'd2;
    localparam ST_CONFIRM   = 3'd3;
    localparam ST_LOCK      = 3'd4;

    reg [2:0] state;
    reg [31:0] data_prev;
    reg [5:0]  cycle_cnt;      // Counter for periodicity
    reg [2:0]  confirm_cnt;    // Counter for consecutive matches

    // END field pattern: CW22 (16'h9C78) repeated twice.
    // In the data stream, it appears as 32'h9C789C78 if aligned.
    localparam [31:0] AMCTL_END_PATTERN = 32'h9C789C78;

    wire [63:0] sliding_window = {data_in, data_prev};

    // Find pattern in sliding window
    reg pattern_found;
    reg [4:0] found_pos;
    integer i;
    always @(*) begin
        pattern_found = 1'b0;
        found_pos = 5'd0;
        for (i = 0; i < 32; i = i + 1) begin
            if (sliding_window[i +: 32] == AMCTL_END_PATTERN) begin
                pattern_found = 1'b1;
                found_pos = i[4:0];
            end
        end
        // DEBUG: Print when we see 0x9c789c78
        if (data_valid && data_in == 32'h9C789C78)
            $display("AMCTL_LOCK [%m] DEBUG: data_in=%h, data_prev=%h, sliding_window=%h, pattern_found=%b",
                     data_in, data_prev, sliding_window, pattern_found);
    end

    // Interval between END fields = interval + 10 cycles
    wire [5:0] period = training_mode ? 6'd42 : 6'd50;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_LOCK_INIT;
            lane_locked <= 1'b0;
            marker_pos <= 5'd0;
            data_prev <= 32'd0;
            cycle_cnt <= 6'd0;
            confirm_cnt <= 3'd0;
        end else if (!en) begin
            state <= ST_LOCK_INIT;
            lane_locked <= 1'b0;
        end else if (data_valid) begin
            // DEBUG: Print every data_in
            if (state == ST_SLIP && (cycle_cnt % 10 == 0))
                $display("AMCTL_LOCK [%m] data_in=%h", data_in);
            data_prev <= data_in;
            
            case (state)
                ST_LOCK_INIT: begin
                    state <= ST_SLIP;
                end

                ST_SLIP: begin
                    if (pattern_found) begin
                        marker_pos <= found_pos;
                        cycle_cnt <= 6'd1; // We just found it
                        state <= ST_ALIGN;
                    end
                end

                ST_ALIGN: begin
                    if (cycle_cnt == period) begin
                        cycle_cnt <= 6'd1;
                        if (pattern_found && (found_pos == marker_pos)) begin
                            confirm_cnt <= 3'd1;
                            state <= ST_CONFIRM;
                        end else begin
                            state <= ST_SLIP;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 1;
                    end
                end

                ST_CONFIRM: begin
                    if (cycle_cnt == period) begin
                        cycle_cnt <= 6'd1;
                        if (pattern_found && (found_pos == marker_pos)) begin
                            if (confirm_cnt == 3'd3) begin // Total 4 matches (1 in ALIGN, 3 in CONFIRM)
                                $display("AMCTL_LOCK [%m] LOCKED at pos %d", marker_pos);
                                lane_locked <= 1'b1;
                                state <= ST_LOCK;
                            end
 else begin
                                confirm_cnt <= confirm_cnt + 1;
                            end
                        end else begin
                            state <= ST_SLIP;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 1;
                    end
                end

                ST_LOCK: begin
                    if (cycle_cnt == period) begin
                        cycle_cnt <= 6'd1;
                        if (!(pattern_found && (found_pos == marker_pos))) begin
                            lane_locked <= 1'b0;
                            state <= ST_SLIP;
                        end
                    end else begin
                        cycle_cnt <= cycle_cnt + 1;
                    end
                end

                default: state <= ST_LOCK_INIT;
            endcase
        end
    end

endmodule
