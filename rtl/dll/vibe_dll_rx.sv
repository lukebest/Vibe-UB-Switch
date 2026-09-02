// AS-0.1.2 / FS-0.2.7 overlay B: 640b PCS → 4 flits, unBCRC (wire flits
// including CRC in last 32b of the group), pack to 512b NW beats with
// remainder. LPH is the first 160b flit of the assembled packet.
// CFG0 terminate. FEC/BCRC fail → Go-Back-N. dll_rxbuf = 1024 flit/VL.
module vibe_dll_rx #(
  parameter int RXBUF = 1024
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         link_up,
  input  logic         fec_fail,
  input  logic [639:0] pcs_data,
  input  logic         pcs_vld,
  output logic         pcs_ready,
  output logic [511:0] nw_data,
  output logic         nw_vld,
  input  logic         nw_ready,
  output logic         cfg0_hit,
  output logic [639:0] cfg0_data,
  output logic         bcrc_fail,
  output logic         start_retry,
  output logic         rx_ovf,
  output logic         start_ack
);
  `include "vibe_ub_fn.vh"

  logic [159:0] rbuf [0:15][0:RXBUF-1];
  logic [10:0]  wptr [0:15];
  logic [10:0]  rptr [0:15];
  logic [639:0] hold;
  logic         have;
  logic [1279:0] by_lj;
  logic [7:0]    by_n;
  logic          pkt_act;
  logic [15:0]   pkt_left;
  integer        v;

  wire [159:0] f0 = pcs_data[639:480];
  wire [3:0]   cfg = vibe_lph_cfg(f0);
  wire [3:0]   vl  = vibe_lph_vl(f0);
  wire         is_cfg0 = (cfg == 4'd0);

  assign pcs_ready = link_up ?
                     (is_cfg0 || (!have && (by_n == 8'd0) && !pkt_act)) : 1'b1;
  assign start_retry = fec_fail || bcrc_fail;
  assign start_ack   = 1'b0;

  wire [15:0] hdr_bytes = vibe_pkt_bytes(by_lj[1279:1120]);
  wire        need_hdr  = !pkt_act && (by_n >= 8'd20);
  wire [15:0] left_now  = need_hdr ? hdr_bytes : pkt_left;
  wire        have_pkt  = pkt_act || need_hdr;
  wire [7:0]  emit_n    = (have_pkt && (left_now >= 16'd64) && (by_n >= 8'd64)) ? 8'd64 :
                          (have_pkt && (left_now > 16'd0) && (left_now <= 16'd64) &&
                           (by_n >= left_now[7:0])) ? left_now[7:0] : 8'd0;
  wire        can_emit  = (emit_n != 8'd0) && (!nw_vld || nw_ready);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      have      <= 1'b0;
      hold      <= 640'd0;
      nw_data   <= 512'd0;
      nw_vld    <= 1'b0;
      cfg0_hit  <= 1'b0;
      cfg0_data <= 640'd0;
      bcrc_fail <= 1'b0;
      rx_ovf    <= 1'b0;
      by_lj     <= 1280'd0;
      by_n      <= 8'd0;
      pkt_act   <= 1'b0;
      pkt_left  <= 16'd0;
      for (v = 0; v < 16; v = v + 1) begin
        wptr[v] <= 11'd0;
        rptr[v] <= 11'd0;
      end
    end else if (port_rst || !link_up) begin
      have     <= 1'b0;
      nw_vld   <= 1'b0;
      cfg0_hit <= 1'b0;
      pkt_act  <= 1'b0;
      if (!link_up && (have || (by_n != 8'd0))) begin
        nw_data <= {by_lj[1279:800], 1'b0, 1'b1, 30'd0};
        nw_vld  <= 1'b1;
      end
      by_lj    <= 1280'd0;
      by_n     <= 8'd0;
      pkt_left <= 16'd0;
    end else begin
      cfg0_hit  <= 1'b0;
      bcrc_fail <= 1'b0;
      if (nw_vld && nw_ready)
        nw_vld <= 1'b0;

      if (pcs_vld && pcs_ready) begin
        if (is_cfg0) begin
          cfg0_hit  <= 1'b1;
          cfg0_data <= pcs_data;
        end else if (wptr[vl] - rptr[vl] >= RXBUF[10:0]) begin
          rx_ovf <= 1'b1;
        end else begin
          hold     <= pcs_data;
          have     <= 1'b1;
          wptr[vl] <= wptr[vl] + 11'd4;
        end
      end

      if (have && (by_n <= 8'd80)) begin
        by_lj <= by_lj | ({hold, 640'b0} >> (by_n * 8));
        by_n  <= by_n + 8'd80;
        have  <= 1'b0;
      end else if (can_emit) begin
        nw_data <= by_lj[1279:768] & ({512{1'b1}} << (9'd512 - {1'b0, emit_n} * 9'd8));
        nw_vld  <= 1'b1;
        by_lj   <= by_lj << (emit_n * 8);
        by_n    <= by_n - emit_n;
        if (left_now <= {8'b0, emit_n}) begin
          pkt_act  <= 1'b0;
          pkt_left <= 16'd0;
        end else begin
          pkt_act  <= 1'b1;
          pkt_left <= left_now - {8'b0, emit_n};
        end
      end else if (need_hdr) begin
        pkt_act  <= 1'b1;
        pkt_left <= hdr_bytes;
      end

      if (fec_fail)
        bcrc_fail <= 1'b0;
    end
  end
endmodule
