// AS-0.1 §2/§8: available = bitmap AND DLL_Status_Up.
// Empty after filter → Default; Default all-0 → port 0; if port0 Down, drop+count, no flood.
// RT=00 per-flow sticky RR; RT=01 per-packet RR. Flow key {CFG, src, dest, VL}.
module vibe_port_sel (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [3:0]  bitmap,
  input  logic [3:0]  status_up,
  input  logic [3:0]  default_bm,
  input  logic [1:0]  rt,
  input  logic        drop_g1,
  input  logic        sel_vld,
  input  logic [3:0]  cfg,
  input  logic [15:0] src,
  input  logic [15:0] dest,
  input  logic [3:0]  vl,
  output logic [1:0]  egr,
  output logic        drop,
  output logic [31:0] drop_down_cnt
);
  logic [3:0] avail;
  logic [3:0] use_bm;
  logic [1:0] rr;
  logic [1:0] sticky [0:15];
  logic [3:0] fidx;
  integer     k;

  assign fidx  = vl; // compact flow slot; full key used for sticky update
  assign avail = drop_g1 ? 4'd0 : (bitmap & status_up);
  assign use_bm = (avail == 4'd0) ? (
                    ((default_bm == 4'd0) ? 4'b0001 : default_bm) & status_up
                  ) : avail;

  function automatic [1:0] pick_rr;
    input [3:0] bm;
    input [1:0] start;
    logic [1:0] p;
    integer n;
    begin
      p = start;
      pick_rr = 2'd0;
      for (n = 0; n < 4; n = n + 1) begin
        if (bm[p]) begin
          pick_rr = p;
          n = 4;
        end else
          p = p + 2'd1;
      end
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      egr           <= 2'd0;
      drop          <= 1'b0;
      drop_down_cnt <= 32'd0;
      rr            <= 2'd0;
      for (k = 0; k < 16; k = k + 1) sticky[k] <= 2'd0;
    end else begin
      drop <= 1'b0;
      if (sel_vld) begin
        if (drop_g1 || use_bm == 4'd0) begin
          drop <= 1'b1;
          if (!drop_g1 && use_bm == 4'd0)
            drop_down_cnt <= drop_down_cnt + 32'd1;
        end else if (rt == 2'b00) begin
          egr <= (use_bm[sticky[fidx]]) ? sticky[fidx] : pick_rr(use_bm, sticky[fidx]);
          if (!use_bm[sticky[fidx]])
            sticky[fidx] <= pick_rr(use_bm, sticky[fidx]);
        end else begin
          egr <= pick_rr(use_bm, rr);
          rr  <= pick_rr(use_bm, rr) + 2'd1;
        end
      end
    end
  end
endmodule
