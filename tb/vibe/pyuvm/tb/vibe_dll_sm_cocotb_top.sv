// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL link SM (AS-0.1 §12): Disabled / Param / Credit / Normal.
// Disabled when LinkUp==0. Entity reset is not a pin. Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_sm_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       link_up,
  input  logic       param_ok,
  input  logic       credit_ok,
  input  logic       dll_error,
  output logic [1:0] state,
  output logic       status_up,
  output logic       disabled
);
  vibe_dll_sm u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .param_ok(param_ok), .credit_ok(credit_ok), .dll_error(dll_error),
    .state(state), .status_up(status_up), .disabled(disabled)
  );
endmodule
