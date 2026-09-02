// AS-0.1 §8/§14: VOQ 32 flit/VL/egress. Deadlock timeout 1us from enqueue.
module vibe_voq_egr #(
  parameter int DEPTH = 32
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [3:0]   wr_vl,
  input  logic         wr_en,
  input  logic [511:0] wr_data,
  input  logic         wr_sop,
  input  logic         wr_eop,
  output logic         wr_ready,
  input  logic [3:0]   rd_vl,
  input  logic         rd_en,
  output logic [511:0] rd_data,
  output logic         rd_sop,
  output logic         rd_eop,
  output logic [15:0]  nonempty,
  output logic [5:0]   occ_vl0,
  output logic         deadlock_drop,
  output logic [31:0]  deadlock_cnt
);
  `include "vibe_ub_params.vh"

  logic [511:0] mem [0:15][0:DEPTH-1];
  logic         sopm [0:15][0:DEPTH-1];
  logic         eopm [0:15][0:DEPTH-1];
  logic [5:0]   wptr [0:15];
  logic [5:0]   rptr [0:15];
  logic [10:0]  age  [0:15][0:DEPTH-1];
  integer       v, j;

  wire [5:0] occ = wptr[wr_vl] - rptr[wr_vl];
  assign wr_ready = occ < DEPTH[5:0];
  assign rd_data  = mem[rd_vl][rptr[rd_vl][4:0]];
  assign rd_sop   = sopm[rd_vl][rptr[rd_vl][4:0]];
  assign rd_eop   = eopm[rd_vl][rptr[rd_vl][4:0]];
  assign occ_vl0  = wptr[0] - rptr[0];

  always @* begin
    for (v = 0; v < 16; v = v + 1)
      nonempty[v] = (wptr[v] != rptr[v]);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      deadlock_drop <= 1'b0;
      deadlock_cnt  <= 32'd0;
      for (v = 0; v < 16; v = v + 1) begin
        wptr[v] <= 6'd0;
        rptr[v] <= 6'd0;
      end
    end else begin
      deadlock_drop <= 1'b0;
      if (wr_en && wr_ready) begin
        mem[wr_vl][wptr[wr_vl][4:0]]  <= wr_data;
        sopm[wr_vl][wptr[wr_vl][4:0]] <= wr_sop;
        eopm[wr_vl][wptr[wr_vl][4:0]] <= wr_eop;
        age[wr_vl][wptr[wr_vl][4:0]]  <= VIBE_US_CYC[10:0];
        wptr[wr_vl] <= wptr[wr_vl] + 6'd1;
      end
      if (rd_en)
        rptr[rd_vl] <= rptr[rd_vl] + 6'd1;
      for (v = 0; v < 16; v = v + 1) begin
        for (j = 0; j < DEPTH; j = j + 1) begin
          if (age[v][j] != 0)
            age[v][j] <= age[v][j] - 11'd1;
        end
        if ((wptr[v] != rptr[v]) && age[v][rptr[v][4:0]] == 0) begin
          rptr[v]        <= rptr[v] + 6'd1;
          deadlock_drop  <= 1'b1;
          deadlock_cnt   <= deadlock_cnt + 32'd1;
        end
      end
    end
  end
endmodule
