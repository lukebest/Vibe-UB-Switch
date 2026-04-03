//-----------------------------------------------------------------------------
// Module: ub_xbar_fabric
// 4x4 crossbar switching fabric with round-robin arbitration and
// store-and-forward output queues. 512-bit packet interface.
//-----------------------------------------------------------------------------
module ub_xbar_fabric (
    input  wire         clk,
    input  wire         rst_n,
    // 4 input ports
    input  wire [511:0] in_pkt_data_0,
    input  wire         in_pkt_valid_0,
    input  wire         in_pkt_sop_0,
    input  wire         in_pkt_eop_0,
    input  wire [1:0]   in_dest_port_0,
    output wire         in_pkt_ready_0,

    input  wire [511:0] in_pkt_data_1,
    input  wire         in_pkt_valid_1,
    input  wire         in_pkt_sop_1,
    input  wire         in_pkt_eop_1,
    input  wire [1:0]   in_dest_port_1,
    output wire         in_pkt_ready_1,

    input  wire [511:0] in_pkt_data_2,
    input  wire         in_pkt_valid_2,
    input  wire         in_pkt_sop_2,
    input  wire         in_pkt_eop_2,
    input  wire [1:0]   in_dest_port_2,
    output wire         in_pkt_ready_2,

    input  wire [511:0] in_pkt_data_3,
    input  wire         in_pkt_valid_3,
    input  wire         in_pkt_sop_3,
    input  wire         in_pkt_eop_3,
    input  wire [1:0]   in_dest_port_3,
    output wire         in_pkt_ready_3,

    // 4 output ports
    output wire [511:0] out_pkt_data_0,
    output wire         out_pkt_valid_0,
    output wire         out_pkt_sop_0,
    output wire         out_pkt_eop_0,
    input  wire         out_pkt_ready_0,

    output wire [511:0] out_pkt_data_1,
    output wire         out_pkt_valid_1,
    output wire         out_pkt_sop_1,
    output wire         out_pkt_eop_1,
    input  wire         out_pkt_ready_1,

    output wire [511:0] out_pkt_data_2,
    output wire         out_pkt_valid_2,
    output wire         out_pkt_sop_2,
    output wire         out_pkt_eop_2,
    input  wire         out_pkt_ready_2,

    output wire [511:0] out_pkt_data_3,
    output wire         out_pkt_valid_3,
    output wire         out_pkt_sop_3,
    output wire         out_pkt_eop_3,
    input  wire         out_pkt_ready_3
);

    //-------------------------------------------------------------------------
    // Input arrays for cleaner internal logic
    //-------------------------------------------------------------------------
    wire [511:0] in_data  [0:3];
    wire         in_valid [0:3];
    wire         in_sop   [0:3];
    wire         in_eop   [0:3];
    wire [1:0]   in_dest  [0:3];

    assign in_data[0] = in_pkt_data_0;  assign in_valid[0] = in_pkt_valid_0;
    assign in_sop[0]  = in_pkt_sop_0;   assign in_eop[0]   = in_pkt_eop_0;
    assign in_dest[0] = in_dest_port_0;
    assign in_data[1] = in_pkt_data_1;  assign in_valid[1] = in_pkt_valid_1;
    assign in_sop[1]  = in_pkt_sop_1;   assign in_eop[1]   = in_pkt_eop_1;
    assign in_dest[1] = in_dest_port_1;
    assign in_data[2] = in_pkt_data_2;  assign in_valid[2] = in_pkt_valid_2;
    assign in_sop[2]  = in_pkt_sop_2;   assign in_eop[2]   = in_pkt_eop_2;
    assign in_dest[2] = in_dest_port_2;
    assign in_data[3] = in_pkt_data_3;  assign in_valid[3] = in_pkt_valid_3;
    assign in_sop[3]  = in_pkt_sop_3;   assign in_eop[3]   = in_pkt_eop_3;
    assign in_dest[3] = in_dest_port_3;

    wire         out_ready [0:3];
    assign out_ready[0] = out_pkt_ready_0;
    assign out_ready[1] = out_pkt_ready_1;
    assign out_ready[2] = out_pkt_ready_2;
    assign out_ready[3] = out_pkt_ready_3;

    //-------------------------------------------------------------------------
    // Per-output-port request, arbiter, MUX, queue — all explicit
    //-------------------------------------------------------------------------

    // Arbiter grants and output queue ready signals
    wire [3:0]  arb_grant [0:3];
    wire [1:0]  arb_idx   [0:3];
    wire        outq_wr_ready [0:3];

    // MUX outputs per output port
    wire [511:0] mux_data [0:3];
    wire         mux_valid[0:3];
    wire         mux_sop  [0:3];
    wire         mux_eop  [0:3];

    // Output queue read-side wires
    wire [511:0] oq_rd_data [0:3];
    wire         oq_rd_valid[0:3];
    wire         oq_rd_sop  [0:3];
    wire         oq_rd_eop  [0:3];

    genvar j, k;
    generate
        for (j = 0; j < 4; j = j + 1) begin : gen_outport
            // Request vectors
            wire [3:0] req_vec;
            wire [3:0] sop_vec;
            wire [3:0] eop_vec;
            for (k = 0; k < 4; k = k + 1) begin : gen_req
                assign req_vec[k] = in_valid[k] && (in_dest[k] == j[1:0]);
                assign sop_vec[k] = in_sop[k]   && in_valid[k] && (in_dest[k] == j[1:0]);
                assign eop_vec[k] = in_eop[k]   && in_valid[k] && (in_dest[k] == j[1:0]);
            end

            // Arbiter
            ub_xbar_arbiter u_arb (
                .clk(clk), .rst_n(rst_n),
                .req(req_vec), .req_sop(sop_vec), .req_eop(eop_vec),
                .grant(arb_grant[j]), .grant_idx(arb_idx[j])
            );

            // 4:1 MUX
            assign mux_data[j]  = arb_grant[j][0] ? in_data[0]  :
                                  arb_grant[j][1] ? in_data[1]  :
                                  arb_grant[j][2] ? in_data[2]  :
                                  arb_grant[j][3] ? in_data[3]  : 512'd0;
            assign mux_valid[j] = |arb_grant[j];
            assign mux_sop[j]   = arb_grant[j][0] ? in_sop[0] :
                                  arb_grant[j][1] ? in_sop[1] :
                                  arb_grant[j][2] ? in_sop[2] :
                                  arb_grant[j][3] ? in_sop[3] : 1'b0;
            assign mux_eop[j]   = arb_grant[j][0] ? in_eop[0] :
                                  arb_grant[j][1] ? in_eop[1] :
                                  arb_grant[j][2] ? in_eop[2] :
                                  arb_grant[j][3] ? in_eop[3] : 1'b0;

            // Output queue
            ub_xbar_outq #(.DEPTH(8)) u_outq (
                .clk(clk), .rst_n(rst_n),
                .wr_data(mux_data[j]),
                .wr_valid(mux_valid[j] && outq_wr_ready[j]),
                .wr_sop(mux_sop[j]),
                .wr_eop(mux_eop[j]),
                .wr_ready(outq_wr_ready[j]),
                .rd_data(oq_rd_data[j]),
                .rd_valid(oq_rd_valid[j]),
                .rd_sop(oq_rd_sop[j]),
                .rd_eop(oq_rd_eop[j]),
                .rd_ready(out_ready[j])
            );
        end
    endgenerate

    // Map output queue read-side to output ports
    assign out_pkt_data_0  = oq_rd_data[0];
    assign out_pkt_valid_0 = oq_rd_valid[0];
    assign out_pkt_sop_0   = oq_rd_sop[0];
    assign out_pkt_eop_0   = oq_rd_eop[0];

    assign out_pkt_data_1  = oq_rd_data[1];
    assign out_pkt_valid_1 = oq_rd_valid[1];
    assign out_pkt_sop_1   = oq_rd_sop[1];
    assign out_pkt_eop_1   = oq_rd_eop[1];

    assign out_pkt_data_2  = oq_rd_data[2];
    assign out_pkt_valid_2 = oq_rd_valid[2];
    assign out_pkt_sop_2   = oq_rd_sop[2];
    assign out_pkt_eop_2   = oq_rd_eop[2];

    assign out_pkt_data_3  = oq_rd_data[3];
    assign out_pkt_valid_3 = oq_rd_valid[3];
    assign out_pkt_sop_3   = oq_rd_sop[3];
    assign out_pkt_eop_3   = oq_rd_eop[3];

    //-------------------------------------------------------------------------
    // Input ready
    //-------------------------------------------------------------------------
    assign in_pkt_ready_0 = arb_grant[in_dest[0]][0] && outq_wr_ready[in_dest[0]];
    assign in_pkt_ready_1 = arb_grant[in_dest[1]][1] && outq_wr_ready[in_dest[1]];
    assign in_pkt_ready_2 = arb_grant[in_dest[2]][2] && outq_wr_ready[in_dest[2]];
    assign in_pkt_ready_3 = arb_grant[in_dest[3]][3] && outq_wr_ready[in_dest[3]];

endmodule
