//-----------------------------------------------------------------------------
// Module: ub_pcs_rx_gearbox
// RX width conversion: 2x512b -> 1024b -> FEC decode -> 960b ->
// output as 640b flits (3 flits per 2 FEC codewords, inverse of TX).
// Operates in DL clock domain (1.25 GHz).
//-----------------------------------------------------------------------------
module ub_pcs_rx_gearbox (
    input  wire          clk,
    input  wire          rst_n,
    // 512-bit input (from per-lane descrambler, reassembled)
    input  wire [511:0]  data_in,
    input  wire          data_valid_in,
    output wire          data_ready,
    // 640-bit flit output (to DLL RX engine)
    output reg  [639:0]  flit_out,
    output reg           flit_valid,
    input  wire          flit_ready,
    // Status
    output wire          fec_fail
);

    // FEC decoder instance
    reg  [1023:0] fec_cw_in;
    reg           fec_valid_in;
    wire [959:0]  fec_msg_out;
    wire          fec_valid_out;
    wire          fec_fail_out;

    ub_pcs_fec_dec u_fec_dec (
        .clk       (clk),
        .rst_n     (rst_n),
        .cw_in     (fec_cw_in),
        .valid_in  (fec_valid_in),
        .msg_out   (fec_msg_out),
        .valid_out (fec_valid_out),
        .fec_fail  (fec_fail_out)
    );

    assign fec_fail = fec_fail_out;

    //-------------------------------------------------------------------------
    // State machine — inverse of TX gearbox
    // 2 FEC codewords (2x960b = 1920b) -> 3 flits (3x640b = 1920b)
    //
    // Accumulate 2x512b -> 1024b -> FEC dec -> 960b
    // Block 1 decoded (960b): output flit 0 [639:0] from decoded[959:320]
    //                         save decoded[319:0] as remainder
    // Block 2 decoded (960b): output flit 1 [639:0] from {remainder, decoded[959:640]}
    //                         output flit 2 [639:0] from decoded[639:0]
    //-------------------------------------------------------------------------

    localparam ST_ACC1_0   = 3'd0;  // Accumulate first 512b of codeword 1
    localparam ST_ACC1_1   = 3'd1;  // Accumulate second 512b, trigger FEC dec 1
    localparam ST_FEC1     = 3'd2;  // Wait for FEC decode 1
    localparam ST_FLIT0    = 3'd3;  // Output flit 0
    localparam ST_ACC2_0   = 3'd4;  // Accumulate first 512b of codeword 2
    localparam ST_ACC2_1   = 3'd5;  // Accumulate second 512b, trigger FEC dec 2
    localparam ST_FEC2     = 3'd6;  // Wait for FEC decode 2
    localparam ST_FLIT12   = 3'd7;  // Output flit 1 then flit 2

    reg [2:0]    state;
    reg [511:0]  acc_hi;        // first 512b of codeword
    reg [319:0]  remainder;     // remainder from block 1
    reg [959:0]  decoded_reg;   // decoded message for flit output
    reg          flit12_cnt;    // 0 = flit 1, 1 = flit 2

    // Accept data in accumulation states
    assign data_ready = (state == ST_ACC1_0 || state == ST_ACC1_1 ||
                         state == ST_ACC2_0 || state == ST_ACC2_1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= ST_ACC1_0;
            acc_hi       <= 512'd0;
            remainder    <= 320'd0;
            decoded_reg  <= 960'd0;
            flit_out     <= 640'd0;
            flit_valid   <= 1'b0;
            fec_cw_in    <= 1024'd0;
            fec_valid_in <= 1'b0;
            flit12_cnt   <= 1'b0;
        end else begin
            fec_valid_in <= 1'b0;

            case (state)
                ST_ACC1_0: begin
                    flit_valid <= 1'b0;
                    if (data_valid_in) begin
                        acc_hi <= data_in;
                        state  <= ST_ACC1_1;
                    end
                end

                ST_ACC1_1: begin
                    if (data_valid_in) begin
                        fec_cw_in    <= {acc_hi, data_in};
                        fec_valid_in <= 1'b1;
                        state        <= ST_FEC1;
                    end
                end

                ST_FEC1: begin
                    if (fec_valid_out) begin
                        // decoded = 960b, output flit 0 = top 640b
                        flit_out   <= fec_msg_out[959:320];
                        flit_valid <= 1'b1;
                        remainder  <= fec_msg_out[319:0];
                        state      <= ST_FLIT0;
                    end
                end

                ST_FLIT0: begin
                    if (flit_ready) begin
                        flit_valid <= 1'b0;
                        state      <= ST_ACC2_0;
                    end
                end

                ST_ACC2_0: begin
                    if (data_valid_in) begin
                        acc_hi <= data_in;
                        state  <= ST_ACC2_1;
                    end
                end

                ST_ACC2_1: begin
                    if (data_valid_in) begin
                        fec_cw_in    <= {acc_hi, data_in};
                        fec_valid_in <= 1'b1;
                        state        <= ST_FEC2;
                    end
                end

                ST_FEC2: begin
                    if (fec_valid_out) begin
                        decoded_reg <= fec_msg_out;
                        // Output flit 1 = {decoded2[959:640] (flit1 upper), remainder (flit1 lower)}
                        flit_out    <= {fec_msg_out[959:640], remainder};
                        flit_valid  <= 1'b1;
                        flit12_cnt  <= 1'b0;
                        state       <= ST_FLIT12;
                    end
                end

                ST_FLIT12: begin
                    if (flit_ready) begin
                        if (flit12_cnt == 1'b0) begin
                            // Flit 1 accepted, now output flit 2 = decoded[639:0]
                            flit_out   <= decoded_reg[639:0];
                            flit_valid <= 1'b1;
                            flit12_cnt <= 1'b1;
                        end else begin
                            // Flit 2 accepted, cycle complete
                            flit_valid <= 1'b0;
                            flit12_cnt <= 1'b0;
                            state      <= ST_ACC1_0;
                        end
                    end
                end

                default: state <= ST_ACC1_0;
            endcase
        end
    end

endmodule
