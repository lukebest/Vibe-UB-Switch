class vibe_switch_base_test extends uvm_test;
  `uvm_component_utils(vibe_switch_base_test)
  vibe_switch_env env;
  virtual vibe_clk_rst_if clk_vif;
  virtual vibe_cfg_if     cfg_vif;
  virtual vibe_pma_if     pma_vif[4];
  int fail;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    int p;
    super.build_phase(phase);
    env = vibe_switch_env::type_id::create("env", this);
    if (!uvm_config_db#(virtual vibe_clk_rst_if)::get(this, "", "clk_vif", clk_vif))
      `uvm_fatal("TOP", "clk_vif")
    if (!uvm_config_db#(virtual vibe_cfg_if)::get(this, "", "cfg_vif", cfg_vif))
      `uvm_fatal("TOP", "cfg_vif")
    for (p = 0; p < 4; p++)
      if (!uvm_config_db#(virtual vibe_pma_if)::get(this, "", $sformatf("pma_%0d", p), pma_vif[p]))
        `uvm_fatal("TOP", $sformatf("pma_%0d", p))
  endfunction

  task tb_reset();
    int p;
    clk_vif.rst_n = 1'b0;
    cfg_vif.idle();
    for (p = 0; p < 4; p++) pma_vif[p].idle_rx();
    repeat (8) @(posedge clk_vif.clk);
    clk_vif.rst_n = 1'b1;
    repeat (8) @(posedge clk_vif.clk);
  endtask
endclass

class tc_top_smoke extends vibe_switch_base_test;
  `uvm_component_utils(tc_top_smoke)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    tb_reset();
    if ($bits(cfg_vif.cmd) !== 4) begin
      vibe_uvm_fail("tc_top_smoke", "reset", "cfg_wr_cmd[3:0] (4 bits)",
                    "width not 4", "dut.cfg_wr_cmd");
      fail = 1;
    end else if (!cfg_vif.ready) begin
      vibe_uvm_fail("tc_top_smoke", "reset", "cfg_wr_ready=1", "0", "cfg_wr_ready");
      fail = 1;
    end else if (cfg_vif.irq_logic !== 1'b0) begin
      vibe_uvm_fail("tc_top_smoke", "reset, idle PMA", "irq_logic=0", "1", "irq_logic");
      fail = 1;
    end else begin
      cfg_vif.write(4'd0, 16'd0, 32'h0000_0001);
      if (!fail) vibe_uvm_pass("tc_top_smoke");
    end
    phase.drop_objection(this);
  endtask
endclass
