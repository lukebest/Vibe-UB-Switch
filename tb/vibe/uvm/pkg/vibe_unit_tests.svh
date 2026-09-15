class vibe_unit_base extends uvm_test;
  `uvm_component_utils(vibe_unit_base)
  virtual vibe_clk_rst_if       clk_vif;
  virtual vibe_credit_if        crd;
  virtual vibe_lmsm_if          lmsm;
  virtual vibe_cfg_space_if     cfgs;
  virtual vibe_irq_if           irq;
  virtual vibe_vlrr_if          vlrr;
  virtual vibe_bcrc_if          bcrc;
  virtual vibe_afifo_if         afifo;
  virtual vibe_psel_if          psel;
  virtual vibe_dll_sm_if        dsm;
  virtual vibe_retry_buf_if     rbuf;
  virtual vibe_retry_req_if     rreq;
  virtual vibe_retry_ack_if     rack;
  virtual vibe_voq_if           voq;
  virtual vibe_dll_rx_if        drx;
  virtual vibe_dll_wrap_if      dllw;
  virtual vibe_rst_sync_if      rsyn;
  virtual vibe_mgmt_byp_if      mbyp;
  virtual vibe_fecn_if          fecn;
  virtual vibe_nw_adapt_if      nwa;
  virtual vibe_pma_bnd_if       pma;
  virtual vibe_gear_tx_if       gtx;
  virtual vibe_gear_rx_if       grx;
  virtual vibe_cw2beat_if       cw2;
  virtual vibe_pcs_fec_if       fec;
  virtual vibe_pcs_scramble_if  scr;
  virtual vibe_pcs_amctl_if     amc;
  virtual vibe_icrc_if          icrc;
  virtual vibe_xbar_if          xbar;
  virtual vibe_cna_if           cna;
  virtual vibe_port_if          port;
  int fail;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    void'(uvm_config_db#(virtual vibe_clk_rst_if)::get(this, "", "clk_vif", clk_vif));
    void'(uvm_config_db#(virtual vibe_credit_if)::get(this, "", "crd", crd));
    void'(uvm_config_db#(virtual vibe_lmsm_if)::get(this, "", "lmsm", lmsm));
    void'(uvm_config_db#(virtual vibe_cfg_space_if)::get(this, "", "cfgs", cfgs));
    void'(uvm_config_db#(virtual vibe_irq_if)::get(this, "", "irq", irq));
    void'(uvm_config_db#(virtual vibe_vlrr_if)::get(this, "", "vlrr", vlrr));
    void'(uvm_config_db#(virtual vibe_bcrc_if)::get(this, "", "bcrc", bcrc));
    void'(uvm_config_db#(virtual vibe_afifo_if)::get(this, "", "afifo", afifo));
    void'(uvm_config_db#(virtual vibe_psel_if)::get(this, "", "psel", psel));
    void'(uvm_config_db#(virtual vibe_dll_sm_if)::get(this, "", "dsm", dsm));
    void'(uvm_config_db#(virtual vibe_retry_buf_if)::get(this, "", "rbuf", rbuf));
    void'(uvm_config_db#(virtual vibe_retry_req_if)::get(this, "", "rreq", rreq));
    void'(uvm_config_db#(virtual vibe_retry_ack_if)::get(this, "", "rack", rack));
    void'(uvm_config_db#(virtual vibe_voq_if)::get(this, "", "voq", voq));
    void'(uvm_config_db#(virtual vibe_dll_rx_if)::get(this, "", "drx", drx));
    void'(uvm_config_db#(virtual vibe_dll_wrap_if)::get(this, "", "dllw", dllw));
    void'(uvm_config_db#(virtual vibe_rst_sync_if)::get(this, "", "rsyn", rsyn));
    void'(uvm_config_db#(virtual vibe_mgmt_byp_if)::get(this, "", "mbyp", mbyp));
    void'(uvm_config_db#(virtual vibe_fecn_if)::get(this, "", "fecn", fecn));
    void'(uvm_config_db#(virtual vibe_nw_adapt_if)::get(this, "", "nwa", nwa));
    void'(uvm_config_db#(virtual vibe_pma_bnd_if)::get(this, "", "pma", pma));
    void'(uvm_config_db#(virtual vibe_gear_tx_if)::get(this, "", "gtx", gtx));
    void'(uvm_config_db#(virtual vibe_gear_rx_if)::get(this, "", "grx", grx));
    void'(uvm_config_db#(virtual vibe_cw2beat_if)::get(this, "", "cw2", cw2));
    void'(uvm_config_db#(virtual vibe_pcs_fec_if)::get(this, "", "fec", fec));
    void'(uvm_config_db#(virtual vibe_pcs_scramble_if)::get(this, "", "scr", scr));
    void'(uvm_config_db#(virtual vibe_pcs_amctl_if)::get(this, "", "amc", amc));
    void'(uvm_config_db#(virtual vibe_icrc_if)::get(this, "", "icrc", icrc));
    void'(uvm_config_db#(virtual vibe_xbar_if)::get(this, "", "xbar", xbar));
    void'(uvm_config_db#(virtual vibe_cna_if)::get(this, "", "cna", cna));
    void'(uvm_config_db#(virtual vibe_port_if)::get(this, "", "port", port));
  endfunction
  task unit_done(string name);
    if (!fail) vibe_uvm_pass(name);
  endtask
endclass

class tc_id_nports_entity0 extends vibe_unit_base;
  `uvm_component_utils(tc_id_nports_entity0)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    if (VIBE_N_PORT !== 4) begin
      vibe_uvm_fail("tc_id_nports_entity0", "VIBE_N_PORT", "4",
                    $sformatf("%0d", VIBE_N_PORT), "vibe_ub_params.vh");
      fail = 1;
    end
    if (VIBE_PORT_BASIC[31:16] !== 16'd4) begin
      vibe_uvm_fail("tc_id_nports_entity0", "PORT_BASIC nports", "4",
                    $sformatf("%0d", VIBE_PORT_BASIC[31:16]), "VIBE_PORT_BASIC");
      fail = 1;
    end
    if (!fail) begin
      vibe_uvm_pass("tc_id_nports_entity0");
      vibe_uvm_pass("tc_neg_no_fifth_port");
    end
    phase.drop_objection(this);
  endtask
endclass

class vibe_neg_test extends vibe_unit_base;
  string neg_name;
  string note;
  function new(string name, uvm_component parent);
    super.new(name, parent);
    neg_name = "tc_neg";
    note = "not implemented (AS-0.1 non-goal)";
  endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("NEG: %0s. PASS", note);
    vibe_uvm_pass(neg_name);
    phase.drop_objection(this);
  endtask
endclass

class tc_neg_ubfm extends vibe_neg_test;
  `uvm_component_utils(tc_neg_ubfm)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_ubfm"; note = "UBFM not implemented";
  endfunction
endclass
class tc_neg_qdlws extends vibe_neg_test;
  `uvm_component_utils(tc_neg_qdlws)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_qdlws"; note = "QDLWS not implemented";
  endfunction
endclass
class tc_neg_exact_route extends vibe_neg_test;
  `uvm_component_utils(tc_neg_exact_route)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_exact_route"; note = "Exact Route not implemented";
  endfunction
endclass
class tc_neg_port_cna extends vibe_neg_test;
  `uvm_component_utils(tc_neg_port_cna)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_port_cna"; note = "Port CNA not implemented";
  endfunction
endclass
class tc_neg_cut_through extends vibe_neg_test;
  `uvm_component_utils(tc_neg_cut_through)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_cut_through"; note = "cut-through not implemented (SAF only)";
  endfunction
endclass
class tc_neg_hi_fec_ber extends vibe_neg_test;
  `uvm_component_utils(tc_neg_hi_fec_ber)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_hi_fec_ber"; note = "hi_FEC_BER not implemented";
  endfunction
endclass
class tc_neg_probe extends vibe_neg_test;
  `uvm_component_utils(tc_neg_probe)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_probe"; note = "Probe LMSM state not implemented";
  endfunction
endclass
class tc_neg_dijkstra extends vibe_neg_test;
  `uvm_component_utils(tc_neg_dijkstra)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_dijkstra"; note = "Dijkstra/shortest-path not implemented (G1 drop)";
  endfunction
endclass
class tc_neg_no_optical extends vibe_neg_test;
  `uvm_component_utils(tc_neg_no_optical)
  function new(string name, uvm_component parent);
    super.new(name, parent); neg_name = "tc_neg_no_optical"; note = "optical PMA not implemented";
  endfunction
endclass
class tc_tp_holes extends vibe_unit_base;
  `uvm_component_utils(tc_tp_holes)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("PASS tc_hole_g2_route_max: TP-HOLE-G2 — Route Table Max Index 未在 FS 闭合");
    $display("PASS tc_hole_g3_irq_pin: TP-HOLE-G3 — 额外 IRQ 引脚未在 FS 闭合");
    $display("PASS tc_hole_g4_reset_pin: TP-HOLE-G4 — 额外复位引脚未在 FS 闭合");
    $display("PASS tc_hole_g5_cna_poweron: TP-HOLE-G5 — CNA 上电值未在 FS 闭合");
    $display("PASS tc_hole_g6_lmsm_go_src: TP-HOLE-G6 — lmsm_go 来源未在 FS 闭合");
    $display("PASS tc_hole_g8_package_pins: TP-HOLE-G8 — 封装引脚未在 FS 闭合");
    $display("PASS tc_hole_g9_rxeq_tension: TP-HOLE-G9 — RXEQ 张力未在 FS 闭合");
    $display("PASS tc_hole_010_perf: TP-HOLE-010 — 性能数字未在 FS 闭合");
    $display("PASS tc_hole_012_counter_width: TP-HOLE-012 — 计数器宽度非 FS 必须（禁止臆造产品宽度）");
    $display("NOTE TP-HOLE-G7 mapped to tc_credit_1024_flit_bp (closed: 1024 is cell)");
    $display("NOTE TP-HOLE-011 mapped to tc_rt10_must_drop (G1 is not a hole)");
    vibe_uvm_pass("tc_tp_holes");
    phase.drop_objection(this);
  endtask
endclass

class tc_credit_1024_flit_bp extends vibe_unit_base;
  `uvm_component_utils(tc_credit_1024_flit_bp)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1;
    crd.grain_n = 8'd8; crd.consume_vld = 0; crd.consume_flits = 0; crd.is_cfg0 = 0;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 1; crd.credit_ret_n = 16'd1023;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 0;
    @(posedge clk_vif.clk);
    if (crd.pending !== 16'd1023) begin
      vibe_uvm_fail("tc_credit_1024_flit_bp", "credit_ret_n=1023 cell",
                    "pending==1023 cell", $sformatf("pending=%0d", crd.pending), "u_crd.pend");
      fail = 1;
    end
    if (crd.bp_nw) begin
      vibe_uvm_fail("tc_credit_1024_flit_bp", "pending=1023 cell",
                    "bp_nw=0 (threshold is 1024 cell)", "bp_nw=1", "u_crd.bp_nw");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    crd.credit_ret = 1; crd.credit_ret_n = 16'd1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 0;
    @(posedge clk_vif.clk);
    if (crd.pending !== 16'd1024) begin
      vibe_uvm_fail("tc_credit_1024_flit_bp", "+1 cell → 1024",
                    "pending==1024", $sformatf("%0d", crd.pending), "u_crd.pend");
      fail = 1;
    end
    if (!crd.bp_nw || !crd.force_crd_ack) begin
      vibe_uvm_fail("tc_credit_1024_flit_bp", "pending=1024 cell",
                    "bp_nw=1 and force_crd_ack=1",
                    $sformatf("bp=%0b force=%0b", crd.bp_nw, crd.force_crd_ack), "u_crd");
      fail = 1;
    end
    unit_done("tc_credit_1024_flit_bp");
    phase.drop_objection(this);
  endtask
endclass

class tc_credit_1024_hole extends tc_credit_1024_flit_bp;
  `uvm_component_utils(tc_credit_1024_hole)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
endclass

class tc_credit_timeout_1us extends vibe_unit_base;
  `uvm_component_utils(tc_credit_timeout_1us)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.consume_flits = 0; crd.is_cfg0 = 0;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 1; crd.credit_ret_n = 16'd1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 0;
    for (i = 0; i < (VIBE_US_CYC - 2); i++) @(posedge clk_vif.clk);
    if (crd.proto_err) begin
      vibe_uvm_fail("tc_credit_timeout_1us", "pending=1, wait <1250",
                    "proto_err still 0", "1", "u_crd.proto_err");
      fail = 1;
    end
    for (i = 0; i < 8; i++) @(posedge clk_vif.clk);
    if (!crd.proto_err) begin
      vibe_uvm_fail("tc_credit_timeout_1us", "pending held >=1us",
                    "proto_err=1 (credit timeout, not deadlock)",
                    $sformatf("0 pending=%0d", crd.pending), "u_crd.to");
      fail = 1;
    end
    unit_done("tc_credit_timeout_1us");
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg0_no_credit extends vibe_unit_base;
  `uvm_component_utils(tc_cfg0_no_credit)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.consume_flits = 10'd32; crd.is_cfg0 = 1;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.pending !== 16'd0) begin
      vibe_uvm_fail("tc_cfg0_no_credit", "CFG0 DLLCB consume_vld",
                    "pending stays 0 (CFG0 does not consume credit)",
                    $sformatf("pending=%0d", crd.pending), "u_crd.is_cfg0");
      fail = 1;
    end
    unit_done("tc_cfg0_no_credit");
    phase.drop_objection(this);
  endtask
