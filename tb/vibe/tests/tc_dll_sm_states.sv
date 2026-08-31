// DLL SM: Disabled / Param_Init / Credit_Init / Normal. LinkUp==0 → Disabled.
// Entity reset is not a pin on this SM (must not force Disabled by itself).
`timescale 1ns/1ps
module tc_dll_sm_states;
  logic clk, rst_n, port_rst, link_up, param_ok, credit_ok, dll_error;
  logic [1:0] state;
  logic status_up, disabled;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_sm u_sm (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .param_ok(param_ok), .credit_ok(credit_ok), .dll_error(dll_error),
    .state(state), .status_up(status_up), .disabled(disabled)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 0; param_ok = 0; credit_ok = 0; dll_error = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (state !== 2'd0 || !disabled) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : reset LinkUp=0");
      $display("  expected : ST_DIS disabled=1");
      $display("  actual   : state=%0d dis=%0b", state, disabled);
      $display("  hier     : u_sm.st");
      fail = 1;
    end
    link_up = 1;
    @(posedge clk);
    @(posedge clk); // --cc: ST_DIS → Param (link_up already qualified)
    if (state !== 2'd1) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : LinkUp=1");
      $display("  expected : Param_Init (1)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    // hold Param_Init while !param_ok (case else)
    param_ok = 0;
    repeat (3) @(posedge clk);
    if (state !== 2'd1) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : LinkUp=1 param_ok=0");
      $display("  expected : stay Param_Init");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    param_ok = 1;
    @(posedge clk);
    if (state !== 2'd2) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : param_ok");
      $display("  expected : Credit_Init (2)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    credit_ok = 0;
    repeat (3) @(posedge clk);
    if (state !== 2'd2) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : Credit_Init credit_ok=0");
      $display("  expected : stay Credit_Init");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    credit_ok = 1;
    @(posedge clk);
    if (state !== 2'd3 || !status_up) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : credit_ok");
      $display("  expected : Normal status_up=1");
      $display("  actual   : state=%0d up=%0b", state, status_up);
      fail = 1;
    end
    // No device_rst pin: staying in Normal proves entity reset is not wired here.
    repeat (4) @(posedge clk);
    if (state !== 2'd3) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : hold Normal (no port_rst)");
      $display("  expected : remain Normal (entity rst must not force Disabled)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    link_up = 0;
    @(posedge clk);
    if (state !== 2'd0) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : LinkUp=0");
      $display("  expected : Disabled");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    // port_rst → Disabled even if LinkUp=1
    link_up = 1; param_ok = 1; credit_ok = 1;
    @(posedge clk);
    @(posedge clk);
    @(posedge clk);
    port_rst = 1;
    @(posedge clk);
    #0;
    if (state !== 2'd0) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : port_rst while LinkUp=1");
      $display("  expected : Disabled (sample while port_rst held)");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    port_rst = 0;
    @(posedge clk);
    // dll_error → Disabled from Normal
    link_up = 1;
    @(posedge clk); // DIS→PARM
    @(posedge clk); // PARM→CRD
    @(posedge clk); // CRD→NRM
    dll_error = 1;
    @(posedge clk);
    dll_error = 0;
    if (state !== 2'd0) begin
      $display("FAIL tc_dll_sm_states");
      $display("  stimulus : dll_error in Normal");
      $display("  expected : Disabled");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    if (!fail) $display("PASS tc_dll_sm_states");
    $finish;
  end
endmodule
