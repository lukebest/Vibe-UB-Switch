// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL RETRY_REQ_SM (AS-0.1 §12): NORMAL / REQ (1 Idle + burst
// Req) / WAIT (RETRY_WAIT_CYC, default 12500) / RETRAIN / ERROR.
// Instantiated by vibe_dll u_req. Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_retry_req_sm_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       device_rst,
  input  logic       start_retry,
  input  logic       phy_retrain,
  input  logic       wait_done_ack,
  output logic [2:0] state,
  output logic       drop_data,
  output logic       retrain_req,
  output logic       retry_error,
  output logic       send_idle,
  output logic       send_req,
  output logic [4:0] send_cnt
);
  vibe_dll_retry_req_sm u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .start_retry(start_retry), .phy_retrain(phy_retrain),
    .wait_done_ack(wait_done_ack),
    .state(state), .drop_data(drop_data), .retrain_req(retrain_req),
    .retry_error(retry_error), .send_idle(send_idle), .send_req(send_req),
    .send_cnt(send_cnt)
  );
endmodule
