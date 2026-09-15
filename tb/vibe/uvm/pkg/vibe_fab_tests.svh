class vibe_fab_base_test extends uvm_test;
  `uvm_component_utils(vibe_fab_base_test)
  vibe_fab_env env;
  virtual vibe_clk_rst_if   clk_vif;
  virtual vibe_cfg_if       cfg_vif;
  virtual vibe_nw4_if       ing_vif;
  virtual vibe_nw4_if       egr_vif;
  virtual vibe_fab_probe_if probe;
  virtual vibe_psel_if      psel;
  virtual vibe_cna_if       cna;
  int pass_count;
  int fail_count;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = vibe_fab_env::type_id::create("env", this);
    if (!uvm_config_db#(virtual vibe_clk_rst_if)::get(this, "", "clk_vif", clk_vif))
      `uvm_fatal(get_type_name(), "clk_vif")
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "cfg_vif", cfg_vif))
      `uvm_fatal(get_type_name(), "cfg_vif")
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "ing_vif", ing_vif))
      `uvm_fatal(get_type_name(), "ing_vif")
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "egr_vif", egr_vif))
      `uvm_fatal(get_type_name(), "egr_vif")
    if (!uvm_config_db#(virtual vibe_fab_probe_if)::get(this, "", "probe", probe))
      `uvm_fatal(get_type_name(), "probe")
    void'(uvm_config_db#(virtual vibe_psel_if)::get(this, "", "psel", psel));
    void'(uvm_config_db#(virtual vibe_cna_if)::get(this, "", "cna", cna));
  endfunction

  task tb_cycles(int n);
    repeat (n) @(posedge clk_vif.clk);
  endtask

  task tb_reset();
    int p;
    clk_vif.rst_n = 1'b0;
    cfg_vif.idle();
    ing_vif.idle_master();
    egr_vif.idle_slave_ready();
    probe.status_up = 4'b1111;
    if (cna != null) begin
      cna.cna = 16'd0; cna.cna_written = 1'b0; cna.hit = 4'd0; cna.rready = 4'b1111;
      for (p = 0; p < 4; p++) cna.data[p] = 512'd0;
    end
    tb_cycles(4);
    clk_vif.rst_n = 1'b1;
    tb_cycles(4);
    probe.clr_mon();
  endtask

  task tb_cfg(input bit [3:0] cmd, input bit [15:0] idx, input bit [31:0] data);
    cfg_vif.write(cmd, idx, data);
    if (cmd == VIBE_TB_CMD_CNA) env.sb.note_cna(data[15:0], 1'b1);
    if (cmd == VIBE_TB_CMD_ROUTE) env.sb.note_route(idx, data[3:0]);
    if (cmd == VIBE_TB_CMD_DEFAULT) env.sb.note_default(data[3:0]);
    if (cmd == VIBE_TB_CMD_DEVRST) env.sb.note_cna(16'd0, 1'b0);
  endtask

  task tb_wr_route(input bit [15:0] dest, input bit [3:0] bm);
    tb_cfg(VIBE_TB_CMD_ROUTE, dest, {28'd0, bm});
  endtask

  task tb_inject(int port, bit [511:0] beat0, int extra_beats);
    int n, b;
    n = extra_beats;
    if (n < 1) n = 1;
    for (b = 0; b < n; b++) begin
      @(negedge clk_vif.clk);
      while (!ing_vif.ready[port]) @(posedge clk_vif.clk);
      ing_vif.data[port] = (b == 0) ? beat0 : {160'd0, beat0[351:0]};
      ing_vif.vld[port]  = 1'b1;
      @(posedge clk_vif.clk);
    end
    @(negedge clk_vif.clk);
    ing_vif.vld[port] = 1'b0;
  endtask

  task tb_inject_hdr(
      int port, bit [3:0] cfg, bit [1:0] rt, bit [3:0] vl,
      bit [15:0] scna, bit [15:0] dcna, bit [13:0] plen,
      bit [2:0] nlp, bit [7:0] opc);
    bit [159:0] fl;
    int nb;
    fl = vibe_tb_mk_flit(cfg, rt, vl, scna, dcna, plen, 16'd0, 8'd0, nlp, opc);
    nb = vibe_tb_decl_beats(plen);
    tb_inject(port, vibe_tb_mk_beat(fl), nb);
  endtask

  task tb_hold_egr(bit hold);
    egr_vif.ready = hold ? 4'd0 : 4'b1111;
  endtask

  task tb_wait_egr(int timeout);
    int t;
    t = 0;
    while ((t < timeout) && !(|egr_vif.vld)) begin
      @(posedge clk_vif.clk);
      t++;
    end
  endtask

  task tb_expect_no_egr(int timeout);
    tb_cycles(timeout);
  endtask

  task tb_preload_cnt(bit [31:0] v);
    probe.preload_val = v;
    probe.preload_req = 1'b1;
    @(posedge clk_vif.clk);
    wait (probe.preload_done);
    probe.preload_req = 1'b0;
    @(posedge clk_vif.clk);
  endtask

  task tb_pass(string name);
    pass_count++;
    vibe_uvm_pass(name);
  endtask

  task tb_fail(string name, string stim, string exp, string act, string hier);
    fail_count++;
    vibe_uvm_fail(name, stim, exp, act, hier);
  endtask

  task expect_drop_only(string name, bit [31:0] cnt_before);
    tb_hold_egr(1'b0);
    tb_expect_no_egr(20);
    if (|probe.saw_egr)
      tb_fail(name,
        "inject RT=1x 2-beat pkt dest=1 vl=0",
        "no egress beat; packet dropped (not shortest-path / not RT=00)",
        "saw_egr != 0 (forwarded)",
        "u_fab.x_in_v / fab_nw_vld / saw_egr");
    else if (cnt_before != 32'hFFFF_FFFF &&
             probe.rt_shortest_unimpl !== (cnt_before + 32'd1))
      tb_fail(name,
        "inject RT=1x packet",
        "drop AND rt_shortest_unimpl += 1 (AS-0.1 G1)",
        $sformatf("cnt before=%0h after=%0h", cnt_before, probe.rt_shortest_unimpl),
        "u_fab.rt_shortest_unimpl / g1_evt");
    else
      tb_pass(name);
  endtask

  function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    $display("SUITE pass=%0d fail=%0d", pass_count, fail_count);
    if (fail_count == 0)
      $display("SUITE_RESULT PASS");
    else
      $display("SUITE_RESULT FAIL");
  endfunction
endclass

class tc_rt00_per_flow_rr_fwd extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt00_per_flow_rr_fwd)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int p0a, p0b, p1a;
    phase.raise_objection(this);
    $display("=== tc_rt00_per_flow_rr_fwd ===");
    psel.reset();
    psel.wr_route(16'h0001, 4'b1111);
    psel.select(2'b00, 4'd0, 16'hA000, 16'h0001);
    p0a = psel.drop ? -1 : psel.egr;
    psel.select(2'b00, 4'd0, 16'hA000, 16'h0001);
    p0b = psel.drop ? -1 : psel.egr;
    psel.select(2'b00, 4'd7, 16'hA000, 16'h0001);
    p1a = psel.drop ? -1 : psel.egr;
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    tb_inject_hdr(0, 4'd3, 2'b00, 4'd0, 16'hA000, 16'h0001, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(12);
    if (p0a < 0 || p0b < 0 || p1a < 0)
      tb_fail("tc_rt00_per_flow_rr_fwd", "port_sel+route_lu RT=00 dest=1 bitmap=1111",
              "drop=0 (forward on bitmap)", "drop=1", "psel.drop");
    else if (p0a != p0b)
      tb_fail("tc_rt00_per_flow_rr_fwd", "same flow {CFG,src,dest,VL} twice",
              "sticky same egr", "egr changed", "psel.sticky");
    else if (!probe.saw_xin[0] || probe.g1_comb[0])
      tb_fail("tc_rt00_per_flow_rr_fwd", "fabric inject RT=00",
              "x_in_v[0]=1 and not G1", "x_in_v/g1 mismatch", "u_fab.x_in_v");
    else
      tb_pass("tc_rt00_per_flow_rr_fwd");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt01_per_packet_rr_fwd extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt01_per_packet_rr_fwd)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int seqb[4];
    int i, ok;
    phase.raise_objection(this);
    $display("=== tc_rt01_per_packet_rr_fwd ===");
    psel.reset();
    psel.wr_route(16'h0002, 4'b1111);
    for (i = 0; i < 4; i++) begin
      psel.select(2'b01, 4'd1, 16'hB000, 16'h0002);
      seqb[i] = psel.drop ? -1 : psel.egr;
    end
    ok = 1;
    for (i = 0; i < 4; i++) if (seqb[i] < 0) ok = 0;
    if (!ok)
      tb_fail("tc_rt01_per_packet_rr_fwd", "4x port_sel RT=01 dest=2 bitmap=1111",
              "each select drop=0", "a select dropped", "psel.drop");
    else if (seqb[0] == seqb[1] && seqb[1] == seqb[2] && seqb[2] == seqb[3])
      tb_fail("tc_rt01_per_packet_rr_fwd", "4x RT=01 bitmap=1111",
              "per-packet RR walks ports", "all 4 egr identical", "psel.rr");
    else
      tb_pass("tc_rt01_per_packet_rr_fwd");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt10_must_drop extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt10_must_drop)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    bit [31:0] c0;
    phase.raise_objection(this);
    $display("=== tc_rt10_must_drop (TP-RT-003) ===");
    tb_reset();
    tb_wr_route(16'h0003, 4'b1110);
    probe.clr_mon();
    c0 = probe.rt_shortest_unimpl;
    tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'hC000, 16'h0003, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    expect_drop_only("tc_rt10_must_drop", c0);
    phase.drop_objection(this);
  endtask
endclass

class tc_rt11_must_drop extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt11_must_drop)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    bit [31:0] c0;
    phase.raise_objection(this);
    $display("=== tc_rt11_must_drop (TP-RT-004) ===");
    tb_reset();
    tb_wr_route(16'h0004, 4'b0111);
    probe.clr_mon();
    c0 = probe.rt_shortest_unimpl;
    tb_inject_hdr(0, 4'd3, 2'b11, 4'd2, 16'hC001, 16'h0004, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    expect_drop_only("tc_rt11_must_drop", c0);
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_shortest_unimpl_count extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt_shortest_unimpl_count)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    bit [31:0] c0, c1, c2;
    phase.raise_objection(this);
    $display("=== tc_rt_shortest_unimpl_count ===");
    tb_reset();
    c0 = probe.rt_shortest_unimpl;
    tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'h1, 16'h5, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(16);
    c1 = probe.rt_shortest_unimpl;
    tb_inject_hdr(1, 4'd3, 2'b11, 4'd0, 16'h1, 16'h6, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(16);
    c2 = probe.rt_shortest_unimpl;
    if (c0 !== 32'd0)
      tb_fail("tc_rt_shortest_unimpl_count", "reset then two G1 packets",
              "counter starts 0", "nonzero after reset", "rt_shortest_unimpl");
    else if (c1 !== 32'd1 || c2 !== 32'd2)
      tb_fail("tc_rt_shortest_unimpl_count", "RT=10 then RT=11",
              "rt_shortest_unimpl == 1 then 2",
              $sformatf("c1=%0d c2=%0d", c1, c2), "rt_shortest_unimpl");
    else
      tb_pass("tc_rt_shortest_unimpl_count");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_shortest_irq_logic extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt_shortest_irq_logic)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_rt_shortest_irq_logic ===");
    tb_reset();
    if (probe.irq_logic !== 1'b0)
      tb_fail("tc_rt_shortest_irq_logic", "reset", "irq_logic=0", "already 1", "u_irq.sticky");
    else begin
      tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'h1, 16'h7, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
      tb_cycles(16);
      if (probe.irq_logic !== 1'b1)
        tb_fail("tc_rt_shortest_irq_logic", "one RT=10 packet",
                "irq_logic=1", "stayed 0", "drop_g1 -> u_irq");
      else
        tb_pass("tc_rt_shortest_irq_logic");
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_irq_logic_sticky extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt_irq_logic_sticky)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int still;
    phase.raise_objection(this);
    $display("=== tc_rt_irq_logic_sticky ===");
    tb_reset();
    tb_inject_hdr(0, 4'd3, 2'b11, 4'd0, 16'h1, 16'h8, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(12);
    still = 1;
    tb_cycles(20);
    if (probe.irq_logic !== 1'b1) still = 0;
    if (!still)
      tb_fail("tc_rt_irq_logic_sticky", "RT=11 then wait 20 cycles",
              "irq_logic remains 1", "cleared by itself", "u_irq.sticky");
    else begin
      tb_cfg(VIBE_TB_CMD_NOPCLR, 16'd0, 32'd0);
      tb_cycles(4);
      if (probe.irq_logic !== 1'b0)
        tb_fail("tc_rt_irq_logic_sticky", "static cfg_wr_cmd=7 after sticky irq",
                "irq_logic=0 (AS-0.1 s10 clear on static write)", "still 1", "irq_clr");
      else begin
        tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'h1, 16'h9, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
        tb_cycles(12);
        tb_cfg(VIBE_TB_CMD_DEVRST, 16'd0, 32'd0);
        tb_cycles(12);
        if (probe.irq_logic !== 1'b0)
          tb_fail("tc_rt_irq_logic_sticky", "second G1 then device reset",
                  "irq_logic=0", "still 1", "device_rst / u_irq");
        else
          tb_pass("tc_rt_irq_logic_sticky");
      end
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_no_rewrite extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt_no_rewrite)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int bad;
    phase.raise_objection(this);
    $display("=== tc_rt_no_rewrite ===");
    tb_reset();
    tb_wr_route(16'h000A, 4'b0010);
    probe.clr_mon();
    tb_hold_egr(1'b1);
    tb_inject_hdr(0, 4'd3, 2'b00, 4'd0, 16'h1, 16'h000A, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(8);
    tb_hold_egr(1'b0);
    tb_wait_egr(40);
    bad = 0;
    if (|probe.saw_egr) begin
      if (probe.last_rt_egr[0] !== 2'b00 && probe.last_rt_egr[1] !== 2'b00 &&
          probe.last_rt_egr[2] !== 2'b00 && probe.last_rt_egr[3] !== 2'b00)
        bad = 1;
    end
    tb_reset();
    tb_wr_route(16'h000A, 4'b0010);
    probe.clr_mon();
    tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'h1, 16'h000A, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(16);
    if (|probe.saw_egr) begin
      if ((probe.saw_egr[0] && probe.last_rt_egr[0] !== 2'b10) ||
          (probe.saw_egr[1] && probe.last_rt_egr[1] !== 2'b10) ||
          (probe.saw_egr[2] && probe.last_rt_egr[2] !== 2'b10) ||
          (probe.saw_egr[3] && probe.last_rt_egr[3] !== 2'b10))
        bad = 2;
    end
    if (bad == 1)
      tb_fail("tc_rt_no_rewrite", "RT=00 forwarded packet", "egress LPH.RT still 00",
              "RT field rewritten", "fab_nw_data flit[23:22]");
    else if (bad == 2)
      tb_fail("tc_rt_no_rewrite", "RT=10 leaked", "must not rewrite RT to 00/01",
              "forwarded beat has rewritten RT", "saf_d / egr");
    else
      tb_pass("tc_rt_no_rewrite");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt10_not_as_rt00 extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt10_not_as_rt00)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int d00, d10, e00;
    phase.raise_objection(this);
    $display("=== tc_rt10_not_as_rt00 ===");
    psel.reset();
    psel.wr_route(16'h000B, 4'b0100);
    psel.select(2'b00, 4'd3, 16'h22, 16'h000B);
    d00 = psel.drop;
    e00 = psel.egr;
    psel.select(2'b10, 4'd3, 16'h22, 16'h000B);
    d10 = psel.drop;
    tb_reset();
    tb_wr_route(16'h000B, 4'b0100);
    tb_inject_hdr(0, 4'd3, 2'b10, 4'd3, 16'h22, 16'h000B, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(16);
    if (d00 || e00 !== 2'd2)
      tb_fail("tc_rt10_not_as_rt00", "control RT=00 dest=B bitmap=port2",
              "drop=0 egr=2", "RT=00 did not take bitmap port 2", "psel.egr");
    else if (!d10)
      tb_fail("tc_rt10_not_as_rt00", "same dest RT=10",
              "port_sel.drop=1", "drop=0 — treated as implemented RT", "drop_g1");
    else if (probe.saw_xin[0] || |probe.saw_egr)
      tb_fail("tc_rt10_not_as_rt00", "fabric RT=10 same dest",
              "x_in_v=0 and no egress", "presented to xbar or forwarded", "x_in_v");
    else
      tb_pass("tc_rt10_not_as_rt00");
    phase.drop_objection(this);
  endtask
endclass

class tc_rt_counter_32b_sat extends vibe_fab_base_test;
  `uvm_component_utils(tc_rt_counter_32b_sat)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_rt_counter_32b_sat ===");
    tb_reset();
    tb_preload_cnt(32'hFFFF_FFFE);
    tb_cycles(2);
    if (probe.rt_shortest_unimpl !== 32'hFFFF_FFFE)
      tb_fail("tc_rt_counter_32b_sat", "preload FFFFFFFE",
              "counter reads FFFFFFFE", "preload did not stick", "rt_shortest_unimpl");
    else begin
      tb_inject_hdr(0, 4'd3, 2'b10, 4'd0, 16'h1, 16'hC, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
      tb_cycles(16);
      if (probe.rt_shortest_unimpl !== 32'hFFFF_FFFF)
        tb_fail("tc_rt_counter_32b_sat", "preload FFFFFFFE + one RT=10",
                "FFFFFFFF (sat, no wrap)", "not FFFFFFFF", "rt_shortest_unimpl");
      else begin
        tb_inject_hdr(0, 4'd3, 2'b11, 4'd0, 16'h1, 16'hD, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
        tb_cycles(16);
        if (probe.rt_shortest_unimpl !== 32'hFFFF_FFFF)
          tb_fail("tc_rt_counter_32b_sat", "second G1 at FFFFFFFF",
                  "stay FFFFFFFF (no wrap to 0)", "wrapped or changed", "rt_shortest_unimpl");
        else
          tb_pass("tc_rt_counter_32b_sat");
      end
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg_identity_guid_class extends vibe_fab_base_test;
  `uvm_component_utils(tc_cfg_identity_guid_class)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_cfg_identity_guid_class ===");
    tb_reset();
    tb_cfg(VIBE_TB_CMD_CNA, 16'd0, 32'h0000_00AB);
    if (probe.guid0 !== {24'd0, VIBE_GUID_TYPE})
      tb_fail("tc_cfg_identity_guid_class", "probe guid0", "GUID Type 0x3",
              "guid0 mismatch", "u_cfg.guid0");
    else if (probe.class_code !== {16'd0, VIBE_CLASS_CODE})
      tb_fail("tc_cfg_identity_guid_class", "probe class_code", "Class 0x0300",
              "class_code mismatch", "u_cfg.class_code");
    else if (probe.port_basic !== VIBE_PORT_BASIC || probe.port_cap !== VIBE_PORT_CAP)
      tb_fail("tc_cfg_identity_guid_class", "PORT_BASIC / CAP",
              "4p, x4, Mode-2", "constant mismatch", "u_cfg.port_basic");
    else if (probe.cna !== 16'h00AB || probe.cna_written !== 1'b1)
      tb_fail("tc_cfg_identity_guid_class", "cfg_wr_cmd=0 data=00AB",
              "cna=00AB and cna_written=1", "CNA static write did not land", "u_cfg.cna");
    else
      tb_pass("tc_cfg_identity_guid_class");
    phase.drop_objection(this);
  endtask
endclass

class tc_default_rt_all0_port0 extends vibe_fab_base_test;
  `uvm_component_utils(tc_default_rt_all0_port0)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_default_rt_all0_port0 ===");
    psel.reset();
    psel.select(2'b00, 4'd0, 16'h30, 16'h00FF);
    if (psel.drop || psel.egr !== 2'd0)
      tb_fail("tc_default_rt_all0_port0", "RT=00 dest=00FF table all-0 default_bm=0",
              "drop=0 egr=0", "wrong egr or drop", "psel.use_bm");
    else
      tb_pass("tc_default_rt_all0_port0");
    phase.drop_objection(this);
  endtask
endclass

class tc_pkt_len_err_drop extends vibe_fab_base_test;
  `uvm_component_utils(tc_pkt_len_err_drop)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int fwd;
    phase.raise_objection(this);
    $display("=== tc_pkt_len_err_drop ===");
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    probe.clr_mon();
    tb_inject(0, vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_oversize(),
        16'd0, 8'd0, 3'd0, 8'd0)), 1);
    tb_cycles(12);
    fwd = |probe.saw_egr;
    if (!probe.saw_len_err[0])
      tb_fail("tc_pkt_len_err_drop", "declared 224 flits (4480 B)",
              "len_err[0] pulse; drop; irq_logic", "len_err not seen", "u_saf.len_err");
    else if (fwd)
      tb_fail("tc_pkt_len_err_drop", "oversize declared length",
              "drop (no egress)", "packet forwarded", "fab_nw_vld");
    else if (probe.irq_logic !== 1'b1)
      tb_fail("tc_pkt_len_err_drop", "len_err observed",
              "irq_logic sticky 1 (AS-0.1 s15)", "irq_logic=0", "u_irq");
    else begin
      $display("NOTE tc_pkt_len_err_drop: <16 B not reachable (decl_flits clamp to 1 = 20 B)");
      tb_pass("tc_pkt_len_err_drop");
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg6_term_vs_fwd extends vibe_fab_base_test;
  `uvm_component_utils(tc_cfg6_term_vs_fwd)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int term_us, term_nlp, term_opc, fwd_miss, fwd_opc_nous, unw;
    phase.raise_objection(this);
    $display("=== tc_cfg6_term_vs_fwd ===");
    tb_reset();
    cna.cna = 16'h1111; cna.cna_written = 1'b1; cna.hit = 4'd0;
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    @(posedge clk_vif.clk);
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    term_us = cna.cons[0] && cna.rvld[0];
    cna.hit[0] = 1'b0;
    @(posedge clk_vif.clk);
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd1, 8'd0));
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    term_nlp = cna.cons[0];
    cna.hit[0] = 1'b0;
    @(posedge clk_vif.clk);
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'h10));
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    term_opc = cna.cons[0];
    cna.hit[0] = 1'b0;
    @(posedge clk_vif.clk);
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'h10));
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    fwd_opc_nous = !cna.cons[0];
    cna.hit[0] = 1'b0;
    @(posedge clk_vif.clk);
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    fwd_miss = !cna.cons[0];
    cna.hit = 4'd0;
    @(posedge clk_vif.clk);
    cna.cna_written = 1'b0; cna.cna = 16'h1111;
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    cna.hit[0] = 1'b1;
    @(posedge clk_vif.clk);
    unw = !cna.cons[0];
    cna.hit = 4'd0;
    @(posedge clk_vif.clk);
    tb_reset();
    tb_cfg(VIBE_TB_CMD_CNA, 16'd0, 32'h0000_1111);
    tb_inject_hdr(0, 4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(16);
    tb_inject_hdr(0, 4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(32);
    if (!term_us)
      tb_fail("tc_cfg6_term_vs_fwd", "cna_ep CFG6 DCNA==written CNA",
              "consume=1", "no consume", "u_c6.term");
    else if (!term_nlp)
      tb_fail("tc_cfg6_term_vs_fwd", "CFG6 NLP=1 DCNA!=CNA",
              "consume=1 (enumerate terminate)", "consume=0", "u_c6.nlp");
    else if (!term_opc)
      tb_fail("tc_cfg6_term_vs_fwd", "CFG6 opcode 0x10 DCNA==CNA",
              "consume=1", "consume=0", "u_c6.opc");
    else if (!fwd_opc_nous)
      tb_fail("tc_cfg6_term_vs_fwd", "CFG6 opcode 0x10 DCNA!=CNA",
              "consume=0 (forward)", "consume=1", "u_c6.term");
    else if (!fwd_miss)
      tb_fail("tc_cfg6_term_vs_fwd", "CFG6 DCNA!=CNA NLP=0 opc=0",
              "consume=0", "consume=1", "u_c6.term");
    else if (!unw)
      tb_fail("tc_cfg6_term_vs_fwd", "CNA not written, DCNA==power-on CNA",
              "consume=0", "consume=1", "cna_written");
    else
      tb_pass("tc_cfg6_term_vs_fwd");
    phase.drop_objection(this);
  endtask
endclass

class tc_saf_full_pkt extends vibe_fab_base_test;
  `uvm_component_utils(tc_saf_full_pkt)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int early;
    phase.raise_objection(this);
    $display("=== tc_saf_full_pkt ===");
    tb_reset();
    tb_wr_route(16'h0001, 4'b0001);
    probe.clr_mon();
    tb_hold_egr(1'b0);
    @(negedge clk_vif.clk);
    while (!ing_vif.ready[0]) @(posedge clk_vif.clk);
    ing_vif.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h0001, vibe_tb_plen_nflit(5),
        16'd0, 8'd0, 3'd0, 8'd0));
    ing_vif.vld[0] = 1'b1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    ing_vif.vld[0] = 1'b0;
    tb_cycles(8);
    early = |probe.saf_v;
    @(negedge clk_vif.clk);
    ing_vif.data[0] = 512'd0;
    ing_vif.vld[0] = 1'b1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    ing_vif.vld[0] = 1'b0;
    tb_cycles(8);
    if (early)
      tb_fail("tc_saf_full_pkt", "1 of 2 declared beats only",
              "saf_v=0 (store-and-forward; no xbar yet)",
              "saf_v rose before EOP", "u_saf.done");
    else if (!(|probe.saf_v) && !(|probe.saw_egr)) begin
      tb_wait_egr(30);
      if (!(|probe.saw_egr) && !(|probe.saf_v))
        tb_fail("tc_saf_full_pkt", "second beat completed declared length",
                "packet presented (saf_v or egress)", "never presented", "saf_v");
      else
        tb_pass("tc_saf_full_pkt");
    end else
      tb_pass("tc_saf_full_pkt");
    phase.drop_objection(this);
  endtask
endclass

class tc_icrc_transit_no_recompute extends vibe_fab_base_test;
  `uvm_component_utils(tc_icrc_transit_no_recompute)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    bit [159:0] in_f;
    phase.raise_objection(this);
    $display("=== tc_icrc_transit_no_recompute ===");
    tb_reset();
    tb_wr_route(16'h0003, 4'b1000);
    in_f = vibe_tb_mk_flit(4'd3, 2'b00, 4'd4, 16'hAA, 16'h0003,
                           vibe_tb_plen_nflit(5), 16'hA5A5, 8'h5A, 3'd0, 8'h00);
    probe.clr_mon();
    tb_hold_egr(1'b1);
    tb_inject(0, vibe_tb_mk_beat(in_f), 2);
    tb_cycles(8);
    tb_hold_egr(1'b0);
    tb_wait_egr(40);
    if (vibe_nth_cci(vibe_nw512_flit0(probe.saf_d[0])) !== vibe_nth_cci(in_f) ||
        vibe_nth_lbf(vibe_nw512_flit0(probe.saf_d[0])) !== vibe_nth_lbf(in_f))
      tb_fail("tc_icrc_transit_no_recompute", "transit CFG3 sitting in SAF",
              "CCI/LBF unchanged (fabric has no vibe_icrc)",
              "SAF header CCI/LBF changed", "saf_d");
    else
      tb_pass("tc_icrc_transit_no_recompute");
    phase.drop_objection(this);
  endtask
endclass

class vibe_cfg_fwd_test extends vibe_fab_base_test;
  bit [3:0]  fwd_cfg;
  string     fwd_name;
  function new(string name, uvm_component parent);
    super.new(name, parent);
    fwd_cfg  = 4'd3;
    fwd_name = "tc_cfg_fwd";
  endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== %0s ===", fwd_name);
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    probe.clr_mon();
    tb_inject_hdr(0, fwd_cfg, 2'b00, 4'd0, 16'h0001, 16'h0001,
                  vibe_tb_plen_nflit(5), 3'd0, 8'd0);
    tb_cycles(14);
    if (probe.fab_mgmt_cfg6_hit[0])
      tb_fail(fwd_name, "inject CFG to dest=1 bitmap=1111",
              "fab_mgmt_cfg6_hit=0", "fab_mgmt_cfg6_hit=1", "fab_mgmt_cfg6_hit");
    else if (!probe.saw_xin[0] && !probe.g1_comb[0] && !(|probe.saw_egr))
      tb_fail(fwd_name, "inject non-term CFG RT=00",
              "x_in_v=1 (forward / xbar)", "not presented to xbar", "x_in_v");
    else
      tb_pass(fwd_name);
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg3_fwd extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg3_fwd)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd3; fwd_name = "tc_cfg3_fwd";
  endfunction
endclass
class tc_cfg4_fwd extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg4_fwd)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd4; fwd_name = "tc_cfg4_fwd";
  endfunction
endclass
class tc_cfg5_fwd extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg5_fwd)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd5; fwd_name = "tc_cfg5_fwd";
  endfunction
endclass
class tc_cfg7_fwd extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg7_fwd)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd7; fwd_name = "tc_cfg7_fwd";
  endfunction
endclass
class tc_cfg9_fwd extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg9_fwd)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd9; fwd_name = "tc_cfg9_fwd";
  endfunction
endclass
class tc_cfg0_fabric_no_special extends vibe_cfg_fwd_test;
  `uvm_component_utils(tc_cfg0_fabric_no_special)
  function new(string name, uvm_component parent);
    super.new(name, parent); fwd_cfg = 4'd0; fwd_name = "tc_cfg0_fabric_no_special";
  endfunction
endclass

class tc_cfg_reserved_fwd extends vibe_fab_base_test;
  `uvm_component_utils(tc_cfg_reserved_fwd)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i, nfail;
    bit [3:0] cfgs[5];
    phase.raise_objection(this);
    $display("=== tc_cfg_reserved_fwd ===");
    cfgs[0] = 4'd1; cfgs[1] = 4'd2; cfgs[2] = 4'd8; cfgs[3] = 4'd10; cfgs[4] = 4'd15;
    nfail = 0;
    for (i = 0; i < 5; i++) begin
      tb_reset();
      tb_wr_route(16'h0001, 4'b1111);
      probe.clr_mon();
      tb_inject_hdr(0, cfgs[i], 2'b00, 4'd0, 16'h0001, 16'h0001,
                    vibe_tb_plen_nflit(5), 3'd0, 8'd0);
      tb_cycles(14);
      if (probe.fab_mgmt_cfg6_hit[0] ||
          (!probe.saw_xin[0] && !probe.g1_comb[0] && !(|probe.saw_egr)))
        nfail++;
    end
    if (nfail)
      tb_fail("tc_cfg_reserved_fwd", "CFG 1,2,8,10,15 RT=00 dest=1",
              "each x_in_v=1 and fab_mgmt_cfg6_hit=0",
              "one or more reserved CFGs not forwarded", "x_in_v");
    else
      tb_pass("tc_cfg_reserved_fwd");
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg_fwd_class extends vibe_fab_base_test;
  `uvm_component_utils(tc_cfg_fwd_class)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i, nfail;
    bit [3:0] cfgs[10];
    phase.raise_objection(this);
    $display("=== tc_cfg_fwd_class ===");
    cfgs[0] = 4'd3; cfgs[1] = 4'd4; cfgs[2] = 4'd5; cfgs[3] = 4'd7; cfgs[4] = 4'd9;
    cfgs[5] = 4'd1; cfgs[6] = 4'd2; cfgs[7] = 4'd8; cfgs[8] = 4'd10; cfgs[9] = 4'd15;
    nfail = 0;
    for (i = 0; i < 10; i++) begin
      tb_reset();
      tb_wr_route(16'h0001, 4'b1111);
      probe.clr_mon();
      tb_inject_hdr(0, cfgs[i], 2'b00, 4'd0, 16'h0001, 16'h0001,
                    vibe_tb_plen_nflit(5), 3'd0, 8'd0);
      tb_cycles(14);
      if (probe.fab_mgmt_cfg6_hit[0] ||
          (!probe.saw_xin[0] && !probe.g1_comb[0] && !(|probe.saw_egr)))
        nfail++;
    end
    if (nfail)
      tb_fail("tc_cfg_fwd_class", "CFG 3/4/5/7/9 + reserved",
              "each forwarded and fab_mgmt_cfg6_hit=0",
              "one or more CFGs terminated or dropped", "x_in_v");
    else
      tb_pass("tc_cfg_fwd_class");
    phase.drop_objection(this);
  endtask
endclass

class tc_port_rst_via_cfg extends vibe_fab_base_test;
  `uvm_component_utils(tc_port_rst_via_cfg)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_port_rst_via_cfg ===");
    tb_reset();
    tb_cfg(VIBE_TB_CMD_PORTRST, 16'd2, VIBE_TB_PORTRST_NOP);
    if (probe.port_rst[2] || probe.port_rst_rw1c[2])
      tb_fail("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=0",
              "port_rst[2]=0", "port_rst or rw1c bit 2 set", "port_rst");
    else begin
      tb_cfg(VIBE_TB_CMD_PORTRST, 16'd2, VIBE_TB_PORTRST_W1C);
      if (!probe.port_rst[2])
        tb_fail("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=1",
                "port_rst[2]=1", "port_rst[2]=0", "port_rst");
      else if (probe.port_rst[0] || probe.port_rst[1] || probe.port_rst[3])
        tb_fail("tc_port_rst_via_cfg", "port reset index 2 data[0]=1",
                "only bit 2", "other bits set", "port_rst");
      else if (!probe.port_rst_rw1c[2])
        tb_fail("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=1",
                "port_rst_rw1c[2]=1", "rw1c[2]=0", "port_rst_rw1c");
      else
        tb_pass("tc_port_rst_via_cfg");
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_device_rst_via_cfg extends vibe_fab_base_test;
  `uvm_component_utils(tc_device_rst_via_cfg)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    $display("=== tc_device_rst_via_cfg ===");
    tb_reset();
    tb_cfg(VIBE_TB_CMD_CNA, 16'd0, 32'h0000_00AA);
    tb_cfg(VIBE_TB_CMD_DEVRST, 16'd0, 32'd0);
    if (!probe.device_rst)
      tb_fail("tc_device_rst_via_cfg", "cfg_wr_cmd=4 device reset",
              "device_rst hold=1", "device_rst=0", "u_rst.device_rst");
    else begin
      tb_cycles(12);
      if (probe.cna_written !== 1'b0)
        tb_fail("tc_device_rst_via_cfg", "device reset after CNA write",
                "CNA unwritten", "cna_written still 1", "u_cfg.cna_written");
      else
        tb_pass("tc_device_rst_via_cfg");
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_pkt_len_legal_16_4300 extends vibe_fab_base_test;
  `uvm_component_utils(tc_pkt_len_legal_16_4300)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int bad20, bad4300;
    phase.raise_objection(this);
    $display("=== tc_pkt_len_legal_16_4300 ===");
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    probe.clr_mon();
    tb_inject_hdr(0, 4'd3, 2'b00, 4'd0, 16'h1, 16'h0001,
                  vibe_tb_plen_min_try(), 3'd0, 8'd0);
    tb_cycles(16);
    bad20 = probe.saw_len_err[0];
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    probe.clr_mon();
    tb_inject_hdr(0, 4'd3, 2'b00, 4'd0, 16'h1, 16'h0001,
                  vibe_tb_plen_4300(), 3'd0, 8'd0);
    tb_cycles(80);
    bad4300 = probe.saw_len_err[0];
    if (bad20)
      tb_fail("tc_pkt_len_legal_16_4300", "1-flit / 20 B",
              "len_err=0 (inside 16..4300)", "len_err pulsed", "len_err");
    else if (bad4300)
      tb_fail("tc_pkt_len_legal_16_4300", "declared 215 flits = 4300 B",
              "len_err=0", "len_err pulsed", "len_err");
    else begin
      $display("NOTE tc_pkt_len_legal_16_4300: 16 B not reachable (1-flit clamp=20 B)");
      tb_pass("tc_pkt_len_legal_16_4300");
    end
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg9_no_icrc extends vibe_fab_base_test;
  `uvm_component_utils(tc_cfg9_no_icrc)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    logic [159:0] in_f, saf_f;
    int saw_x;
    phase.raise_objection(this);
    $display("=== tc_cfg9_no_icrc ===");
    tb_reset();
    tb_wr_route(16'h0001, 4'b1111);
    probe.clr_mon();
    in_f = vibe_tb_mk_flit(4'd9, 2'b00, 4'd0, 16'h0002, 16'h0001,
                           vibe_tb_plen_nflit(5), 16'hA5A5, 8'h5A, 3'd0, 8'h00);
    tb_inject(0, vibe_tb_mk_beat(in_f), 2);
    saw_x = 0;
    saf_f = 160'd0;
    repeat (16) begin
      @(posedge clk_vif.clk);
      if (probe.x_in_v[0]) begin
        saw_x = 1;
        saf_f = probe.saf_d[0][511:352];
      end
    end
    if (saf_f === 160'd0)
      saf_f = probe.saf_d[0][511:352];
    if (probe.fab_mgmt_cfg6_hit[0])
      tb_fail("tc_cfg9_no_icrc", "CFG9 RT=00 dest=1 (not terminate class)",
              "fab_mgmt_cfg6_hit=0 (CFG9 has no ICRC; forward)",
              "fab_mgmt_cfg6_hit=1", "u_fab.fab_mgmt_cfg6_hit");
    else if (vibe_nth_cci(saf_f) !== vibe_nth_cci(in_f) ||
             vibe_nth_lbf(saf_f) !== vibe_nth_lbf(in_f))
      tb_fail("tc_cfg9_no_icrc", "CFG9 sitting in SAF (AS-0.1 §13 no ICRC)",
              "CCI/LBF unchanged (fabric has no vibe_icrc)",
              "SAF CCI/LBF rewritten", "u_fab.saf_d");
    else if (!saw_x && !probe.g1_comb[0])
      tb_fail("tc_cfg9_no_icrc", "CFG9 RT=00 dest=1 bitmap=1111",
              "x_in_v=1 (forward; no ICRC terminate)",
              "not presented to xbar", "u_fab.x_in_v");
    else
      tb_pass("tc_cfg9_no_icrc");
    phase.drop_objection(this);
  endtask
endclass
