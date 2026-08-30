// RETRY_ACK_SM: start_ack → ACK burst then replay.
`timescale 1ns/1ps
module tc_retry_ack_replay;
  logic clk, rst_n, port_rst, start_ack, send_idle, send_ack, replay;
  logic [7:0] wr_ptr, rcv_ptr, rd_ptr;
  logic [2:0] state;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_retry_ack_sm u_a (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst),
    .start_ack(start_ack), .wr_ptr(wr_ptr), .rcv_ptr(rcv_ptr),
    .state(state), .send_idle(send_idle), .send_ack(send_ack),
    .replay(replay), .rd_ptr(rd_ptr)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; start_ack = 0; wr_ptr = 8'd4; rcv_ptr = 8'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    start_ack = 1;
    @(posedge clk);
    start_ack = 0;
    repeat (2) @(posedge clk);
    if (state === 3'd0) begin
      $display("FAIL tc_retry_ack_replay");
      $display("  stimulus : start_ack wr_ptr=4 rcv=0");
      $display("  expected : leave NORMAL (ACK or replay)");
      $display("  actual   : still NORMAL");
      $display("  hier     : u_a.st");
      fail = 1;
    end
    if (!fail) $display("PASS tc_retry_ack_replay");
    $finish;
  end
endmodule
