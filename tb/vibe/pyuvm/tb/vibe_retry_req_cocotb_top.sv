// Thin parameter / array wrapper. DUT RTL never edited.
`timescale 1ns/1ps

module vibe_retry_req_cocotb_top (
  input  logic       clk, rst_n, port_rst, device_rst,
  input  logic       start_retry, phy_retrain, wait_done_ack,
  output logic [2:0] state,
  output logic       drop_data, retrain_req, retry_error, send_idle, send_req,
  output logic [4:0] send_cnt
);
  vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(4)) u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .start_retry(start_retry), .phy_retrain(phy_retrain), .wait_done_ack(wait_done_ack),
    .state(state), .drop_data(drop_data), .retrain_req(retrain_req),
    .retry_error(retry_error), .send_idle(send_idle), .send_req(send_req),
    .send_cnt(send_cnt)
  );
endmodule
