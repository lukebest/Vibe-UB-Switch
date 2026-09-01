// TP-CRD-001 / TP-CRD-002: ceil(flits/n) default n=8; cells sat 65535 → fc_ovf.
`timescale 1ns/1ps
module tc_credit_grain_n;
  `include "vibe_ub_params.vh"
  logic        clk, rst_n, port_rst, link_up;
  logic        consume_vld, is_cfg0, credit_ret;
  logic [7:0]  grain_n;
  logic [9:0]  consume_flits;
  logic [15:0] credit_ret_n, pending;
  logic        credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf;
  integer      fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(grain_n),
    .consume_vld(consume_vld), .consume_flits(consume_flits), .is_cfg0(is_cfg0),
    .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );

  initial begin
    fail = 0;
    rst_n = 0; port_rst = 0; link_up = 1;
    grain_n = 8'd8; consume_vld = 0; consume_flits = 10'd0; is_cfg0 = 0;
    credit_ret = 0; credit_ret_n = 16'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);

    // 8 flits / n=8 → +1 cell
    @(negedge clk);
    consume_flits = 10'd8; consume_vld = 1;
    @(posedge clk);
    @(negedge clk);
    consume_vld = 0;
    @(posedge clk);
    if (u_crd.cells !== 16'd1) begin
      $display("FAIL tc_credit_grain_n");
      $display("  stimulus : consume 8 flits grain_n=8");
      $display("  expected : cells=1 (ceil(8/8))");
      $display("  actual   : cells=%0d", u_crd.cells);
      $display("  hier     : u_crd.cells / ceil_div");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end

    // n=1, 8 flits → +8
    grain_n = 8'd1;
    @(negedge clk);
    consume_flits = 10'd8; consume_vld = 1;
    @(posedge clk);
    @(negedge clk);
    consume_vld = 0;
    @(posedge clk);
    if (u_crd.cells !== 16'd9) begin
      $display("FAIL tc_credit_grain_n");
      $display("  stimulus : consume 8 flits grain_n=1 after cells=1");
      $display("  expected : cells=9");
      $display("  actual   : cells=%0d", u_crd.cells);
      $display("  hier     : u_crd.cells");
      fail = 1;
    end

    // Reach 65534 without force: n=1, +1023 cells ×64 = +65472 → 9+65472=65481, then +53.
    grain_n = 8'd1;
    begin : climb
      integer k;
      for (k = 0; k < 64; k = k + 1) begin
        @(negedge clk);
        consume_flits = 10'd1023; consume_vld = 1;
        @(posedge clk);
        @(negedge clk);
        consume_vld = 0;
      end
      @(negedge clk);
      consume_flits = 10'd53; consume_vld = 1;
      @(posedge clk);
      @(negedge clk);
      consume_vld = 0;
      @(posedge clk);
    end
    if (u_crd.cells !== 16'd65534) begin
      $display("FAIL tc_credit_grain_n");
      $display("  stimulus : climb cells to 65534 via n=1 consumes");
      $display("  expected : cells=65534");
      $display("  actual   : cells=%0d", u_crd.cells);
      $display("  hier     : u_crd.cells");
      fail = 1;
    end
    @(negedge clk);
    consume_flits = 10'd4; consume_vld = 1;
    @(posedge clk);
    @(negedge clk);
    consume_vld = 0;
    @(posedge clk);
    if (!fc_ovf || u_crd.cells !== 16'd65535) begin
      $display("FAIL tc_credit_grain_n");
      $display("  stimulus : cells=65534 + 4 flits n=1");
      $display("  expected : fc_ovf=1 cells=65535");
      $display("  actual   : fc_ovf=%0b cells=%0d", fc_ovf, u_crd.cells);
      $display("  hier     : u_crd.fc_ovf / cells_sum");
      fail = 1;
    end
    if (!fail) $display("PASS tc_credit_grain_n");
    $finish;
  end
endmodule
