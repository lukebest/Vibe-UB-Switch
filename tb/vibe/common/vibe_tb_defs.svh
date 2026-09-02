// Vibe-UB-Switch TB helpers (AS-0.1 + FS-0.2.3 G1).
// Header bit layout matches rtl/common/vibe_ub_fn.vh only — not old tb/.
// No include-guard: Icarus treats `define as compilation-unit global, so a
// guard would skip the second module that includes this file.

`include "vibe_ub_fn.vh"
`include "vibe_ub_params.vh"

// cfg_wr_cmd (AS-0.1 §10)
localparam [2:0] VIBE_TB_CMD_CNA     = 3'd0;
localparam [2:0] VIBE_TB_CMD_ROUTE   = 3'd1;
localparam [2:0] VIBE_TB_CMD_DEFAULT = 3'd2;
localparam [2:0] VIBE_TB_CMD_PORTRST = 3'd3;
localparam [2:0] VIBE_TB_CMD_DEVRST  = 3'd4;
localparam [2:0] VIBE_TB_CMD_LMSMGO  = 3'd5;
localparam [2:0] VIBE_TB_CMD_NOPCLR  = 3'd7; // ignored opcode; still irq_clr

// LPH PLENGTH for N declared flits (nblk=1, lastn=N) — 1 beat if N<=4.
function automatic [13:0] vibe_tb_plen_nflit;
  input integer n;
  integer lastn;
  begin
    lastn = (n < 1) ? 1 : n;
    if (lastn > 32) lastn = 32;
    vibe_tb_plen_nflit = {4'd0, lastn[4:0] - 5'd1, 5'd0};
  end
endfunction

// Legal max 4300 B = 215 flits: nblk=7 lastn=23 → {6,22,0}.
function automatic [13:0] vibe_tb_plen_4300;
  begin
    vibe_tb_plen_4300 = {4'd6, 5'd22, 5'd0};
  end
endfunction

// Oversize declared length: nblk=7, lastn=32 → 224 flits * 20 = 4480 B > 4300.
function automatic [13:0] vibe_tb_plen_oversize;
  begin
    vibe_tb_plen_oversize = {4'd6, 5'd31, 5'd0};
  end
endfunction

// Undersize attempt: nblk/lastn fields zero (clamped to 1 flit / 20 B in RTL).
function automatic [13:0] vibe_tb_plen_min_try;
  begin
    vibe_tb_plen_min_try = 14'd0;
  end
endfunction

function automatic [159:0] vibe_tb_mk_flit;
  input [3:0]  cfg;
  input [1:0]  rt;
  input [3:0]  vl;
  input [15:0] scna;
  input [15:0] dcna;
  input [13:0] plen;
  input [15:0] cci;
  input [7:0]  lbf;
  input [2:0]  nlp;
  input [7:0]  opc;
  reg   [159:0] f;
  begin
    f          = 160'd0;
    f[11:8]    = cfg;
    f[23:22]   = rt;
    f[0]       = vl[0];
    f[15:13]   = vl[3:1];
    f[21:16]   = plen[13:8];
    f[31:24]   = plen[7:0];
    f[47:32]   = scna;
    f[63:48]   = dcna;
    f[79:64]   = cci;
    f[87:80]   = lbf;
    f[95:93]   = nlp;
    f[103:96]  = opc; // cna_ep opcode slot (AS-0.1 §9)
    vibe_tb_mk_flit = f;
  end
endfunction

// Overlay B NW/fabric beat: SOP LPH is [511:352]; [351:0] is payload.
// Not {flit0, 480'd0} (old 640) and not README DCNA=[511:496].
function automatic [511:0] vibe_tb_mk_beat;
  input [159:0] flit0;
  begin
    vibe_tb_mk_beat = {flit0, 352'd0};
  end
endfunction

// DLL↔PCS is still 640 (4×160). Do not use this on fabric/NW pins.
function automatic [639:0] vibe_tb_mk_pcs_beat;
  input [159:0] flit0;
  begin
    vibe_tb_mk_pcs_beat = {flit0, 480'd0};
  end
endfunction

// Overlay B: ceil(packet_bytes / 64), matching vibe_nw512_decl_beats.
function automatic integer vibe_tb_decl_beats;
  input [13:0] plen;
  integer dflits, bytes;
  begin
    dflits = vibe_decl_flits(plen);
    bytes  = dflits * 20;
    vibe_tb_decl_beats = (bytes + 63) >> 6;
    if (vibe_tb_decl_beats < 1) vibe_tb_decl_beats = 1;
  end
endfunction
