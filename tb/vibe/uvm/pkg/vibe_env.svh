class vibe_fab_env extends uvm_env;
  `uvm_component_utils(vibe_fab_env)
  vibe_cfg_agent      cfg;
  vibe_nw_agent       ing;
  vibe_nw_agent       egr;
  vibe_as_scoreboard  sb;
  virtual vibe_clk_rst_if   clk_vif;
  virtual vibe_fab_probe_if probe;
  virtual vibe_psel_if      psel;
  virtual vibe_cna_if       cna;
  virtual vibe_nw4_if       ing_vif;
  virtual vibe_nw4_if       egr_vif;
  virtual vibe_cfg_if       cfg_vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    cfg = vibe_cfg_agent::type_id::create("cfg", this);
    ing = vibe_nw_agent::type_id::create("ing", this);
    egr = vibe_nw_agent::type_id::create("egr", this);
    sb  = vibe_as_scoreboard::type_id::create("sb", this);
    egr.is_active = UVM_PASSIVE;
    uvm_config_db#(bit)::set(this, "ing.mon", "is_ingress", 1'b1);
    uvm_config_db#(bit)::set(this, "egr.mon", "is_ingress", 1'b0);
    if (!uvm_config_db#(virtual vibe_clk_rst_if)::get(this, "", "clk_vif", clk_vif))
      `uvm_fatal("ENV", "clk_vif")
    if (!uvm_config_db#(virtual vibe_fab_probe_if)::get(this, "", "probe", probe))
      `uvm_fatal("ENV", "probe")
    void'(uvm_config_db#(virtual vibe_psel_if)::get(this, "", "psel", psel));
    void'(uvm_config_db#(virtual vibe_cna_if)::get(this, "", "cna", cna));
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "ing_vif", ing_vif))
      `uvm_fatal("ENV", "ing_vif")
    if (!uvm_config_db#(virtual vibe_nw4_if)::get(this, "", "egr_vif", egr_vif))
      `uvm_fatal("ENV", "egr_vif")
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "cfg_vif", cfg_vif))
      `uvm_fatal("ENV", "cfg_vif")
    uvm_config_db#(virtual vibe_cfg_if)::set(this, "cfg.*", "vif", cfg_vif);
    uvm_config_db#(virtual vibe_nw4_if)::set(this, "ing.*", "vif", ing_vif);
    uvm_config_db#(virtual vibe_nw4_if)::set(this, "egr.*", "vif", egr_vif);
    uvm_config_db#(virtual vibe_fab_probe_if)::set(this, "sb", "probe", probe);
    uvm_config_db#(virtual vibe_cfg_if)::set(this, "sb", "cfg_vif", cfg_vif);
    uvm_config_db#(virtual vibe_nw4_if)::set(this, "sb", "egr_vif", egr_vif);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    ing.mon.ap.connect(sb.ing_imp);
  endfunction
endclass

class vibe_switch_env extends uvm_env;
  `uvm_component_utils(vibe_switch_env)
  vibe_cfg_agent cfg;
  vibe_pma_agent pma;
  virtual vibe_clk_rst_if clk_vif;
  virtual vibe_cfg_if     cfg_vif;
  virtual vibe_pma_if     pma_vif[4];

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    int p;
    super.build_phase(phase);
    cfg = vibe_cfg_agent::type_id::create("cfg", this);
    pma = vibe_pma_agent::type_id::create("pma", this);
    if (!uvm_config_db#(virtual vibe_clk_rst_if)::get(this, "", "clk_vif", clk_vif))
      `uvm_fatal("SENV", "clk_vif")
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "cfg_vif", cfg_vif))
      `uvm_fatal("SENV", "cfg_vif")
    uvm_config_db#(virtual vibe_cfg_if)::set(this, "cfg.*", "vif", cfg_vif);
    for (p = 0; p < 4; p++) begin
      if (!uvm_config_db#(virtual vibe_pma_if)::get(this, "", $sformatf("pma_%0d", p), pma_vif[p]))
        `uvm_fatal("SENV", $sformatf("pma_%0d", p))
      uvm_config_db#(virtual vibe_pma_if)::set(this, "pma.*", $sformatf("vif_%0d", p), pma_vif[p]);
    end
  endfunction
endclass
