`timescale 1ns/1ps

module ub_pcs_amctl_lock_tb;

    reg clk;
    reg rst_n;
    reg en;
    reg training_mode;
    reg [31:0] data_in;
    reg data_valid;

    wire lane_locked;
    wire [4:0] marker_pos;

    ub_pcs_amctl_lock uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .training_mode(training_mode),
        .data_in(data_in),
        .data_valid(data_valid),
        .lane_locked(lane_locked),
        .marker_pos(marker_pos)
    );

    always #5 clk = ~clk;

    integer i, j;
    localparam [31:0] END_PATTERN = 32'h9C789C78;
    localparam [31:0] DUMMY_DATA = 32'h12345678;

    task send_cycle(input [31:0] val);
        begin
            data_in = val;
            data_valid = 1;
            @(posedge clk);
            #1;
        end
    endtask

    // Helper to send AMCTL with specific bit offset
    task send_amctl(input [4:0] offset);
        reg [63:0] win;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                if (j == 3) begin
                    // END field
                    win = {END_PATTERN, 32'h0} >> offset;
                    send_cycle(win[31:0]);
                    // Wait, next cycle will have the rest of END if offset > 0
                end else if (j == 4 && offset > 0) begin
                    win = {32'h0, END_PATTERN} >> offset;
                    send_cycle(win[31:0]);
                end else begin
                    send_cycle(DUMMY_DATA);
                end
            end
        end
    endtask

    // More precise task to send periodic AMCTLs
    task send_periodic_amctls(input [4:0] offset, input integer count, input integer interval_cycles);
        reg [63:0] combined;
        integer c, k;
        begin
            for (c = 0; c < count; c = c + 1) begin
                // Send 10 cycles of AMCTL-like data
                for (k = 0; k < 10; k = k + 1) begin
                    if (k == 3) begin
                        combined = {32'hAAAA_AAAA, END_PATTERN} << offset;
                        send_cycle(combined[31:0]);
                    end else if (k == 4) begin
                        combined = {32'hAAAA_AAAA, END_PATTERN} << offset;
                        send_cycle(combined[63:32]);
                    end else begin
                        send_cycle(DUMMY_DATA);
                    end
                end
                // Send interval cycles of data
                for (k = 0; k < interval_cycles; k = k + 1) begin
                    send_cycle(DUMMY_DATA);
                end
            end
        end
    endtask

    initial begin
        $dumpfile("ub_pcs_amctl_lock_tb.vcd");
        $dumpvars(0, ub_pcs_amctl_lock_tb);

        clk = 0;
        rst_n = 0;
        en = 0;
        training_mode = 1; // 32 cycle interval
        data_in = 0;
        data_valid = 0;

        #20 rst_n = 1;
        #20 en = 1;

        // Send dummy data for a while
        for (i = 0; i < 20; i = i + 1) send_cycle(DUMMY_DATA);

        // Send periodic AMCTLs with offset 5
        // Total period = 32 (data) + 10 (AMCTL) = 42
        // We send 6 AMCTLs to ensure it locks (requires 4)
        send_periodic_amctls(5, 6, 32);

        if (lane_locked)
            $display("SUCCESS: Lane locked at pos %d", marker_pos);
        else
            $display("FAILURE: Lane NOT locked");

        // Test loss of lock
        for (i = 0; i < 100; i = i + 1) send_cycle(DUMMY_DATA);
        
        if (!lane_locked)
            $display("SUCCESS: Lane unlocked after missing AMCTLs");
        else
            $display("FAILURE: Lane still locked after missing AMCTLs");

        #100;
        $finish;
    end

endmodule
