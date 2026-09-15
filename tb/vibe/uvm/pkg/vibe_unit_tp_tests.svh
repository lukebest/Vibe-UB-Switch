// UVM leaf tests covering remaining official TP-0.3 IDs (Icarus ports).

class tc_neg_official extends vibe_unit_base;
  `uvm_component_utils(tc_neg_official)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task one(int hit, string name, string token);
    if (hit) begin
      vibe_uvm_fail(name, $sformatf("scan rtl/vibe_*.sv for %0s", token),
                    "identifier absent from code (comments citing ban OK)",
                    "token present in RTL", "rtl/**/vibe_*.sv");
      fail = 1;
    end else
      vibe_uvm_pass(name);
  endtask
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    if (NEG_SCAN_OPEN_FAIL) begin
      vibe_uvm_fail("tc_neg_official", "scan_official_neg.py --inc",
                    "rtl/ readable, include generated",
                    "NEG_SCAN_OPEN_FAIL=1", "tb/vibe/scripts/scan_official_neg.py");
      fail = 1;
    end
    one(HIT_UB3,     "tc_id_spec_2_0_only",        "UB_BASE_3 / ub_base_3");
    one(HIT_APXD,    "tc_id_appendix_d_subset",    "QDLWS / APPENDIX_D_FULL");
    one(HIT_SL,      "tc_vl_no_sl",                "SL_MAP / sl_to_vl");
    one(HIT_CAQM,    "tc_fecn_no_caqm",            "CAQM");
    one(HIT_NPI,     "tc_qos_npi_disabled",        "npi_filter / npi_en");
    one(HIT_UPI,     "tc_nw_no_upi_port_ip",       "UPI_ROUTE / port_ip_lu");
    one(HIT_HOP,     "tc_fab_no_hop_qdepth_must",  "hop_cnt / qdepth_must");
    one(HIT_HOTPLUG, "tc_irq_no_hotplug",          "hotplug");
    one(HIT_ATTACK,  "tc_err_no_attack_req",       "attack_detect");
    one(HIT_XPORT,   "tc_neg_no_transport_ep",     "transport_ep / function_ep");
    one(HIT_UMMU,    "tc_neg_no_ummu",             "UMMU");
    one(HIT_UBOE,    "tc_neg_no_uboe",             "UBoE");
    one(HIT_ANA,     "tc_neg_no_analog_pma",       "gray_map / precoder / serdes_ana");
    one(HIT_SECRET,  "tc_neg_no_secret_ip",        "secret_ip");
    one(HIT_HCSR,    "tc_neg_no_host_csr",         "apb_paddr / axi4_ / host_csr_");
    one(HIT_OFFCHIP, "tc_neg_no_offchip_mgmt",     "i2c_sda / jtag_tck");
    one(HIT_README,  "tc_neg_no_readme_numbers",   "OLD_README / ub_v0_nport");
    one(HIT_FS7,     "tc_neg_no_fs7_bundle",       "FS7_ / fs7_bundle");
    one(HIT_P5,      "tc_neg_no_fifth_port",       "pcs_pma_txdata_4 / vibe_port_4");
    unit_done("tc_neg_official");
    phase.drop_objection(this);
  endtask
endclass

class tc_neg_absent_features extends vibe_unit_base;
  `uvm_component_utils(tc_neg_absent_features)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    lmsm.rst_n = 0; lmsm.port_rst = 0; lmsm.lmsm_go = 0;
    lmsm.am_locked = 0; lmsm.lid_bad = 0; lmsm.lane0_fail = 0;
    lmsm.eq_negotiated = 0; lmsm.retrain_req = 0;
    repeat (3) @(posedge clk_vif.clk);
    lmsm.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd0) begin
      vibe_uvm_fail("tc_neg_absent_features", "reset", "ST_IDLE (no Probe state)",
                    $sformatf("state=%0d", lmsm.state), "u_lmsm.st");
      fail = 1;
    end
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd1) begin
      vibe_uvm_fail("tc_neg_absent_features", "pulse lmsm_go from Idle",
                    "Discovery.Active (5'd1) — not Probe / QDLWS / RXEQ_Optimize",
                    $sformatf("state=%0d", lmsm.state), "u_lmsm.st");
      fail = 1;
    end
    repeat (8) @(posedge clk_vif.clk);
    if (lmsm.state === 5'd12 || lmsm.state === 5'd13 || lmsm.state === 5'd31) begin
      vibe_uvm_fail("tc_neg_absent_features", "after lmsm_go",
                    "remain in implemented subset (no Probe encoding)",
                    $sformatf("state=%0d", lmsm.state), "u_lmsm.st");
      fail = 1;
    end
    unit_done("tc_neg_absent_features");
    phase.drop_objection(this);
  endtask
endclass

class tc_dll_sm_states extends vibe_unit_base;
  `uvm_component_utils(tc_dll_sm_states)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    dsm.rst_n = 0; dsm.port_rst = 0; dsm.link_up = 0;
    dsm.param_ok = 0; dsm.credit_ok = 0; dsm.dll_error = 0;
    repeat (3) @(posedge clk_vif.clk);
    dsm.rst_n = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd0 || !dsm.disabled) begin
      vibe_uvm_fail("tc_dll_sm_states", "reset LinkUp=0", "ST_DIS disabled=1",
                    $sformatf("state=%0d dis=%0b", dsm.state, dsm.disabled), "u_dsm.st");
      fail = 1;
    end
    dsm.link_up = 1;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd1) begin
      vibe_uvm_fail("tc_dll_sm_states", "LinkUp=1", "Param_Init (1)",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.param_ok = 0;
    repeat (3) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd1) begin
      vibe_uvm_fail("tc_dll_sm_states", "LinkUp=1 param_ok=0", "stay Param_Init",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.param_ok = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd2) begin
      vibe_uvm_fail("tc_dll_sm_states", "param_ok", "Credit_Init (2)",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.credit_ok = 0;
    repeat (3) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd2) begin
      vibe_uvm_fail("tc_dll_sm_states", "Credit_Init credit_ok=0", "stay Credit_Init",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.credit_ok = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd3 || !dsm.status_up) begin
      vibe_uvm_fail("tc_dll_sm_states", "credit_ok", "Normal status_up=1",
                    $sformatf("state=%0d up=%0b", dsm.state, dsm.status_up), "u_dsm.st");
      fail = 1;
    end
    repeat (4) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd3) begin
      vibe_uvm_fail("tc_dll_sm_states", "hold Normal (no port_rst)",
                    "remain Normal (entity rst must not force Disabled)",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.link_up = 0;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd0) begin
      vibe_uvm_fail("tc_dll_sm_states", "LinkUp=0", "Disabled",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.link_up = 1; dsm.param_ok = 1; dsm.credit_ok = 1;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    dsm.port_rst = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (dsm.state !== 2'd0) begin
      vibe_uvm_fail("tc_dll_sm_states", "port_rst while LinkUp=1",
                    "Disabled (sample while port_rst held)",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    dsm.port_rst = 0;
    @(posedge clk_vif.clk);
    dsm.link_up = 1;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    dsm.dll_error = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    dsm.dll_error = 0;
    if (dsm.state !== 2'd0) begin
      vibe_uvm_fail("tc_dll_sm_states", "dll_error in Normal", "Disabled",
                    $sformatf("%0d", dsm.state), "u_dsm.st");
      fail = 1;
    end
    unit_done("tc_dll_sm_states");
    phase.drop_objection(this);
  endtask
endclass

class tc_route_lu extends vibe_unit_base;
  `uvm_component_utils(tc_route_lu)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    psel.reset();
    psel.dest = 16'd1; psel.rt = 2'b00;
    @(negedge clk_vif.clk);
    psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    psel.sel_vld = 0;
    if (psel.bitmap !== 4'd0 || psel.drop_g1) begin
      vibe_uvm_fail("tc_route_lu", "lu dest=1 empty table", "bitmap=0 drop_g1=0",
                    $sformatf("bm=%04b g1=%0b", psel.bitmap, psel.drop_g1), "u_rt");
      fail = 1;
    end
    psel.wr_route(16'd1, 4'b1111);
    psel.dest = 16'd1; psel.rt = 2'b00;
    @(negedge clk_vif.clk);
    psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    psel.sel_vld = 0;
    if (psel.bitmap !== 4'b1111) begin
      vibe_uvm_fail("tc_route_lu", "wr dest=1 data=F, lu RT=00", "bitmap=1111",
                    $sformatf("%04b", psel.bitmap), "u_rt.tbl[1]");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    psel.rt = 2'b10; psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (!psel.drop_g1 || psel.bitmap !== 4'd0) begin
      vibe_uvm_fail("tc_route_lu", "RT=10", "drop_g1=1 bitmap=0 (not alias 00)",
                    $sformatf("g1=%0b bm=%04b", psel.drop_g1, psel.bitmap), "u_rt");
      fail = 1;
    end
    psel.sel_vld = 0;
    @(negedge clk_vif.clk);
    psel.rt = 2'b11; psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (!psel.drop_g1) begin
      vibe_uvm_fail("tc_route_lu", "RT=11", "drop_g1", "0", "u_rt");
      fail = 1;
    end
    psel.sel_vld = 0;
    @(negedge clk_vif.clk);
    psel.rt = 2'b01; psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (psel.drop_g1 || psel.bitmap !== 4'b1111) begin
      vibe_uvm_fail("tc_route_lu", "RT=01 after write", "forward bitmap=F",
                    $sformatf("g1=%0b bm=%04b", psel.drop_g1, psel.bitmap), "u_rt");
      fail = 1;
    end
    psel.sel_vld = 0;
    @(negedge clk_vif.clk);
    psel.device_rst = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    psel.device_rst = 0;
    psel.dest = 16'd1; psel.rt = 2'b00; psel.sel_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (psel.bitmap !== 4'd0) begin
      vibe_uvm_fail("tc_route_lu", "device_rst then lu", "table all-0",
                    $sformatf("%04b", psel.bitmap), "u_rt");
      fail = 1;
    end
    unit_done("tc_route_lu");
    phase.drop_objection(this);
  endtask
endclass

class tc_rst_sync extends vibe_unit_base;
  `uvm_component_utils(tc_rst_sync)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    rsyn.rst_n_in = 0;
    repeat (3) @(posedge clk_vif.clk);
    if (rsyn.rst_n_out !== 1'b0) begin
      vibe_uvm_fail("tc_rst_sync", "rst_n_in=0", "rst_n_out=0 async assert",
                    $sformatf("%0b", rsyn.rst_n_out), "u_rsyn");
      fail = 1;
    end
    rsyn.rst_n_in = 1;
    @(posedge clk_vif.clk);
    if (rsyn.rst_n_out !== 1'b0) begin
      vibe_uvm_fail("tc_rst_sync", "deassert, first dest clock", "still 0 (2-FF)",
                    $sformatf("%0b", rsyn.rst_n_out), "u_rsyn");
      fail = 1;
    end
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    if (rsyn.rst_n_out !== 1'b1) begin
      vibe_uvm_fail("tc_rst_sync", "two dest clocks after deassert", "rst_n_out=1",
                    $sformatf("%0b", rsyn.rst_n_out), "u_rsyn");
      fail = 1;
    end
    unit_done("tc_rst_sync");
    phase.drop_objection(this);
  endtask
endclass

class tc_mgmt_byp extends vibe_unit_base;
  `uvm_component_utils(tc_mgmt_byp)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    mbyp.rst_n = 0; mbyp.in_vld = 0; mbyp.out_ready = 0; mbyp.in_data = 512'hA5;
    repeat (3) @(posedge clk_vif.clk);
    mbyp.rst_n = 1;
    @(negedge clk_vif.clk);
    mbyp.in_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    mbyp.in_vld = 0;
    @(posedge clk_vif.clk);
    if (!mbyp.out_vld || mbyp.out_data !== 512'hA5) begin
      vibe_uvm_fail("tc_mgmt_byp", "one 512b write, out_ready=0",
                    "out_vld=1 data=A5 (held, not xbar)",
                    $sformatf("vld=%0b data=%h", mbyp.out_vld, mbyp.out_data), "u_mbyp");
      fail = 1;
    end
    mbyp.out_ready = 1;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    if (mbyp.out_vld) begin
      vibe_uvm_fail("tc_mgmt_byp", "out_ready after one beat", "empty",
                    "still vld", "u_mbyp");
      fail = 1;
    end
    unit_done("tc_mgmt_byp");
    phase.drop_objection(this);
  endtask
endclass

class tc_fecn_mark extends vibe_unit_base;
  `uvm_component_utils(tc_fecn_mark)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    fecn.cci_in = 16'd0; fecn.voq_occ = 6'd0;
    #1;
    if (fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "empty VOQ mode 0", "not marked", "1", "u_fecn");
      fail = 1;
    end
    fecn.cci_in = {3'b100, 11'd0, 2'b01};
    fecn.voq_occ = 6'd24;
    #1;
    if (!fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "Mode=100 FECN=01 occ=24", "marked (local worse)",
                    $sformatf("marked=0 cci_out=%h", fecn.cci_out), "u_fecn");
      fail = 1;
    end
    fecn.cci_in = {3'b010, 11'd0, 2'b01};
    fecn.voq_occ = 6'd24;
    #1;
    if (!fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "Mode=010 FECN=01 occ=24", "marked", "0", "u_fecn");
      fail = 1;
    end
    fecn.cci_in = {3'b100, 11'd0, 2'b00};
    #1;
    if (fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "FECN=00", "not marked", "1", "u_fecn");
      fail = 1;
    end
    fecn.cci_in = {3'b100, 11'd0, 2'b11};
    #1;
    if (fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "FECN=11 already severe", "not marked (not worse)",
                    "1", "u_fecn");
      fail = 1;
    end
    fecn.cci_in = {3'b000, 11'd0, 2'b01};
    #1;
    if (fecn.marked) begin
      vibe_uvm_fail("tc_fecn_mark", "Mode=000", "not marked", "1", "u_fecn");
      fail = 1;
    end
    unit_done("tc_fecn_mark");
    phase.drop_objection(this);
  endtask
endclass
