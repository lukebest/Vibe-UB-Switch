// VL RR among nonempty VOQs; FCFS within VL. No SL (AS-0.1 §8).
`timescale 1ns/1ps

module tc_vl_rr;
  logic        clk, rst_n, grant, valid;
  logic [15:0] nonempty;
  logic [3:0]  vl_sel;
  integer      fail;
  integer      a, b, c;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_vl_rr u_rr (
    .clk(clk), .rst_n(rst_n), .nonempty(nonempty),
    .grant(grant), .vl_sel(vl_sel), .valid(valid)
  );

  initial begin
    fail = 0;
    rst_n = 0; nonempty = 16'd0; grant = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    nonempty = 16'b0000_0000_0000_0101; // VL0 and VL2
    @(posedge clk);
    a = vl_sel;
    grant = 1;
    @(posedge clk);
    grant = 0;
    @(posedge clk);
    b = vl_sel;
    grant = 1;
    @(posedge clk);
    grant = 0;
    @(posedge clk);
    c = vl_sel;
    if (!valid) begin
      $display("FAIL tc_vl_rr");
      $display("  stimulus : nonempty=VL0|VL2");
      $display("  expected : valid=1");
      $display("  actual   : valid=0");
      $display("  hier     : u_rr.valid");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end else if (a == b && b == c) begin
      $display("FAIL tc_vl_rr");
      $display("  stimulus : nonempty VL0+VL2, three grants");
      $display("  expected : RR walks both VLs (not pinned)");
      $display("  actual   : vl_sel stayed %0d", a);
      $display("  hier     : u_rr.rr / vl_sel");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (!fail) $display("PASS tc_vl_rr");
    $finish;
  end
endmodule
