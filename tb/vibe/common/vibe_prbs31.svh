// TB golden for PMA pin-idle PRBS31 (SPEC §4.4 / CR-PMA-IDLE-PRBS31).
// Matches rtl/pma/vibe_pma_bnd.sv and pycircuit/pma/prbs31.py:
//   poly x^31+x^28+1, step {s[29:0], s[30]^s[27]},
//   per-lane seed {27'd1, lid[1:0], 2'b01}.
// No PMA_IDLE_MARK XOR. Do not use PCS scramble(0) PRBS23 as idle.
// No include-guard: Icarus `define is compilation-unit global (see vibe_tb_defs).

function automatic [30:0] vibe_tb_prbs31_step;
  input [30:0] s;
  begin
    vibe_tb_prbs31_step = {s[29:0], s[30] ^ s[27]};
  end
endfunction

function automatic [30:0] vibe_tb_prbs31_seed;
  input [1:0] lid;
  begin
    vibe_tb_prbs31_seed = {27'd1, lid, 2'b01};
  end
endfunction

function automatic [127:0] vibe_tb_prbs31_word;
  input [30:0] s;
  logic [30:0] t;
  integer      i;
  begin
    t = s;
    for (i = 0; i < 128; i = i + 1) begin
      vibe_tb_prbs31_word[i] = t[0];
      t = vibe_tb_prbs31_step(t);
    end
  end
endfunction

function automatic [30:0] vibe_tb_prbs31_adv128;
  input [30:0] s;
  logic [30:0] t;
  integer      i;
  begin
    t = s;
    for (i = 0; i < 128; i = i + 1)
      t = vibe_tb_prbs31_step(t);
    vibe_tb_prbs31_adv128 = t;
  end
endfunction

function automatic vibe_tb_prbs31_word_ok;
  input [127:0] w;
  integer       i;
  begin
    vibe_tb_prbs31_word_ok = 1'b1;
    for (i = 31; i < 128; i = i + 1)
      if (w[i] != (w[i-31] ^ w[i-28]))
        vibe_tb_prbs31_word_ok = 1'b0;
  end
endfunction

function automatic [511:0] vibe_tb_prbs31_pack4;
  input [30:0] s0;
  input [30:0] s1;
  input [30:0] s2;
  input [30:0] s3;
  begin
    vibe_tb_prbs31_pack4 = {vibe_tb_prbs31_word(s3),
                            vibe_tb_prbs31_word(s2),
                            vibe_tb_prbs31_word(s1),
                            vibe_tb_prbs31_word(s0)};
  end
endfunction

function automatic vibe_tb_prbs31_pack_ok;
  input [511:0] w;
  begin
    vibe_tb_prbs31_pack_ok =
      vibe_tb_prbs31_word_ok(w[127:0]) &&
      vibe_tb_prbs31_word_ok(w[255:128]) &&
      vibe_tb_prbs31_word_ok(w[383:256]) &&
      vibe_tb_prbs31_word_ok(w[511:384]);
  end
endfunction
