module ub_pcs_ebch16_lut (
    input  wire [2:0]  index,
    output reg  [15:0] codeword
);

    always @(*) begin
        case (index)
            3'd0: codeword = 16'b00100111_11011000;
            3'd1: codeword = 16'b00011011_00011011;
            3'd2: codeword = 16'b11100100_11100100;
            3'd3: codeword = 16'b11011000_00100111;
            3'd4: codeword = 16'b01100011_10000111;
            3'd5: codeword = 16'b01111000_10011100;
            3'd6: codeword = 16'b10000111_01100011;
            3'd7: codeword = 16'b10011100_01111000;
            default: codeword = 16'h0000;
        endcase
    end

endmodule
