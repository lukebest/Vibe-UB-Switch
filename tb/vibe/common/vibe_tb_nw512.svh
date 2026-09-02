// FS-0.2.7 Overlay B GOLDEN: unique 512-bit NW beat.
// 设计: SOP LPH is [511:352] (160b); [351:0] is packet data on that beat.
// Not all-zero. Not old640[511:0]. Not README DCNA=[511:496].
// 160b LPH field offsets match vibe_ub_fn.vh (applied to the SOP window only).
// Included per-module (no guard).

// 4-flit / 80 B packet (nblk=1 lastn=4) so one SOP beat is 64 B of a complete DP.
function automatic [13:0] vibe_tb_nw512_plen4;
  begin
    vibe_tb_nw512_plen4 = {4'd0, 5'd3, 5'd0};
  end
endfunction

function automatic [159:0] vibe_tb_nw512_sop;
  input [3:0]  cfg;
  input [1:0]  rt;
  input [15:0] scna;
  input [15:0] dcna;
  input [13:0] plen;
  reg   [159:0] f;
  begin
    f          = 160'd0;
    f[11:8]    = cfg;
    f[23:22]   = rt;
    f[21:16]   = plen[13:8];
    f[31:24]   = plen[7:0];
    f[47:32]   = scna;
    f[63:48]   = dcna;
    vibe_tb_nw512_sop = f;
  end
endfunction

function automatic [511:0] vibe_tb_nw512_golden_tx;
  begin
    vibe_tb_nw512_golden_tx = {
      vibe_tb_nw512_sop(4'd3, 2'b00, 16'hA11A, 16'hB22B, vibe_tb_nw512_plen4()),
      352'hA5A55A5A_01234567_89ABCDEF_FEDCBA98_76543210_11112222_33334444_55556666_77778888_99AABBCC_DDEEFF00
    };
  end
endfunction

function automatic [511:0] vibe_tb_nw512_golden_rx;
  begin
    vibe_tb_nw512_golden_rx = {
      vibe_tb_nw512_sop(4'd3, 2'b00, 16'hC33C, 16'hD44D, vibe_tb_nw512_plen4()),
      352'h3C3CC3C3_0F0FF0F0_01010101_02020202_03030303_04040404_05050505_06060606_07070707_08080808_09090A0A
    };
  end
endfunction

// Second NW beat: remaining 16 B of the 80 B / 4-flit packet (left-justified).
function automatic [511:0] vibe_tb_nw512_golden_tx_b2;
  begin
    vibe_tb_nw512_golden_tx_b2 = {128'hB2B2C3C3_D4D4E5E5, 384'd0};
  end
endfunction

// Packet n SOP GOLDEN: same 设计 LPH [511:352] (CFG=3 RT=00 plen=4-flit);
// [351:0] unique per n. n=0 is vibe_tb_nw512_golden_tx(). Never all-zero.
function automatic [511:0] vibe_tb_nw512_golden_tx_n;
  input integer n;
  reg [31:0]  k;
  reg [351:0] pld;
  begin
    k = n;
    if (n == 0)
      vibe_tb_nw512_golden_tx_n = vibe_tb_nw512_golden_tx();
    else begin
      pld = {
        32'hA5A55A5A ^ k,
        32'h01234567 + k,
        32'h89ABCDEF ^ {k[7:0], k[7:0], k[7:0], k[7:0]},
        32'hFEDCBA98 + (k << 8),
        32'h76543210 ^ (k * 32'h00010001),
        32'h11112222 + k,
        32'h33334444 ^ k,
        32'h55556666 + (k << 16),
        32'h77778888 ^ {16'h0000, k[15:0]},
        32'h99AABBCC + k,
        32'h00000100 + k
      };
      vibe_tb_nw512_golden_tx_n = {
        vibe_tb_nw512_sop(4'd3, 2'b00, 16'hA11A, 16'hB22B, vibe_tb_nw512_plen4()),
        pld
      };
    end
  end
endfunction

function automatic [511:0] vibe_tb_nw512_golden_tx_b2_n;
  input integer n;
  reg [31:0] k;
  begin
    k = n;
    if (n == 0)
      vibe_tb_nw512_golden_tx_b2_n = vibe_tb_nw512_golden_tx_b2();
    else
      vibe_tb_nw512_golden_tx_b2_n = {96'hB2B2C3C3_D4D4E5E5, k, 384'd0};
  end
endfunction

function automatic integer vibe_tb_nw512_vec_fail;
  input integer dut_w;
  input [511:0] exp;
  input [511:0] act;
  begin
    if (dut_w !== 512)
      vibe_tb_nw512_vec_fail = 1;
    else if (act !== exp)
      vibe_tb_nw512_vec_fail = 1;
    else
      vibe_tb_nw512_vec_fail = 0;
  end
endfunction

// SOP LPH: compare the 160b window and named fields (160b layout, not [511:496]).
function automatic integer vibe_tb_nw512_sop_lph_fail;
  input [511:0] exp;
  input [511:0] act;
  reg [159:0] e, a;
  begin
    e = exp[511:352];
    a = act[511:352];
    vibe_tb_nw512_sop_lph_fail =
        (e !== a) ||
        (e[11:8] !== a[11:8]) ||
        (e[23:22] !== a[23:22]) ||
        (e[47:32] !== a[47:32]) ||
        (e[63:48] !== a[63:48]);
  end
endfunction

task automatic vibe_tb_nw512_fail_print;
  input [8*40-1:0] tc;
  input [8*96-1:0] stim;
  input [511:0]    exp;
  input integer    act_w;
  input [511:0]    act;
  input [8*72-1:0] hier;
  begin
    $display("FAIL %0s", tc);
    $display("  stimulus : %0s", stim);
    $display("  expected : width=512 data=%h", exp);
    $display("  actual   : width=%0d data=%h", act_w, act);
    $display("  hier     : %0s", hier);
    $display("  reproduce: make -C tb/vibe units");
  end
endtask

task automatic vibe_tb_nw512_fail_print_pkt;
  input [8*40-1:0] tc;
  input integer    pkt_i;
  input integer    npkt;
  input [8*96-1:0] stim;
  input [511:0]    exp;
  input integer    act_w;
  input [511:0]    act;
  input [8*72-1:0] hier;
  begin
    $display("FAIL %0s", tc);
    $display("  packet   : %0d / %0d", pkt_i, npkt);
    $display("  stimulus : %0s", stim);
    $display("  expected : width=512 data=%h", exp);
    $display("  actual   : width=%0d data=%h", act_w, act);
    $display("  hier     : %0s", hier);
    $display("  reproduce: make -C tb/vibe units");
  end
endtask

task automatic vibe_tb_nw512_sop_lph_print;
  input [8*40-1:0] tc;
  input [8*96-1:0] stim;
  input [511:0]    exp;
  input [511:0]    act;
  input [8*72-1:0] hier;
  reg [159:0] e, a;
  begin
    e = exp[511:352];
    a = act[511:352];
    $display("FAIL %0s", tc);
    $display("  stimulus : %0s", stim);
    $display("  expected : SOP[511:352] CFG=%0d RT=%02b SCNA=%04h DCNA=%04h flit=%h",
             e[11:8], e[23:22], e[47:32], e[63:48], e);
    $display("  actual   : SOP[511:352] CFG=%0d RT=%02b SCNA=%04h DCNA=%04h flit=%h",
             a[11:8], a[23:22], a[47:32], a[63:48], a);
    $display("  hier     : %0s", hier);
    $display("  reproduce: make -C tb/vibe units");
  end
endtask
