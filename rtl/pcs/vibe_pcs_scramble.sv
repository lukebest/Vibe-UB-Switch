// AS-0.1 §5: scramble LTB and DLL data; not AMCTL/EEIB. Per-lane additive PRBS23.
module vibe_pcs_scramble (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [1:0]   lane_id,
  input  logic         seed_load,
  input  logic         en,       // 0 = pass-through (AMCTL/EEIB)
  input  logic         in_vld,
  input  logic [159:0] in_data,
  output logic         out_vld,
  output logic [159:0] out_data
);
  `include "vibe_ub_params.vh"

  logic [22:0] lfsr;
  logic [159:0] xmask;
  integer i;

  function automatic [22:0] step;
    input [22:0] s;
    begin
      step = {s[21:0], s[22] ^ s[17]};
    end
  endfunction

  always @* begin
    xmask = 160'd0;
    begin : gen_mask
      logic [22:0] t;
      t = lfsr;
      for (i = 0; i < 160; i = i + 1) begin
        xmask[i] = t[0];
        t = step(t);
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      lfsr     <= {21'd0, 2'b01};
      out_vld  <= 1'b0;
      out_data <= 160'd0;
    end else begin
      if (seed_load)
        lfsr <= {19'd1, lane_id, 2'b01};
      out_vld <= in_vld;
      if (in_vld) begin
        out_data <= en ? (in_data ^ xmask) : in_data;
        if (en) begin
          begin : adv
            logic [22:0] t;
            t = lfsr;
            for (i = 0; i < 160; i = i + 1) t = step(t);
            lfsr <= t;
          end
        end
      end
    end
  end
endmodule
