// irq_logic sticky OR (AS-0.1 §10/§15). Clear on irq_clr / reset. Includes G1.
`timescale 1ns/1ps
module tc_irq_agg;
  logic clk, rst_n, irq_clr, icrc_fail, drop_g1, irq_logic;
  logic [3:0] rx_ovf, fc_ovf, proto_err, retry_error, len_err, deadlock_drop, afifo_ovf;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_irq_agg u_i (
    .clk(clk), .rst_n(rst_n), .irq_clr(irq_clr),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .icrc_fail(icrc_fail),
    .len_err(len_err), .deadlock_drop(deadlock_drop),
    .drop_g1(drop_g1), .afifo_ovf(afifo_ovf),
    .irq_logic(irq_logic)
  );
  task automatic pulse1;
    input integer which;
    begin
      rx_ovf = 0; fc_ovf = 0; proto_err = 0; retry_error = 0;
      icrc_fail = 0; len_err = 0; deadlock_drop = 0; drop_g1 = 0; afifo_ovf = 0;
      case (which)
        0: rx_ovf = 4'b0001;
        1: fc_ovf = 4'b0010;
        2: proto_err = 4'b0100;
        3: retry_error = 4'b1000;
        4: icrc_fail = 1;
        5: len_err = 4'b0001;
        6: deadlock_drop = 4'b0010;
        7: drop_g1 = 1;
        default: afifo_ovf = 4'b0100;
      endcase
      @(posedge clk);
      rx_ovf = 0; fc_ovf = 0; proto_err = 0; retry_error = 0;
      icrc_fail = 0; len_err = 0; deadlock_drop = 0; drop_g1 = 0; afifo_ovf = 0;
      @(posedge clk);
    end
  endtask
  initial begin
    fail = 0;
    rst_n = 0; irq_clr = 0;
    rx_ovf = 0; fc_ovf = 0; proto_err = 0; retry_error = 0;
    icrc_fail = 0; len_err = 0; deadlock_drop = 0; drop_g1 = 0; afifo_ovf = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (irq_logic) begin
      $display("FAIL tc_irq_agg");
      $display("  stimulus : reset");
      $display("  expected : irq_logic=0");
      fail = 1;
    end
    begin : srcs
      integer s;
      for (s = 0; s < 9; s = s + 1) begin
        irq_clr = 1;
        @(posedge clk);
        irq_clr = 0;
        @(posedge clk);
        if (irq_logic) begin
          $display("FAIL tc_irq_agg");
          $display("  stimulus : irq_clr");
          $display("  expected : 0");
          fail = 1;
        end
        pulse1(s);
        if (!irq_logic) begin
          $display("FAIL tc_irq_agg");
          $display("  stimulus : error source %0d", s);
          $display("  expected : sticky 1");
          $display("  actual   : 0");
          fail = 1;
        end
        @(posedge clk);
        if (!irq_logic) begin
          $display("FAIL tc_irq_agg");
          $display("  stimulus : source %0d deasserted", s);
          $display("  expected : still sticky");
          fail = 1;
        end
      end
    end
    rst_n = 0;
    @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    if (irq_logic) begin
      $display("FAIL tc_irq_agg");
      $display("  stimulus : reset after sticky");
      $display("  expected : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_irq_agg");
    $finish;
  end
endmodule
