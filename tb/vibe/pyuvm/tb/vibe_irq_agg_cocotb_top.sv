// Thin cocotb wrapper. DUT RTL never edited.
// Product mgmt sticky OR (AS-0.1 §10/§15, SPEC §14): irq_logic is
// the 1-bit flop of |rx_ovf | |fc_ovf | |proto_err | |retry_error
// | icrc_fail | |len_err | |deadlock_drop | drop_g1 | |afifo_ovf.
// Clear on irq_clr (wins) or async-low rst_n. No per-cause status
// and no extra product IRQ pins. Port Reset / device_rst are wrap
// concerns (vibe_mgmt ORs device_rst into irq_clr). Instantiated
// by vibe_mgmt u_irq. Clock from entry_unit (2 ns). Instance u_u
// matches Decision-I leaf wrappers.
`timescale 1ns/1ps

module vibe_irq_agg_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       irq_clr,
  input  logic [3:0] rx_ovf,
  input  logic [3:0] fc_ovf,
  input  logic [3:0] proto_err,
  input  logic [3:0] retry_error,
  input  logic       icrc_fail,
  input  logic [3:0] len_err,
  input  logic [3:0] deadlock_drop,
  input  logic       drop_g1,
  input  logic [3:0] afifo_ovf,
  output logic       irq_logic
);
  vibe_irq_agg u_u (
    .clk(clk), .rst_n(rst_n), .irq_clr(irq_clr),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .icrc_fail(icrc_fail),
    .len_err(len_err), .deadlock_drop(deadlock_drop),
    .drop_g1(drop_g1), .afifo_ovf(afifo_ovf),
    .irq_logic(irq_logic)
  );
endmodule
