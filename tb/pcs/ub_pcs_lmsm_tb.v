module ub_pcs_lmsm_tb;
    reg clk, rst_n, start_train;
    reg [159:0] rx_flit_in;
    wire [159:0] tx_flit_out;
    wire link_up, link_ready;
    wire [2:0] current_state;

    ub_pcs_lmsm uut (
        .clk(clk), .rst_n(rst_n),
        .start_train(start_train),
        .rx_flit_in(rx_flit_in),
        .tx_flit_out(tx_flit_out),
        .link_up(link_up),
        .link_ready(link_ready),
        .state_dbg(current_state)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("ub_pcs_lmsm_tb.vcd");
        $dumpvars(0, ub_pcs_lmsm_tb);
        clk = 0; rst_n = 0; start_train = 0; rx_flit_in = 160'd0;
        #20 rst_n = 1;
        #10 if (current_state !== 3'd0) $display("FAIL: Not in LINK_IDLE");
        else $display("PASS: In LINK_IDLE");

        // Set start_train
        @(posedge clk);
        start_train <= 1;
        @(posedge clk);
        #1;
        if (current_state !== 3'd1) $display("FAIL: Expected PROBE_WAIT (3'd1), got %d", current_state);
        else $display("PASS: In PROBE_WAIT");
        start_train <= 0;

        // Wait for Discovery
        repeat (10) @(posedge clk);
        #1;
        if (current_state !== 3'd2) $display("FAIL: Expected DISC_ACTIVE (3'd2), got %d", current_state);
        else $display("PASS: In DISC_ACTIVE");

        // Feed 8 DLTBs (8'h01)
        repeat (8) begin
            @(posedge clk);
            rx_flit_in <= {8'h01, 152'h0};
        end
        @(posedge clk);
        rx_flit_in <= 160'd0;
        #1;
        if (current_state !== 3'd3) $display("FAIL: Expected DISC_CONFIRM (3'd3), got %d", current_state);
        else $display("PASS: In DISC_CONFIRM");

        // Feed 8 DLTBs (8'h02)
        repeat (8) begin
            @(posedge clk);
            rx_flit_in <= {8'h02, 152'h0};
        end
        @(posedge clk);
        rx_flit_in <= 160'd0;
        #1;
        if (current_state !== 3'd4) $display("FAIL: Expected CONFIG_ACTIVE (3'd4), got %d", current_state);
        else $display("PASS: In CONFIG_ACTIVE");

        // Feed 2 CLTBs (8'h03)
        repeat (2) begin
            @(posedge clk);
            rx_flit_in <= {8'h03, 152'h0};
        end
        @(posedge clk);
        rx_flit_in <= 160'd0;
        #1;
        if (current_state !== 3'd5) $display("FAIL: Expected CONFIG_CHECK (3'd5), got %d", current_state);
        else $display("PASS: In CONFIG_CHECK");

        // Feed 2 CLTBs (8'h04)
        repeat (2) begin
            @(posedge clk);
            rx_flit_in <= {8'h04, 152'h0};
        end
        @(posedge clk);
        rx_flit_in <= 160'd0;
        #1;
        if (current_state !== 3'd6) $display("FAIL: Expected LINK_ACTIVE (3'd6), got %d", current_state);
        else $display("PASS: In LINK_ACTIVE");

        // Wait one more cycle for link_up and link_ready to update
        @(posedge clk);
        #1;
        // Verify link_up and link_ready
        if (link_up && link_ready) $display("PASS: Link is UP and READY");
        else $display("FAIL: Link is NOT UP or READY (up=%b, ready=%b)", link_up, link_ready);

        $finish;
    end
endmodule
