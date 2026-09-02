// Official TP-NEG-* / ID-005/006 / … — RTL scan (generated include).
// FAIL if a forbidden identifier appears in vibe_*.sv code (not prohibition comments).
`timescale 1ns/1ps
module tc_neg_official;
  `include "neg_official_scan.inc"
  integer fail;

  task automatic one;
    input integer hit;
    input [8*40-1:0] name;
    input [8*60-1:0] token;
    begin
      if (hit) begin
        $display("FAIL %0s", name);
        $display("  stimulus : scan rtl/vibe_*.sv for %0s", token);
        $display("  expected : identifier absent from code (comments citing ban OK)");
        $display("  actual   : token present in RTL");
        $display("  hier     : rtl/**/vibe_*.sv");
        $display("  reproduce: python3 tb/vibe/scripts/scan_official_neg.py rtl --inc /tmp/n.inc");
        fail = 1;
      end else
        $display("PASS %0s", name);
    end
  endtask

  initial begin
    fail = 0;
    if (NEG_SCAN_OPEN_FAIL) begin
      $display("FAIL tc_neg_official");
      $display("  stimulus : scan_official_neg.py --inc");
      $display("  expected : rtl/ readable, include generated");
      $display("  actual   : NEG_SCAN_OPEN_FAIL=1");
      $display("  hier     : tb/vibe/scripts/scan_official_neg.py");
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
    one(HIT_P5,      "tc_neg_no_fifth_port",       "txdata_4 / vibe_port_4");
    if (!fail) $display("PASS tc_neg_official");
    $finish;
  end
endmodule
