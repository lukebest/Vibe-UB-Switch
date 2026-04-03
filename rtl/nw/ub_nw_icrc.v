module ub_nw_icrc (
    input clk,
    input rst_n,
    input [159:0] data_in,
    input data_valid,
    input is_sop,
    output [31:0] icrc_out
);

    // Step 1: Implement bit-reversal function
    // Per Section 5.3.7: "Bit 0 to bit 7 in each byte are reversed"
    function [7:0] bit_rev8;
        input [7:0] in;
        integer i;
        begin
            for (i=0; i<8; i=i+1) bit_rev8[i] = in[7-i];
        end
    endfunction

    // Function to reverse 32 bits for the final output
    function [31:0] bit_rev32;
        input [31:0] in;
        integer i;
        begin
            for (i=0; i<32; i=i+1) bit_rev32[i] = in[31-i];
        end
    endfunction

    // Step 2: Implement masking logic
    // CCI and LBF fields (Bytes 4-7 of NTH) replaced with 1s.
    // Note: In the 160-bit flit, if NTH is at the start, CCI is [125:110] and LBF is [109:102].
    wire [159:0] masked_data;
    assign masked_data = is_sop ? {data_in[159:126], 16'hFFFF, 8'hFF, data_in[101:0]} : data_in;

    // Apply bit reversal to each input byte
    wire [159:0] rev_data;
    genvar b;
    generate
        for (b=0; b<20; b=b+1) begin : gen_rev
            assign rev_data[b*8 +: 8] = bit_rev8(masked_data[b*8 +: 8]);
        end
    endgenerate

    // Step 3: Implement 160-bit parallel CRC-32 for ICRC
    // Polynomial: 0x04C11DB7
    function [31:0] next_crc32;
        input [31:0] current_crc;
        input [159:0] data;
        integer i;
        reg [31:0] crc;
        begin
            crc = current_crc;
            // Process bits from MSB to LSB of the reversed data.
            // Since we reversed each byte, rev_data[159] is original bit 0 of Byte 0.
            for (i = 159; i >= 0; i = i - 1) begin
                if (crc[31] ^ data[i])
                    crc = (crc << 1) ^ 32'h04C11DB7;
                else
                    crc = (crc << 1);
            end
            next_crc32 = crc;
        end
    endfunction

    reg [31:0] crc_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            crc_reg <= 32'hFFFFFFFF;
        end else if (data_valid) begin
            if (is_sop) begin
                // Initial value is 0xFFFFFFFF
                crc_reg <= next_crc32(32'hFFFFFFFF, rev_data);
            end else begin
                crc_reg <= next_crc32(crc_reg, rev_data);
            end
        end
    end

    // "The resulting CRC is then bit-reversed and inverted to obtain the ICRC."
    always @(posedge clk) begin
        if (data_valid) begin
            $display("ICRC [%m] Processing data=%h, sop=%b", masked_data, is_sop);
        end
    end
    
    assign icrc_out = ~bit_rev32(crc_reg);

endmodule
