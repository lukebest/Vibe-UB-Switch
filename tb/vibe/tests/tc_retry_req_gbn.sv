// RETRY_REQ_SM: start_retry (FEC/BCRC) → REQ; drop_data in REQ|WAIT. Short wait param.
`timescale 1ns/1ps
module tc_retry_req_gbn;
  logic clk, rst_n, port_rst, device_rst, start_retry, phy_retrain, wait_done_ack;
  logic [2:0] state;
  logic drop_data, retrain_req, retry_error, send_idle, send_req;
  logic [4:0] send_cnt;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(4)) u_r (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .start_retry(start_retry), .phy_retrain(phy_retrain), .wait_done_ack(wait_done_ack),
    .state(state), .drop_data(drop_data), .retrain_req(retrain_req),
    .retry_error(retry_error), .send_idle(send_idle), .send_req(send_req),
    .send_cnt(send_cnt)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; device_rst = 0; start_retry = 0;
    phy_retrain = 0; wait_done_ack = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    start_retry = 1;
    @(posedge clk);
    start_retry = 0;
    @(posedge clk);
    if (state !== 3'd1 || !drop_data) begin
      $display("FAIL tc_retry_req_gbn");
      $display("  stimulus : start_retry (Go-Back-N)");
      $display("  expected : ST_REQ drop_data=1");
      $display("  actual   : st=%0d drop=%0b", state, drop_data);
      $display("  hier     : u_r.st");
      fail = 1;
    end
    if (!fail) $display("PASS tc_retry_req_gbn");
    $finish;
  end
endmodule
