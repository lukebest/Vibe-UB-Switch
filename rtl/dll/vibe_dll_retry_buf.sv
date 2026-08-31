// AS-0.1 §12: retry_buf depth 256 FS-must. Null and Retry blocks do not enter.
// NumFreeBuf+ReleaseSize>256 → DL Protocol Error.
module vibe_dll_retry_buf (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         link_up,
  input  logic         wr_en,
  input  logic         is_null,
  input  logic         is_retry,
  input  logic [159:0] wr_flit,
  input  logic [7:0]   send_size,
  input  logic         ack_rel,
  input  logic [7:0]   rel_size,
  input  logic [7:0]   rd_ptr_i,
  output logic [159:0] rd_flit,
  output logic [7:0]   wr_ptr,
  output logic [7:0]   tail_ptr,
  output logic [7:0]   rcv_ptr,
  output logic [8:0]   num_free,
  output logic         proto_err,
  output logic         can_send
);
  `include "vibe_ub_params.vh"

  logic [159:0] mem [0:255];
  logic [7:0]   wrp, tail, rcv;
  logic [8:0]   freeb;

  assign wr_ptr   = wrp;
  assign tail_ptr = tail;
  assign rcv_ptr  = rcv;
  assign num_free = freeb;
  assign can_send = (freeb >= {1'b0, send_size});
  assign rd_flit  = mem[rd_ptr_i];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wrp       <= 8'd0;
      tail      <= 8'd0;
      rcv       <= 8'd0;
      freeb     <= 9'd256;
      proto_err <= 1'b0;
    end else if (port_rst || !link_up) begin
      wrp       <= 8'd0;
      tail      <= 8'd0;
      rcv       <= 8'd0;
      freeb     <= 9'd256;
    end else begin
      if (wr_en && !is_null && !is_retry && can_send) begin
        mem[wrp] <= wr_flit;
        wrp      <= wrp + 8'd1;
        freeb    <= freeb - 9'd1;
      end
      if (ack_rel) begin
        if (freeb + {1'b0, rel_size} > 9'd256)
          proto_err <= 1'b1;
        else begin
          freeb <= freeb + {1'b0, rel_size};
          tail  <= tail + rel_size;
          rcv   <= rcv + rel_size;
        end
      end
    end
  end
endmodule
