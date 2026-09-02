// AS-0.1.2 / FS-0.2.7 overlay B: 512b NW byte stream → 20B flits with
// cross-beat remainder (64B beat, 20B flit, rem 4B). When 4 flits are
// ready, emit one 640b beat to PCS with BCRC (CRC30, last 32b of the 640).
// Backpressure if credit low / retry full / REQ|WAIT dropping data /
// pending >= 1024 cell. CFG0 does not consume credit.
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
  input  logic [511:0] nw_data,
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
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  logic [159:0] rem_lj;
  logic [4:0]   rem_b;
  logic         pkt_act;
  logic [15:0]  pkt_left;

  logic [159:0] fq [0:7];
  logic [3:0]   fq_n;

  wire emitting = (fq_n >= 4'd4) && (pcs_ready || !pcs_vld) &&
                  !send_idle && !send_req && !send_ack && !replay;
  wire [3:0] fq_occ = fq_n - (emitting ? 4'd4 : 4'd0);

  assign nw_ready = link_up && status_up && !credit_low && !bp_pending &&
                    !drop_data && can_send && !replay &&
                    !send_idle && !send_req && !send_ack &&
                    (fq_occ <= 4'd4);

  wire [159:0] sop_flit  = vibe_nw512_flit0(nw_data);
  wire [15:0]  sop_bytes = vibe_pkt_bytes(sop_flit);
  wire [15:0]  cur_left  = pkt_act ? pkt_left : sop_bytes;
  wire [6:0]   val_b     = (cur_left > 16'd64) ? 7'd64 : cur_left[6:0];
  wire [7:0]   tot_b     = {3'b0, rem_b} + {1'b0, val_b};
  wire [2:0]   n_flits   = tot_b / 8'd20;
  wire [4:0]   new_rem_b = tot_b % 8'd20;

  function automatic [29:0] crc30_bit;
    input [29:0] c;
    input        b;
    logic        fb;
    begin
      fb = c[29] ^ b;
      crc30_bit = {c[28:0], 1'b0} ^ ({30{fb}} & VIBE_BCRC_POLY);
    end
  endfunction

  function automatic [29:0] crc30_flit;
    input [29:0]  c;
    input [159:0] f;
    integer       i;
    begin
      crc30_flit = c;
      for (i = 0; i < 160; i = i + 1)
        crc30_flit = crc30_bit(crc30_flit, f[i]);
    end
  endfunction

  // Left-justified rem || valid NW bytes in a 672b window.
  reg  [671:0] stream;
  reg  [159:0] rem_c;
  reg  [511:0] nw_c;
  integer      rem_bits, val_bits, gap;
  always @* begin
    rem_bits = rem_b * 8;
    val_bits = val_b * 8;
    if (rem_b == 5'd0)
      rem_c = 160'd0;
    else
      rem_c = rem_lj & ({160{1'b1}} << (160 - rem_bits));
    if (val_b == 7'd0)
      nw_c = 512'd0;
    else
      nw_c = nw_data & ({512{1'b1}} << (512 - val_bits));
    gap    = 160 - rem_bits;
    stream = {rem_c, 512'b0} | ({160'b0, nw_c} << gap);
  end

  wire [159:0] nf0 = stream[671:512];
  wire [159:0] nf1 = stream[511:352];
  wire [159:0] nf2 = stream[351:192];
  wire [159:0] nf3 = stream[191:32];
  wire [671:0] stream_sh = stream << (n_flits * 16'd160);
  wire [159:0] new_rem_lj = stream_sh[671:512];

  wire [29:0] crc0 = crc30_flit({30{1'b1}}, fq[0]);
  wire [29:0] crc1 = crc30_flit(crc0, fq[1]);
  wire [29:0] crc2 = crc30_flit(crc1, fq[2]);
  wire [29:0] crc3 = crc30_flit(crc2, fq[3]);
  wire [31:0] crc_w = {1'b0, 1'b0, crc3};
  wire [639:0] pcs_beat = {fq[0], fq[1], fq[2], fq[3][159:32], crc_w};

  assign is_null  = send_idle;
  assign is_retry = send_req || send_ack;
  assign wr_en    = emitting && !is_null && !is_retry;
  assign wr_flit  = fq[0];

  assign consume_cfg0  = !pkt_act && (vibe_lph_cfg(sop_flit) == 4'd0);
  assign consume_flits = {7'b0, n_flits};
  assign consume_vld   = nw_vld && nw_ready;

  reg [159:0] fq_nxt [0:7];
  reg [3:0]   fq_n_nxt;
  integer     k;
  always @* begin
    for (k = 0; k < 8; k = k + 1)
      fq_nxt[k] = fq[k];
    fq_n_nxt = fq_n;
    if (emitting) begin
      for (k = 0; k < 4; k = k + 1)
        fq_nxt[k] = fq[k+4];
      for (k = 4; k < 8; k = k + 1)
        fq_nxt[k] = 160'd0;
      fq_n_nxt = fq_n - 4'd4;
    end
    if (nw_vld && nw_ready) begin
      if (n_flits >= 3'd1) fq_nxt[fq_n_nxt]        = nf0;
      if (n_flits >= 3'd2) fq_nxt[fq_n_nxt + 4'd1] = nf1;
      if (n_flits >= 3'd3) fq_nxt[fq_n_nxt + 4'd2] = nf2;
      if (n_flits >= 3'd4) fq_nxt[fq_n_nxt + 4'd3] = nf3;
      fq_n_nxt = fq_n_nxt + {1'b0, n_flits};
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rem_lj   <= 160'd0;
      rem_b    <= 5'd0;
      pkt_act  <= 1'b0;
      pkt_left <= 16'd0;
      fq_n     <= 4'd0;
      pcs_data <= 640'd0;
      pcs_vld  <= 1'b0;
      for (k = 0; k < 8; k = k + 1)
        fq[k] <= 160'd0;
    end else if (!link_up) begin
      rem_lj   <= 160'd0;
      rem_b    <= 5'd0;
      pkt_act  <= 1'b0;
      pkt_left <= 16'd0;
      fq_n     <= 4'd0;
      pcs_vld  <= 1'b0;
    end else begin
      for (k = 0; k < 8; k = k + 1)
        fq[k] <= fq_nxt[k];
      fq_n <= fq_n_nxt;

      if (send_idle || send_req || send_ack) begin
        if (pcs_ready || !pcs_vld) begin
          pcs_data <= {4{160'd0}};
          pcs_vld  <= 1'b1;
        end
      end else if (replay) begin
        if (pcs_ready || !pcs_vld) begin
          pcs_data <= {replay_flit, 480'd0};
          pcs_vld  <= 1'b1;
        end
      end else if (emitting) begin
        pcs_data <= pcs_beat;
        pcs_vld  <= 1'b1;
      end else if (pcs_vld && pcs_ready) begin
        pcs_vld <= 1'b0;
      end

      if (nw_vld && nw_ready) begin
        if (cur_left <= {9'b0, val_b}) begin
          pkt_act  <= 1'b0;
          pkt_left <= 16'd0;
          rem_b    <= 5'd0;
          rem_lj   <= 160'd0;
        end else begin
          pkt_act  <= 1'b1;
          pkt_left <= cur_left - {9'b0, val_b};
          rem_b    <= new_rem_b;
          rem_lj   <= new_rem_lj;
        end
      end
    end
  end
endmodule
