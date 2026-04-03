//-----------------------------------------------------------------------------
// Module: ub_switch_top
// 4-port 400Gbps UB ASIC switch top level.
// 4x ub_port + ub_xbar_fabric.
// Dual clock: dl_clk (1.25 GHz), pcs_clk (875 MHz).
//-----------------------------------------------------------------------------
module ub_switch_top (
    // Global clocks
    input  wire          dl_clk,
    input  wire          dl_rst_n,
    input  wire          pcs_clk,
    input  wire          pcs_rst_n,
    // Port 0 SerDes
    output wire [127:0]  p0_serdes_tx_lane0, p0_serdes_tx_lane1,
    output wire [127:0]  p0_serdes_tx_lane2, p0_serdes_tx_lane3,
    output wire          p0_serdes_tx_valid,
    input  wire [127:0]  p0_serdes_rx_lane0, p0_serdes_rx_lane1,
    input  wire [127:0]  p0_serdes_rx_lane2, p0_serdes_rx_lane3,
    input  wire          p0_serdes_rx_valid,
    // Port 1 SerDes
    output wire [127:0]  p1_serdes_tx_lane0, p1_serdes_tx_lane1,
    output wire [127:0]  p1_serdes_tx_lane2, p1_serdes_tx_lane3,
    output wire          p1_serdes_tx_valid,
    input  wire [127:0]  p1_serdes_rx_lane0, p1_serdes_rx_lane1,
    input  wire [127:0]  p1_serdes_rx_lane2, p1_serdes_rx_lane3,
    input  wire          p1_serdes_rx_valid,
    // Port 2 SerDes
    output wire [127:0]  p2_serdes_tx_lane0, p2_serdes_tx_lane1,
    output wire [127:0]  p2_serdes_tx_lane2, p2_serdes_tx_lane3,
    output wire          p2_serdes_tx_valid,
    input  wire [127:0]  p2_serdes_rx_lane0, p2_serdes_rx_lane1,
    input  wire [127:0]  p2_serdes_rx_lane2, p2_serdes_rx_lane3,
    input  wire          p2_serdes_rx_valid,
    // Port 3 SerDes
    output wire [127:0]  p3_serdes_tx_lane0, p3_serdes_tx_lane1,
    output wire [127:0]  p3_serdes_tx_lane2, p3_serdes_tx_lane3,
    output wire          p3_serdes_tx_valid,
    input  wire [127:0]  p3_serdes_rx_lane0, p3_serdes_rx_lane1,
    input  wire [127:0]  p3_serdes_rx_lane2, p3_serdes_rx_lane3,
    input  wire          p3_serdes_rx_valid,
    // Global control
    input  wire          training_mode,
    input  wire [3:0]    start_train,
    // CSR bus
    input  wire [1:0]    csr_port_sel,
    input  wire          csr_wen,
    input  wire [15:0]   csr_wdata,
    // Status
    output wire [3:0]    port_link_up,
    output wire [3:0]    port_link_ready
);

    //=========================================================================
    // Internal wires: port <-> crossbar
    //=========================================================================
    // Port RX -> crossbar input
    wire [511:0] port_rx_data  [0:3];
    wire         port_rx_valid [0:3];
    wire         port_rx_sop   [0:3];
    wire         port_rx_eop   [0:3];

    // Crossbar output -> port TX
    wire [511:0] xbar_out_data  [0:3];
    wire         xbar_out_valid [0:3];
    wire         xbar_out_sop   [0:3];
    wire         xbar_out_eop   [0:3];
    wire         xbar_out_ready [0:3];

    // Port local SCNA for routing
    wire [15:0]  port_scna [0:3];

    // Destination port for crossbar routing (derived from received packet header)
    // DCNA is in the top 16 bits of the 512-bit packet data [511:496]
    wire [1:0] dest_port [0:3];

    genvar p;
    generate
        for (p = 0; p < 4; p = p + 1) begin : gen_dest_lookup
            wire [15:0] rx_dcna = port_rx_data[p][511:496];
            assign dest_port[p] = (rx_dcna == port_scna[0]) ? 2'd0 :
                                  (rx_dcna == port_scna[1]) ? 2'd1 :
                                  (rx_dcna == port_scna[2]) ? 2'd2 :
                                  (rx_dcna == port_scna[3]) ? 2'd3 : 2'd0;
        end
    endgenerate

    // Crossbar input ready -> port (unused in current design, ports always accept)
    wire xbar_in_ready [0:3];

    //=========================================================================
    // CSR demux
    //=========================================================================
    wire csr_wen_0 = csr_wen && (csr_port_sel == 2'd0);
    wire csr_wen_1 = csr_wen && (csr_port_sel == 2'd1);
    wire csr_wen_2 = csr_wen && (csr_port_sel == 2'd2);
    wire csr_wen_3 = csr_wen && (csr_port_sel == 2'd3);

    //=========================================================================
    // Port 0
    //=========================================================================
    ub_port #(.DEFAULT_SCNA(16'h0001)) u_port0 (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .tx_pkt_data(xbar_out_data[0]), .tx_pkt_valid(xbar_out_valid[0]),
        .tx_pkt_sop(xbar_out_sop[0]), .tx_pkt_eop(xbar_out_eop[0]),
        .tx_pkt_ready(xbar_out_ready[0]),
        .rx_pkt_data(port_rx_data[0]), .rx_pkt_valid(port_rx_valid[0]),
        .rx_pkt_sop(port_rx_sop[0]), .rx_pkt_eop(port_rx_eop[0]),
        .serdes_tx_lane0(p0_serdes_tx_lane0), .serdes_tx_lane1(p0_serdes_tx_lane1),
        .serdes_tx_lane2(p0_serdes_tx_lane2), .serdes_tx_lane3(p0_serdes_tx_lane3),
        .serdes_tx_valid(p0_serdes_tx_valid),
        .serdes_rx_lane0(p0_serdes_rx_lane0), .serdes_rx_lane1(p0_serdes_rx_lane1),
        .serdes_rx_lane2(p0_serdes_rx_lane2), .serdes_rx_lane3(p0_serdes_rx_lane3),
        .serdes_rx_valid(p0_serdes_rx_valid),
        .csr_wen(csr_wen_0), .csr_wdata(csr_wdata), .local_scna(port_scna[0]),
        .link_up(port_link_up[0]), .link_ready(port_link_ready[0]),
        .all_lanes_aligned(), .fec_fail(),
        .training_mode(training_mode), .start_train(start_train[0])
    );

    //=========================================================================
    // Port 1
    //=========================================================================
    ub_port #(.DEFAULT_SCNA(16'h0002)) u_port1 (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .tx_pkt_data(xbar_out_data[1]), .tx_pkt_valid(xbar_out_valid[1]),
        .tx_pkt_sop(xbar_out_sop[1]), .tx_pkt_eop(xbar_out_eop[1]),
        .tx_pkt_ready(xbar_out_ready[1]),
        .rx_pkt_data(port_rx_data[1]), .rx_pkt_valid(port_rx_valid[1]),
        .rx_pkt_sop(port_rx_sop[1]), .rx_pkt_eop(port_rx_eop[1]),
        .serdes_tx_lane0(p1_serdes_tx_lane0), .serdes_tx_lane1(p1_serdes_tx_lane1),
        .serdes_tx_lane2(p1_serdes_tx_lane2), .serdes_tx_lane3(p1_serdes_tx_lane3),
        .serdes_tx_valid(p1_serdes_tx_valid),
        .serdes_rx_lane0(p1_serdes_rx_lane0), .serdes_rx_lane1(p1_serdes_rx_lane1),
        .serdes_rx_lane2(p1_serdes_rx_lane2), .serdes_rx_lane3(p1_serdes_rx_lane3),
        .serdes_rx_valid(p1_serdes_rx_valid),
        .csr_wen(csr_wen_1), .csr_wdata(csr_wdata), .local_scna(port_scna[1]),
        .link_up(port_link_up[1]), .link_ready(port_link_ready[1]),
        .all_lanes_aligned(), .fec_fail(),
        .training_mode(training_mode), .start_train(start_train[1])
    );

    //=========================================================================
    // Port 2
    //=========================================================================
    ub_port #(.DEFAULT_SCNA(16'h0003)) u_port2 (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .tx_pkt_data(xbar_out_data[2]), .tx_pkt_valid(xbar_out_valid[2]),
        .tx_pkt_sop(xbar_out_sop[2]), .tx_pkt_eop(xbar_out_eop[2]),
        .tx_pkt_ready(xbar_out_ready[2]),
        .rx_pkt_data(port_rx_data[2]), .rx_pkt_valid(port_rx_valid[2]),
        .rx_pkt_sop(port_rx_sop[2]), .rx_pkt_eop(port_rx_eop[2]),
        .serdes_tx_lane0(p2_serdes_tx_lane0), .serdes_tx_lane1(p2_serdes_tx_lane1),
        .serdes_tx_lane2(p2_serdes_tx_lane2), .serdes_tx_lane3(p2_serdes_tx_lane3),
        .serdes_tx_valid(p2_serdes_tx_valid),
        .serdes_rx_lane0(p2_serdes_rx_lane0), .serdes_rx_lane1(p2_serdes_rx_lane1),
        .serdes_rx_lane2(p2_serdes_rx_lane2), .serdes_rx_lane3(p2_serdes_rx_lane3),
        .serdes_rx_valid(p2_serdes_rx_valid),
        .csr_wen(csr_wen_2), .csr_wdata(csr_wdata), .local_scna(port_scna[2]),
        .link_up(port_link_up[2]), .link_ready(port_link_ready[2]),
        .all_lanes_aligned(), .fec_fail(),
        .training_mode(training_mode), .start_train(start_train[2])
    );

    //=========================================================================
    // Port 3
    //=========================================================================
    ub_port #(.DEFAULT_SCNA(16'h0004)) u_port3 (
        .dl_clk(dl_clk), .dl_rst_n(dl_rst_n),
        .pcs_clk(pcs_clk), .pcs_rst_n(pcs_rst_n),
        .tx_pkt_data(xbar_out_data[3]), .tx_pkt_valid(xbar_out_valid[3]),
        .tx_pkt_sop(xbar_out_sop[3]), .tx_pkt_eop(xbar_out_eop[3]),
        .tx_pkt_ready(xbar_out_ready[3]),
        .rx_pkt_data(port_rx_data[3]), .rx_pkt_valid(port_rx_valid[3]),
        .rx_pkt_sop(port_rx_sop[3]), .rx_pkt_eop(port_rx_eop[3]),
        .serdes_tx_lane0(p3_serdes_tx_lane0), .serdes_tx_lane1(p3_serdes_tx_lane1),
        .serdes_tx_lane2(p3_serdes_tx_lane2), .serdes_tx_lane3(p3_serdes_tx_lane3),
        .serdes_tx_valid(p3_serdes_tx_valid),
        .serdes_rx_lane0(p3_serdes_rx_lane0), .serdes_rx_lane1(p3_serdes_rx_lane1),
        .serdes_rx_lane2(p3_serdes_rx_lane2), .serdes_rx_lane3(p3_serdes_rx_lane3),
        .serdes_rx_valid(p3_serdes_rx_valid),
        .csr_wen(csr_wen_3), .csr_wdata(csr_wdata), .local_scna(port_scna[3]),
        .link_up(port_link_up[3]), .link_ready(port_link_ready[3]),
        .all_lanes_aligned(), .fec_fail(),
        .training_mode(training_mode), .start_train(start_train[3])
    );

    //=========================================================================
    // 4x4 Crossbar Fabric
    //=========================================================================
    ub_xbar_fabric u_xbar (
        .clk(dl_clk), .rst_n(dl_rst_n),
        // Input ports (from port RX)
        .in_pkt_data_0(port_rx_data[0]), .in_pkt_valid_0(port_rx_valid[0]),
        .in_pkt_sop_0(port_rx_sop[0]), .in_pkt_eop_0(port_rx_eop[0]),
        .in_dest_port_0(dest_port[0]), .in_pkt_ready_0(xbar_in_ready[0]),
        .in_pkt_data_1(port_rx_data[1]), .in_pkt_valid_1(port_rx_valid[1]),
        .in_pkt_sop_1(port_rx_sop[1]), .in_pkt_eop_1(port_rx_eop[1]),
        .in_dest_port_1(dest_port[1]), .in_pkt_ready_1(xbar_in_ready[1]),
        .in_pkt_data_2(port_rx_data[2]), .in_pkt_valid_2(port_rx_valid[2]),
        .in_pkt_sop_2(port_rx_sop[2]), .in_pkt_eop_2(port_rx_eop[2]),
        .in_dest_port_2(dest_port[2]), .in_pkt_ready_2(xbar_in_ready[2]),
        .in_pkt_data_3(port_rx_data[3]), .in_pkt_valid_3(port_rx_valid[3]),
        .in_pkt_sop_3(port_rx_sop[3]), .in_pkt_eop_3(port_rx_eop[3]),
        .in_dest_port_3(dest_port[3]), .in_pkt_ready_3(xbar_in_ready[3]),
        // Output ports (to port TX)
        .out_pkt_data_0(xbar_out_data[0]), .out_pkt_valid_0(xbar_out_valid[0]),
        .out_pkt_sop_0(xbar_out_sop[0]), .out_pkt_eop_0(xbar_out_eop[0]),
        .out_pkt_ready_0(xbar_out_ready[0]),
        .out_pkt_data_1(xbar_out_data[1]), .out_pkt_valid_1(xbar_out_valid[1]),
        .out_pkt_sop_1(xbar_out_sop[1]), .out_pkt_eop_1(xbar_out_eop[1]),
        .out_pkt_ready_1(xbar_out_ready[1]),
        .out_pkt_data_2(xbar_out_data[2]), .out_pkt_valid_2(xbar_out_valid[2]),
        .out_pkt_sop_2(xbar_out_sop[2]), .out_pkt_eop_2(xbar_out_eop[2]),
        .out_pkt_ready_2(xbar_out_ready[2]),
        .out_pkt_data_3(xbar_out_data[3]), .out_pkt_valid_3(xbar_out_valid[3]),
        .out_pkt_sop_3(xbar_out_sop[3]), .out_pkt_eop_3(xbar_out_eop[3]),
        .out_pkt_ready_3(xbar_out_ready[3])
    );

endmodule
