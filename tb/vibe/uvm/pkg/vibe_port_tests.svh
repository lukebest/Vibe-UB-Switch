class vibe_port_base_test extends vibe_unit_base;
  `uvm_component_utils(vibe_port_base_test)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  // which_cells: 64 or 512 — literals only (xsim rejects automatic force RHS).
  // hold_crd: keep cells/pend forced (Icarus loopback holds 512/0 so the 1µs
  // Crd_Ack timeout cannot tear the link while PMA RX of 100 packets drains).
  task bring_link(bit loop, int which_cells, bit hold_crd);
    int w;
    port.loop_en = loop;
    port.rst_n = 0; port.port_rst = 0; port.device_rst = 0; port.lmsm_go = 0;
    port.fab_nw_vld = 0; port.nw_fab_ready = 1; port.mgmt_nw_vld = 0;
    port.fab_nw_data = 0; port.mgmt_nw_data = 0;
    repeat (8) @(posedge clk_vif.clk);
    port.rst_n = 1;
    repeat (8) @(posedge clk_vif.clk);
    port.force_am_lock = 1;
    port.force_lid_ok  = 1;
    @(negedge clk_vif.clk);
    port.lmsm_go = 1;
    @(posedge clk_vif.clk);
    port.lmsm_go = 0;
    w = 0;
    while (!(port.link_ready && port.status_up) && w < 64) begin
      @(posedge clk_vif.clk);
      w++;
    end
    if (!port.link_ready || !port.status_up) begin
      vibe_uvm_fail(get_type_name(), "lmsm_go + force am_locked=1111 lid_bad=0",
                    "link_ready=1 status_up=1 (TX and RX domains up)",
                    "LMSM/DLL did not reach ACTIVE/NRM",
                    "u_p.u_lmsm / u_p.u_dll.u_sm");
      fail = 1;
    end
    if (which_cells >= 512)
      port.force_crd512 = 1;
    else
      port.force_crd64 = 1;
    port.force_pend0 = 1;
    @(posedge clk_vif.clk);
    if (!hold_crd) begin
      port.force_crd64 = 0;
      port.force_crd512 = 0;
      port.force_pend0 = 0;
    end
    port.force_st_active = 1;
    port.force_am_lock = 0;
    port.force_lid_ok = 0;
    @(posedge clk_vif.clk);
  endtask

  task send_one(input logic [511:0] beat, output int accepted);
    int i;
    accepted = 0;
    port.fab_nw_data = beat;
    for (i = 0; i < 32; i++) begin
      @(negedge clk_vif.clk);
      port.fab_nw_vld = 1;
      if (port.fab_nw_ready) begin
        @(posedge clk_vif.clk);
        accepted = 1;
        port.fab_nw_vld = 0;
        i = 32;
      end else
        @(posedge clk_vif.clk);
    end
    port.fab_nw_vld = 0;
  endtask
endclass

class tc_port_smoke extends vibe_port_base_test;
  `uvm_component_utils(tc_port_smoke)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    logic [511:0] golden_tx, last_pack, last_rx;
    int accepted, saw_tx, pack_ok, saw_rx, last_v, i, nw_w, dll_w, rx_w;
    phase.raise_objection(this);
    fail = 0; accepted = 0; saw_tx = 0; pack_ok = 1; saw_rx = 0; last_v = 0;
    last_rx = 512'd0;
    golden_tx = vibe_tb_nw512_golden_tx();
    nw_w = $bits(port.fab_nw_data);
    dll_w = $bits(port.nw_dll_data);
    rx_w = $bits(port.nw_fab_data);
    bring_link(1'b1, 64, 1'b0);
    if (fail) begin phase.drop_objection(this); return; end
    send_one(golden_tx, accepted);
    if (accepted) begin
      if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, port.nw_dll_data)) begin
        vibe_tb_nw512_fail_print("tc_port_smoke",
            "TX NW→DLL accepted beat GOLDEN_TX",
            golden_tx, dll_w, port.nw_dll_data, "u_p.nw_dll_data");
        fail = 1;
      end else if (vibe_tb_nw512_sop_lph_fail(golden_tx, port.nw_dll_data)) begin
        vibe_tb_nw512_sop_lph_print("tc_port_smoke",
            "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
            golden_tx, port.nw_dll_data, "u_p.nw_dll_data[511:352]");
        fail = 1;
      end
    end
    send_one(vibe_tb_nw512_golden_tx_b2(), i);
    if (!accepted) begin
      vibe_uvm_fail("tc_port_smoke", "fab_nw_vld GOLDEN_TX after LinkReady+cells=64",
                    "fab_nw_ready handshake (packet accepted)", "not accepted",
                    "u_p.u_nw.fab_nw_ready");
      fail = 1;
    end
    fork
      begin
        int t;
        for (t = 0; t < 20000; t++) begin
          @(posedge port.txclk);
          if (last_v) begin
            saw_tx = 1;
            if (port.pcs_pma_txdata === 512'd0) pack_ok = 0;
            if (port.pcs_pma_txdata !== last_pack) pack_ok = 0;
          end
          last_v = port.afifo_pma_lane_vld;
          last_pack = {port.afifo_pma_lane3, port.afifo_pma_lane2,
                       port.afifo_pma_lane1, port.afifo_pma_lane0};
        end
      end
      begin
        int r;
        for (r = 0; r < 20000; r++) begin
          @(negedge clk_vif.clk);
          if (port.nw_fab_vld) begin
            last_rx = port.nw_fab_data;
            if (!vibe_tb_nw512_vec_fail(rx_w, golden_tx, port.nw_fab_data) &&
                !vibe_tb_nw512_sop_lph_fail(golden_tx, port.nw_fab_data))
              saw_rx = 1;
          end
        end
      end
    join
    if (!saw_tx) begin
      vibe_uvm_fail("tc_port_smoke", "legal NW beat accepted; watch PMA pcs_pma_txdata",
                    "pcs_pma_txdata[511:0] nonzero (full-duplex TX)",
                    "pcs_pma_txdata stayed 0 or afifo_pma_lane_vld never rose",
                    "u_p.u_pma");
      fail = 1;
    end
    if (!pack_ok) begin
      vibe_uvm_fail("tc_port_smoke", "afifo_pma_lane_vld beats after accept",
                    "pcs_pma_txdata[127:0]=lane0 .. [511:384]=lane3",
                    "lane pack mismatch or zero beat", "u_p.u_pma");
      fail = 1;
    end
    if (!saw_rx) begin
      vibe_tb_nw512_fail_print("tc_port_smoke",
          "PMA loopback; recover NW RX data[511:0] === GOLDEN_TX",
          golden_tx, rx_w, last_rx, "u_p.nw_fab_data");
      fail = 1;
    end
    unit_done("tc_port_smoke");
    phase.drop_objection(this);
  endtask
endclass

class tc_nw_pkt_to_pma_tx extends vibe_port_base_test;
  `uvm_component_utils(tc_nw_pkt_to_pma_tx)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  task run_phase(uvm_phase phase);
    logic [511:0] golden_tx, last_pack;
    int accepted, dummy, saw_pma, pack_ok, pack_n, last_v, i, dll_w;
    phase.raise_objection(this);
    fail = 0; accepted = 0; saw_pma = 0; pack_ok = 1; pack_n = 0; last_v = 0;
    golden_tx = vibe_tb_nw512_golden_tx();
    dll_w = $bits(port.nw_dll_data);
    bring_link(1'b0, 64, 1'b0);
    if (fail) begin phase.drop_objection(this); return; end
    send_one(golden_tx, accepted);
    if (accepted) begin
      if (vibe_tb_nw512_vec_fail(dll_w, golden_tx, port.nw_dll_data)) begin
        vibe_tb_nw512_fail_print("tc_nw_pkt_to_pma_tx",
            "TX NW→DLL accepted beat GOLDEN_TX",
            golden_tx, dll_w, port.nw_dll_data, "u_p.nw_dll_data");
        fail = 1;
      end else if (vibe_tb_nw512_sop_lph_fail(golden_tx, port.nw_dll_data)) begin
        vibe_tb_nw512_sop_lph_print("tc_nw_pkt_to_pma_tx",
            "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
            golden_tx, port.nw_dll_data, "u_p.nw_dll_data[511:352]");
        fail = 1;
      end
    end else begin
      vibe_uvm_fail("tc_nw_pkt_to_pma_tx",
                    "fab_nw_vld GOLDEN_TX 1-beat after LinkReady+cells=64",
                    "fab_nw_ready handshake (packet accepted / TX backpressure path)",
                    "not accepted", "u_p.u_nw.fab_nw_ready");
      fail = 1;
    end
    send_one(vibe_tb_nw512_golden_tx_b2(), dummy);
    for (i = 0; i < 4000; i++) begin
      @(posedge clk_vif.clk);
      @(posedge port.txclk);
      if (last_v) begin
        saw_pma = 1;
        pack_n++;
        if (port.pcs_pma_txdata !== last_pack) pack_ok = 0;
      end
      last_v = port.afifo_pma_lane_vld;
      last_pack = {port.afifo_pma_lane3, port.afifo_pma_lane2,
                   port.afifo_pma_lane1, port.afifo_pma_lane0};
    end
    if (!saw_pma || port.pcs_pma_txdata === 512'd0) begin
      vibe_uvm_fail("tc_nw_pkt_to_pma_tx", "packet accepted; wait 4000 txclk",
                    "afifo_pma_lane_vld and pcs_pma_txdata[511:0] nonzero",
                    "PMA stayed idle", "u_p.u_pma");
      fail = 1;
    end
    if (!pack_ok) begin
      vibe_uvm_fail("tc_nw_pkt_to_pma_tx", "afifo_pma_lane_vld beats after accept",
                    "pcs_pma_txdata[127:0]=lane0 .. [511:384]=lane3 (TP-PHY-018)",
                    "pack mismatch", "u_p.u_pma");
      fail = 1;
    end
    unit_done("tc_nw_pkt_to_pma_tx");
    phase.drop_objection(this);
  endtask
endclass

class tc_nw_pkt_pma_loopback extends vibe_port_base_test;
  `uvm_component_utils(tc_nw_pkt_pma_loopback)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction
  localparam int NPKT = 100;
  localparam int WAIT_MAX = 200000;
  localparam int BEAT_TO = 4096;
  task run_phase(uvm_phase phase);
    logic [511:0] exp_sop [0:NPKT-1];
    logic [511:0] last_rx, beat;
    int i, j, pkt, tx_n, rx_n, accepted, beat_w, wait_i, hit_other;
    int saw_am, saw_fec_fail, nw_w, dll_w, rx_w;
    phase.raise_objection(this);
    fail = 0; tx_n = 0; rx_n = 0; last_rx = 0; saw_am = 0; saw_fec_fail = 0;
    nw_w = $bits(port.fab_nw_data);
    dll_w = $bits(port.nw_dll_data);
    rx_w = $bits(port.nw_fab_data);
    for (i = 0; i < NPKT; i++) begin
      exp_sop[i] = vibe_tb_nw512_golden_tx_n(i);
      if (exp_sop[i] === 512'd0) begin
        vibe_uvm_fail("tc_nw_pkt_pma_loopback", "build 100 unique GOLDEN SOP beats",
                      "data[511:0] nonzero", "GOLDEN all-zero",
                      "vibe_tb_nw512_golden_tx_n");
        fail = 1;
      end
    end
    for (i = 0; i < NPKT; i++)
      for (j = i + 1; j < NPKT; j++)
        if (exp_sop[i] === exp_sop[j]) begin
          vibe_uvm_fail("tc_nw_pkt_pma_loopback", "build 100 unique GOLDEN SOP beats",
                        "each packet data[511:0] distinct", "duplicate GOLDEN",
                        "vibe_tb_nw512_golden_tx_n");
          fail = 1;
        end
    if (fail) begin phase.drop_objection(this); return; end
    bring_link(1'b1, 512, 1'b1);
    if (fail) begin phase.drop_objection(this); return; end
    for (pkt = 0; pkt < NPKT && !fail; pkt++) begin
      beat = exp_sop[pkt];
      accepted = 0; beat_w = 0;
      port.fab_nw_data = beat;
      while (!accepted && !fail && beat_w < BEAT_TO) begin
        @(negedge clk_vif.clk);
        if (port.fec_fail) saw_fec_fail = 1;
        if (|port.am_locked) saw_am = 1;
        if (port.nw_fab_vld) begin
          last_rx = port.nw_fab_data;
          if (rx_n < NPKT && port.nw_fab_data === exp_sop[rx_n]) begin
            if (vibe_tb_nw512_vec_fail(rx_w, exp_sop[rx_n], port.nw_fab_data) ||
                vibe_tb_nw512_sop_lph_fail(exp_sop[rx_n], port.nw_fab_data))
              fail = 1;
            else
              rx_n++;
          end else if (rx_n < NPKT) begin
            hit_other = -1;
            for (j = 0; j < NPKT; j++)
              if (port.nw_fab_data === exp_sop[j] && j != rx_n) hit_other = j;
            if (hit_other >= 0) fail = 1;
          end
        end
        port.fab_nw_vld = 1;
        if (port.fab_nw_ready) begin
          @(posedge clk_vif.clk);
          if (vibe_tb_nw512_vec_fail(dll_w, beat, port.nw_dll_data) ||
              vibe_tb_nw512_sop_lph_fail(beat, port.nw_dll_data))
            fail = 1;
          else
            tx_n++;
          port.fab_nw_vld = 0;
          accepted = 1;
        end else
          @(posedge clk_vif.clk);
        beat_w++;
      end
      port.fab_nw_vld = 0;
      if (!accepted && !fail) fail = 1;
      if (!fail)
        send_one(vibe_tb_nw512_golden_tx_b2_n(pkt), accepted);
      wait_i = 0;
      while (rx_n <= pkt && !fail && wait_i < WAIT_MAX) begin
        @(negedge clk_vif.clk);
        if (port.fec_fail) saw_fec_fail = 1;
        if (|port.am_locked) saw_am = 1;
        if (port.nw_fab_vld) begin
          last_rx = port.nw_fab_data;
          if (rx_n < NPKT && port.nw_fab_data === exp_sop[rx_n])
            rx_n++;
        end
        wait_i++;
      end
      if (!fail && rx_n <= pkt) begin
        vibe_tb_nw512_fail_print_pkt("tc_nw_pkt_pma_loopback", pkt, NPKT,
            "PMA loopback; recover this packet GOLDEN (timeout, not a pass)",
            exp_sop[pkt], rx_w, last_rx, "u_p.nw_fab_data");
        fail = 1;
      end
      if (!fail && ((pkt % 10) == 9))
        $display("  progress : tx_n=%0d rx_n=%0d (after packet %0d)", tx_n, rx_n, pkt);
    end
    if (saw_fec_fail) begin
      vibe_uvm_fail("tc_nw_pkt_pma_loopback",
                    "supporting: fec_fail during 100-pkt GOLDEN loopback",
                    "fec_fail=0", "fec_fail=1", "u_p.fec_fail");
      fail = 1;
    end
    if (rx_n !== NPKT) begin
      vibe_tb_nw512_fail_print_pkt("tc_nw_pkt_pma_loopback", rx_n, NPKT,
          "PMA loopback; recover each GOLDEN in order",
          (rx_n < NPKT) ? exp_sop[rx_n] : 512'd0, rx_w, last_rx, "u_p.nw_fab_data");
      fail = 1;
    end
    if (!saw_am) begin
      vibe_uvm_fail("tc_nw_pkt_pma_loopback",
                    "supporting: am_locked during GOLDEN loopback",
                    "am_locked nonzero", "am_locked stayed 0", "u_p.am_locked");
      fail = 1;
    end
    if (!fail) begin
      vibe_uvm_pass("tc_nw_pkt_pma_loopback");
      $display("  scored : %0d / %0d packets; each TX GOLDEN and RX nw_fab_data[511:0] matched in order",
               rx_n, NPKT);
    end
    phase.drop_objection(this);
  endtask
endclass
