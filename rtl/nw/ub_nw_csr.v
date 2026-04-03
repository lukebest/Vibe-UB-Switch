module ub_nw_csr (
    input clk, rst_n,
    input reg_wen,
    input [15:0] reg_wdata,
    output reg [15:0] local_scna
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) local_scna <= 16'h0001; // Default CNA
        else if (reg_wen) local_scna <= reg_wdata;
    end
endmodule
