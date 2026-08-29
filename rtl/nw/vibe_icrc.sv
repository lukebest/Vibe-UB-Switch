// AS-0.1 §13: CRC32 0x04C11DB7 init 0xFFFFFFFF, per-byte bit reverse then reverse+invert.
// Used only by cna_ep (sender/receiver). Transit has NO ICRC unit.
module vibe_icrc (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_byte,
  input  logic         last,
  output logic [31:0]  crc_out,
  output logic         done
);
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  logic [31:0] crc;
  integer i;

  function automatic [31:0] step8;
    input [31:0] c;
    input [7:0]  b;
    logic [31:0] t;
    logic [7:0]  br;
    integer k;
    begin
      br = vibe_rev8(b);
      t = c;
      for (k = 0; k < 8; k = k + 1) begin
        if (t[31] ^ br[7-k])
          t = {t[30:0], 1'b0} ^ VIBE_ICRC_POLY;
        else
          t = {t[30:0], 1'b0};
      end
      step8 = t;
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      crc     <= 32'hFFFF_FFFF;
      crc_out <= 32'd0;
      done    <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start)
        crc <= 32'hFFFF_FFFF;
      else if (in_vld) begin
        crc <= step8(crc, in_byte);
        if (last) begin
          crc_out <= ~vibe_rev32(step8(crc, in_byte));
          done    <= 1'b1;
        end
      end
    end
  end
endmodule
