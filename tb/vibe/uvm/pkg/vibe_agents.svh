// Agents: cfg_wr (AS §10), Overlay-B NW (AS §3), PMA (AS §18).

class vibe_cfg_driver extends uvm_driver #(vibe_cfg_item);
  `uvm_component_utils(vibe_cfg_driver)
  virtual vibe_cfg_if vif;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFGDRV", "no vibe_cfg_if")
  endfunction
  task run_phase(uvm_phase phase);
    vibe_cfg_item t;
    vif.idle();
    @(posedge vif.rst_n);
    forever begin
      seq_item_port.get_next_item(t);
      vif.write(t.cmd, t.idx, t.data);
      seq_item_port.item_done();
    end
  endtask
endclass

class vibe_cfg_monitor extends uvm_monitor;
  `uvm_component_utils(vibe_cfg_monitor)
  virtual vibe_cfg_if vif;
  uvm_analysis_port #(vibe_cfg_item) ap;
  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFGMON", "no vibe_cfg_if")
  endfunction
  task run_phase(uvm_phase phase);
    vibe_cfg_item t;
    forever begin
      @(posedge vif.clk);
      if (vif.rst_n && vif.vld && vif.ready) begin
        t = vibe_cfg_item::type_id::create("cfg");
        t.cmd  = vif.cmd;
        t.idx  = vif.idx;
        t.data = vif.data;
        ap.write(t);
      end
    end
  endtask
endclass

