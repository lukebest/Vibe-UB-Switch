// FS-0.2.7 Overlay B: unique 512-bit NW GOLDEN vectors.
// Not all-zero. Not old640[511:0]. Do not extract LPH/NTH from these beats.
// Included per-module (no guard).

function automatic [511:0] vibe_tb_nw512_golden_tx;
  begin
    vibe_tb_nw512_golden_tx = {
      32'h4E573531, 32'h54582121,
      32'hA5A5A5A5, 32'h5A5A5A5A,
      32'h01234567, 32'h89ABCDEF,
      32'hFEDCBA98, 32'h76543210,
      32'h11111111, 32'h22222222,
      32'h33333333, 32'h44444444,
      32'h55555555, 32'h66666666,
      32'h77777777, 32'h88888888
    };
  end
endfunction

function automatic [511:0] vibe_tb_nw512_golden_rx;
  begin
    vibe_tb_nw512_golden_rx = {
      32'h4E573531, 32'h52582121,
      32'h3C3C3C3C, 32'hC3C3C3C3,
      32'h0F0F0F0F, 32'hF0F0F0F0,
      32'h01010101, 32'h02020202,
      32'h03030303, 32'h04040404,
      32'h05050505, 32'h06060606,
      32'h07070707, 32'h08080808,
      32'h09090909, 32'h0A0A0A0A
    };
  end
endfunction

// PASS only if DUT pin width is 512 and the 512-bit value equals GOLDEN.
// A 640-bit DUT is always FAIL here, even if a 512-bit TB view matches GOLDEN.
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
