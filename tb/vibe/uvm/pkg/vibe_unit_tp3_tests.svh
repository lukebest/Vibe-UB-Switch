class tc_dll_rx_errflag extends vibe_unit_base;
  `uvm_component_utils(tc_dll_rx_errflag)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    drx.rst_n = 0; drx.port_rst = 0; drx.link_up = 1; drx.fec_fail = 0;
    drx.pcs_dll_vld = 0; drx.pcs_dll_data = 640'd0; drx.dll_nw_ready = 0;
    repeat (4) @(posedge clk_vif.clk);
    drx.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    drx.pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    drx.pcs_dll_vld = 1;
    drx.dll_nw_ready = 0;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    drx.pcs_dll_vld = 0;
    drx.link_up = 0;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (!drx.dll_nw_vld) begin
      vibe_uvm_fail("tc_dll_rx_errflag", "drop link_up on negedge after have",
                    "dll_nw_vld + pad0/ERROR_FLAG",
                    $sformatf("dll_nw_vld=0 have=%0b", drx.have), "u_drx");
      fail = 1;
    end
    drx.link_up = 1;
    drx.dll_nw_ready = 1;
    unit_done("tc_dll_rx_errflag");
    phase.drop_objection(this);
  endtask
endclass

class tc_fec_fail_gbn extends vibe_unit_base;
  `uvm_component_utils(tc_fec_fail_gbn)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    drx.rst_n = 0; drx.port_rst = 0; drx.link_up = 1; drx.fec_fail = 0;
    drx.pcs_dll_vld = 0; drx.pcs_dll_data = 0; drx.dll_nw_ready = 1;
    repeat (4) @(posedge clk_vif.clk);
    drx.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    if (drx.start_retry !== 1'b0) begin
      vibe_uvm_fail("tc_fec_fail_gbn", "reset fec_fail=0", "start_retry=0",
                    $sformatf("%0b", drx.start_retry), "u_drx.start_retry");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    drx.fec_fail = 1;
    #0;
    if (drx.start_retry !== 1'b1) begin
      vibe_uvm_fail("tc_fec_fail_gbn", "pulse fec_fail=1 (RS decode fail)",
                    "start_retry=1 (Go-Back-N; AS-0.1 §6/§12)",
                    $sformatf("start_retry=%0b bcrc_fail=%0b", drx.start_retry, drx.bcrc_fail),
                    "u_drx.start_retry");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    drx.fec_fail = 0;
    #0;
    if (drx.start_retry !== 1'b0) begin
      vibe_uvm_fail("tc_fec_fail_gbn", "fec_fail deassert",
                    "start_retry=0 (combo follows fec_fail)",
                    $sformatf("%0b", drx.start_retry), "u_drx.start_retry");
      fail = 1;
    end
    unit_done("tc_fec_fail_gbn");
    phase.drop_objection(this);
  endtask
endclass

class tc_cfg0_term_not_fabric extends vibe_unit_base;
  `uvm_component_utils(tc_cfg0_term_not_fabric)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  bit saw_cfg0, saw_nw;
  task send_beat(bit [3:0] cfg);
    @(negedge clk_vif.clk);
    drx.pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        cfg, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    drx.pcs_dll_vld = 1'b1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    drx.pcs_dll_vld = 1'b0;
  endtask
  task run_phase(uvm_phase phase);
    int k, w;
    phase.raise_objection(this);
    fail = 0;
    saw_cfg0 = 0; saw_nw = 0;
    drx.rst_n = 0; drx.port_rst = 0; drx.link_up = 1; drx.fec_fail = 0;
    drx.pcs_dll_vld = 0; drx.pcs_dll_data = 0; drx.dll_nw_ready = 1;
    fork
      forever begin
        @(posedge clk_vif.clk);
        if (drx.cfg0_hit) saw_cfg0 = 1;
        if (drx.dll_nw_vld) saw_nw = 1;
      end
    join_none
    repeat (4) @(posedge clk_vif.clk);
    drx.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    send_beat(4'd0);
    repeat (6) @(posedge clk_vif.clk);
    if (!saw_cfg0) begin
      vibe_uvm_fail("tc_cfg0_term_not_fabric", "CFG=0 beat on dll_rx pcs_*",
                    "cfg0_hit pulse (terminate in DLL)", "no cfg0_hit", "u_drx.cfg0_hit");
      fail = 1;
    end
    if (saw_nw) begin
      vibe_uvm_fail("tc_cfg0_term_not_fabric", "CFG0 beat",
                    "dll_nw_vld never rises (does not enter fabric)",
                    "dll_nw_vld pulsed", "u_drx.dll_nw_vld");
      fail = 1;
    end
    saw_nw = 0;
    send_beat(4'd3);
    repeat (8) @(posedge clk_vif.clk);
    if (!saw_nw) begin
      vibe_uvm_fail("tc_cfg0_term_not_fabric", "CFG=3 beat (must reach NW/fabric)",
                    "dll_nw_vld pulse", "no dll_nw_vld", "u_drx.have");
      fail = 1;
    end
    drx.dll_nw_ready = 1;
    for (k = 0; k < 12; k++) begin
      w = 0;
      @(negedge clk_vif.clk);
      while (!drx.pcs_dll_ready && w < 40) begin @(posedge clk_vif.clk); w++; end
      drx.pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
          4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
          16'd0, 8'd0, 3'd0, 8'd0));
      drx.pcs_dll_vld = 1;
      @(posedge clk_vif.clk);
      @(negedge clk_vif.clk);
      drx.pcs_dll_vld = 0;
      repeat (6) @(posedge clk_vif.clk);
    end
    if (!drx.rx_ovf) begin
      vibe_uvm_fail("tc_cfg0_term_not_fabric", "12 ready-gated CFG3 beats, RXBUF=32",
                    "rx_ovf (wptr-rptr >= 32)", "rx_ovf=0", "u_drx.rx_ovf");
      fail = 1;
    end
    drx.fec_fail = 1;
    @(posedge clk_vif.clk);
    if (!drx.start_retry) begin
      vibe_uvm_fail("tc_cfg0_term_not_fabric", "fec_fail", "start_retry=1", "0", "u_drx");
      fail = 1;
    end
    drx.fec_fail = 0;
    disable fork;
    unit_done("tc_cfg0_term_not_fabric");
    phase.drop_objection(this);
  endtask
endclass

class tc_dll extends vibe_unit_base;
  `uvm_component_utils(tc_dll)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    dllw.rst_n = 0; dllw.port_rst = 0; dllw.device_rst = 0; dllw.link_up = 0;
    dllw.fec_fail = 0; dllw.nw_dll_vld = 0; dllw.dll_nw_ready = 1;
    dllw.dll_pcs_ready = 1; dllw.pcs_dll_vld = 0;
    dllw.nw_dll_data = 0; dllw.pcs_dll_data = 0;
    repeat (3) @(posedge clk_vif.clk);
    dllw.rst_n = 1;
    @(posedge clk_vif.clk);
    if (!dllw.disabled) begin
      vibe_uvm_fail("tc_dll", "LinkUp=0", "disabled", "0", "u_dll");
      fail = 1;
    end
    dllw.link_up = 1;
    repeat (8) @(posedge clk_vif.clk);
    dllw.nw_dll_data = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    for (i = 0; i < 8; i++) begin
      @(negedge clk_vif.clk);
      dllw.nw_dll_vld = dllw.nw_dll_ready;
      @(posedge clk_vif.clk);
    end
    dllw.nw_dll_vld = 0;
    dllw.pcs_dll_data = vibe_tb_mk_pcs_beat(vibe_tb_mk_flit(
        4'd0, 2'b00, 4'd0, 16'h1, 16'h2, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    @(negedge clk_vif.clk);
    dllw.pcs_dll_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    dllw.pcs_dll_vld = 0;
    dllw.fec_fail = 1;
    @(posedge clk_vif.clk);
    dllw.fec_fail = 0;
    dllw.port_rst = 1;
    @(posedge clk_vif.clk);
    dllw.port_rst = 0;
    unit_done("tc_dll");
    phase.drop_objection(this);
  endtask
endclass

class tc_lmsm_walk extends vibe_unit_base;
  `uvm_component_utils(tc_lmsm_walk)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task hard_rst();
    lmsm.rst_n = 0; lmsm.port_rst = 0; lmsm.lmsm_go = 0; lmsm.am_locked = 0;
    lmsm.lid_bad = 0; lmsm.lane0_fail = 0; lmsm.eq_negotiated = 0; lmsm.retrain_req = 0;
    repeat (2) @(posedge clk_vif.clk);
    lmsm.rst_n = 1;
    @(posedge clk_vif.clk);
  endtask
  task chk(bit [4:0] exp, int tag);
    @(negedge clk_vif.clk);
    if (lmsm.state !== exp) begin
      vibe_uvm_fail("tc_lmsm_walk", $sformatf("tag=%0d", tag),
                    $sformatf("%0d", exp), $sformatf("%0d", lmsm.state), "u_lmsm.st");
      fail = 1;
    end
  endtask
  task zap_tmr();
    lmsm.zap_tmr = 1;
  endtask
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    hard_rst();
    if (lmsm.width_fail !== 1'b0) begin
      vibe_uvm_fail("tc_lmsm_walk", "reset", "width_fail=0 (x4-only; no Probe)",
                    "1", "u_lmsm");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    chk(5'd1, 1);
    zap_tmr();
    @(posedge clk_vif.clk);
    lmsm.zap_tmr = 0;
    chk(5'd0, 2);
    @(negedge clk_vif.clk);
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(negedge clk_vif.clk);
    lmsm.am_locked = 4'b1111;
    @(posedge clk_vif.clk);
    chk(5'd2, 3);
    @(posedge clk_vif.clk);
    chk(5'd3, 4);
    @(posedge clk_vif.clk);
    chk(5'd4, 5);
    @(posedge clk_vif.clk);
    chk(5'd5, 6);
    @(posedge clk_vif.clk);
    chk(5'd8, 7);
    if (!lmsm.link_up || !lmsm.sdf_period) begin
      vibe_uvm_fail("tc_lmsm_walk", "NULL", "link_up sdf_period",
                    $sformatf("up=%0b sdf=%0b", lmsm.link_up, lmsm.sdf_period), "u_lmsm");
      fail = 1;
    end
    repeat (10) @(posedge clk_vif.clk);
    chk(5'd9, 8);
    if (!lmsm.link_ready) begin
      vibe_uvm_fail("tc_lmsm_walk", "ACTIVE", "link_ready", "0", "u_lmsm");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    lmsm.retrain_req = 1;
    @(posedge clk_vif.clk);
    lmsm.retrain_req = 0;
    chk(5'd10, 9);
    @(posedge clk_vif.clk);
    chk(5'd11, 10);
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (lmsm.state !== 5'd1 && lmsm.state !== 5'd2) begin
      vibe_uvm_fail("tc_lmsm_walk", "RTR_C x4_ok tag=11", "Disc.A or Disc.C",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    hard_rst();
    @(negedge clk_vif.clk);
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(negedge clk_vif.clk);
    lmsm.am_locked = 4'b1111;
    lmsm.eq_negotiated = 1;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    chk(5'd6, 15);
    zap_tmr();
    @(posedge clk_vif.clk);
    lmsm.zap_tmr = 0;
    chk(5'd7, 16);
    zap_tmr();
    @(posedge clk_vif.clk);
    lmsm.zap_tmr = 0;
    chk(5'd8, 17);
    lmsm.eq_negotiated = 0;
    hard_rst();
    @(negedge clk_vif.clk);
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(negedge clk_vif.clk);
    lmsm.am_locked = 4'b1111;
    repeat (8) @(posedge clk_vif.clk);
    repeat (10) @(posedge clk_vif.clk);
    chk(5'd9, 19);
    @(negedge clk_vif.clk);
    lmsm.lane0_fail = 1;
    @(posedge clk_vif.clk);
    lmsm.lane0_fail = 0;
    chk(5'd10, 20);
    zap_tmr();
    @(posedge clk_vif.clk);
    lmsm.zap_tmr = 0;
    chk(5'd0, 21);
    unit_done("tc_lmsm_walk");
    phase.drop_objection(this);
  endtask
endclass

class tc_lmsm_vlock extends vibe_unit_base;
  `uvm_component_utils(tc_lmsm_vlock)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task hard_rst();
    lmsm.rst_n = 0; lmsm.port_rst = 0; lmsm.lmsm_go = 0; lmsm.am_locked = 0;
    lmsm.lid_bad = 0; lmsm.lane0_fail = 0; lmsm.eq_negotiated = 0; lmsm.retrain_req = 0;
    repeat (4) @(posedge clk_vif.clk);
    lmsm.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
  endtask
  task go_disc();
    lmsm.lmsm_go = 1;
    @(posedge clk_vif.clk);
    lmsm.lmsm_go = 0;
    @(posedge clk_vif.clk);
  endtask
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    hard_rst();
    go_disc();
    if (lmsm.state !== 5'd1) begin
      vibe_uvm_fail("tc_lmsm_vlock", "lmsm_go + 2 posedge", "Disc.A (1)",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    lmsm.am_locked = 4'b1111;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd2 && lmsm.state !== 5'd3) begin
      vibe_uvm_fail("tc_lmsm_vlock", "am_locked=1111", "Disc.C or CFG_A",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    repeat (6) @(posedge clk_vif.clk);
    repeat (12) @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd9) begin
      vibe_uvm_fail("tc_lmsm_vlock", "lock walk", "ACTIVE (9)",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    lmsm.retrain_req = 1;
    @(posedge clk_vif.clk);
    lmsm.retrain_req = 0;
    @(posedge clk_vif.clk);
    if (lmsm.state < 5'd10) begin
      vibe_uvm_fail("tc_lmsm_vlock", "retrain_req", "RTR_A/C",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    hard_rst();
    go_disc();
    lmsm.am_locked = 4'b1111;
    lmsm.eq_negotiated = 1;
    repeat (8) @(posedge clk_vif.clk);
    if (lmsm.state !== 5'd6 && lmsm.state !== 5'd7 && lmsm.state !== 5'd8) begin
      vibe_uvm_fail("tc_lmsm_vlock", "eq_negotiated", "EQ_P/EQ_A/NULL",
                    $sformatf("%0d", lmsm.state), "u_lmsm");
      fail = 1;
    end
    unit_done("tc_lmsm_vlock");
    phase.drop_objection(this);
  endtask
endclass