class vibe_cfg_sequencer extends uvm_sequencer #(vibe_cfg_item);
  `uvm_component_utils(vibe_cfg_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

class vibe_cfg_agent extends uvm_agent;
  `uvm_component_utils(vibe_cfg_agent)
  vibe_cfg_driver    drv;
  vibe_cfg_monitor   mon;
  vibe_cfg_sequencer sqr;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    mon = vibe_cfg_monitor::type_id::create("mon", this);
    if (get_is_active() == UVM_ACTIVE) begin
      drv = vibe_cfg_driver::type_id::create("drv", this);
      sqr = vibe_cfg_sequencer::type_id::create("sqr", this);
    end
  endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (get_is_active() == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass

class vibe_nw_driver extends uvm_driver #(vibe_pkt_item);
  `uvm_component_utils(vibe_nw_driver)
  virtual vibe_nw4_if vif;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "vif", vif))
      `uvm_fatal("NWDRV", "no vibe_nw4_if")
  endfunction
  task drive_item(vibe_pkt_item t);
    bit [511:0] beats[];
    int b, p;
    p = t.port;
    t.pack_beats(beats);
    for (b = 0; b < beats.size(); b++) begin
      @(negedge vif.clk);
      while (!vif.ready[p]) @(posedge vif.clk);
      vif.data[p] = beats[b];
      vif.vld[p]  = 1'b1;
      @(posedge vif.clk);
    end
    @(negedge vif.clk);
    vif.vld[p] = 1'b0;
  endtask
  task run_phase(uvm_phase phase);
    vibe_pkt_item t;
    vif.idle_master();
    @(posedge vif.rst_n);
    forever begin
      seq_item_port.get_next_item(t);
      drive_item(t);
      seq_item_port.item_done();
    end
  endtask
endclass

class vibe_nw_monitor extends uvm_monitor;
  `uvm_component_utils(vibe_nw_monitor)
  virtual vibe_nw4_if vif;
  uvm_analysis_port #(vibe_pkt_item) ap;
  bit is_ingress;
  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
    is_ingress = 1;
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "vif", vif))
      `uvm_fatal("NWMON", "no vibe_nw4_if")
    void'(uvm_config_db#(bit)::get(this, "", "is_ingress", is_ingress));
  endfunction
  task run_phase(uvm_phase phase);
    int p;
    forever begin
      @(posedge vif.clk);
      if (!vif.rst_n) continue;
      for (p = 0; p < 4; p++) begin
        if (vif.vld[p] && vif.ready[p]) begin
          vibe_pkt_item t;
          bit [159:0] f;
          t = vibe_pkt_item::type_id::create("beat");
          t.port       = p[1:0];
          t.payload_lo = vif.data[p][351:0];
          f            = vif.data[p][511:352];
          t.cfg  = vibe_lph_cfg(f);
          t.rt   = vibe_lph_rt(f);
          t.vl   = vibe_lph_vl(f);
          t.scna = vibe_nth_scna(f);
          t.dcna = vibe_nth_dcna(f);
          t.plen = vibe_lph_plength(f);
          t.cci  = vibe_nth_cci(f);
          t.lbf  = vibe_nth_lbf(f);
          t.nlp  = vibe_nth_nlp(f);
          t.opc  = f[103:96];
          ap.write(t);
        end
      end
    end
  endtask
endclass

class vibe_nw_sequencer extends uvm_sequencer #(vibe_pkt_item);
  `uvm_component_utils(vibe_nw_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

class vibe_nw_agent extends uvm_agent;
  `uvm_component_utils(vibe_nw_agent)
  vibe_nw_driver    drv;
  vibe_nw_monitor   mon;
  vibe_nw_sequencer sqr;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    mon = vibe_nw_monitor::type_id::create("mon", this);
    if (get_is_active() == UVM_ACTIVE) begin
      drv = vibe_nw_driver::type_id::create("drv", this);
      sqr = vibe_nw_sequencer::type_id::create("sqr", this);
    end
  endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (get_is_active() == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass

class vibe_pma_driver extends uvm_driver #(vibe_pma_beat);
  `uvm_component_utils(vibe_pma_driver)
  virtual vibe_pma_if vif[4];
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    int p;
    super.build_phase(phase);
    for (p = 0; p < 4; p++)
      if (!uvm_config_db#(virtual vibe_pma_if)::get(this, "", $sformatf("vif_%0d", p), vif[p]))
        `uvm_fatal("PMADRV", $sformatf("no pma vif %0d", p))
  endfunction
  task run_phase(uvm_phase phase);
    vibe_pma_beat t;
    int p;
    for (p = 0; p < 4; p++) vif[p].idle_rx();
    forever begin
      seq_item_port.get_next_item(t);
      vif[t.port].pma_pcs_rxdata = t.rxdata;
      seq_item_port.item_done();
    end
  endtask
endclass

class vibe_pma_monitor extends uvm_monitor;
  `uvm_component_utils(vibe_pma_monitor)
  virtual vibe_pma_if vif[4];
  uvm_analysis_port #(vibe_pma_beat) ap;
  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction
  function void build_phase(uvm_phase phase);
    int p;
    super.build_phase(phase);
    for (p = 0; p < 4; p++)
      if (!uvm_config_db#(virtual vibe_pma_if)::get(this, "", $sformatf("vif_%0d", p), vif[p]))
        `uvm_fatal("PMAMON", $sformatf("no pma vif %0d", p))
  endfunction
  task run_phase(uvm_phase phase);
    int p;
    forever begin
      @(posedge vif[0].txclk);
      for (p = 0; p < 4; p++) begin
        if (vif[p].pcs_pma_txdata !== 512'd0) begin
          vibe_pma_beat t;
          t = vibe_pma_beat::type_id::create("tx");
          t.port   = p[1:0];
          t.rxdata = vif[p].pcs_pma_txdata;
          ap.write(t);
        end
      end
    end
  endtask
endclass

class vibe_pma_sequencer extends uvm_sequencer #(vibe_pma_beat);
  `uvm_component_utils(vibe_pma_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

class vibe_pma_agent extends uvm_agent;
  `uvm_component_utils(vibe_pma_agent)
  vibe_pma_driver    drv;
  vibe_pma_monitor   mon;
  vibe_pma_sequencer sqr;
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    mon = vibe_pma_monitor::type_id::create("mon", this);
    if (get_is_active() == UVM_ACTIVE) begin
      drv = vibe_pma_driver::type_id::create("drv", this);
      sqr = vibe_pma_sequencer::type_id::create("sqr", this);
    end
  endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (get_is_active() == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass
