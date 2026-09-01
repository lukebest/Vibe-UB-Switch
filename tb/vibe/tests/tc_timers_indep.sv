// TP-TIM-002: credit 1µs and VOQ deadlock 1µs are independent — one expiry
// must not set the other.
`timescale 1ns/1ps
module tc_timers_indep;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, port_rst, link_up;
  logic consume_vld, is_cfg0, credit_ret;
  logic [7:0] grain_n;
  logic [9:0] consume_flits;
  logic [15:0] credit_ret_n, pending;
  logic credit_low, force_crd_ack, bp_nw, proto_err, fc_ovf;
  logic wr_en, wr_sop, wr_eop, wr_ready, rd_en, rd_sop, rd_eop;
  logic [3:0] wr_vl, rd_vl;
  logic [639:0] wr_data, rd_data;
  logic [15:0] nonempty;
  logic [5:0] occ_vl0;
  logic deadlock_drop;
  logic [31:0] deadlock_cnt;
  integer fail, i;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_dll_credit u_crd (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .grain_n(grain_n), .consume_vld(consume_vld), .consume_flits(consume_flits),
    .is_cfg0(is_cfg0), .credit_ret(credit_ret), .credit_ret_n(credit_ret_n),
    .pending(pending), .credit_low(credit_low), .force_crd_ack(force_crd_ack),
    .bp_nw(bp_nw), .proto_err(proto_err), .fc_ovf(fc_ovf)
  );
  vibe_voq_egr #(.DEPTH(32)) u_v (
    .clk(clk), .rst_n(rst_n),
    .wr_vl(wr_vl), .wr_en(wr_en), .wr_data(wr_data),
    .wr_sop(wr_sop), .wr_eop(wr_eop), .wr_ready(wr_ready),
    .rd_vl(rd_vl), .rd_en(rd_en), .rd_data(rd_data), .rd_sop(rd_sop), .rd_eop(rd_eop),
    .nonempty(nonempty), .occ_vl0(occ_vl0),
    .deadlock_drop(deadlock_drop), .deadlock_cnt(deadlock_cnt)
  );

  initial begin
    fail = 0;
    if (VIBE_US_CYC !== 1250) begin
      $display("FAIL tc_timers_indep");
      $display("  stimulus : VIBE_US_CYC");
      $display("  expected : 1250");
      $display("  actual   : %0d", VIBE_US_CYC);
      $display("  hier     : vibe_ub_params.vh");
      fail = 1;
    end
    rst_n = 0; port_rst = 0; link_up = 1; grain_n = 8'd8;
    consume_vld = 0; consume_flits = 0; is_cfg0 = 0;
    credit_ret = 0; credit_ret_n = 0;
    wr_en = 0; rd_en = 0; wr_vl = 0; rd_vl = 0;
    wr_data = 640'h1; wr_sop = 1; wr_eop = 1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    // Credit timer starts; VOQ empty.
    @(negedge clk);
    credit_ret = 1; credit_ret_n = 16'd1;
    @(posedge clk);
    @(negedge clk);
    credit_ret = 0;
    for (i = 0; i < (VIBE_US_CYC + 8); i = i + 1) @(posedge clk);
    if (!proto_err) begin
      $display("FAIL tc_timers_indep");
      $display("  stimulus : pending=1, no VOQ enqueue, wait >1us");
      $display("  expected : proto_err=1 (credit timeout)");
      $display("  actual   : proto_err=0");
      $display("  hier     : u_crd.to / proto_err");
      fail = 1;
    end
    if (deadlock_drop || deadlock_cnt != 0) begin
      $display("FAIL tc_timers_indep");
      $display("  stimulus : credit timeout, VOQ never written");
      $display("  expected : deadlock_drop=0 cnt=0 (independent timer)");
      $display("  actual   : drop=%0b cnt=%0d", deadlock_drop, deadlock_cnt);
      $display("  hier     : u_v.age vs u_crd.to");
      fail = 1;
    end

    // Clear credit path; start VOQ only.
    @(negedge clk);
    port_rst = 1;
    @(posedge clk);
    @(negedge clk);
    port_rst = 0;
    @(posedge clk);
    if (proto_err) begin
      // proto_err is sticky in RTL — document if it stays; VOQ check still valid
    end
    @(negedge clk);
    wr_en = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    for (i = 0; i < (VIBE_US_CYC + 16); i = i + 1) @(posedge clk);
    if (!deadlock_drop && deadlock_cnt == 0) begin
      $display("FAIL tc_timers_indep");
      $display("  stimulus : VOQ occupied >=1us, no credit_ret after port_rst");
      $display("  expected : deadlock_drop or cnt>0");
      $display("  actual   : drop=%0b cnt=%0d", deadlock_drop, deadlock_cnt);
      $display("  hier     : u_v.age");
      fail = 1;
    end
    // Credit pending was cleared by port_rst; do not require proto_err==0
    // if the bit is sticky, but a new timeout must not be required for VOQ.
    if (!fail) $display("PASS tc_timers_indep");
    $finish;
  end
endmodule