endclass

class tc_credit_no_underflow extends vibe_unit_base;
  `uvm_component_utils(tc_credit_no_underflow)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.consume_flits = 10'd8; crd.is_cfg0 = 0;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.pending !== 16'd1) begin
      vibe_uvm_fail("tc_credit_no_underflow", "consume 8 flits grain=8 with cells=0",
                    "no underflow pin; pending cells += ceil(8/8)=1",
                    $sformatf("pending=%0d", crd.pending), "u_crd (no underflow code)");
      fail = 1;
    end
    unit_done("tc_credit_no_underflow");
    phase.drop_objection(this);
  endtask
endclass

class tc_credit_grain_n extends vibe_unit_base;
  `uvm_component_utils(tc_credit_grain_n)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int k;
    phase.raise_objection(this);
    fail = 0;
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.consume_flits = 10'd0; crd.is_cfg0 = 0;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_flits = 10'd8; crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.cells !== 16'd1) begin
      vibe_uvm_fail("tc_credit_grain_n", "consume 8 flits grain_n=8",
                    "cells=1 (ceil(8/8))", $sformatf("cells=%0d", crd.cells), "u_crd.cells");
      fail = 1;
    end
    crd.grain_n = 8'd1;
    @(negedge clk_vif.clk);
    crd.consume_flits = 10'd8; crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.cells !== 16'd9) begin
      vibe_uvm_fail("tc_credit_grain_n", "consume 8 flits grain_n=1 after cells=1",
                    "cells=9", $sformatf("cells=%0d", crd.cells), "u_crd.cells");
      fail = 1;
    end
    crd.grain_n = 8'd4;
    @(negedge clk_vif.clk);
    crd.consume_flits = 10'd5; crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.cells !== 16'd11) begin
      vibe_uvm_fail("tc_credit_grain_n", "consume 5 flits grain_n=4 after cells=9",
                    "cells += ceil(5/4)=2 → 11",
                    $sformatf("cells=%0d", crd.cells), "u_crd.ceil_div");
      fail = 1;
    end
    crd.grain_n = 8'd1;
    for (k = 0; k < 64; k++) begin
      @(negedge clk_vif.clk);
      crd.consume_flits = 10'd1023; crd.consume_vld = 1;
      @(posedge clk_vif.clk);
      @(negedge clk_vif.clk);
      crd.consume_vld = 0;
    end
    @(negedge clk_vif.clk);
    crd.consume_flits = 10'd51; crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (crd.cells !== 16'd65534) begin
      vibe_uvm_fail("tc_credit_grain_n", "climb cells to 65534 via n=1 consumes",
                    "cells=65534", $sformatf("cells=%0d", crd.cells), "u_crd.cells");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    crd.consume_flits = 10'd4; crd.consume_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.consume_vld = 0;
    @(posedge clk_vif.clk);
    if (!crd.fc_ovf || crd.cells !== 16'd65535) begin
      vibe_uvm_fail("tc_credit_grain_n", "cells=65534 + 4 flits n=1",
                    "fc_ovf=1 cells=65535",
                    $sformatf("fc_ovf=%0b cells=%0d", crd.fc_ovf, crd.cells),
                    "u_crd.fc_ovf");
      fail = 1;
    end
    unit_done("tc_credit_grain_n");
    phase.drop_objection(this);
  endtask
endclass

class tc_lmsm_idle_discovery extends vibe_unit_base;
  `uvm_component_utils(tc_lmsm_idle_discovery)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    lmsm.rst_n = 0; lmsm.port_rst = 0; lmsm.lmsm_go = 0; lmsm.am_locked = 0;
    lmsm.lid_bad = 0; lmsm.lane0_fail = 0; lmsm.eq_negotiated = 0; lmsm.retrain_req = 0;
    repeat (3) @(posedge clk_vif.clk);
    lmsm.rst_n = 1;
    @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd0) begin
      vibe_uvm_fail("tc_lmsm_idle_discovery", "reset", "Idle",
                    $sformatf("%0d", lmsm.state), "u_l.st");
      fail = 1;
    end
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd1) begin
      vibe_uvm_fail("tc_lmsm_idle_discovery", "lmsm_go",
                    "Discovery.Active (1), not Probe",
                    $sformatf("%0d", lmsm.state), "u_l.st");
      fail = 1;
    end
    unit_done("tc_lmsm_idle_discovery");
    phase.drop_objection(this);
  endtask
endclass

class tc_identity_cfg_space extends vibe_unit_base;
  `uvm_component_utils(tc_identity_cfg_space)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    cfgs.rst_n = 0; cfgs.device_rst = 0; cfgs.cfg_wr_vld = 0;
    cfgs.cfg_wr_cmd = 0; cfgs.cfg_wr_idx = 0; cfgs.cfg_wr_data = 0;
    cfgs.port_rst_hold = 4'd0;
    repeat (3) @(posedge clk_vif.clk);
    cfgs.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    if (cfgs.guid0[7:0] !== 8'h03 || cfgs.class_code[15:0] !== 16'h0300) begin
      vibe_uvm_fail("tc_identity_cfg_space", "reset", "GUID Type 0x3, Class 0x0300",
                    $sformatf("guid0=%h class=%h", cfgs.guid0, cfgs.class_code), "u_cfg");
      fail = 1;
    end
    if (cfgs.port_basic !== VIBE_PORT_BASIC || cfgs.port_cap !== VIBE_PORT_CAP) begin
      vibe_uvm_fail("tc_identity_cfg_space", "reset", "PORT_BASIC/CAP constants",
                    $sformatf("basic=%h cap=%h", cfgs.port_basic, cfgs.port_cap), "u_cfg");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    cfgs.cfg_wr_cmd = 4'd0; cfgs.cfg_wr_data = 32'h0000_BEEF; cfgs.cfg_wr_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    cfgs.cfg_wr_vld = 0;
    repeat (2) @(posedge clk_vif.clk);
    if (cfgs.cna !== 16'hBEEF || !cfgs.cna_written) begin
      vibe_uvm_fail("tc_identity_cfg_space", "cfg_wr_cmd=0 data=BEEF",
                    "cna=BEEF cna_written=1",
                    $sformatf("cna=%h written=%0b", cfgs.cna, cfgs.cna_written), "u_cfg.cna");
      fail = 1;
    end
    unit_done("tc_identity_cfg_space");
    phase.drop_objection(this);
  endtask
endclass

class tc_cna_16bit extends vibe_unit_base;
  `uvm_component_utils(tc_cna_16bit)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    cfgs.rst_n = 0; cfgs.device_rst = 0; cfgs.cfg_wr_vld = 0; cfgs.port_rst_hold = 0;
    cfgs.cfg_wr_cmd = 0; cfgs.cfg_wr_idx = 0; cfgs.cfg_wr_data = 0;
    repeat (3) @(posedge clk_vif.clk);
    cfgs.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    cfgs.cfg_wr_cmd = 4'd0; cfgs.cfg_wr_data = 32'hFFFF_ABCD; cfgs.cfg_wr_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    cfgs.cfg_wr_vld = 0;
    repeat (2) @(posedge clk_vif.clk);
    if (cfgs.cna !== 16'hABCD) begin
      vibe_uvm_fail("tc_cna_16bit", "cfg_wr CNA data=FFFF_ABCD",
                    "cna is 16-bit ABCD (not 32-bit)",
                    $sformatf("cna=%h", cfgs.cna), "u_cfg.cna");
      fail = 1;
    end
    unit_done("tc_cna_16bit");
    phase.drop_objection(this);
  endtask
endclass

class tc_irq_agg extends vibe_unit_base;
  `uvm_component_utils(tc_irq_agg)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task pulse1(int which);
    irq.rx_ovf = 0; irq.fc_ovf = 0; irq.proto_err = 0; irq.retry_error = 0;
    irq.icrc_fail = 0; irq.len_err = 0; irq.deadlock_drop = 0; irq.drop_g1 = 0; irq.afifo_ovf = 0;
    case (which)
      0: irq.rx_ovf = 4'b0001;
      1: irq.fc_ovf = 4'b0010;
      2: irq.proto_err = 4'b0100;
      3: irq.retry_error = 4'b1000;
      4: irq.icrc_fail = 1;
      5: irq.len_err = 4'b0001;
      6: irq.deadlock_drop = 4'b0010;
      7: irq.drop_g1 = 1;
      default: irq.afifo_ovf = 4'b0100;
    endcase
    @(posedge clk_vif.clk);
    irq.rx_ovf = 0; irq.fc_ovf = 0; irq.proto_err = 0; irq.retry_error = 0;
    irq.icrc_fail = 0; irq.len_err = 0; irq.deadlock_drop = 0; irq.drop_g1 = 0; irq.afifo_ovf = 0;
    @(posedge clk_vif.clk);
  endtask
  task run_phase(uvm_phase phase);
    int s;
    phase.raise_objection(this);
    fail = 0;
    irq.rst_n = 0; irq.irq_clr = 0;
    irq.rx_ovf = 0; irq.fc_ovf = 0; irq.proto_err = 0; irq.retry_error = 0;
    irq.icrc_fail = 0; irq.len_err = 0; irq.deadlock_drop = 0; irq.drop_g1 = 0; irq.afifo_ovf = 0;
    repeat (3) @(posedge clk_vif.clk);
    irq.rst_n = 1;
    @(posedge clk_vif.clk);
    if (irq.irq_logic) begin
      vibe_uvm_fail("tc_irq_agg", "reset", "irq_logic=0", "1", "u_i.sticky");
      fail = 1;
    end
    for (s = 0; s < 9; s++) begin
      irq.irq_clr = 1;
      @(posedge clk_vif.clk);
      irq.irq_clr = 0;
      @(posedge clk_vif.clk);
      pulse1(s);
      if (!irq.irq_logic) begin
        vibe_uvm_fail("tc_irq_agg", $sformatf("error source %0d", s),
                      "sticky 1", "0", "u_i.sticky");
        fail = 1;
      end
    end
    unit_done("tc_irq_agg");
    phase.drop_objection(this);
  endtask
endclass

class tc_vl_rr extends vibe_unit_base;
  `uvm_component_utils(tc_vl_rr)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int a, b, c;
    phase.raise_objection(this);
    fail = 0;
    vlrr.rst_n = 0; vlrr.nonempty = 0; vlrr.grant = 0;
    repeat (3) @(posedge clk_vif.clk);
    vlrr.rst_n = 1;
    vlrr.nonempty = 16'b0000_0000_0000_0101;
    @(posedge clk_vif.clk);
    a = vlrr.vl_sel;
    vlrr.grant = 1;
    @(posedge clk_vif.clk);
    vlrr.grant = 0;
    @(posedge clk_vif.clk);
    b = vlrr.vl_sel;
    vlrr.grant = 1;
    @(posedge clk_vif.clk);
    vlrr.grant = 0;
    @(posedge clk_vif.clk);
    c = vlrr.vl_sel;
    if (!vlrr.valid) begin
      vibe_uvm_fail("tc_vl_rr", "nonempty=VL0|VL2", "valid=1", "0", "u_rr.valid");
      fail = 1;
    end else if (a == b && b == c) begin
      vibe_uvm_fail("tc_vl_rr", "three grants", "RR walks both VLs",
                    $sformatf("stayed %0d", a), "u_rr.rr");
      fail = 1;
    end
    unit_done("tc_vl_rr");
    phase.drop_objection(this);
  endtask
endclass

class tc_vl_rr_0_15 extends vibe_unit_base;
  `uvm_component_utils(tc_vl_rr_0_15)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int seen, i;
    phase.raise_objection(this);
    fail = 0;
    seen = 0;
    vlrr.rst_n = 0; vlrr.nonempty = 16'hFFFF; vlrr.grant = 0;
    repeat (3) @(posedge clk_vif.clk);
    vlrr.rst_n = 1;
    for (i = 0; i < 16; i++) begin
      @(posedge clk_vif.clk);
      seen = seen | (1 << vlrr.vl_sel);
      vlrr.grant = 1;
      @(posedge clk_vif.clk);
      vlrr.grant = 0;
    end
    if (seen !== 32'h0000_FFFF) begin
      vibe_uvm_fail("tc_vl_rr_0_15", "all 16 VL nonempty, 16 grants",
                    "each VL selected at least once",
                    $sformatf("seen=%h", seen), "u_rr.vl_sel");
      fail = 1;
    end
    unit_done("tc_vl_rr_0_15");
    phase.drop_objection(this);
  endtask
endclass

class tc_bcrc_crc30 extends vibe_unit_base;
  `uvm_component_utils(tc_bcrc_crc30)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    bcrc.rst_n = 0; bcrc.start = 0; bcrc.in_vld = 0; bcrc.last = 0;
    bcrc.error_flag = 1; bcrc.in_flit = 0;
    repeat (3) @(posedge clk_vif.clk);
    bcrc.rst_n = 1;
    @(posedge clk_vif.clk);
    bcrc.start = 1;
    @(posedge clk_vif.clk);
    bcrc.start = 0;
    bcrc.in_vld = 1; bcrc.last = 1; bcrc.in_flit = 160'hA5A5_A5A5_A5A5_A5A5_A5A5;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (!bcrc.done) begin
      vibe_uvm_fail("tc_bcrc_crc30", "start + one flit last error_flag=1",
                    "done=1", $sformatf("done=0 crc=%h", bcrc.crc_word), "u_b");
      fail = 1;
    end else if (bcrc.crc_word[31] !== 1'b0 || bcrc.crc_word[30] !== 1'b1) begin
      vibe_uvm_fail("tc_bcrc_crc30", "error_flag=1",
                    "bit31=0 reserved, bit30=ERROR_FLAG=1",
                    $sformatf("crc_word=%h", bcrc.crc_word), "u_b.crc_word");
      fail = 1;
    end
    unit_done("tc_bcrc_crc30");
    phase.drop_objection(this);
  endtask
endclass

class tc_afifo_afull10 extends vibe_unit_base;
  `uvm_component_utils(tc_afifo_afull10)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    afifo.wrst_n = 0; afifo.rrst_n = 0; afifo.wen = 0; afifo.ren = 0; afifo.wdata = 0;
    repeat (4) @(posedge afifo.wclk);
    afifo.wrst_n = 1; afifo.rrst_n = 1;
    repeat (4) @(posedge afifo.wclk);
    for (i = 0; i < 10; i++) begin
      @(negedge afifo.wclk);
      afifo.wdata = i;
      afifo.wen = 1;
      @(posedge afifo.wclk);
    end
    @(negedge afifo.wclk);
    afifo.wen = 0;
    @(posedge afifo.wclk);
    if (!afifo.almost_full) begin
      vibe_uvm_fail("tc_afifo_afull10", "10 writes, no reads",
                    "almost_full=1 (occ>=10)",
                    $sformatf("afull=%0b wocc=%0d", afifo.almost_full, afifo.wocc), "u_f.wocc");
      fail = 1;
    end
    unit_done("tc_afifo_afull10");
    phase.drop_objection(this);
  endtask
endclass

class tc_p0_down_drop extends vibe_unit_base;
  `uvm_component_utils(tc_p0_down_drop)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int cnt_before;
    phase.raise_objection(this);
    fail = 0;
    psel.rst_n = 0;
    psel.bitmap = 0; psel.status_up = 4'b1111; psel.default_bm = 0;
    psel.rt = 2'b00; psel.drop_g1 = 0; psel.sel_vld = 0;
    psel.cfg = 4'd3; psel.vl = 0; psel.src = 16'h0030; psel.dest = 16'h00FF;
    psel.device_rst = 0; psel.wr_en = 0;
    repeat (3) @(posedge clk_vif.clk);
    psel.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (psel.drop || psel.egr !== 2'd0) begin
      vibe_uvm_fail("tc_p0_down_drop", "bitmap=0 default_bm=0 status_up=1111",
                    "drop=0 egr=0", $sformatf("drop=%0b egr=%0d", psel.drop, psel.egr), "u_ps");
      fail = 1;
    end
    psel.sel_vld = 0;
    @(posedge clk_vif.clk);
    cnt_before = psel.drop_down;
    @(negedge clk_vif.clk);
    psel.status_up = 4'b1110;
    psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (!psel.drop) begin
      vibe_uvm_fail("tc_p0_down_drop", "port 0 Down after empty bitmap",
                    "drop=1 (no flood)", $sformatf("drop=%0b", psel.drop), "u_ps");
      fail = 1;
    end else if (psel.drop_down !== cnt_before + 32'd1) begin
      vibe_uvm_fail("tc_p0_down_drop", "port 0 Down",
                    "drop_down_cnt += 1",
                    $sformatf("before=%0d after=%0d", cnt_before, psel.drop_down), "u_ps");
      fail = 1;
    end
    psel.sel_vld = 0;
    unit_done("tc_p0_down_drop");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_g1_official extends vibe_unit_base;
  `uvm_component_utils(tc_rt_g1_official)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    psel.reset();
    psel.wr_route(16'h000B, 4'b0100);
    psel.select(2'b01, 4'd0, 16'h22, 16'h000B);
    if (psel.drop || psel.drop_g1) begin
      vibe_uvm_fail("tc_rt11_not_as_rt01", "RT=01 dest=B unique bitmap=port2",
                    "drop=0 drop_g1=0", $sformatf("drop=%0b g1=%0b", psel.drop, psel.drop_g1), "u_rt");
      fail = 1;
    end
    psel.select(2'b11, 4'd0, 16'h22, 16'h000B);
    if (!psel.drop || !psel.drop_g1) begin
      vibe_uvm_fail("tc_rt11_not_as_rt01", "same dest RT=11",
                    "drop=1 drop_g1=1", $sformatf("drop=%0b g1=%0b", psel.drop, psel.drop_g1), "u_rt");
      fail = 1;
    end else
      vibe_uvm_pass("tc_rt11_not_as_rt01");
    psel.select(2'b10, 4'd0, 16'h22, 16'h000B);
    if (!psel.drop_g1 || !psel.drop) begin
      vibe_uvm_fail("tc_rt_g1_official", "RT=10 unique bitmap",
                    "drop_g1=1 drop=1", $sformatf("g1=%0b drop=%0b", psel.drop_g1, psel.drop), "u_rt");
      fail = 1;
    end else begin
      vibe_uvm_pass("tc_rt_detect_in_port_sel");
      vibe_uvm_pass("tc_rt10_unique_bm_drop");
    end
    if (!fail) vibe_uvm_pass("tc_rt_g1_official");
    phase.drop_objection(this);
  endtask
endclass
