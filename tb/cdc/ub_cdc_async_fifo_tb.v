//-----------------------------------------------------------------------------
// Testbench: ub_cdc_async_fifo_tb
// Verifies async FIFO with dual clocks (1.25GHz write, 921.875MHz read)
//-----------------------------------------------------------------------------
`timescale 1ps/1ps

module ub_cdc_async_fifo_tb;

    parameter DATA_WIDTH = 128;
    parameter ADDR_WIDTH = 4;
    parameter NUM_PACKETS = 200;

    // Clock periods in ps
    localparam WR_CLK_PERIOD = 800;    // 1.25 GHz = 800 ps
    localparam RD_CLK_PERIOD = 1085;   // 921.875 MHz ~ 1085 ps

    reg                    wr_clk, rd_clk;
    reg                    wr_rst_n, rd_rst_n;
    reg  [DATA_WIDTH-1:0]  wr_data;
    reg                    wr_en;
    wire                   wr_full;
    wire [DATA_WIDTH-1:0]  rd_data;
    reg                    rd_en;
    wire                   rd_empty;

    // Reference model
    reg [DATA_WIDTH-1:0] ref_queue [0:NUM_PACKETS-1];
    integer wr_count, rd_count;
    integer errors;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    ub_cdc_async_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .wr_clk   (wr_clk),
        .wr_rst_n (wr_rst_n),
        .wr_data  (wr_data),
        .wr_en    (wr_en),
        .wr_full  (wr_full),
        .rd_clk   (rd_clk),
        .rd_rst_n (rd_rst_n),
        .rd_data  (rd_data),
        .rd_en    (rd_en),
        .rd_empty (rd_empty)
    );

    //-------------------------------------------------------------------------
    // Clock generation
    //-------------------------------------------------------------------------
    initial wr_clk = 0;
    always #(WR_CLK_PERIOD/2) wr_clk = ~wr_clk;

    initial rd_clk = 0;
    always #(RD_CLK_PERIOD/2) rd_clk = ~rd_clk;

    //-------------------------------------------------------------------------
    // Write process
    //-------------------------------------------------------------------------
    initial begin
        wr_rst_n = 0;
        wr_en    = 0;
        wr_data  = 0;
        wr_count = 0;
        #(WR_CLK_PERIOD * 10);
        wr_rst_n = 1;
        #(WR_CLK_PERIOD * 5);

        while (wr_count < NUM_PACKETS) begin
            @(posedge wr_clk);
            #1;
            if (!wr_full) begin
                wr_data = {wr_count[31:0], wr_count[31:0], wr_count[31:0], wr_count[31:0]};
                wr_en   = 1;
                ref_queue[wr_count] = wr_data;
                wr_count = wr_count + 1;
            end else begin
                wr_en = 0;
            end
        end
        // Hold wr_en for one more cycle so last entry is captured
        @(posedge wr_clk);
        #1;
        wr_en = 0;
        $display("WRITE DONE: wrote %0d entries", wr_count);
    end

    //-------------------------------------------------------------------------
    // Read process
    //-------------------------------------------------------------------------
    initial begin
        rd_rst_n = 0;
        rd_en    = 0;
        rd_count = 0;
        errors   = 0;
        #(RD_CLK_PERIOD * 10);
        rd_rst_n = 1;
        #(RD_CLK_PERIOD * 5);

        while (rd_count < NUM_PACKETS) begin
            @(posedge rd_clk);
            #1;
            if (!rd_empty) begin
                // Capture data before asserting rd_en
                if (rd_data !== ref_queue[rd_count]) begin
                    $display("ERROR [%0d]: expected %h, got %h", rd_count, ref_queue[rd_count], rd_data);
                    errors = errors + 1;
                end
                rd_en = 1;
                rd_count = rd_count + 1;
            end else begin
                rd_en = 0;
            end
        end
        @(posedge rd_clk);
        rd_en = 0;

        #(RD_CLK_PERIOD * 10);
        if (errors == 0)
            $display("PASS: All %0d entries matched.", NUM_PACKETS);
        else
            $display("FAIL: %0d errors out of %0d.", errors, NUM_PACKETS);
        $finish;
    end

    // Timeout
    initial begin
        #(RD_CLK_PERIOD * NUM_PACKETS * 200);
        $display("TIMEOUT: wr_count=%0d rd_count=%0d", wr_count, rd_count);
        $display("  wr_full=%b rd_empty=%b", wr_full, rd_empty);
        $display("  wr_ptr_bin=%h rd_ptr_bin=%h", dut.wr_ptr_bin, dut.rd_ptr_bin);
        $display("  wr_ptr_gray=%h rd_ptr_gray=%h", dut.wr_ptr_gray, dut.rd_ptr_gray);
        $display("  wr_ptr_gray_sync=%h rd_ptr_gray_sync=%h", dut.wr_ptr_gray_sync, dut.rd_ptr_gray_sync);
        $finish;
    end

endmodule
