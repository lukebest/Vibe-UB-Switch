// AS-0.1 scoreboard: G1 drop, length, CFG6 term vs fwd, transit ICRC, irq sticky.
class vibe_as_scoreboard extends uvm_component;
  `uvm_component_utils(vibe_as_scoreboard)
  uvm_analysis_imp #(vibe_pkt_item, vibe_as_scoreboard) ing_imp;
  virtual vibe_fab_probe_if probe;
  virtual vibe_cfg_if       cfg_vif;
  virtual vibe_nw4_if       egr_vif;

  bit [15:0]  exp_cna;
  bit         exp_cna_written;
  bit [3:0]   route_bm [0:255];
  bit [3:0]   default_bm;
  int unsigned exp_g1_cnt;
  int         n_g1_seen;
  int         n_len_err;
  int         n_fwd;
  int         mismatch;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ing_imp = new("ing_imp", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    void'(uvm_config_db#(virtual vibe_fab_probe_if)::get(this, "", "probe", probe));
    void'(uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "cfg_vif", cfg_vif));
    void'(uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "egr_vif", egr_vif));
  endfunction

  function bit cfg6_term(vibe_pkt_item t);
    bit us;
    us = exp_cna_written && (t.dcna == exp_cna);
    return us || (t.nlp == 3'd1) || ((t.opc == 8'h10) && us);
  endfunction

  function bit len_illegal(vibe_pkt_item t);
    int bytes;
    bytes = vibe_decl_flits(t.plen) * 20;
    return (bytes < VIBE_PKT_LEN_MIN) || (bytes > VIBE_PKT_LEN_MAX);
  endfunction

  function void write(vibe_pkt_item t);
    bit [159:0] f;
    // Continuation beats have SOP window 0 — skip predict on those.
    f = t.mk_flit();
    if (t.cfg == 4'd0 && t.rt == 2'b00 && t.dcna == 16'd0 && t.scna == 16'd0 &&
        t.plen == 14'd0 && t.payload_lo == 352'd0)
      return;

    if (t.rt == 2'b10 || t.rt == 2'b11) begin
      n_g1_seen++;
      exp_g1_cnt = (exp_g1_cnt == 32'hFFFF_FFFF) ? 32'hFFFF_FFFF : exp_g1_cnt + 1;
      return;
    end
    if (len_illegal(t)) begin
      n_len_err++;
      return;
    end
    if (t.cfg == 4'd6 && cfg6_term(t))
      return;
    n_fwd++;
  endfunction

  function void note_cna(bit [15:0] c, bit w);
    exp_cna = c;
    exp_cna_written = w;
  endfunction

  function void note_route(bit [15:0] dest, bit [3:0] bm);
    route_bm[dest[7:0]] = bm;
  endfunction

  function void note_default(bit [3:0] bm);
    default_bm = bm;
  endfunction

  // Directed G1 check used by suite tests (AS §2/§15).
  task check_g1_drop(string name, bit [31:0] cnt_before);
    begin
      if (|probe.saw_egr) begin
        vibe_uvm_fail(name,
          "inject RT=1x packet",
          "no egress beat; packet dropped (not shortest-path / not RT=00)",
          "saw_egr != 0 (forwarded)",
          "u_fab.x_in_v / fab_nw_vld / saw_egr");
        mismatch++;
      end else if (cnt_before != 32'hFFFF_FFFF &&
                   probe.rt_shortest_unimpl !== (cnt_before + 32'd1)) begin
        vibe_uvm_fail(name,
          "inject RT=1x packet",
          "drop AND rt_shortest_unimpl += 1 (AS-0.1 G1)",
          $sformatf("cnt before=%0h after=%0h", cnt_before, probe.rt_shortest_unimpl),
          "u_fab.rt_shortest_unimpl / g1_evt");
        mismatch++;
      end else
        vibe_uvm_pass(name);
    end
  endtask

  function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info("AS_SB", $sformatf(
        "g1_pkts=%0d len_err=%0d fwd_pred=%0d mismatch=%0d",
        n_g1_seen, n_len_err, n_fwd, mismatch), UVM_LOW)
  endfunction
endclass
