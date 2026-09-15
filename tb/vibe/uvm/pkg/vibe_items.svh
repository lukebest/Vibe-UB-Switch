// Overlay-B packet and cfg_wr sequence items (AS-0.1 §3/§8/§10).
class vibe_cfg_item extends uvm_sequence_item;
  rand bit [3:0]  cmd;
  rand bit [15:0] idx;
  rand bit [31:0] data;
  `uvm_object_utils(vibe_cfg_item)
  function new(string name = "vibe_cfg_item");
    super.new(name);
  endfunction
  constraint c_cmd_as {
    cmd inside {4'd0, 4'd1, 4'd2, 4'd3, 4'd4, 4'd5, 4'd7};
  }
endclass

class vibe_pkt_item extends uvm_sequence_item;
  rand bit [1:0]  port;
  rand bit [3:0]  cfg;
  rand bit [1:0]  rt;
  rand bit [3:0]  vl;
  rand bit [15:0] scna;
  rand bit [15:0] dcna;
  rand bit [13:0] plen;
  rand bit [15:0] cci;
  rand bit [7:0]  lbf;
  rand bit [2:0]  nlp;
  rand bit [7:0]  opc;
  bit [511:0]     payload_lo;
  int             extra_beats; // 0 => use declared beat count

  `uvm_object_utils(vibe_pkt_item)

  function new(string name = "vibe_pkt_item");
    super.new(name);
    payload_lo  = 352'd0;
    extra_beats = 0;
  endfunction

  constraint c_port { port inside {[0:3]}; }
  constraint c_vl   { vl inside {[0:15]}; }
  constraint c_legal_len {
    // Default directed legal 5-flit / 1–2 Overlay-B beats. Tests override.
    plen == {4'd0, 5'd4, 5'd0};
  }

  function bit [159:0] mk_flit();
    bit [159:0] f;
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
    f[103:96]  = opc;
    return f;
  endfunction

  function bit [511:0] sop_beat();
    return {mk_flit(), payload_lo};
  endfunction

  function int decl_beats();
    int dflits, bytes, n;
    dflits = vibe_decl_flits(plen);
    bytes  = dflits * 20;
    n      = (bytes + 63) >> 6;
    if (n < 1) n = 1;
    return n;
  endfunction

  function void pack_beats(output bit [511:0] beats[]);
    int n, b;
    n = (extra_beats > 0) ? extra_beats : decl_beats();
    if (n < 1) n = 1;
    beats = new[n];
    for (b = 0; b < n; b++)
      beats[b] = (b == 0) ? sop_beat() : {160'd0, payload_lo};
  endfunction
endclass

class vibe_pma_beat extends uvm_sequence_item;
  rand bit [1:0]   port;
  rand bit [511:0] rxdata;
  `uvm_object_utils(vibe_pma_beat)
  function new(string name = "vibe_pma_beat");
    super.new(name);
  endfunction
endclass
