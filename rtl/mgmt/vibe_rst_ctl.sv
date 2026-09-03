// AS-0.1.2 §10 / Table D-103: device reset clears RW config (CNA unwritten),
// MUST NOT force DLL_Disabled. LMSM → Link_Idle.
// Port Reset is RW1C in vibe_cfg_space (stored bit = 1 while this hold is
// active). A write-1 pulse starts the existing stretch; HW returns the
// readable bit to 0 when this hold ends. Port p only: LMSM Link_Idle,
// DLL_Disabled, retry ptrs 0, NumFreeBuf=256. Not an irq_agg clear.
module vibe_rst_ctl (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       device_rst_pulse,
  input  logic [3:0] port_rst_pulse,
  output logic       device_rst,
  output logic [3:0] port_rst
);
  logic       dhold;
  logic [3:0] phold;
  logic [2:0] dct, pct [0:3];
  integer     i;

  assign device_rst = dhold;
  assign port_rst   = phold;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      dhold <= 1'b0;
      phold <= 4'd0;
      dct   <= 3'd0;
      for (i = 0; i < 4; i = i + 1) pct[i] <= 3'd0;
    end else begin
      if (device_rst_pulse) begin
        dhold <= 1'b1;
        dct   <= 3'd7;
      end else if (dct != 0) begin
        dct <= dct - 3'd1;
        if (dct == 3'd1) dhold <= 1'b0;
      end
      for (i = 0; i < 4; i = i + 1) begin
        if (port_rst_pulse[i]) begin
          phold[i] <= 1'b1;
          pct[i]   <= 3'd7;
        end else if (pct[i] != 0) begin
          pct[i] <= pct[i] - 3'd1;
          if (pct[i] == 3'd1) phold[i] <= 1'b0;
        end
      end
    end
  end
endmodule
