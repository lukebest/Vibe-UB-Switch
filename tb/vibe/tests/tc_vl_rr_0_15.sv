// VL0-15 RR: all 16 VLs nonempty, grant walks every VL.
`timescale 1ns/1ps
module tc_vl_rr_0_15;
  logic clk, rst_n, grant, valid;
  logic [15:0] nonempty;
  logic [3:0]  vl_sel;
  integer fail, i;
  logic [15:0] seen;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_vl_rr u_rr (
    .clk(clk), .rst_n(rst_n), .nonempty(nonempty),
    .grant(grant), .vl_sel(vl_sel), .valid(valid)
  );
  initial begin
    fail = 0; seen = 16'd0;
    rst_n = 0; nonempty = 16'hFFFF; grant = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    for (i = 0; i < 16; i = i + 1) begin
      if (!valid) fail = 1;
      seen[vl_sel] = 1'b1;
      grant = 1;
      @(posedge clk);
      grant = 0;
      @(posedge clk);
    end
    if (seen !== 16'hFFFF) begin
      $display("FAIL tc_vl_rr_0_15");
      $display("  stimulus : nonempty=FFFF, 16 grants");
      $display("  expected : every VL0-15 selected once (RR)");
      $display("  actual   : seen=%h", seen);
      $display("  hier     : u_rr.rr / vl_sel");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_vl_rr_0_15");
    $finish;
  end
endmodule
