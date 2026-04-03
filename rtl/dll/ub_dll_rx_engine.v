//-----------------------------------------------------------------------------
// Module: ub_dll_rx_engine
// DLL RX engine: demultiplexes incoming 640-bit flits into data (DLLDP)
// and control (DLLCB), extracts retry/credit signaling.
//-----------------------------------------------------------------------------
module ub_dll_rx_engine (
    input  wire         clk,
    input  wire         rst_n,
    // Flit input from PCS RX pipe (640-bit)
    input  wire [639:0] flit_in,
    input  wire         flit_valid,
    // Network layer output
    output reg  [639:0] nw_flit_out,
    output reg          nw_flit_valid,
    output reg          nw_flit_sop,
    output reg          nw_flit_eop,
    input  wire         nw_flit_ready,
    // Signaling to TX engine
    output reg          retry_req_to_send,
    output reg  [7:0]   retry_rcvptr,
    output reg          ack_to_send,
    output reg  [7:0]   ack_ptr,
    output reg          credit_return_to_send,
    output reg  [7:0]   credit_return_amt
);

    // Flit classification:
    // bit 639 = 1 -> DLLDP (data flit)
    // bit 639 = 0 -> DLLCB (control), sub-type in bits [638:632]:
    //   7'h00 = null block (discard)
    //   7'h01 = retry_req (rcvptr in [631:624])
    //   7'h02 = retry_ack (ack_ptr in [631:624])
    //   7'h04 = crd_ack   (amount in [631:624])

    wire is_data    = flit_in[639];
    wire [6:0] ctrl_type = flit_in[638:632];

    // Track receive pointer for retry
    reg [7:0] rcv_ptr;

    // SOP/EOP extraction from data flit header
    // bit 638 = sop, bit 637 = eop (simplified encoding)
    wire data_sop = flit_in[638];
    wire data_eop = flit_in[637];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            nw_flit_out         <= 640'd0;
            nw_flit_valid       <= 1'b0;
            nw_flit_sop         <= 1'b0;
            nw_flit_eop         <= 1'b0;
            retry_req_to_send   <= 1'b0;
            retry_rcvptr        <= 8'd0;
            ack_to_send         <= 1'b0;
            ack_ptr             <= 8'd0;
            credit_return_to_send <= 1'b0;
            credit_return_amt   <= 8'd0;
            rcv_ptr             <= 8'd0;
        end else begin
            // Default: clear pulses
            retry_req_to_send    <= 1'b0;
            ack_to_send          <= 1'b0;
            credit_return_to_send <= 1'b0;
            nw_flit_valid        <= 1'b0;

            if (flit_valid) begin
                if (is_data) begin
                    // Data flit -> forward to NW layer
                    nw_flit_out   <= flit_in;
                    nw_flit_valid <= 1'b1;
                    nw_flit_sop   <= data_sop;
                    nw_flit_eop   <= data_eop;
                    rcv_ptr       <= rcv_ptr + 1'b1;

                    // Piggyback ACK: return ack every 8 flits
                    if (rcv_ptr[2:0] == 3'd7) begin
                        ack_to_send <= 1'b1;
                        ack_ptr     <= rcv_ptr + 1'b1;
                    end

                    // Piggyback credit return every 16 flits
                    if (rcv_ptr[3:0] == 4'd15) begin
                        credit_return_to_send <= 1'b1;
                        credit_return_amt     <= 8'd2; // 2 cells = 16 flits
                    end
                end else begin
                    // Control flit
                    case (ctrl_type)
                        7'h00: ; // Null block — discard
                        7'h01: begin
                            // Retry request from peer
                            retry_req_to_send <= 1'b1;
                            retry_rcvptr      <= flit_in[631:624];
                        end
                        7'h02: begin
                            // Retry ACK from peer
                            ack_to_send <= 1'b1;
                            ack_ptr     <= flit_in[631:624];
                        end
                        7'h04: begin
                            // Credit return from peer
                            credit_return_to_send <= 1'b1;
                            credit_return_amt     <= flit_in[631:624];
                        end
                        default: ; // Unknown — discard
                    endcase
                end
            end
        end
    end

endmodule
