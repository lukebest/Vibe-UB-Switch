// VOQ deadlock timeout 1 us from enqueue — separate from credit timeout.
`timescale 1ns/1ps
module tc_deadlock_timeout_1us;
  `include "vibe_ub_params.vh"
  logic clk, rst_n, wr_en, wr_sop, wr_eop, wr_ready, rd_en, rd_sop, rd_eop;
  logic [3:0] wr_vl, rd_vl;
  logic [511:0] wr_data, rd_data;
  logic [15:0] nonempty;
  logic [5:0] occ_vl0;
  logic deadlock_drop;
  logic [31:0] deadlock_cnt;
  integer fail, i;
  initial clk = 0;
  always #1 clk = ~clk;

  vibe_voq_egr #(.DEPTH(32)) u_v (
    .clk(clk), .rst_n(rst_n),
    .wr_vl(wr_vl), .wr_en(wr_en), .wr_data(wr_data),
    .wr_sop(wr_sop), .wr_eop(wr_eop), .wr_ready(wr_ready),
    .rd_vl(rd_vl), .rd_en(rd_en), .rd_data(rd_data), .rd_sop(rd_sop), .rd_eop(rd_eop),
    .nonempty(nonempty), .occ_vl0(occ_vl0),
    .deadlock_drop(deadlock_drop), .deadlock_cnt(deadlock_cnt)
  );
  wire [10:0] wav_age00 = u_v.age[0][0];  // VOQ age, not credit `to`

  initial begin
    if ($test$plusargs("DUMP") || $test$plusargs("VCD")) begin
      begin : dump_open
        reg [8*256-1:0] dump_fn;
        dump_fn = "voq_deadlock_1us.vcd";
        if ($value$plusargs("DUMPFILE=%s", dump_fn)) ;
        $dumpfile(dump_fn);
        $dumpvars(0, clk, rst_n, wr_en, rd_en, wr_vl, nonempty, occ_vl0,
                  deadlock_drop, deadlock_cnt, wav_age00);
      end
    end
  end

  initial begin
    fail = 0;
    rst_n = 0; wr_en = 0; rd_en = 0; wr_vl = 0; rd_vl = 0;
    wr_data = 512'h1; wr_sop = 1; wr_eop = 1;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 1;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0;
    for (i = 0; i < (VIBE_US_CYC - 4); i = i + 1) @(posedge clk);
    if (deadlock_drop) begin
      $display("FAIL tc_deadlock_timeout_1us");
      $display("  stimulus : enqueue, wait <1us, no read");
      $display("  expected : deadlock_drop still 0");
      $display("  actual   : 1");
      fail = 1;
    end
    for (i = 0; i < 16; i = i + 1) @(posedge clk);
    if (!deadlock_drop && deadlock_cnt == 0) begin
      $display("FAIL tc_deadlock_timeout_1us");
      $display("  stimulus : VOQ occupied >=1250 cycles without drain");
      $display("  expected : deadlock_drop pulse / cnt>0");
      $display("  actual   : drop=%0b cnt=%0d nonempty=%h", deadlock_drop, deadlock_cnt, nonempty);
      $display("  hier     : u_v.age / rptr");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    // normal drain path
    @(negedge clk);
    wr_en = 1; wr_vl = 4'd1; wr_data = 512'h2;
    @(posedge clk);
    @(negedge clk);
    wr_en = 0; rd_vl = 4'd1; rd_en = 1;
    @(posedge clk);
    rd_en = 0;
    if (!fail) $display("PASS tc_deadlock_timeout_1us");
    $finish;
  end
endmodule
