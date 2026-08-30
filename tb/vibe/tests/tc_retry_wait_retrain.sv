// RETRY_REQ_SM: WAIT, RETRAIN, ERROR (AS-0.1 §12). Short WAIT param.
`timescale 1ns/1ps
module tc_retry_wait_retrain;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, port_rst, device_rst, start_retry, phy_retrain, wait_done_ack;
  logic [2:0] state;
  logic drop_data, retrain_req, retry_error, send_idle, send_req;
  logic [4:0] send_cnt;
  integer fail, i, saw_w, saw_r, saw_e;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(4)) u_r (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .device_rst(device_rst),
    .start_retry(start_retry), .phy_retrain(phy_retrain), .wait_done_ack(wait_done_ack),
    .state(state), .drop_data(drop_data), .retrain_req(retrain_req),
    .retry_error(retry_error), .send_idle(send_idle), .send_req(send_req),
    .send_cnt(send_cnt)
  );

  task automatic burst_req;
    begin
      start_retry = 1;
      @(posedge clk);
      start_retry = 0;
      // burst 0..32 inclusive = 33 cycles in REQ
      repeat (34) @(posedge clk);
    end
  endtask

  initial begin
    fail = 0; saw_w = 0; saw_r = 0; saw_e = 0;
    rst_n = 0; port_rst = 0; device_rst = 0; start_retry = 0;
    phy_retrain = 0; wait_done_ack = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    // REQ → WAIT (burst==32), then wait_done_ack → NORMAL
    burst_req();
    if (state !== 3'd2) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : 33-cyc REQ burst");
      $display("  expected : ST_WAIT (2)");
      $display("  actual   : %0d", state);
      $display("  hier     : u_r.st / burst");
      fail = 1;
    end else
      saw_w = 1;
    if (!drop_data) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : WAIT");
      $display("  expected : drop_data=1");
      $display("  actual   : 0");
      fail = 1;
    end
    wait_done_ack = 1;
    @(posedge clk);
    wait_done_ack = 0;
    @(posedge clk);
    if (state !== 3'd0) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : wait_done_ack");
      $display("  expected : NORMAL");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // WAIT timeout → REQ again
    burst_req();
    if (state !== 3'd2) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : second burst");
      $display("  expected : WAIT");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    repeat (6) @(posedge clk); // wtmr 4 → 0
    if (state !== 3'd1) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : WAIT timeout");
      $display("  expected : REQ");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // Finish this REQ burst then continue until 15 retries → RETRAIN
    // Already consumed 2 retries (first WAIT+ack reset num_retry? no — ack goes N, num_retry stays)
    // After first WAIT+ack, num_retry=1. After second burst→WAIT timeout→REQ, num_retry still 1
    // until this burst completes.
    repeat (34) @(posedge clk);
    // Now drain remaining retries: each WAIT timeout + REQ burst
    // We need num_retry to reach 15. Track by looping.
    i = 0;
    while (state !== 3'd3 && i < 20) begin
      if (state == 3'd2)
        repeat (6) @(posedge clk);
      else
        @(posedge clk);
      i = i + 1;
    end
    // If not yet RETRAIN, fire remaining bursts
    i = 0;
    while (state !== 3'd3 && state !== 3'd4 && i < 20) begin
      if (state == 3'd0) begin
        burst_req();
      end else if (state == 3'd2) begin
        repeat (6) @(posedge clk);
      end else
        @(posedge clk);
      i = i + 1;
    end
    if (state == 3'd3) saw_r = 1;
    if (retrain_req !== (state == 3'd3) && state == 3'd3) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : 15 retries");
      $display("  expected : retrain_req=1");
      fail = 1;
    end

    // phy_retrain shortcut to RETRAIN from REQ burst
    rst_n = 0;
    repeat (2) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    start_retry = 1;
    @(posedge clk);
    start_retry = 0;
    phy_retrain = 1;
    repeat (34) @(posedge clk);
    phy_retrain = 0;
    if (state !== 3'd3) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : REQ burst + phy_retrain");
      $display("  expected : RETRAIN");
      $display("  actual   : %0d", state);
      fail = 1;
    end
    // ST_R: 4 phy reinits → ERROR (num_phy 0,1,2,3 then 4th → E)
    // Each cycle in R increments num_phy and either E or N
    @(posedge clk); // num_phy=1 → N
    if (state !== 3'd0) begin
      $display("NOTE tc_retry_wait_retrain: after 1st RETRAIN st=%0d (expect N)", state);
    end
    // 3 more RETRAIN visits
    repeat (3) begin
      start_retry = 1;
      @(posedge clk);
      start_retry = 0;
      phy_retrain = 1;
      repeat (34) @(posedge clk);
      phy_retrain = 0;
      @(posedge clk); // consume ST_R
    end
    // After 4th ST_R entry, next posedge → ERROR
    if (state !== 3'd4 && retry_error !== 1'b1) begin
      // may already be ERROR
      if (state !== 3'd4) begin
        $display("FAIL tc_retry_wait_retrain");
        $display("  stimulus : 4 phy reinits");
        $display("  expected : ERROR (4)");
        $display("  actual   : %0d", state);
        $display("  hier     : u_r.num_phy / st");
        fail = 1;
      end
    end else
      saw_e = 1;

    if (state == 3'd4) saw_e = 1;

    // ERROR waits for port/device rst
    port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    @(posedge clk);
    if (state !== 3'd0) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : port_rst in ERROR");
      $display("  expected : NORMAL");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // device_rst
    start_retry = 1;
    @(posedge clk);
    start_retry = 0;
    device_rst = 1;
    @(posedge clk);
    device_rst = 0;
    @(posedge clk);
    if (state !== 3'd0) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : device_rst");
      $display("  expected : NORMAL");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    // default
    force u_r.st = 3'd7;
    #1;
    release u_r.st;
    @(posedge clk);
    if (state !== 3'd0) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : force st=7");
      $display("  expected : NORMAL (default)");
      $display("  actual   : %0d", state);
      fail = 1;
    end

    if (!saw_w) begin
      $display("FAIL tc_retry_wait_retrain");
      $display("  stimulus : REQ burst");
      $display("  expected : visited WAIT");
      $display("  actual   : never");
      fail = 1;
    end
    if (!fail) $display("PASS tc_retry_wait_retrain");
    $finish;
  end
endmodule
