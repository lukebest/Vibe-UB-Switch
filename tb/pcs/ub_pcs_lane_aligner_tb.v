`timescale 1ns/1ps

module ub_pcs_lane_aligner_tb;

    reg clk;
    reg rst_n;
    reg en;
    reg training_mode;

    reg [31:0] l0_in, l1_in, l2_in, l3_in;
    reg l0_vld, l1_vld, l2_vld, l3_vld;

    wire [31:0] l0_out, l1_out, l2_out, l3_out;
    wire l0_out_vld, l1_out_vld, l2_out_vld, l3_out_vld;
    wire all_aligned;

    // Instantiate Unit Under Test
    ub_pcs_lane_aligner uut (
        .clk(clk),
        .rst_n(rst_n),
        .lane0_data_in(l0_in),
        .lane0_data_valid(l0_vld),
        .lane1_data_in(l1_in),
        .lane1_data_valid(l1_vld),
        .lane2_data_in(l2_in),
        .lane2_data_valid(l2_vld),
        .lane3_data_in(l3_in),
        .lane3_data_valid(l3_vld),
        .en(en),
        .training_mode(training_mode),
        .lane0_data_out(l0_out),
        .lane0_data_out_valid(l0_out_vld),
        .lane1_data_out(l1_out),
        .lane1_data_out_valid(l1_out_vld),
        .lane2_data_out(l2_out),
        .lane2_data_out_valid(l2_out_vld),
        .lane3_data_out(l3_out),
        .lane3_data_out_valid(l3_out_vld),
        .all_lanes_aligned(all_aligned)
    );

    // Clock generation
    always #5 clk = ~clk;

    localparam [31:0] AMCTL_END = 32'h9C789C78;
    localparam [31:0] DUMMY = 32'hDEADBEEF;

    // Master stream generation
    reg [31:0] master_stream [0:4095];
    
    task gen_amctl(input integer start_idx);
        begin
            master_stream[start_idx+0] = 32'hA1A1A1A1; // BODY
            master_stream[start_idx+1] = 32'hB2B2B2B2; // BODY
            master_stream[start_idx+2] = 32'hC3C3C3C3; // BODY
            master_stream[start_idx+3] = AMCTL_END;    // END
            master_stream[start_idx+4] = 32'h11111111; // LID
            master_stream[start_idx+5] = 32'h22222222; // LID
            master_stream[start_idx+6] = 32'h33333333; // CTRL
            master_stream[start_idx+7] = 32'h44444444; // CTRL
            master_stream[start_idx+8] = 32'h55555555; // DETAIL
            master_stream[start_idx+9] = 32'h66666666; // DETAIL
        end
    endtask

    integer s, p;
    initial begin
        for (s = 0; s < 4096; s = s + 1) master_stream[s] = DUMMY;
        
        // Periodic AMCTL every 42 words (training_mode=1)
        for (p = 0; p < 80; p = p + 1) begin
            gen_amctl(100 + p*42);
            // Fill with unique data after AMCTL
            for (s = 100 + p*42 + 10; s < 100 + (p+1)*42; s = s + 1)
                master_stream[s] = s;
        end
    end

    // Lane senders with skew and bit offset
    task send_lane(input integer lane, input integer cycle_skew, input integer bit_offset);
        integer t;
        reg [63:0] win;
        begin
            $display("SEND_LANE[%0d] START: skew=%d, bit_offset=%d", lane, cycle_skew, bit_offset);
            for (t = 1; t < 3000; t = t + 1) begin
                // DEBUG: Print every 50 iterations
                if (lane == 0 && t % 50 == 0)
                    $display("SEND_LANE[%0d]: t=%d", lane, t);

                if (t < cycle_skew + 2) begin
                    case(lane)
                        0: begin l0_in = DUMMY; l0_vld = 1; end
                        1: begin l1_in = DUMMY; l1_vld = 1; end
                        2: begin l2_in = DUMMY; l2_vld = 1; end
                        3: begin l3_in = DUMMY; l3_vld = 1; end
                    endcase
                end else begin
                    // Apply bit offset via sliding window
                    // win[63:32] = current data, win[31:0] = previous data
                    win = {master_stream[t-cycle_skew], master_stream[(t-cycle_skew-1 < 0) ? 0 : t-cycle_skew-1]};
                    // DEBUG: Print AMCTL data around cycle 100
                    if (lane == 0 && t > 95 && t < 110)
                        $display("SEND_LANE: t=%d | master_stream[%d]=%h | win=%h | bit_offset=%d",
                                 t, t-cycle_skew, master_stream[t-cycle_skew], win, bit_offset);

                    // Extract from high 32 bits (current data) + bit_offset
                    case(lane)
                        0: begin l0_in = win[32+bit_offset +: 32]; l0_vld = 1; end
                        1: begin l1_in = win[32+bit_offset +: 32]; l1_vld = 1; end
                        2: begin l2_in = win[32+bit_offset +: 32]; l2_vld = 1; end
                        3: begin l3_in = win[32+bit_offset +: 32]; l3_vld = 1; end
                    endcase
                    // DEBUG: Print l0_in value for Lane 0
                    if (lane == 0 && t > 95 && t < 110)
                        $display("SEND_LANE: t=%d | l0_in=%h", t, l0_in);
                end
                @(posedge clk);
                #1;
            end
            $display("SEND_LANE[%0d] END: t reached %d", lane, t);
        end
    endtask

    initial begin
        $dumpfile("ub_pcs_lane_aligner_tb.vcd");
        $dumpvars(0, ub_pcs_lane_aligner_tb);

        clk = 0;
        rst_n = 0;
        en = 0;
        training_mode = 1;
        l0_in = 0; l0_vld = 0;
        l1_in = 0; l1_vld = 0;
        l2_in = 0; l2_vld = 0;
        l3_in = 0; l3_vld = 0;

        #100 rst_n = 1;
        #100 en = 1;

        fork
            send_lane(0, 0,  0);  
            send_lane(1, 5,  8);  
            send_lane(2, 12, 17); 
            send_lane(3, 8,  31); 
        join

        #20000;
        $display("Simulation finished.");
        $finish;
    end

    // Verification and Debug Logic
    integer aligned_count = 0;
    reg first_aligned = 1;
    integer debug_cnt = 0;
    always @(posedge clk) begin
        // DEBUG: Sample data stream (around cycle 100-200 where AMCTL should be)
        if (debug_cnt < 30 && uut.i_lock0.data_valid) begin
            $display("TIME: %t | L0 data: %h | state=%d | pattern_found=%b | cnt=%d",
                     $time, uut.i_lock0.data_in, uut.i_lock0.state, uut.i_lock0.pattern_found, debug_cnt);
            debug_cnt = debug_cnt + 1;
        end
        // DEBUG: Monitor lane lock status
        if (uut.lane0_locked) begin
            $display("TIME: %t | Lane 0 Locked | marker_pos=%d", $time, uut.i_lock0.marker_pos);
        end
        if (all_aligned) begin
            if (first_aligned) begin
                $display("TIME: %t | FIRST ALIGNMENT ACHIEVED", $time);
                first_aligned = 0;
            end
            if (l0_out_vld && l1_out_vld && l2_out_vld && l3_out_vld) begin
                if (l0_out == l1_out && l1_out == l2_out && l2_out == l3_out) begin
                    aligned_count = aligned_count + 1;
                    if (aligned_count % 100 == 0)
                        $display("TIME: %t | ALL LANES ALIGNED | DATA: %h", $time, l0_out);
                end else begin
                    $display("TIME: %t | ERROR: MISALIGNMENT DETECTED!", $time);
                    $display("  L0: %h, L1: %h, L2: %h, L3: %h", l0_out, l1_out, l2_out, l3_out);
                end
            end
        end
    end

    initial begin
        forever begin
            #5000;
            $display("TIME: %t | STATUS: L0_lock=%b, L1_lock=%b, L2_lock=%b, L3_lock=%b", 
                     $time, uut.lane0_locked, uut.lane1_locked, uut.lane2_locked, uut.lane3_locked);
            $display("TIME: %t | STATUS: L0_ready=%b, L1_ready=%b, L2_ready=%b, L3_ready=%b", 
                     $time, uut.lane0_fifo_ready, uut.lane1_fifo_ready, uut.lane2_fifo_ready, uut.lane3_fifo_ready);
        end
    end

endmodule
