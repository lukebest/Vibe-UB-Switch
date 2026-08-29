// AS-0.1 §5 T1 / §12: slice 640b=4 flits + BCRC.
// Backpressure if credit low / retry full / REQ|WAIT dropping data / pending >= 1024.
// DLLDP >32 flits split into ≤16 DLLDB of ≤32 flits. CFG0 does not consume credit.
module vibe_dll_tx (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         link_up,
  input  logic         status_up,
  input  logic         credit_low,
  input  logic         bp_pending,
  input  logic         drop_data,
  input  logic         can_send,
  input  logic         replay,
  input  logic [159:0] replay_flit,
  input  logic         send_idle,
  input  logic         send_req,
  input  logic         send_ack,
  input  logic [639:0] nw_data,
  input  logic         nw_vld,
  output logic         nw_ready,
  output logic [639:0] pcs_data,
  output logic         pcs_vld,
  input  logic         pcs_ready,
  output logic         wr_en,
  output logic [159:0] wr_flit,
  output logic         is_null,
  output logic         is_retry,
  output logic [9:0]   consume_flits,
  output logic         consume_vld,
  output logic         consume_cfg0
);
  `include "vibe_ub_fn.vh"

  logic [639:0] hold;
  logic         have;
  logic [1:0]   fidx;
  logic [159:0] flit;
  logic [31:0]  bcrc;
  logic         bcrc_done;

  assign flit = replay ? replay_flit :
                (fidx == 2'd0) ? hold[639:480] :
                (fidx == 2'd1) ? hold[479:320] :
                (fidx == 2'd2) ? hold[319:160] :
                                 hold[159:0];

  assign nw_ready = link_up && status_up && !credit_low && !bp_pending &&
                    !drop_data && can_send && !have && !replay &&
                    !send_idle && !send_req && !send_ack;

  assign is_null  = send_idle;
  assign is_retry = send_req || send_ack;
  assign wr_en    = pcs_vld && pcs_ready && !is_null && !is_retry;
  assign wr_flit  = flit;

  wire [3:0] cfg0 = vibe_lph_cfg(hold[639:480]);
  assign consume_cfg0  = (cfg0 == 4'd0);
  assign consume_flits = 10'd4;
  assign consume_vld   = nw_vld && nw_ready;

  vibe_bcrc u_crc (
    .clk(clk), .rst_n(rst_n), .start(nw_vld && nw_ready),
    .in_vld(have && pcs_ready), .in_flit(flit),
    .last(fidx == 2'd3), .error_flag(1'b0),
    .crc_word(bcrc), .done(bcrc_done)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hold    <= 640'd0;
      have    <= 1'b0;
      fidx    <= 2'd0;
      pcs_data<= 640'd0;
      pcs_vld <= 1'b0;
    end else begin
      if (!link_up) begin
        have    <= 1'b0;
        pcs_vld <= 1'b0;
      end else if (send_idle || send_req || send_ack) begin
        if (pcs_ready || !pcs_vld) begin
          pcs_data <= {4{160'd0}};
          pcs_vld  <= 1'b1;
        end
      end else if (replay) begin
        if (pcs_ready || !pcs_vld) begin
          pcs_data <= {replay_flit, 480'd0};
          pcs_vld  <= 1'b1;
        end
      end else if (nw_vld && nw_ready) begin
        hold <= nw_data;
        have <= 1'b1;
        fidx <= 2'd0;
      end else if (have && (pcs_ready || !pcs_vld)) begin
        if (fidx == 2'd3) begin
          pcs_data <= {hold[639:32], bcrc};
          pcs_vld  <= 1'b1;
          have     <= 1'b0;
        end else begin
          pcs_data <= hold;
          pcs_vld  <= 1'b1;
          fidx     <= fidx + 2'd1;
        end
      end else if (pcs_vld && pcs_ready) begin
        pcs_vld <= 1'b0;
      end
    end
  end
endmodule
