class tc_pcs_cw2beat extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_cw2beat)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int n;
    phase.raise_objection(this);
    fail = 0; n = 0;
    cw2.rst_n = 0; cw2.cw_vld = 0; cw2.beat_ready = 1;
    cw2.cw_data = {512'hA, 512'hB};
    repeat (3) @(posedge clk_vif.clk);
    cw2.rst_n = 1;
    @(negedge clk_vif.clk);
    cw2.cw_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    cw2.cw_vld = 0;
    repeat (6) begin
      @(posedge clk_vif.clk);
      if (cw2.beat_vld) n++;
    end
    if (n < 2) begin
      vibe_uvm_fail("tc_pcs_cw2beat", "one 1024b cw", "two 512b beats",
                    $sformatf("%0d", n), "u_cw2");
      fail = 1;
    end
    unit_done("tc_pcs_cw2beat");
    phase.drop_objection(this);
  endtask
endclass

class tc_pcs_fec_dual_enc extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_fec_dual_enc)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int saw_a, saw_b;
    phase.raise_objection(this);
    fail = 0; saw_a = 0; saw_b = 0;
    fec.rst_n = 0; fec.fec_mode = VIBE_FEC_T4; fec.win_vld = 0; fec.cw_ready = 1;
    fec.win_data = 960'h3;
    fork
      forever begin
        @(posedge clk_vif.clk);
        if (fec.enc_a_start) saw_a = 1;
        if (fec.enc_b_start) saw_b = 1;
      end
    join_none
    repeat (3) @(posedge clk_vif.clk);
    fec.rst_n = 1;
    @(negedge clk_vif.clk);
    fec.win_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    fec.win_vld = 0;
    repeat (280) @(posedge clk_vif.clk);
    if (!saw_a || !saw_b) begin
      vibe_uvm_fail("tc_pcs_fec_dual_enc", "fec_mode=T4 two windows",
                    "enc_a_start and enc_b_start (dual interleave)",
                    $sformatf("a=%0d b=%0d", saw_a, saw_b), "u_fec");
      fail = 1;
    end
    disable fork;
    unit_done("tc_pcs_fec_dual_enc");
    phase.drop_objection(this);
  endtask
endclass

class tc_pcs_fec_t2 extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_fec_t2)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int saw_a, saw_b;
    phase.raise_objection(this);
    fail = 0; saw_a = 0; saw_b = 0;
    fec.rst_n = 0; fec.fec_mode = VIBE_FEC_T2; fec.win_vld = 0; fec.cw_ready = 1;
    fec.win_data = 960'h5;
    fork
      forever begin
        @(posedge clk_vif.clk);
        if (fec.enc_a_start) saw_a = 1;
        if (fec.enc_b_start) saw_b = 1;
      end
    join_none
    repeat (3) @(posedge clk_vif.clk);
    fec.rst_n = 1;
    @(negedge clk_vif.clk);
    fec.win_vld = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    fec.win_data = 960'h6;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    fec.win_vld = 0;
    repeat (200) @(posedge clk_vif.clk);
    if (!saw_a || !saw_b) begin
      vibe_uvm_fail("tc_pcs_fec_t2", "fec_mode=T2 two 960b windows",
                    "enc_a_start and enc_b_start (not bypass)",
                    $sformatf("a=%0d b=%0d", saw_a, saw_b), "u_fec");
      fail = 1;
    end
    disable fork;
    unit_done("tc_pcs_fec_t2");
    phase.drop_objection(this);
  endtask
endclass

