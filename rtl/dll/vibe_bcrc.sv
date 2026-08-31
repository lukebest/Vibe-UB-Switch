// AS-0.1 §12: BCRC CRC30, init all-1, no invert. bit31 reserved, bit30 ERROR_FLAG.
module vibe_bcrc (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [159:0] in_flit,
  input  logic         last,
  input  logic         error_flag,
  output logic [31:0]  crc_word,
  output logic         done
);
  `include "vibe_ub_params.vh"

  logic [29:0] crc;
  integer i;

  function automatic [29:0] crc30_step;
    input [29:0] c;
    input        b;
    logic        fb;
    begin
      fb = c[29] ^ b;
      crc30_step = {c[28:0], 1'b0} ^ ({30{fb}} & VIBE_BCRC_POLY);
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      crc      <= {30{1'b1}};
      crc_word <= 32'd0;
      done     <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start)
        crc <= {30{1'b1}};
      else if (in_vld) begin
        begin : eat
          logic [29:0] t;
          t = crc;
          for (i = 0; i < 160; i = i + 1)
            t = crc30_step(t, in_flit[i]);
          crc <= t;
          if (last) begin
            crc_word <= {1'b0, error_flag, t};
            done     <= 1'b1;
          end
        end
      end
    end
  end
endmodule
