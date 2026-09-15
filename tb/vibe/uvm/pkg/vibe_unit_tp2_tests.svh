class tc_retry_buf_256 extends vibe_unit_base;
  `uvm_component_utils(tc_retry_buf_256)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    rbuf.rst_n = 0; rbuf.port_rst = 0; rbuf.link_up = 1;
    rbuf.wr_en = 0; rbuf.is_null = 0; rbuf.is_retry = 0;
    rbuf.ack_rel = 0; rbuf.send_size = 8'd1; rbuf.rel_size = 0;
    rbuf.rd_ptr_i = 0; rbuf.wr_flit = 0;
    repeat (3) @(posedge clk_vif.clk);
    rbuf.rst_n = 1;
    @(posedge clk_vif.clk);
    if (rbuf.num_free !== 9'd256) begin
      vibe_uvm_fail("tc_retry_buf_256", "reset", "NumFreeBuf=256",
                    $sformatf("%0d", rbuf.num_free), "u_rbuf.freeb");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    rbuf.wr_en = 1; rbuf.is_null = 1; rbuf.wr_flit = 160'h1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 0; rbuf.is_null = 0;
    @(posedge clk_vif.clk);
    if (rbuf.num_free !== 9'd256 || rbuf.wr_ptr !== 8'd0) begin
      vibe_uvm_fail("tc_retry_buf_256", "wr_en is_null", "free stays 256",
                    $sformatf("free=%0d wrp=%0d", rbuf.num_free, rbuf.wr_ptr), "u_rbuf");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    rbuf.wr_en = 1; rbuf.is_retry = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 0; rbuf.is_retry = 0;
    @(posedge clk_vif.clk);
    if (rbuf.num_free !== 9'd256) begin
      vibe_uvm_fail("tc_retry_buf_256", "is_retry write", "not entered",
                    $sformatf("free=%0d", rbuf.num_free), "u_rbuf");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    rbuf.wr_en = 1; rbuf.wr_flit = 160'h55;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 0;
    @(posedge clk_vif.clk);
    if (rbuf.num_free !== 9'd255) begin
      vibe_uvm_fail("tc_retry_buf_256", "one data flit", "free=255",
                    $sformatf("%0d", rbuf.num_free), "u_rbuf");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    rbuf.ack_rel = 1; rbuf.rel_size = 8'd8;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.ack_rel = 0;
    @(posedge clk_vif.clk);
    if (!rbuf.proto_err) begin
      vibe_uvm_fail("tc_retry_buf_256", "ack_rel 8 with free=255 → 263>256",
                    "proto_err", "0", "u_rbuf.freeb");
      fail = 1;
    end
    rbuf.rst_n = 0;
    repeat (2) @(posedge clk_vif.clk);
    rbuf.rst_n = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 1; rbuf.wr_flit = 160'h11; rbuf.is_null = 0; rbuf.is_retry = 0;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 0; rbuf.ack_rel = 1; rbuf.rel_size = 8'd1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.ack_rel = 0;
    @(posedge clk_vif.clk);
    if (rbuf.num_free !== 9'd256 || rbuf.proto_err) begin
      vibe_uvm_fail("tc_retry_buf_256", "write 1 then ack_rel 1",
                    "free=256 proto_err=0",
                    $sformatf("free=%0d err=%0b", rbuf.num_free, rbuf.proto_err), "u_rbuf");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    rbuf.wr_en = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    rbuf.wr_en = 0; rbuf.port_rst = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    if (rbuf.num_free !== 9'd256) begin
      vibe_uvm_fail("tc_retry_buf_256", "port_rst", "free=256",
                    $sformatf("%0d", rbuf.num_free), "u_rbuf");
      fail = 1;
    end
    rbuf.link_up = 0;
    @(posedge clk_vif.clk);
    rbuf.link_up = 1;
    unit_done("tc_retry_buf_256");
    phase.drop_objection(this);
  endtask
endclass

class tc_retry_req_gbn extends vibe_unit_base;
  `uvm_component_utils(tc_retry_req_gbn)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    rreq.rst_n = 0; rreq.port_rst = 0; rreq.device_rst = 0;
    rreq.start_retry = 0; rreq.phy_retrain = 0; rreq.wait_done_ack = 0;
    repeat (3) @(posedge clk_vif.clk);
    rreq.rst_n = 1;
    @(posedge clk_vif.clk);
    rreq.start_retry = 1;
    @(posedge clk_vif.clk);
    rreq.start_retry = 0;
    @(posedge clk_vif.clk);
    if (rreq.state !== 3'd1 || !rreq.drop_data) begin
      vibe_uvm_fail("tc_retry_req_gbn", "start_retry (Go-Back-N)",
                    "ST_REQ drop_data=1",
                    $sformatf("st=%0d drop=%0b", rreq.state, rreq.drop_data), "u_rreq.st");
      fail = 1;
    end
    unit_done("tc_retry_req_gbn");
    phase.drop_objection(this);
  endtask
endclass

class tc_retry_ack_replay extends vibe_unit_base;
  `uvm_component_utils(tc_retry_ack_replay)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    fail = 0;
    rack.rst_n = 0; rack.port_rst = 0; rack.start_ack = 0;
    rack.wr_ptr = 8'd4; rack.rcv_ptr = 8'd0;
    repeat (3) @(posedge clk_vif.clk);
    rack.rst_n = 1;
    @(posedge clk_vif.clk);
    rack.start_ack = 1;
    @(posedge clk_vif.clk);
    rack.start_ack = 0;
    repeat (2) @(posedge clk_vif.clk);
    if (rack.state === 3'd0) begin
      vibe_uvm_fail("tc_retry_ack_replay", "start_ack wr_ptr=4 rcv=0",
                    "leave NORMAL (ACK or replay)", "still NORMAL", "u_rack.st");
      fail = 1;
    end
    repeat (40) @(posedge clk_vif.clk);
    if (rack.state !== 3'd2 && rack.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_ack_replay", "40 cyc after start_ack",
                    "ST_P replay or back to NORMAL",
                    $sformatf("st=%0d replay=%0b rd=%0d", rack.state, rack.replay, rack.rd_ptr),
                    "u_rack.st");
      fail = 1;
    end
    repeat (8) @(posedge clk_vif.clk);
    if (rack.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_ack_replay", "replay until rd_ptr==wr_ptr=4",
                    "NORMAL", $sformatf("st=%0d rd=%0d", rack.state, rack.rd_ptr), "u_rack");
      fail = 1;
    end
    rack.start_ack = 1;
    @(posedge clk_vif.clk);
    rack.start_ack = 0;
    rack.port_rst = 1;
    @(posedge clk_vif.clk);
    rack.port_rst = 0;
    @(posedge clk_vif.clk);
    if (rack.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_ack_replay", "port_rst during ACK", "NORMAL",
                    $sformatf("%0d", rack.state), "u_rack");
      fail = 1;
    end
    rack.force_st7 = 1;
    @(posedge clk_vif.clk);
    rack.force_st7 = 0;
    @(posedge clk_vif.clk);
    unit_done("tc_retry_ack_replay");
    phase.drop_objection(this);
  endtask
endclass

class tc_retry_wait_retrain extends vibe_unit_base;
  `uvm_component_utils(tc_retry_wait_retrain)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task burst_req();
    rreq.start_retry = 1;
    @(posedge clk_vif.clk);
    rreq.start_retry = 0;
    repeat (34) @(posedge clk_vif.clk);
  endtask
  task run_phase(uvm_phase phase);
    int i, k, saw_w, saw_r, saw_e, saw_this;
    phase.raise_objection(this);
    fail = 0; saw_w = 0; saw_r = 0; saw_e = 0;
    rreq.rst_n = 0; rreq.port_rst = 0; rreq.device_rst = 0;
    rreq.start_retry = 0; rreq.phy_retrain = 0; rreq.wait_done_ack = 0;
    repeat (3) @(posedge clk_vif.clk);
    rreq.rst_n = 1;
    @(posedge clk_vif.clk);
    burst_req();
    if (rreq.state !== 3'd2) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "33-cyc REQ burst", "ST_WAIT (2)",
                    $sformatf("%0d", rreq.state), "u_rreq.st");
      fail = 1;
    end else
      saw_w = 1;
    if (!rreq.drop_data) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "WAIT", "drop_data=1", "0", "u_rreq");
      fail = 1;
    end
    rreq.wait_done_ack = 1;
    @(posedge clk_vif.clk);
    rreq.wait_done_ack = 0;
    @(posedge clk_vif.clk);
    if (rreq.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "wait_done_ack", "NORMAL",
                    $sformatf("%0d", rreq.state), "u_rreq");
      fail = 1;
    end
    burst_req();
    if (rreq.state !== 3'd2) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "second burst", "WAIT",
                    $sformatf("%0d", rreq.state), "u_rreq");
      fail = 1;
    end
    repeat (6) @(posedge clk_vif.clk);
    if (rreq.state !== 3'd1) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "WAIT timeout", "REQ",
                    $sformatf("%0d", rreq.state), "u_rreq");
      fail = 1;
    end
    repeat (34) @(posedge clk_vif.clk);
    i = 0;
    while (rreq.state !== 3'd3 && i < 20) begin
      if (rreq.state == 3'd2) repeat (6) @(posedge clk_vif.clk);
      else @(posedge clk_vif.clk);
      i++;
    end
    i = 0;
    while (rreq.state !== 3'd3 && rreq.state !== 3'd4 && i < 20) begin
      if (rreq.state == 3'd0) burst_req();
      else if (rreq.state == 3'd2) repeat (6) @(posedge clk_vif.clk);
      else @(posedge clk_vif.clk);
      i++;
    end
    if (rreq.state == 3'd3) saw_r = 1;
    rreq.rst_n = 0;
    repeat (2) @(posedge clk_vif.clk);
    rreq.rst_n = 1;
    @(posedge clk_vif.clk);
    for (k = 0; k < 4; k++) begin
      rreq.start_retry = 1;
      @(posedge clk_vif.clk);
      rreq.start_retry = 0;
      rreq.phy_retrain = 1;
      saw_this = 0;
      repeat (40) begin
        @(posedge clk_vif.clk);
        if (rreq.state == 3'd3) begin saw_r = 1; saw_this = 1; end
        if (rreq.state == 3'd4) saw_e = 1;
      end
      rreq.phy_retrain = 0;
      if (!saw_this && rreq.state !== 3'd4) begin
        vibe_uvm_fail("tc_retry_wait_retrain",
                      $sformatf("REQ burst + phy_retrain visit %0d", k),
                      "RETRAIN (1-cycle) or ERROR",
                      $sformatf("st=%0d", rreq.state), "u_rreq.st");
        fail = 1;
      end
    end
    if (!saw_e && !rreq.retry_error) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "4 phy reinits", "ERROR",
                    $sformatf("st=%0d", rreq.state), "u_rreq.num_phy");
      fail = 1;
    end
    rreq.port_rst = 1;
    @(posedge clk_vif.clk);
    rreq.port_rst = 0;
    @(posedge clk_vif.clk);
    if (rreq.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "port_rst in ERROR", "NORMAL",
                    $sformatf("%0d", rreq.state), "u_rreq");
      fail = 1;
    end
    rreq.start_retry = 1;
    @(posedge clk_vif.clk);
    rreq.start_retry = 0;
    rreq.device_rst = 1;
    @(posedge clk_vif.clk);
    rreq.device_rst = 0;
    @(posedge clk_vif.clk);
    if (rreq.state !== 3'd0) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "device_rst", "NORMAL",
                    $sformatf("%0d", rreq.state), "u_rreq");
      fail = 1;
    end
    if (!saw_w) begin
      vibe_uvm_fail("tc_retry_wait_retrain", "REQ burst", "visited WAIT", "never", "u_rreq");
      fail = 1;
    end
    unit_done("tc_retry_wait_retrain");
    phase.drop_objection(this);
  endtask
endclass

class tc_deadlock_timeout_1us extends vibe_unit_base;
  `uvm_component_utils(tc_deadlock_timeout_1us)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    voq.rst_n = 0; voq.wr_en = 0; voq.rd_en = 0; voq.wr_vl = 0; voq.rd_vl = 0;
    voq.wr_data = 512'h1; voq.wr_sop = 1; voq.wr_eop = 1;
    repeat (3) @(posedge clk_vif.clk);
    voq.rst_n = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    voq.wr_en = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    voq.wr_en = 0;
    for (i = 0; i < (VIBE_US_CYC - 4); i++) @(posedge clk_vif.clk);
    if (voq.deadlock_drop) begin
      vibe_uvm_fail("tc_deadlock_timeout_1us", "enqueue, wait <1us, no read",
                    "deadlock_drop still 0", "1", "u_voq");
      fail = 1;
    end
    for (i = 0; i < 16; i++) @(posedge clk_vif.clk);
    if (!voq.deadlock_drop && voq.deadlock_cnt == 0) begin
      vibe_uvm_fail("tc_deadlock_timeout_1us",
                    "VOQ occupied >=1250 cycles without drain",
                    "deadlock_drop pulse / cnt>0",
                    $sformatf("drop=%0b cnt=%0d nonempty=%h",
                              voq.deadlock_drop, voq.deadlock_cnt, voq.nonempty),
                    "u_voq.age");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    voq.wr_en = 1; voq.wr_vl = 4'd1; voq.wr_data = 512'h2;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    voq.wr_en = 0; voq.rd_vl = 4'd1; voq.rd_en = 1;
    @(posedge clk_vif.clk);
    voq.rd_en = 0;
    unit_done("tc_deadlock_timeout_1us");
    phase.drop_objection(this);
  endtask
endclass

class tc_timers_indep extends vibe_unit_base;
  `uvm_component_utils(tc_timers_indep)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    int i;
    phase.raise_objection(this);
    fail = 0;
    if (VIBE_US_CYC !== 1250) begin
      vibe_uvm_fail("tc_timers_indep", "VIBE_US_CYC", "1250",
                    $sformatf("%0d", VIBE_US_CYC), "vibe_ub_params.vh");
      fail = 1;
    end
    crd.rst_n = 0; crd.port_rst = 0; crd.link_up = 1; crd.grain_n = 8'd8;
    crd.consume_vld = 0; crd.consume_flits = 0; crd.is_cfg0 = 0;
    crd.credit_ret = 0; crd.credit_ret_n = 0;
    voq.rst_n = 0; voq.wr_en = 0; voq.rd_en = 0; voq.wr_vl = 0; voq.rd_vl = 0;
    voq.wr_data = 512'h1; voq.wr_sop = 1; voq.wr_eop = 1;
    repeat (3) @(posedge clk_vif.clk);
    crd.rst_n = 1; voq.rst_n = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 1; crd.credit_ret_n = 16'd1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.credit_ret = 0;
    for (i = 0; i < (VIBE_US_CYC + 8); i++) @(posedge clk_vif.clk);
    if (!crd.proto_err) begin
      vibe_uvm_fail("tc_timers_indep", "pending=1, no VOQ enqueue, wait >1us",
                    "proto_err=1 (credit timeout)", "0", "u_crd.to");
      fail = 1;
    end
    if (voq.deadlock_drop || voq.deadlock_cnt != 0) begin
      vibe_uvm_fail("tc_timers_indep", "credit timeout, VOQ never written",
                    "deadlock_drop=0 cnt=0 (independent timer)",
                    $sformatf("drop=%0b cnt=%0d", voq.deadlock_drop, voq.deadlock_cnt),
                    "u_voq.age vs u_crd.to");
      fail = 1;
    end
    @(negedge clk_vif.clk);
    crd.port_rst = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    crd.port_rst = 0;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    voq.wr_en = 1;
    @(posedge clk_vif.clk);
    @(negedge clk_vif.clk);
    voq.wr_en = 0;
    for (i = 0; i < (VIBE_US_CYC + 16); i++) @(posedge clk_vif.clk);
    if (!voq.deadlock_drop && voq.deadlock_cnt == 0) begin
      vibe_uvm_fail("tc_timers_indep",
                    "VOQ occupied >=1us, no credit_ret after port_rst",
                    "deadlock_drop or cnt>0",
                    $sformatf("drop=%0b cnt=%0d", voq.deadlock_drop, voq.deadlock_cnt),
                    "u_voq.age");
      fail = 1;
    end
    unit_done("tc_timers_indep");
    phase.drop_objection(this);
  endtask
endclass
