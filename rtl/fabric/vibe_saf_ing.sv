// AS-0.1 §8: store-and-forward. Do not present to xbar until EOP/full declared length.
// Length not in 16–4300B → Packet Length Error, drop, irq.
module vibe_saf_ing #(
  parameter int DEPTH = 128
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [511:0] in_data,
  input  logic         in_vld,
  output logic         in_ready,
  output logic [511:0] pkt_data,
  output logic         pkt_vld,
  input  logic         pkt_ready,
  output logic         pkt_sop,
  output logic         pkt_eop,
  output logic [15:0]  pkt_bytes,
  output logic         len_err
);
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  logic [511:0] mem [0:DEPTH-1];
  logic [6:0]   wptr, rptr;
  logic [6:0]   beat_cnt, decl_beats;
  logic [15:0]  bytes;
  logic         assembling, done;
  logic [13:0]  plen;
  integer       dflits;

  assign in_ready = (wptr + 7'd1) != rptr;
  assign pkt_vld  = done && (rptr != wptr);
  assign pkt_data = mem[rptr];
  assign pkt_sop  = pkt_vld && (rptr == 7'd0 || beat_cnt == 0);
  assign pkt_eop  = pkt_vld && (rptr + 7'd1 == wptr);
  assign pkt_bytes= bytes;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr        <= 7'd0;
      rptr        <= 7'd0;
      beat_cnt    <= 7'd0;
      decl_beats  <= 7'd0;
      bytes       <= 16'd0;
      assembling  <= 1'b0;
      done        <= 1'b0;
      len_err     <= 1'b0;
    end else begin
      len_err <= 1'b0;
      if (in_vld && in_ready) begin
        mem[wptr] <= in_data;
        wptr      <= wptr + 7'd1;
        if (!assembling) begin
          assembling <= 1'b1;
          plen       = vibe_lph_plength(vibe_nw512_flit0(in_data));
          dflits     = vibe_decl_flits(plen);
          decl_beats <= vibe_nw512_decl_beats(vibe_nw512_flit0(in_data));
          bytes      <= dflits * 20;
          beat_cnt   <= 7'd1;
          if ((dflits * 20) < VIBE_PKT_LEN_MIN || (dflits * 20) > VIBE_PKT_LEN_MAX) begin
            len_err    <= 1'b1;
            assembling <= 1'b0;
            wptr       <= wptr; // drop: rewind
            wptr       <= rptr;
          end else if (vibe_nw512_decl_beats(vibe_nw512_flit0(in_data)) == 8'd1) begin
            // 1-beat (≤64 B): complete on SOP so pkt_sop && pkt_eop coincide
            assembling <= 1'b0;
            done       <= 1'b1;
          end
        end else begin
          beat_cnt <= beat_cnt + 7'd1;
          if (beat_cnt + 7'd1 >= decl_beats) begin
            assembling <= 1'b0;
            done       <= 1'b1;
          end
        end
      end
      if (pkt_vld && pkt_ready) begin
        rptr <= rptr + 7'd1;
        if (pkt_eop) begin
          done <= 1'b0;
          wptr <= 7'd0;
          rptr <= 7'd0;
        end
      end
    end
  end
endmodule
