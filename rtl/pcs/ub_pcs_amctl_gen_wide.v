//-----------------------------------------------------------------------------
// Module: ub_pcs_amctl_gen_wide
// Wide AMCTL generator for 4x128b lanes (512b total).
// Inserts alignment markers per-lane, each lane gets its own AMCTL pattern.
// Uses the same eBCH-16 codewords and timing as the original ub_pcs_amctl_gen.
//-----------------------------------------------------------------------------
module ub_pcs_amctl_gen_wide (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         en,
    input  wire         training_mode,
    // 4x128b lane data input
    input  wire [127:0] lane0_data_in,
    input  wire [127:0] lane1_data_in,
    input  wire [127:0] lane2_data_in,
    input  wire [127:0] lane3_data_in,
    input  wire         data_valid_in,
    // 4x128b lane data output
    output reg  [127:0] lane0_data_out,
    output reg  [127:0] lane1_data_out,
    output reg  [127:0] lane2_data_out,
    output reg  [127:0] lane3_data_out,
    output reg          data_valid_out,
    output wire         ready
);

    // eBCH-16 Codewords
    localparam CW21 = 16'h789C;
    localparam CW28 = 16'h1B1B;
    localparam CW22 = 16'h9C78;
    localparam CW3  = 16'hE4E4;
    localparam CW8  = 16'h27D8;
    localparam CW9  = 16'h6387;
    localparam CW10 = 16'h8763;
    localparam CW23 = 16'hD827;

    function [15:0] get_lid_cw;
        input [2:0] lid;
        begin
            case (lid)
                3'd0: get_lid_cw = CW3;
                3'd1: get_lid_cw = CW8;
                3'd2: get_lid_cw = CW9;
                3'd3: get_lid_cw = CW10;
                3'd4: get_lid_cw = CW21;
                3'd5: get_lid_cw = CW22;
                3'd6: get_lid_cw = CW23;
                3'd7: get_lid_cw = CW28;
                default: get_lid_cw = CW3;
            endcase
        end
    endfunction

    // Build 128b AMCTL block for one lane, given lane_id and amctl_cnt
    // Each AMCTL cycle outputs 128 bits = 8 x 16-bit codewords
    // AMCTL block has 20 codewords over 2.5 cycles (but we do 10 cycles of
    // 2 codewords each for the original 32b design). For 128b per lane,
    // we output 8 codewords per cycle, so full AMCTL block = 2.5 cycles.
    // Simplified: 3 cycles x 128b, with last cycle partial (padded).
    //
    // For simplicity, use 5 cycles of 4 codewords (= 64b per cycle,
    // repeated to fill 128b). Actually, 20 codewords / 8 per 128b = 2.5 cycles.
    // Use 3 cycles: cycle 0 = CW[0:7], cycle 1 = CW[8:15], cycle 2 = CW[16:19]+pad.
    function [127:0] get_amctl_data;
        input [2:0] lid;
        input [1:0] cyc; // 0, 1, 2
        reg [15:0] cw [0:7];
        integer k;
        begin
            case (cyc)
                2'd0: begin
                    // CW0..CW7: BODY(6) + END(2)
                    cw[0] = CW21; cw[1] = CW28; cw[2] = CW21;
                    cw[3] = CW28; cw[4] = CW21; cw[5] = CW28;
                    cw[6] = CW22; cw[7] = CW22;
                end
                2'd1: begin
                    // CW8..CW15: LID(4) + CTRL_TYPE(4)
                    cw[0] = CW3;  cw[1] = get_lid_cw(lid);
                    cw[2] = CW3;  cw[3] = get_lid_cw(lid);
                    cw[4] = CW28; cw[5] = CW3;
                    cw[6] = CW28; cw[7] = CW3;
                end
                2'd2: begin
                    // CW16..CW19: CTRL_DETAIL(4) + pad(4)
                    cw[0] = CW3;  cw[1] = CW3;
                    cw[2] = CW3;  cw[3] = CW3;
                    cw[4] = 16'h0; cw[5] = 16'h0;
                    cw[6] = 16'h0; cw[7] = 16'h0;
                end
                default: begin
                    for (k = 0; k < 8; k = k + 1) cw[k] = 16'h0;
                end
            endcase
            get_amctl_data = {cw[7], cw[6], cw[5], cw[4], cw[3], cw[2], cw[1], cw[0]};
        end
    endfunction

    reg [5:0] timer;
    reg [1:0] amctl_cnt;  // 0, 1, 2 (3 cycles of AMCTL)
    reg       inserting;

    wire [5:0] interval = training_mode ? 6'd32 : 6'd40;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timer     <= 6'd0;
            amctl_cnt <= 2'd0;
            inserting <= 1'b0;
        end else if (en) begin
            if (inserting) begin
                if (amctl_cnt == 2'd2) begin
                    amctl_cnt <= 2'd0;
                    inserting <= 1'b0;
                    timer     <= 6'd0;
                end else begin
                    amctl_cnt <= amctl_cnt + 1'b1;
                end
            end else if (data_valid_in) begin
                if (timer == interval - 1) begin
                    inserting <= 1'b1;
                    amctl_cnt <= 2'd0;
                end else begin
                    timer <= timer + 1'b1;
                end
            end
        end
    end

    assign ready = !inserting;

    always @(*) begin
        if (inserting) begin
            lane0_data_out = get_amctl_data(3'd0, amctl_cnt);
            lane1_data_out = get_amctl_data(3'd1, amctl_cnt);
            lane2_data_out = get_amctl_data(3'd2, amctl_cnt);
            lane3_data_out = get_amctl_data(3'd3, amctl_cnt);
            data_valid_out = 1'b1;
        end else begin
            lane0_data_out = lane0_data_in;
            lane1_data_out = lane1_data_in;
            lane2_data_out = lane2_data_in;
            lane3_data_out = lane3_data_in;
            data_valid_out = data_valid_in;
        end
    end

endmodule
