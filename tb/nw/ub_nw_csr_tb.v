module ub_nw_csr_tb;
    reg clk, rst_n, reg_wen;
    reg [15:0] reg_wdata;
    wire [15:0] local_scna;

    ub_nw_csr uut (
        .clk(clk), .rst_n(rst_n),
        .reg_wen(reg_wen), .reg_wdata(reg_wdata),
        .local_scna(local_scna)
    );

    always #5 clk = ~clk;
    initial begin
        clk = 0; rst_n = 0; reg_wen = 0; reg_wdata = 0;
        #20 rst_n = 1;
        #10 reg_wen = 1; reg_wdata = 16'h1234;
        #10 reg_wen = 0;
        #10 if (local_scna != 16'h1234) $display("FAIL: CSR not updated");
        else $display("PASS: Local SCNA = %h", local_scna);
        $finish;
    end
endmodule
