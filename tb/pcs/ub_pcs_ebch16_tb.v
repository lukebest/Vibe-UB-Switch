module ub_pcs_ebch16_tb;
    reg [2:0] index;
    wire [15:0] codeword;

    ub_pcs_ebch16_lut uut (
        .index(index),
        .codeword(codeword)
    );

    integer i;
    initial begin
        $display("Starting eBCH-16 LUT testbench...");
        for (i = 0; i < 8; i = i + 1) begin
            index = i;
            #1;
            $display("Index: %d, Codeword: %b", index, codeword);
            case (index)
                3'd0: if (codeword != 16'b00100111_11011000) $error("Mismatch at index 0");
                3'd1: if (codeword != 16'b00011011_00011011) $error("Mismatch at index 1");
                3'd2: if (codeword != 16'b11100100_11100100) $error("Mismatch at index 2");
                3'd3: if (codeword != 16'b11011000_00100111) $error("Mismatch at index 3");
                3'd4: if (codeword != 16'b01100011_10000111) $error("Mismatch at index 4");
                3'd5: if (codeword != 16'b01111000_10011100) $error("Mismatch at index 5");
                3'd6: if (codeword != 16'b10000111_01100011) $error("Mismatch at index 6");
                3'd7: if (codeword != 16'b10011100_01111000) $error("Mismatch at index 7");
            endcase
        end
        $display("eBCH-16 LUT testbench complete.");
        $finish;
    end
endmodule
