// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL RETRY_ACK_SM (AS-0.1 §12): NORMAL / ACK (1 Idle + 32 Ack)
// then replay RdPtr=RcvPtr until WrPtr. Instantiated by vibe_dll u_ack.
// Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_retry_ack_sm_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       start_ack,
  input  logic [7:0] wr_ptr,
  input  logic [7:0] rcv_ptr,
  output logic [2:0] state,
  output logic       send_idle,
  output logic       send_ack,
  output logic       replay,
  output logic [7:0] rd_ptr
);
  vibe_dll_retry_ack_sm u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst),
    .start_ack(start_ack), .wr_ptr(wr_ptr), .rcv_ptr(rcv_ptr),
    .state(state), .send_idle(send_idle), .send_ack(send_ack),
    .replay(replay), .rd_ptr(rd_ptr)
  );
endmodule
