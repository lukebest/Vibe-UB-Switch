// AMCTL Block Generator
// Assembles BODY, END, LID, CTRL_TYPE, and CTRL_DETAIL fields (320 bits total)
// Periodic insertion logic for training and active modes.

module ub_pcs_amctl_gen (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         en,
    input  wire         training_mode, // 1 for 512 symbols (32 cycles), 0 for 640 symbols (40 cycles)
    input  wire [2:0]   lane0_id,
    input  wire [2:0]   lane1_id,
    input  wire [2:0]   lane2_id,
    input  wire [2:0]   lane3_id,
    input  wire [127:0] data_in,
    input  wire         data_valid_in,
    output reg  [127:0] data_out,
    output reg          data_valid_out,
    output wire         ready
);

    // eBCH-16 Codewords from LUT
    // CW8:  16'h27D8 (Index 0)
    // CW28: 16'h1B1B (Index 1)
    // CW3:  16'hE4E4 (Index 2)
    // CW23: 16'hD827 (Index 3)
    // CW9:  16'h6387 (Index 4)
    // CW21: 16'h789C (Index 5)
    // CW10: 16'h8763 (Index 6)
    // CW22: 16'h9C78 (Index 7)

    function [15:0] get_cw;
        input [2:0] l_id;
        input [4:0] idx; // 0..19
        begin
            case (idx)
                // BODY: CW21, CW28 pattern (3 groups)
                5'd0, 5'd2, 5'd4: get_cw = 16'h789C; // CW21
                5'd1, 5'd3, 5'd5: get_cw = 16'h1B1B; // CW28
                
                // END: CW22, CW22
                5'd6, 5'd7:       get_cw = 16'h9C78; // CW22
                
                // LID: Lane ID Indicator
                5'd8, 5'd10:      get_cw = 16'hE4E4; // CW3
                5'd9, 5'd11:      begin
                    case (l_id)
                        3'd0: get_cw = 16'hE4E4; // CW3
                        3'd1: get_cw = 16'h27D8; // CW8
                        3'd2: get_cw = 16'h6387; // CW9
                        3'd3: get_cw = 16'h8763; // CW10
                        3'd4: get_cw = 16'h789C; // CW21
                        3'd5: get_cw = 16'h9C78; // CW22
                        3'd6: get_cw = 16'hD827; // CW23
                        3'd7: get_cw = 16'h1B1B; // CW28
                        default: get_cw = 16'hE4E4;
                    endcase
                end
                
                // CTRL_TYPE: No Command (CW28, CW3 repeated)
                5'd12, 5'd14:     get_cw = 16'h1B1B; // CW28
                5'd13, 5'd15:     get_cw = 16'hE4E4; // CW3
                
                // CTRL_DETAIL: No Command detail (default CW3)
                5'd16, 5'd17, 5'd18, 5'd19: get_cw = 16'hE4E4; // CW3
                
                default: get_cw = 16'h0000;
            endcase
        end
    endfunction

    reg [5:0] timer;      // Counts LTBs (cycles)
    reg [3:0] amctl_cnt;  // Counts AMCTL cycles (0 to 9)
    reg       inserting;

    wire [5:0] interval = training_mode ? 6'd32 : 6'd40;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timer <= 0;
            amctl_cnt <= 0;
            inserting <= 0;
        end else if (en) begin
            if (inserting) begin
                if (amctl_cnt == 9) begin
                    amctl_cnt <= 0;
                    inserting <= 0;
                    timer <= 0;
                end else begin
                    amctl_cnt <= amctl_cnt + 1;
                end
            end else if (data_valid_in) begin
                if (timer == interval - 1) begin
                    inserting <= 1;
                    amctl_cnt <= 0;
                end else begin
                    timer <= timer + 1;
                end
            end
        end
    end

    assign ready = !inserting;

    reg [127:0] amctl_data_comb;
    integer l_idx, b_idx;
    reg [15:0] c_e, c_o;

    always @(*) begin
        amctl_data_comb = 0;
        for (l_idx = 0; l_idx < 4; l_idx = l_idx + 1) begin
            case (l_idx)
                0: begin c_e = get_cw(lane0_id, {amctl_cnt, 1'b0}); c_o = get_cw(lane0_id, {amctl_cnt, 1'b1}); end
                1: begin c_e = get_cw(lane1_id, {amctl_cnt, 1'b0}); c_o = get_cw(lane1_id, {amctl_cnt, 1'b1}); end
                2: begin c_e = get_cw(lane2_id, {amctl_cnt, 1'b0}); c_o = get_cw(lane2_id, {amctl_cnt, 1'b1}); end
                3: begin c_e = get_cw(lane3_id, {amctl_cnt, 1'b0}); c_o = get_cw(lane3_id, {amctl_cnt, 1'b1}); end
                default: begin c_e = 16'h0; c_o = 16'h0; end
            endcase
            
            for (b_idx = 0; b_idx < 8; b_idx = b_idx + 1) begin
                amctl_data_comb[(b_idx*4 + l_idx)*2 +: 2] = c_e[b_idx*2 +: 2];
                amctl_data_comb[((b_idx+8)*4 + l_idx)*2 +: 2] = c_o[b_idx*2 +: 2];
            end
        end
    end

    always @(*) begin
        if (inserting) begin
            data_out = amctl_data_comb;
            data_valid_out = 1'b1;
        end else begin
            data_out = data_in;
            data_valid_out = data_valid_in;
        end
    end

endmodule
