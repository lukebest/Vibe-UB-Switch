// AS-0.1 §6/§12: BCRC check + CFG0 terminate. FEC/BCRC fail → Go-Back-N.
// LinkUp==0: incomplete RX DLLDP pad 0 + ERROR_FLAG.
// dll_rxbuf = 1024 flit/VL exclusive. Overflow → irq.
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
  output logic [639:0] nw_data,
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
  integer       v;

  wire [159:0] f0 = pcs_data[639:480];
  wire [3:0]   cfg = vibe_lph_cfg(f0);
  wire [3:0]   vl  = vibe_lph_vl(f0);
  wire         is_cfg0 = (cfg == 4'd0);

  assign pcs_ready = link_up ? (!have || nw_ready || is_cfg0) : 1'b1;
  assign start_retry = fec_fail || bcrc_fail;
  assign start_ack   = 1'b0; // set when remote REQ seen (CFG0 retry)

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      have      <= 1'b0;
      hold      <= 640'd0;
      nw_data   <= 640'd0;
      nw_vld    <= 1'b0;
      cfg0_hit  <= 1'b0;
      cfg0_data <= 640'd0;
      bcrc_fail <= 1'b0;
      rx_ovf    <= 1'b0;
      for (v = 0; v < 16; v = v + 1) begin
        wptr[v] <= 11'd0;
        rptr[v] <= 11'd0;
      end
    end else if (port_rst || !link_up) begin
      have    <= 1'b0;
      nw_vld  <= 1'b0;
      cfg0_hit<= 1'b0;
      if (!link_up && have) begin
        nw_data <= {hold[639:32], 1'b0, 1'b1, 30'd0}; // pad 0 + ERROR_FLAG
        nw_vld  <= 1'b1;
      end
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
      if (have && !nw_vld) begin
        nw_data <= hold;
        nw_vld  <= 1'b1;
        have    <= 1'b0;
      end
      if (fec_fail)
        bcrc_fail <= 1'b0;
    end
  end
endmodule
