// PCS RX: 4×160 from vibe_pcs_tx (T=4, same pin as vibe_port). Score
// dll_vld/dll_data vs the injected beat (inverse of TX pack). FAIL if
// dll never valid or LPH mismatches. Coverage-only wv/win/remv force is gone.
`timescale 1ns/1ps
module tc_pcs_rx;
  `include "vibe_tb_defs.svh"
  `include "vibe_tb_nw_pma.svh"

  logic clk, rst_n, link_up, sdf_period, afifo_afull;
  logic [2:0] fec_mode;
  logic [639:0] dll_in, dll_out;
  logic         dll_in_v, dll_in_r, dll_out_v, dll_out_r;
  logic [159:0] lane0, lane1, lane2, lane3;
  logic         lane_vld;
  logic         fec_fail, lid_bad, deskew_ok;
  logic [3:0]   am_locked;
  integer fail, i, accepted, saw_dll, saw_lock, lph_ok;
  logic [639:0] last_dll, pkt;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_pcs_tx u_tx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .fec_mode(fec_mode), .afifo_afull(afifo_afull),
    .dll_data(dll_in), .dll_vld(dll_in_v), .dll_ready(dll_in_r),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3), .lane_vld(lane_vld)
  );

  vibe_pcs_rx u_rx (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .fec_mode(fec_mode),
    .lane0(lane0), .lane1(lane1), .lane2(lane2), .lane3(lane3), .lane_vld(lane_vld),
    .dll_data(dll_out), .dll_vld(dll_out_v), .dll_ready(dll_out_r),
    .fec_fail(fec_fail), .am_locked(am_locked), .lid_bad(lid_bad),
    .deskew_ok(deskew_ok)
  );

  task automatic fail_at;
    input [8*80-1:0] stimulus;
    input [8*80-1:0] expected;
    input [8*80-1:0] actual;
    input [8*80-1:0] hier;
    begin
      fail = 1;
      $display("FAIL tc_pcs_rx");
      $display("  stimulus : %0s", stimulus);
      $display("  expected : %0s", expected);
      $display("  actual   : %0s", actual);
      $display("  hier     : %0s", hier);
      $display("  reproduce: make -C tb/vibe units");
    end
  endtask

  task automatic insert_am_n;
    input integer n;
    integer k;
    begin
      dll_in_v = 0;
      for (k = 0; k < n; k = k + 1) begin
        force u_tx.u_pack.sym_cnt = 10'd640;
        repeat (8) @(posedge clk);
        release u_tx.u_pack.sym_cnt;
        repeat (4) @(posedge clk);
      end
    end
  endtask

  initial begin
    fail = 0; accepted = 0; saw_dll = 0; saw_lock = 0; lph_ok = 0;
    last_dll = 0; pkt = vibe_tb_nw_pma_pkt();
    rst_n = 0; link_up = 0; sdf_period = 1; afifo_afull = 0;
    fec_mode = VIBE_FEC_T4;
    dll_in = 0; dll_in_v = 0; dll_out_r = 1;
    repeat (4) @(posedge clk);
    rst_n = 1;
    repeat (4) @(posedge clk);
    link_up = 1;
    repeat (4) @(posedge clk);

    insert_am_n(6);
    if (am_locked !== 4'b1111) begin
      fail_at("6 TX AMCTL pairs (force pack.sym_cnt, T=4, link_up=1)",
              "am_locked=1111",
              "lock bits not all 1",
              "u_rx.am_locked / u_tx.u_pack.am_phase");
    end else
      saw_lock = 1;

    dll_in = pkt;
    for (i = 0; i < 64; i = i + 1) begin
      @(negedge clk);
      if (dll_in_r) begin
        dll_in_v = 1;
        accepted = 1;
      end else
        dll_in_v = 0;
      @(posedge clk);
    end
    dll_in_v = 0;

    if (!accepted) begin
      fail_at("legal 640b LPH beat after link_up (T=4)",
              "u_tx.dll_ready handshake",
              "TX never accepted dll_vld",
              "u_tx.dll_ready / u_tx.u_g1");
      $finish;
    end

    for (i = 0; i < 4000; i = i + 1) begin
      @(posedge clk);
      if (am_locked == 4'b1111) saw_lock = 1;
      if (dll_out_v) begin
        saw_dll = 1;
        last_dll = dll_out;
        if (vibe_tb_nw_pma_lph_ok(dll_out) ||
            (vibe_lph_cfg(dll_out[639:480]) == 4'd3 &&
             vibe_nth_scna(dll_out[639:480]) == 16'hA11A &&
             vibe_nth_dcna(dll_out[639:480]) == 16'hB22B))
          lph_ok = 1;
      end
    end

    if (!saw_dll) begin
      $display("  detail   : lock=%04b deskew=%0b fec_fail=%0b lid_bad=%0b last=%h",
               am_locked, deskew_ok, fec_fail, lid_bad, last_dll);
      fail_at("TX lanes looped into RX after AM lock + 1 legal dll beat",
              "dll_vld=1 with nonzero dll_data (inverse TX pack)",
              "dll_vld stayed 0",
              "u_rx.dll_vld / u_rx.u_fec / u_rx.u_dsk");
      $finish;
    end
    if (last_dll === 640'd0) begin
      fail_at("RX dll_vld after TX pack",
              "dll_data nonzero (known LPH/payload)",
              "dll_data=0",
              "u_rx.dll_data");
      $finish;
    end
    if (!lph_ok) begin
      $display("  detail   : dll flit0=%h CFG=%0d RT=%02b SCNA=%04h DCNA=%04h",
               last_dll[639:480],
               vibe_lph_cfg(last_dll[639:480]), vibe_lph_rt(last_dll[639:480]),
               vibe_nth_scna(last_dll[639:480]), vibe_nth_dcna(last_dll[639:480]));
      fail_at("RX dll after TX T=4 pack of CFG=3 A11A/B22B",
              "LPH CFG=3 SCNA=A11A DCNA=B22B (inverse of TX pack)",
              "see detail line",
              "u_rx.dll_data");
      $finish;
    end
    if (!saw_lock) begin
      fail_at("AM insert then payload",
              "am_locked seen 1111",
              "never locked",
              "u_rx.am_locked");
      $finish;
    end
    $display("PASS tc_pcs_rx");
    $finish;
  end
endmodule
