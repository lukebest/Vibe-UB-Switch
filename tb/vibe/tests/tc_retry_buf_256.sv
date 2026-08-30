// retry_buf depth 256; Null/Retry do not enter; overflow proto_err.
`timescale 1ns/1ps
module tc_retry_buf_256;
  logic clk, rst_n, port_rst, link_up, wr_en, is_null, is_retry, ack_rel, proto_err, can_send;
  logic [159:0] wr_flit, rd_flit;
  logic [7:0] send_size, rel_size, rd_ptr_i, wr_ptr, tail_ptr, rcv_ptr;
  logic [8:0] num_free;
  integer fail, n;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_dll_retry_buf u_b (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .wr_en(wr_en), .is_null(is_null), .is_retry(is_retry), .wr_flit(wr_flit),
    .send_size(send_size), .ack_rel(ack_rel), .rel_size(rel_size), .rd_ptr_i(rd_ptr_i),
    .rd_flit(rd_flit), .wr_ptr(wr_ptr), .tail_ptr(tail_ptr), .rcv_ptr(rcv_ptr),
    .num_free(num_free), .proto_err(proto_err), .can_send(can_send)
  );
  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1; wr_en = 0; is_null = 0; is_retry = 0;
    ack_rel = 0; send_size = 8'd1; rel_size = 8'd0; rd_ptr_i = 0; wr_flit = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (num_free !== 9'd256) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : reset");
      $display("  expected : NumFreeBuf=256");
      $display("  actual   : %0d", num_free);
      fail = 1;
    end
    // Null does not consume
    @(negedge clk);
    wr_en = 1; is_null = 1; wr_flit = 160'h1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0; is_null = 0;
    @(posedge clk);
    if (num_free !== 9'd256 || wr_ptr !== 8'd0) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : wr_en is_null");
      $display("  expected : free stays 256");
      $display("  actual   : free=%0d wrp=%0d", num_free, wr_ptr);
      fail = 1;
    end
    @(negedge clk);
    wr_en = 1; is_retry = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0; is_retry = 0;
    @(posedge clk);
    if (num_free !== 9'd256) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : is_retry write");
      $display("  expected : not entered");
      $display("  actual   : free=%0d", num_free);
      fail = 1;
    end
    @(negedge clk);
    wr_en = 1; wr_flit = 160'h55;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    @(posedge clk);
    if (num_free !== 9'd255) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : one data flit");
      $display("  expected : free=255");
      $display("  actual   : %0d", num_free);
      fail = 1;
    end
    // overflow release
    @(negedge clk);
    ack_rel = 1; rel_size = 8'd8;
    @(posedge clk);
    @(negedge clk);
    ack_rel = 0;
    @(posedge clk);
    if (!proto_err) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : ack_rel 8 with free=255 → 263>256");
      $display("  expected : proto_err");
      $display("  actual   : 0");
      $display("  hier     : u_b.freeb");
      fail = 1;
    end
    // legal release after a write: free 255 + 1 = 256
    rst_n = 0;
    repeat (2) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 1; wr_flit = 160'h11; is_null = 0; is_retry = 0;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0; ack_rel = 1; rel_size = 8'd1;
    @(posedge clk);
    @(negedge clk);
    ack_rel = 0;
    @(posedge clk);
    if (num_free !== 9'd256 || proto_err) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : write 1 then ack_rel 1");
      $display("  expected : free=256 proto_err=0");
      $display("  actual   : free=%0d err=%0b", num_free, proto_err);
      fail = 1;
    end
    // port_rst / !link_up
    @(negedge clk);
    wr_en = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0; port_rst = 1;
    @(posedge clk);
    port_rst = 0;
    @(posedge clk);
    if (num_free !== 9'd256) begin
      $display("FAIL tc_retry_buf_256");
      $display("  stimulus : port_rst");
      $display("  expected : free=256");
      $display("  actual   : %0d", num_free);
      fail = 1;
    end
    link_up = 0;
    @(posedge clk);
    link_up = 1;
    if (!fail) $display("PASS tc_retry_buf_256");
    $finish;
  end
endmodule
