// AS-0.1 header extract helpers (UB 2.0 LPH/NTH bit layout, parameterized).
// Included per-module (no ifndef) so functions are in each including scope.

function automatic logic [3:0] vibe_lph_cfg;
  input logic [159:0] flit;
  begin
    vibe_lph_cfg = flit[11:8];
  end
endfunction

function automatic logic [1:0] vibe_lph_rt;
  input logic [159:0] flit;
  begin
    vibe_lph_rt = flit[23:22];
  end
endfunction

function automatic logic [3:0] vibe_lph_vl;
  input logic [159:0] flit;
  begin
    // AS uses VL from header; LPH VL spans byte0[0] and byte1[7:5]
    vibe_lph_vl = {flit[15:13], flit[0]};
  end
endfunction

function automatic logic [15:0] vibe_nth_scna;
  input logic [159:0] flit;
  begin
    vibe_nth_scna = flit[47:32];
  end
endfunction

function automatic logic [15:0] vibe_nth_dcna;
  input logic [159:0] flit;
  begin
    vibe_nth_dcna = flit[63:48];
  end
endfunction

function automatic logic [15:0] vibe_nth_cci;
  input logic [159:0] flit;
  begin
    vibe_nth_cci = flit[79:64];
  end
endfunction

function automatic logic [7:0] vibe_nth_lbf;
  input logic [159:0] flit;
  begin
    vibe_nth_lbf = flit[87:80];
  end
endfunction

function automatic logic [2:0] vibe_nth_nlp;
  input logic [159:0] flit;
  begin
    vibe_nth_nlp = flit[95:93];
  end
endfunction

function automatic logic [13:0] vibe_lph_plength;
  input logic [159:0] flit;
  begin
    // Byte2[5:0] || Byte3[7:0] assembled as PLENGTH[13:0]
    vibe_lph_plength = {flit[21:16], flit[31:24]};
  end
endfunction

// AS-0.1 §9 / FS-0.2.3: CFG6 terminate (not all CFG6).
// us = CNA statically written AND DCNA==mgmt CNA.
// NLP=1 enumerate terminates even if DCNA is not us.
// opcode 0x10 terminates only if targeting this device (us).
function automatic logic vibe_cfg6_should_term;
  input logic        cna_written;
  input logic [15:0] cna;
  input logic [159:0] flit;
  logic [15:0] dcna;
  logic [2:0]  nlp;
  logic [7:0]  opc;
  logic        us;
  begin
    dcna = vibe_nth_dcna(flit);
    nlp  = vibe_nth_nlp(flit);
    opc  = flit[103:96];
    us   = cna_written && (dcna == cna);
    vibe_cfg6_should_term = us || (nlp == 3'd1) || ((opc == 8'h10) && us);
  end
endfunction

function automatic integer vibe_decl_flits;
  input logic [13:0] plen;
  integer nblk, lastn;
  begin
    nblk  = plen[13:10] + 1;
    lastn = plen[9:5] + 1;
    vibe_decl_flits = (nblk - 1) * 32 + lastn;
    if (vibe_decl_flits < 1) vibe_decl_flits = 1;
    if (vibe_decl_flits > 512) vibe_decl_flits = 512;
  end
endfunction

// FS-0.2.7 overlay B: first 20B of a 512b NW beat is flit0 (LPH/NTH).
// Not old640[511:0] — LPH lives at beat[511:352], not a slice of a 640 NW beat.
function automatic logic [159:0] vibe_nw512_flit0;
  input logic [511:0] beat;
  begin
    vibe_nw512_flit0 = beat[511:352];
  end
endfunction

function automatic logic [15:0] vibe_pkt_bytes;
  input logic [159:0] flit;
  integer n;
  begin
    n = vibe_decl_flits(vibe_lph_plength(flit));
    vibe_pkt_bytes = n * 16'd20;
  end
endfunction

function automatic logic [7:0] vibe_nw512_decl_beats;
  input logic [159:0] flit;
  logic [15:0] b;
  begin
    b = vibe_pkt_bytes(flit);
    vibe_nw512_decl_beats = (b + 16'd63) >> 6;
    if (vibe_nw512_decl_beats == 8'd0)
      vibe_nw512_decl_beats = 8'd1;
  end
endfunction

function automatic logic [4:0] vibe_bin2gray5;
  input logic [4:0] b;
  begin
    vibe_bin2gray5 = (b >> 1) ^ b;
  end
endfunction

function automatic logic [4:0] vibe_gray2bin5;
  input logic [4:0] g;
  begin
    vibe_gray2bin5[4] = g[4];
    vibe_gray2bin5[3] = g[4] ^ g[3];
    vibe_gray2bin5[2] = g[4] ^ g[3] ^ g[2];
    vibe_gray2bin5[1] = g[4] ^ g[3] ^ g[2] ^ g[1];
    vibe_gray2bin5[0] = g[4] ^ g[3] ^ g[2] ^ g[1] ^ g[0];
  end
endfunction

function automatic logic [7:0] vibe_rev8;
  input logic [7:0] x;
  integer i;
  begin
    for (i = 0; i < 8; i = i + 1) vibe_rev8[i] = x[7-i];
  end
endfunction

function automatic logic [31:0] vibe_rev32;
  input logic [31:0] x;
  integer i;
  begin
    for (i = 0; i < 32; i = i + 1) vibe_rev32[i] = x[31-i];
  end
endfunction

function automatic logic [7:0] vibe_gf256_mul;
  input logic [7:0] a;
  input logic [7:0] b;
  logic [7:0] p, aa;
  logic [7:0] bb;
  integer k;
  begin
    p  = 8'h00;
    aa = a;
    bb = b;
    for (k = 0; k < 8; k = k + 1) begin
      if (bb[0]) p = p ^ aa;
      if (aa[7]) aa = {aa[6:0], 1'b0} ^ 8'h1D;
      else       aa = {aa[6:0], 1'b0};
      bb = bb >> 1;
    end
    vibe_gf256_mul = p;
  end
endfunction
