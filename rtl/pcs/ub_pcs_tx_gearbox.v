//-----------------------------------------------------------------------------
// Module: ub_pcs_tx_gearbox
// TX width conversion: 640b DLL flit -> accumulate 1.5 beats -> 960b ->
// FEC encode -> 1024b -> output 2x512b per FEC codeword.
// Operates in DL clock domain (1.25 GHz).
//-----------------------------------------------------------------------------
module ub_pcs_tx_gearbox (
    input  wire          clk,
    input  wire          rst_n,
    // 640-bit flit input (from DLL TX engine)
    input  wire [639:0]  flit_in,
    input  wire          flit_valid,
    output wire          flit_ready,
    // 512-bit output (to per-lane scrambler)
    output reg  [511:0]  data_out,
    output reg           data_valid_out,
    input  wire          data_ready_in
);

    // FEC encoder instance
    wire [959:0]  fec_msg;
    wire [1023:0] fec_cw;
    reg           fec_valid_in;
    wire          fec_valid_out;

    ub_pcs_fec_enc u_fec_enc (
        .clk       (clk),
        .rst_n     (rst_n),
        .msg_in    (fec_msg),
        .valid_in  (fec_valid_in),
        .cw_out    (fec_cw),
        .valid_out (fec_valid_out)
    );

    //-------------------------------------------------------------------------
    // Accumulation state machine
    // Pattern: 3 flits (640b each) = 1920b -> 2 FEC blocks (960b each)
    //
    // Beat 0: Store flit[639:0]                    -> acc[639:0]
    // Beat 1: Store flit[639:0], form 960b block 1 -> acc[639:0] + flit[319:0]
    //         Remainder: flit[639:320] = 320b saved
    // Beat 2: Store flit[639:0], form 960b block 2 -> saved[319:0] + flit[639:0]
    //         All consumed, back to beat 0
    //-------------------------------------------------------------------------

    localparam ST_ACC0     = 3'd0;  // Accumulate beat 0 (need flit)
    localparam ST_ACC1     = 3'd1;  // Accumulate beat 1 (need flit, triggers FEC block 1)
    localparam ST_FEC1     = 3'd2;  // Wait for FEC result of block 1
    localparam ST_SER1     = 3'd3;  // Serialize FEC codeword 1 (2 beats of 512b)
    localparam ST_ACC2     = 3'd4;  // Accumulate beat 2 (need flit, triggers FEC block 2)
    localparam ST_FEC2     = 3'd5;  // Wait for FEC result of block 2
    localparam ST_SER2     = 3'd6;  // Serialize FEC codeword 2 (2 beats of 512b)

    reg [2:0]    state;
    reg [639:0]  acc_reg;       // stored flit from beat 0
    reg [319:0]  remainder;     // remainder from beat 1
    reg [1023:0] cw_reg;        // FEC codeword for serialization
    reg          ser_cnt;       // 0 = first 512b, 1 = second 512b
    reg [959:0]  fec_msg_reg;

    assign fec_msg = fec_msg_reg;

    // flit_ready: accept new flit in accumulation states
    assign flit_ready = (state == ST_ACC0 || state == ST_ACC1 || state == ST_ACC2);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state         <= ST_ACC0;
            acc_reg       <= 640'd0;
            remainder     <= 320'd0;
            cw_reg        <= 1024'd0;
            ser_cnt       <= 1'b0;
            data_out      <= 512'd0;
            data_valid_out <= 1'b0;
            fec_valid_in  <= 1'b0;
            fec_msg_reg   <= 960'd0;
        end else begin
            fec_valid_in  <= 1'b0;
            data_valid_out <= 1'b0;

            case (state)
                ST_ACC0: begin
                    if (flit_valid) begin
                        acc_reg <= flit_in;
                        state   <= ST_ACC1;
                    end
                end

                ST_ACC1: begin
                    if (flit_valid) begin
                        // Form 960b block 1: acc_reg[639:0] + flit_in[319:0]
                        fec_msg_reg  <= {acc_reg, flit_in[319:0]};
                        fec_valid_in <= 1'b1;
                        // Save remainder
                        remainder <= flit_in[639:320];
                        state     <= ST_FEC1;
                    end
                end

                ST_FEC1: begin
                    if (fec_valid_out) begin
                        cw_reg  <= fec_cw;
                        ser_cnt <= 1'b0;
                        state   <= ST_SER1;
                    end
                end

                ST_SER1: begin
                    if (data_ready_in || !data_valid_out) begin
                        if (ser_cnt == 1'b0) begin
                            data_out       <= cw_reg[1023:512];
                            data_valid_out <= 1'b1;
                            ser_cnt        <= 1'b1;
                        end else begin
                            data_out       <= cw_reg[511:0];
                            data_valid_out <= 1'b1;
                            ser_cnt        <= 1'b0;
                            state          <= ST_ACC2;
                        end
                    end
                end

                ST_ACC2: begin
                    if (flit_valid) begin
                        // Form 960b block 2: remainder[319:0] + flit_in[639:0]
                        fec_msg_reg  <= {remainder, flit_in};
                        fec_valid_in <= 1'b1;
                        state        <= ST_FEC2;
                    end
                end

                ST_FEC2: begin
                    if (fec_valid_out) begin
                        cw_reg  <= fec_cw;
                        ser_cnt <= 1'b0;
                        state   <= ST_SER2;
                    end
                end

                ST_SER2: begin
                    if (data_ready_in || !data_valid_out) begin
                        if (ser_cnt == 1'b0) begin
                            data_out       <= cw_reg[1023:512];
                            data_valid_out <= 1'b1;
                            ser_cnt        <= 1'b1;
                        end else begin
                            data_out       <= cw_reg[511:0];
                            data_valid_out <= 1'b1;
                            ser_cnt        <= 1'b0;
                            state          <= ST_ACC0;
                        end
                    end
                end

                default: state <= ST_ACC0;
            endcase
        end
    end

endmodule