class tc_pcs_fec_bypass extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_fec_bypass)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int ncw;
    phase.raise_objection(this);
    fail = 0; ncw = 0;
    fec.rst_n = 0; fec.fec_mode = VIBE_FEC_BYPASS; fec.win_vld = 0; fec.cw_ready = 1;
    fec.win_data = 960'h1;
    repeat (3) @(posedge clk_vif.clk);
    fec.rst_n = 1;
    @(negedge clk_vif.clk);
    fec.win_vld = 1; fec.win_data = {960{1'b1}};
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    fec.win_data = 960'hA;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    fec.win_vld = 0;
    repeat (16) begin
      @(posedge clk_vif.clk);
      if (fec.cw_vld) ncw++;
    end
    if (ncw < 2) begin
      vibe_uvm_fail("tc_pcs_fec_bypass", "fec_mode=bypass two 960b windows",
                    "two 1024b cw beats (align, no RS)",
                    $sformatf("%0d cw_vld", ncw), "u_fec.bypass");
      fail = 1;
    end
    unit_done("tc_pcs_fec_bypass");
    phase.drop_objection(this);
  endtask
endclass

class tc_pcs_scramble extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_scramble)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    scr.rst_n = 0; scr.lane_id = 0; scr.seed_load = 0; scr.en = 0;
    scr.in_vld = 0; scr.in_data = 160'h55;
    repeat (3) @(posedge clk_vif.clk);
    scr.rst_n = 1;
    @(negedge clk_vif.clk);
    scr.in_vld = 1; scr.en = 0;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    if (scr.out_data !== 160'h55) begin
      vibe_uvm_fail("tc_pcs_scramble", "en=0 in=55", "pass-through (AMCTL/EEIB)",
                    $sformatf("%h", scr.out_data), "u_scr");
      fail = 1;
    end
    scr.seed_load = 1;
    @(posedge clk_vif.clk);
    scr.seed_load = 0; scr.en = 1; scr.in_data = 160'h0;
    @(posedge clk_vif.clk);
    @(posedge clk_vif.clk);
    if (scr.out_data === 160'h0) begin
      vibe_uvm_fail("tc_pcs_scramble", "en=1 in=0 after seed", "scrambled nonzero mask",
                    "0", "u_scr");
      fail = 1;
    end
    unit_done("tc_pcs_scramble");
    phase.drop_objection(this);
  endtask
endclass

class tc_pcs_amctl extends vibe_unit_base;
  `uvm_component_utils(tc_pcs_amctl)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    amc.rst_n = 0; amc.link_up = 1; amc.sdf_period = 1; amc.lane_id = 0; amc.req = 0;
    repeat (3) @(posedge clk_vif.clk);
    amc.rst_n = 1;
    amc.req = 1;
    repeat (4) @(posedge clk_vif.clk);
    if (amc.amctl_40B === 320'd0) begin
      vibe_uvm_fail("tc_pcs_amctl", "link_up sdf_period lane0 req",
                    "nonzero 40-symbol AMCTL (eBCH-16)", "0", "u_amc.amctl_40B");
      fail = 1;
    end
    amc.lane_id = 2'd1; #1;
    amc.lane_id = 2'd2; #1;
    amc.lane_id = 2'd3; #1;
    if (amc.amctl_40B === 320'd0) begin
      vibe_uvm_fail("tc_pcs_amctl", "lane_id=3", "nonzero AMCTL", "0", "u_amc");
      fail = 1;
    end
    amc.link_up = 0; #1;
    if (amc.ack) begin
      vibe_uvm_fail("tc_pcs_amctl", "req=1 link_up=0", "ack=0", "1", "u_amc");
      fail = 1;
    end
    unit_done("tc_pcs_amctl");
    phase.drop_objection(this);
  endtask
endclass

class tc_pma_512b_slice extends vibe_unit_base;
  `uvm_component_utils(tc_pma_512b_slice)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    pma.t0 = 128'h11; pma.t1 = 128'h22; pma.t2 = 128'h33; pma.t3 = 128'h44;
    pma.afifo_pma_lane_vld = 0; pma.pma_pcs_rxdata = 512'd0;
    repeat (2) @(posedge pma.txclk);
    pma.afifo_pma_lane_vld = 1;
    @(posedge pma.txclk);
    @(posedge pma.txclk);
    if (pma.pcs_pma_txdata[127:0] !== 128'h11 ||
        pma.pcs_pma_txdata[255:128] !== 128'h22 ||
        pma.pcs_pma_txdata[383:256] !== 128'h33 ||
        pma.pcs_pma_txdata[511:384] !== 128'h44) begin
      vibe_uvm_fail("tc_pma_512b_slice", "tx lanes 11/22/33/44 vld",
                    "pcs_pma_txdata slices lane0..3",
                    $sformatf("%h", pma.pcs_pma_txdata), "u_pma");
      fail = 1;
    end
    pma.pma_pcs_rxdata = {128'hAA, 128'hBB, 128'hCC, 128'hDD};
    @(posedge pma.rxclk);
    @(posedge pma.rxclk);
    if (pma.r0 !== 128'hDD || pma.r3 !== 128'hAA) begin
      vibe_uvm_fail("tc_pma_512b_slice", "pma_pcs_rxdata {AA,BB,CC,DD}",
                    "lane0=DD lane3=AA",
                    $sformatf("r0=%h r3=%h", pma.r0, pma.r3), "u_pma");
      fail = 1;
    end
    pma.afifo_pma_lane_vld = 0;
    @(posedge pma.txclk);
    unit_done("tc_pma_512b_slice");
    phase.drop_objection(this);
  endtask
endclass

class tc_pma_922mhz extends vibe_unit_base;
  `uvm_component_utils(tc_pma_922mhz)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int edges;
    time t0, t1;
    phase.raise_objection(this);
    fail = 0; edges = 0;
    pma.t0 = 128'hA0; pma.t1 = 128'hA1; pma.t2 = 128'hA2; pma.t3 = 128'hA3;
    pma.afifo_pma_lane_vld = 1; pma.pma_pcs_rxdata = 0;
    @(posedge pma.txclk);
    t0 = $time;
    @(posedge pma.txclk);
    t1 = $time;
    repeat (6) begin
      @(posedge pma.txclk);
      edges++;
    end
    edges += 2;
    if (pma.pcs_pma_txdata[127:0] !== 128'hA0 ||
        pma.pcs_pma_txdata[511:384] !== 128'hA3) begin
      vibe_uvm_fail("tc_pma_922mhz", "512b PMA at T=1085ps (~922 MHz), lanes A0..A3",
                    "packed {A3,A2,A1,A0}", $sformatf("%h", pma.pcs_pma_txdata), "u_pma");
      fail = 1;
    end
    if (edges < 8) begin
      vibe_uvm_fail("tc_pma_922mhz", "8 posedges at 922 MHz period",
                    "clocks advance", $sformatf("edges=%0d", edges), "pma.txclk");
      fail = 1;
    end
    if ((t1 - t0) > 2ns) begin
      vibe_uvm_fail("tc_pma_922mhz", "txclk period",
                    "~1084ps (922 MHz), not clk_fab 2ns",
                    $sformatf("%0t", t1 - t0), "pma.txclk");
      fail = 1;
    end
    unit_done("tc_pma_922mhz");
    phase.drop_objection(this);
  endtask
endclass

class tc_phy_u26_chain extends vibe_unit_base;
  `uvm_component_utils(tc_phy_u26_chain)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int n128, n160, sent;
    phase.raise_objection(this);
    fail = 0; n128 = 0; n160 = 0; sent = 0;
    gtx.rst_n = 0; gtx.in_vld = 0; gtx.out_ready = 1; gtx.in_data = 0;
    grx.rst_n = 0; grx.in_vld = 0; grx.out_ready = 1; grx.in_data = 0;
    pma.t0 = 0; pma.t1 = 0; pma.t2 = 0; pma.t3 = 0;
    pma.afifo_pma_lane_vld = 0; pma.pma_pcs_rxdata = 0;
    fork
      forever begin
        @(posedge clk_vif.clk);
        if (gtx.out_vld && gtx.out_ready) n128++;
        if (grx.out_vld && grx.out_ready) n160++;
      end
    join_none
    repeat (3) @(posedge clk_vif.clk);
    gtx.rst_n = 1; grx.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    while (sent < 4) begin
      @(negedge clk_vif.clk);
      if (gtx.in_ready) begin
        gtx.in_data = {40'hA, 120'h1};
        gtx.in_vld = 1;
        sent++;
      end else
        gtx.in_vld = 0;
      @(posedge clk_vif.clk);
    end
    @(negedge clk_vif.clk);
    gtx.in_vld = 0;
    repeat (16) @(posedge clk_vif.clk);
    pma.t0 = 128'h11; pma.t1 = 128'h22; pma.t2 = 128'h33; pma.t3 = 128'h44;
    pma.afifo_pma_lane_vld = 1;
    @(posedge pma.txclk);
    @(posedge pma.txclk);
    pma.pma_pcs_rxdata = pma.pcs_pma_txdata;
    @(posedge pma.rxclk);
    @(posedge pma.rxclk);
    if (n128 < 5) begin
      vibe_uvm_fail("tc_phy_u26_chain", "4x160 into TX gear",
                    ">=5 x128 beats (U26 4*160=5*128)",
                    $sformatf("%0d", n128), "u_gtx");
      fail = 1;
    end
    if (pma.pcs_pma_txdata[127:0] !== 128'h11 || pma.r0 !== 128'h11) begin
      vibe_uvm_fail("tc_phy_u26_chain",
                    "PMA lanes 11/22/33/44 looped pma_pcs_rxdata=pcs_pma_txdata",
                    "[127:0]=lane0=11 both TX pack and RX slice",
                    $sformatf("tx=%h r0=%h", pma.pcs_pma_txdata[127:0], pma.r0), "u_pma");
      fail = 1;
    end
    sent = 0;
    while (sent < 5) begin
      @(negedge clk_vif.clk);
      if (grx.in_ready) begin
        grx.in_data = 128'h55;
        grx.in_vld = 1;
        sent++;
      end else
        grx.in_vld = 0;
      @(posedge clk_vif.clk);
    end
    @(negedge clk_vif.clk);
    grx.in_vld = 0;
    repeat (16) @(posedge clk_vif.clk);
    if (n160 < 4) begin
      vibe_uvm_fail("tc_phy_u26_chain", "5x128 into RX gear", ">=4 x160 beats",
                    $sformatf("%0d", n160), "u_grx");
      fail = 1;
    end
    disable fork;
    unit_done("tc_phy_u26_chain");
    phase.drop_objection(this);
  endtask
endclass

class tc_phy_nw_dll_512b extends vibe_unit_base;
  `uvm_component_utils(tc_phy_nw_dll_512b)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    logic [511:0] golden_tx, golden_rx;
    int nw_w, dll_w, rx_w, dll_rx_w;
    phase.raise_objection(this);
    fail = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    golden_rx = vibe_tb_nw512_golden_rx();
    nwa.rst_n = 1; nwa.link_ready = 1;
    nwa.fab_nw_data = 0; nwa.mgmt_nw_data = 0; nwa.dll_nw_data = 0;
    nwa.fab_nw_vld = 0; nwa.mgmt_nw_vld = 0; nwa.nw_dll_ready = 1;
    nwa.dll_nw_vld = 0; nwa.nw_fab_ready = 1;
    #1;
    nw_w = $bits(nwa.fab_nw_data);
    dll_w = $bits(nwa.nw_dll_data);
    rx_w = $bits(nwa.nw_fab_data);
    dll_rx_w = $bits(nwa.dll_nw_data);
    if (nw_w !== 512 || rx_w !== 512) begin
      vibe_uvm_fail("tc_phy_nw_dll_512b",
                    "FS-0.2.7 Overlay B — NW↔DLL data[511:0] @1.25GHz",
                    "$bits(fab_nw_data)=512 $bits(nw_fab_data)=512",
                    $sformatf("NW fab=%0d fab_rx=%0d", nw_w, rx_w), "u_nwa");
      fail = 1;
    end
    nwa.link_ready = 1; nwa.nw_dll_ready = 1; nwa.mgmt_nw_vld = 0;
    nwa.fab_nw_data = golden_tx;
    nwa.fab_nw_vld = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, nwa.nw_dll_data) ||
        !nwa.fab_nw_ready || !nwa.nw_dll_vld) begin
      vibe_tb_nw512_fail_print("tc_phy_nw_dll_512b",
          "TX NW→DLL: fab_nw_data=GOLDEN_TX vld/ready",
          golden_tx, dll_w, nwa.nw_dll_data, "u_nwa.nw_dll_data");
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_tx, nwa.nw_dll_data)) begin
      vibe_tb_nw512_sop_lph_print("tc_phy_nw_dll_512b",
          "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
          golden_tx, nwa.nw_dll_data, "u_nwa.nw_dll_data[511:352]");
      fail = 1;
    end
    nwa.fab_nw_vld = 0;
    nwa.dll_nw_data = golden_rx;
    nwa.dll_nw_vld = 1; nwa.nw_fab_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, nwa.nw_fab_data) || !nwa.nw_fab_vld) begin
      vibe_tb_nw512_fail_print("tc_phy_nw_dll_512b",
          "RX DLL→NW: dll_nw_data=GOLDEN_RX vld/ready",
          golden_rx, rx_w, nwa.nw_fab_data, "u_nwa.nw_fab_data");
      fail = 1;
    end else if (vibe_tb_nw512_sop_lph_fail(golden_rx, nwa.nw_fab_data)) begin
      vibe_tb_nw512_sop_lph_print("tc_phy_nw_dll_512b",
          "RX SOP LPH GOLDEN_RX[511:352] vs DUT[511:352]",
          golden_rx, nwa.nw_fab_data, "u_nwa.nw_fab_data[511:352]");
      fail = 1;
    end
    nwa.dll_nw_vld = 0;
    if (!fail) begin
      nwa.link_ready = 0; nwa.fab_nw_vld = 1; #1;
      if (nwa.fab_nw_ready || nwa.nw_dll_vld) begin
        vibe_uvm_fail("tc_phy_nw_dll_512b", "link_ready=0 fab_nw_vld=1",
                      "ready=0 vld=0",
                      $sformatf("rdy=%0b vld=%0b", nwa.fab_nw_ready, nwa.nw_dll_vld),
                      "u_nwa.fab_nw_ready");
        fail = 1;
      end
    end
    unit_done("tc_phy_nw_dll_512b");
    phase.drop_objection(this);
  endtask
endclass

class tc_nw_adapt_linkready extends vibe_unit_base;
  `uvm_component_utils(tc_nw_adapt_linkready)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    logic [511:0] golden_tx, golden_rx;
    int nw_w, dll_w, rx_w;
    phase.raise_objection(this);
    fail = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    golden_rx = vibe_tb_nw512_golden_rx();
    nwa.rst_n = 1; nwa.link_ready = 0;
    nw_w = $bits(nwa.fab_nw_data);
    dll_w = $bits(nwa.nw_dll_data);
    rx_w = $bits(nwa.nw_fab_data);
    if (nw_w !== 512) begin
      vibe_uvm_fail("tc_nw_adapt_linkready", "FS-0.2.7 Overlay B NW↔DLL data[511:0]",
                    "$bits(fab_nw_data)=512", $sformatf("%0d", nw_w), "u_nwa");
      fail = 1;
    end
    nwa.fab_nw_data = golden_tx; nwa.mgmt_nw_data = 0; nwa.dll_nw_data = golden_rx;
    nwa.fab_nw_vld = 1; nwa.mgmt_nw_vld = 0; nwa.nw_dll_ready = 1;
    nwa.dll_nw_vld = 1; nwa.nw_fab_ready = 1;
    #1;
    if (nwa.fab_nw_ready || nwa.nw_dll_vld) begin
      vibe_uvm_fail("tc_nw_adapt_linkready", "link_ready=0 fab_nw_vld GOLDEN_TX",
                    "fab_nw_ready=0 nw_dll_vld=0",
                    $sformatf("rdy=%0b vld=%0b", nwa.fab_nw_ready, nwa.nw_dll_vld),
                    "u_nwa.fab_nw_ready");
      fail = 1;
    end
    nwa.link_ready = 1;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, nwa.nw_dll_data) || !nwa.nw_dll_vld) begin
      vibe_tb_nw512_fail_print("tc_nw_adapt_linkready",
          "TX NW→DLL link_ready=1 fab only GOLDEN_TX",
          golden_tx, dll_w, nwa.nw_dll_data, "u_nwa.nw_dll_data");
      fail = 1;
    end
    if (vibe_tb_nw512_vec_fail(rx_w, golden_rx, nwa.nw_fab_data) || !nwa.nw_fab_vld) begin
      vibe_tb_nw512_fail_print("tc_nw_adapt_linkready",
          "RX DLL→NW dll_rx=GOLDEN_RX",
          golden_rx, rx_w, nwa.nw_fab_data, "u_nwa.nw_fab_data");
      fail = 1;
    end
    nwa.mgmt_nw_vld = 1;
    nwa.mgmt_nw_data = golden_rx;
    #1;
    if (vibe_tb_nw512_vec_fail(dll_w, golden_rx, nwa.nw_dll_data) || nwa.fab_nw_ready) begin
      vibe_tb_nw512_fail_print("tc_nw_adapt_linkready",
          "mgmt GOLDEN_RX priority over fab GOLDEN_TX",
          golden_rx, dll_w, nwa.nw_dll_data, "u_nwa.nw_dll_data");
      fail = 1;
    end
    unit_done("tc_nw_adapt_linkready");
    phase.drop_objection(this);
  endtask
endclass

class tc_xbar_unit extends vibe_unit_base;
  `uvm_component_utils(tc_xbar_unit)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    xbar.rst_n = 0; xbar.status_up = 4'b1111;
    xbar.in_vld = 0; xbar.in_sop = 0; xbar.in_eop = 0; xbar.out_ready = 4'b1111;
    for (i = 0; i < 4; i++) begin
      xbar.in_data[i] = 512'd0;
      xbar.in_dst[i] = 2'd0;
    end
    repeat (3) @(posedge clk_vif.clk);
    xbar.rst_n = 1;
    repeat (2) @(posedge clk_vif.clk);
    xbar.in_data[0] = {160'hA, 352'd0};
    xbar.in_dst[0] = 2'd1;
    xbar.in_vld[0] = 1; xbar.in_sop[0] = 1; xbar.in_eop[0] = 1;
    #0;
    @(posedge clk_vif.clk);
    if (!(xbar.out_vld[1] && xbar.in_ready[0])) begin
      vibe_uvm_fail("tc_xbar_unit", "1-beat in0 dest=1, all ready/up",
                    "out_vld[1]=1 in_ready[0]=1",
                    $sformatf("out_vld=%04b in_ready=%04b", xbar.out_vld, xbar.in_ready),
                    "u_xbar");
      fail = 1;
    end
    xbar.in_vld = 0; xbar.in_sop = 0; xbar.in_eop = 0;
    repeat (2) @(posedge clk_vif.clk);
    xbar.status_up[0] = 1'b0;
    xbar.in_data[2] = {160'hD, 352'd0};
    xbar.in_dst[2] = 2'd0;
    xbar.in_vld[2] = 1; xbar.in_sop[2] = 1; xbar.in_eop[2] = 1;
    #0;
    if (xbar.out_vld[0]) begin
      vibe_uvm_fail("tc_xbar_unit", "dest=0 status_up[0]=0",
                    "out_vld[0]=0 (down, no DLLDP)", "1", "u_xbar");
      fail = 1;
    end
    xbar.in_vld = 0;
    unit_done("tc_xbar_unit");
    phase.drop_objection(this);
  endtask
endclass

class tc_icrc_txrx_vs_transit extends vibe_unit_base;
  `uvm_component_utils(tc_icrc_txrx_vs_transit)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    icrc.rst_n = 0; icrc.start = 0; icrc.in_vld = 0; icrc.last = 0; icrc.in_byte = 0;
    repeat (4) @(posedge clk_vif.clk);
    icrc.rst_n = 1;
    @(posedge clk_vif.clk);
    icrc.start = 1;
    @(posedge clk_vif.clk);
    icrc.start = 0;
    icrc.in_vld = 1; icrc.last = 1; icrc.in_byte = 8'h00;
    @(posedge clk_vif.clk);
    icrc.in_vld = 0; icrc.last = 0;
    repeat (4) @(posedge clk_vif.clk);
    if (!icrc.done && icrc.crc_out === 32'd0) begin
      vibe_uvm_fail("tc_icrc_txrx_vs_transit",
                    "vibe_icrc start + one byte 0x00 last",
                    "done=1 and crc_out computed (CRC32 0x04C11DB7)",
                    $sformatf("done=%0b crc_out=%h", icrc.done, icrc.crc_out), "u_icrc");
      fail = 1;
    end
    $display("NOTE ICRC tx/rx: vibe_cna_ep does not instantiate vibe_icrc (RTL gap, not patched)");
    $display("NOTE ICRC transit: no vibe_icrc in vibe_fabric (AS §13 must)");
    icrc.start = 1;
    @(posedge clk_vif.clk);
    icrc.start = 0;
    icrc.in_vld = 1; icrc.last = 0; icrc.in_byte = 8'h11;
    @(posedge clk_vif.clk);
    icrc.in_byte = 8'h22;
    @(posedge clk_vif.clk);
    icrc.in_byte = 8'h33; icrc.last = 1;
    @(posedge clk_vif.clk);
    icrc.in_vld = 0; icrc.last = 0;
    repeat (2) @(posedge clk_vif.clk);
    unit_done("tc_icrc_txrx_vs_transit");
    phase.drop_objection(this);
  endtask
endclass

class tc_cna_ep extends vibe_unit_base;
  `uvm_component_utils(tc_cna_ep)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int p;
    phase.raise_objection(this);
    fail = 0;
    cna.rst_n = 0; cna.cna = 16'h1111; cna.cna_written = 1;
    cna.hit = 0; cna.rready = 4'b1111;
    for (p = 0; p < 4; p++) cna.data[p] = 512'd0;
    repeat (2) @(posedge clk_vif.clk);
    cna.rst_n = 1;
    cna.data[0] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    #1; cna.hit[0] = 1; #1;
    if (!cna.cons[0] || !cna.rvld[0]) begin
      vibe_uvm_fail("tc_cna_ep", "DCNA==written CNA", "consume+reply (terminate)",
                    $sformatf("cons=%0b vld=%0b", cna.cons[0], cna.rvld[0]), "u_cna");
      fail = 1;
    end
    cna.hit[0] = 0; #1;
    cna.data[1] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd1, 8'd0));
    cna.hit[1] = 1; #1;
    if (!cna.cons[1]) begin
      vibe_uvm_fail("tc_cna_ep", "NLP=1 DCNA!=CNA", "consume", "0", "u_cna");
      fail = 1;
    end
    cna.hit[1] = 0; #1;
    cna.data[2] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h2222, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    cna.hit[2] = 1; #1;
    if (cna.cons[2]) begin
      vibe_uvm_fail("tc_cna_ep", "miss CNA NLP=0", "forward (no consume)",
                    "consume=1", "u_cna");
      fail = 1;
    end
    cna.hit = 0;
    cna.cna_written = 0;
    cna.data[3] = vibe_tb_mk_beat(vibe_tb_mk_flit(
        4'd6, 2'b00, 4'd0, 16'h2, 16'h1111, vibe_tb_plen_nflit(1),
        16'd0, 8'd0, 3'd0, 8'd0));
    cna.hit[3] = 1; #1;
    if (cna.cons[3]) begin
      vibe_uvm_fail("tc_cna_ep", "CNA unwritten", "no match", "consume=1", "u_cna");
      fail = 1;
    end
    if (cna.icrc) begin
      vibe_uvm_fail("tc_cna_ep", "echo path",
                    "icrc_fail=0 (RTL gap: no vibe_icrc in cna_ep)", "1", "u_cna");
      fail = 1;
    end
    unit_done("tc_cna_ep");
    phase.drop_objection(this);
  endtask
endclass
