# TP-0.3 ↔ testcase matrix

159 rows. Official TP-0.3 table is **not in this repo**; IDs are
reconstructed from AS-0.1 MUST bullets + existing `TP-*` prefixes
so the last hole is `TP-HOLE-012`. Planned names such as
`tc_id_guid_class` map to the existing file that already scores
the same locked rule (`tc_identity_cfg_space` /
`tc_cfg_identity_guid_class`). Prefer MAPPED over a duplicate TC.

Verdict: **MAPPED** existing TC scores the rule; **ADDED** new TC
written this pass; **HOLE** unknown not invented (PASS + NOTE);
**NEG** static/scan absent-feature.

Counts: MAPPED=130 ADDED=4 HOLE=12 NEG=13  (sum=159)

| TP | rule (short) | TC name | file | verdict |
|----|--------------|---------|------|---------|
| TP-ID-001 | GUID Type 0x3 | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-002 | Class 0x03/0x00 | `tc_cfg_identity_guid_class` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-ID-003 | PORT_BASIC 4p x4 Mode-2 | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-004 | PORT_CAP constants | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-005 | CNA static write cmd=0 | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-006 | cfg_wr cmd 0..5 space | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-RT-001 | RT=00 per-flow sticky RR | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-002 | RT=01 per-packet RR | `tc_rt01_per_packet_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-003 | RT=10 DROP+count+irq | `tc_rt10_must_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-004 | RT=11 DROP+count+irq | `tc_rt11_must_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-005 | rt_shortest_unimpl +1 | `tc_rt_shortest_unimpl_count` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-006 | G1 asserts irq_logic | `tc_rt_shortest_irq_logic` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-007 | Exact Route absent | `tc_neg_exact_route` | `tb/vibe/tests/tc_neg_exact_route.sv` | NEG |
| TP-RT-008 | do not rewrite RT | `tc_rt_no_rewrite` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-009 | RT=10 not treated as 00 | `tc_rt10_not_as_rt00` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-010 | counter sat 32'hFFFF_FFFF | `tc_rt_counter_32b_sat` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-011 | default table all-0 → port 0 | `tc_default_rt_all0_port0` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-012 | flow key includes VL | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-001 | CFG0 does not consume credit | `tc_cfg0_no_credit` | `tb/vibe/tests/tc_cfg0_no_credit.sv` | MAPPED |
| TP-CFG-002 | CFG0 terminate in DLL not fabric | `tc_cfg0_term_not_fabric` | `tb/vibe/tests/tc_cfg0_term_not_fabric.sv` | MAPPED |
| TP-CFG-003 | CFG3 forward | `tc_cfg3_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-004 | CFG4 forward | `tc_cfg4_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-005 | CFG5 forward | `tc_cfg5_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-006 | CFG6 three terminate classes else FORWARD | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-007 | CFG7 forward | `tc_cfg7_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-008 | CFG9 forward | `tc_cfg9_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-009 | reserved CFG 1/2/8/10/15 forward | `tc_cfg_reserved_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-010 | CFG0 fabric no special path | `tc_cfg0_fabric_no_special` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-011 | CFG9 no ICRC | `tc_cfg9_no_icrc` | `tb/vibe/tests/tc_cfg9_no_icrc.sv` | ADDED |
| TP-CFG-012 | CNA unwritten: no DCNA match | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CRD-001 | pending ≥1024 flit backpressure | `tc_credit_1024_flit_bp` | `tb/vibe/tests/tc_credit_1024_flit_bp.sv` | MAPPED |
| TP-CRD-002 | credit return timeout 1 µs | `tc_credit_timeout_1us` | `tb/vibe/tests/tc_credit_timeout_1us.sv` | MAPPED |
| TP-CRD-003 | VOQ deadlock 1 µs independent | `tc_deadlock_timeout_1us` | `tb/vibe/tests/tc_deadlock_timeout_1us.sv` | MAPPED |
| TP-CRD-004 | G7 closed: 1024 is flit (no cell guess) | `tc_credit_1024_hole` | `tb/vibe/tests/tc_credit_1024_hole.sv` | MAPPED |
| TP-CRD-005 | LinkUp=0 credit/pointers reset | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-CRD-006 | DLL TX credit_low blocks NW | `tc_dll_tx_cfg0` | `tb/vibe/tests/tc_dll_tx_cfg0.sv` | MAPPED |
| TP-CRD-007 | CFG0 DLLCB no data credit | `tc_cfg0_no_credit` | `tb/vibe/tests/tc_cfg0_no_credit.sv` | MAPPED |
| TP-PHY-001 | clk_fab 1.25 GHz domain | `tc_port_smoke` | `tb/vibe/tests/tc_port_smoke.sv` | MAPPED |
| TP-PHY-002 | txclk/rxclk 922 MHz independent | `tc_pma_922mhz` | `tb/vibe/tests/tc_pma_922mhz.sv` | MAPPED |
| TP-PHY-003 | txdata[511:0] no PMA handshake | `tc_pma_512b_slice` | `tb/vibe/tests/tc_pma_512b_slice.sv` | MAPPED |
| TP-PHY-004 | lane slice 128b ×4 | `tc_pma_512b_slice` | `tb/vibe/tests/tc_pma_512b_slice.sv` | MAPPED |
| TP-PHY-005 | NW 640b vld/ready @ clk_fab | `tc_nw_adapt_linkready` | `tb/vibe/tests/tc_nw_adapt_linkready.sv` | MAPPED |
| TP-PHY-006 | flit = 20 bytes never 640b | `tc_pkt_len_legal_16_4300` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-PHY-007 | U26 width chain | `tc_phy_u26_chain` | `tb/vibe/tests/tc_phy_u26_chain.sv` | MAPPED |
| TP-PHY-008 | gear 160↔128 residue | `tc_gear_160_128` | `tb/vibe/tests/tc_gear_160_128.sv` | MAPPED |
| TP-PHY-009 | legal NW/LPH beat accepted | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-PHY-010 | PMA txdata contents vs golden T=4 | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-PHY-011 | AMCTL insert outside FEC | `tc_pcs_amctl` | `tb/vibe/tests/tc_pcs_amctl.sv` | MAPPED |
| TP-PHY-012 | TX→PMA→RX loopback LPH | `tc_nw_pkt_pma_loopback` | `tb/vibe/tests/tc_nw_pkt_pma_loopback.sv` | MAPPED |
| TP-PHY-013 | scramble LTB not AMCTL | `tc_pcs_scramble` | `tb/vibe/tests/tc_pcs_scramble.sv` | MAPPED |
| TP-PHY-014 | no Gray/precoding analog PMA | `tc_neg_absent_features` | `tb/vibe/tests/tc_neg_absent_features.sv` | NEG |
| TP-PHY-015 | AFIFO CDC gray pointers | `tc_afifo_afull10` | `tb/vibe/tests/tc_afifo_afull10.sv` | MAPPED |
| TP-PHY-016 | RX deskew | `tc_pcs_rx_deskew` | `tb/vibe/tests/tc_pcs_rx_deskew.sv` | MAPPED |
| TP-PHY-017 | Mode-2 PAM4 x4 only | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-PHY-018 | txdata lane0=[127:0] .. lane3 | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-FEC-001 | T=4 default RS(128,120) | `tc_pcs_fec_dual_enc` | `tb/vibe/tests/tc_pcs_fec_dual_enc.sv` | MAPPED |
| TP-FEC-002 | T=2 mode pin | `tc_pcs_fec_t2` | `tb/vibe/tests/tc_pcs_fec_t2.sv` | MAPPED |
| TP-FEC-003 | FEC bypass still 6-flit align | `tc_pcs_fec_bypass` | `tb/vibe/tests/tc_pcs_fec_bypass.sv` | MAPPED |
| TP-FEC-004 | dual encoder interleave | `tc_pcs_fec_dual_enc` | `tb/vibe/tests/tc_pcs_fec_dual_enc.sv` | MAPPED |
| TP-FEC-005 | FEC fail → Go-Back-N | `tc_fec_fail_gbn` | `tb/vibe/tests/tc_fec_fail_gbn.sv` | ADDED |
| TP-DLL-001 | LinkUp=0 → Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-002 | Param_Init | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-003 | Credit_Init | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-004 | Normal status_up | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-005 | entity rst must not force Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-006 | port_rst → Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-007 | BCRC CRC30 poly | `tc_bcrc_crc30` | `tb/vibe/tests/tc_bcrc_crc30.sv` | MAPPED |
| TP-DLL-008 | LinkUp=0 pad0 + ERROR_FLAG | `tc_dll_rx_errflag` | `tb/vibe/tests/tc_dll_rx_errflag.sv` | MAPPED |
| TP-DLL-009 | DLL TX CFG0 | `tc_dll_tx_cfg0` | `tb/vibe/tests/tc_dll_tx_cfg0.sv` | MAPPED |
| TP-DLL-010 | VL1–15 hardware usable | `tc_vl_rr_0_15` | `tb/vibe/tests/tc_vl_rr_0_15.sv` | MAPPED |
| TP-DLL-011 | DLL integration smoke | `tc_dll` | `tb/vibe/tests/tc_dll.sv` | MAPPED |
| TP-DLL-012 | dll_error → Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-LMSM-001 | reset → Link_Idle | `tc_lmsm_idle_discovery` | `tb/vibe/tests/tc_lmsm_idle_discovery.sv` | MAPPED |
| TP-LMSM-002 | lmsm_go Idle→Discovery | `tc_lmsm_idle_discovery` | `tb/vibe/tests/tc_lmsm_idle_discovery.sv` | MAPPED |
| TP-LMSM-003 | Discovery walk / timeout | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-004 | Config walk | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-005 | Send_NullBlock → Active | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-006 | Link_Active LinkReady | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-007 | Retrain.Active / Confirm | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-008 | width x4 else Link_Idle | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-009 | lane0 fail → Retrain | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-010 | no Probe / QDLWS / RXEQ | `tc_neg_absent_features` | `tb/vibe/tests/tc_neg_absent_features.sv` | NEG |
| TP-CDC-001 | AFIFO almost_full occ≥10 | `tc_afifo_afull10` | `tb/vibe/tests/tc_afifo_afull10.sv` | MAPPED |
| TP-CDC-002 | gear 160→128 | `tc_gear_160_128` | `tb/vibe/tests/tc_gear_160_128.sv` | MAPPED |
| TP-CDC-003 | gear 128→160 | `tc_gear_128_160` | `tb/vibe/tests/tc_gear_128_160.sv` | MAPPED |
| TP-CDC-004 | rst_sync 2-FF | `tc_rst_sync` | `tb/vibe/tests/tc_rst_sync.sv` | MAPPED |
| TP-CDC-005 | U26 PMA+gear chain | `tc_phy_u26_chain` | `tb/vibe/tests/tc_phy_u26_chain.sv` | MAPPED |
| TP-CDC-006 | RX AFIFO overflow irq source | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-FAB-001 | SAF full packet before xbar | `tc_saf_full_pkt` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-FAB-002 | len not in 16–4300 → drop+irq | `tc_pkt_len_err_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-FAB-003 | legal 20 B / 4300 B | `tc_pkt_len_legal_16_4300` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-FAB-004 | port 0 Down → drop+count no flood | `tc_p0_down_drop` | `tb/vibe/tests/tc_p0_down_drop.sv` | ADDED |
| TP-FAB-005 | xbar ingress RR / grant | `tc_xbar_unit` | `tb/vibe/tests/tc_xbar_unit.sv` | MAPPED |
| TP-FAB-006 | down port no DLLDP | `tc_xbar_unit` | `tb/vibe/tests/tc_xbar_unit.sv` | MAPPED |
| TP-FAB-007 | fabric G1 DROP path | `tc_fabric_g1` | `tb/vibe/tests/tc_fabric_g1.sv` | MAPPED |
| TP-FAB-008 | route_lu dest→bitmap | `tc_route_lu` | `tb/vibe/tests/tc_route_lu.sv` | MAPPED |
| TP-FAB-009 | SAF ingress assemble | `tc_saf_ing` | `tb/vibe/tests/tc_saf_ing.sv` | MAPPED |
| TP-FAB-010 | G1 sat + CFG6 drain | `tc_fabric_line_holes` | `tb/vibe/tests/tc_fabric_line_holes.sv` | MAPPED |
| TP-RTY-001 | retry_buf depth 256 | `tc_retry_buf_256` | `tb/vibe/tests/tc_retry_buf_256.sv` | MAPPED |
| TP-RTY-002 | RETRY_REQ GBN start | `tc_retry_req_gbn` | `tb/vibe/tests/tc_retry_req_gbn.sv` | MAPPED |
| TP-RTY-003 | RETRY_ACK replay | `tc_retry_ack_replay` | `tb/vibe/tests/tc_retry_ack_replay.sv` | MAPPED |
| TP-RTY-004 | WAIT timeout → Retrain | `tc_retry_wait_retrain` | `tb/vibe/tests/tc_retry_wait_retrain.sv` | MAPPED |
| TP-RTY-005 | NUM_RETRY / PHY reinit | `tc_retry_wait_retrain` | `tb/vibe/tests/tc_retry_wait_retrain.sv` | MAPPED |
| TP-RTY-006 | retry ERROR wait Port/device rst | `tc_retry_req_gbn` | `tb/vibe/tests/tc_retry_req_gbn.sv` | MAPPED |
| TP-ICRC-001 | transit MUST NOT recompute ICRC | `tc_icrc_transit_no_recompute` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-ICRC-002 | CRC32 unit sender/receiver | `tc_icrc_txrx_vs_transit` | `tb/vibe/tests/tc_icrc_txrx_vs_transit.sv` | MAPPED |
| TP-ICRC-003 | CFG9 no ICRC | `tc_cfg9_no_icrc` | `tb/vibe/tests/tc_cfg9_no_icrc.sv` | ADDED |
| TP-BCRC-001 | CRC30 poly / init all-1 | `tc_bcrc_crc30` | `tb/vibe/tests/tc_bcrc_crc30.sv` | MAPPED |
| TP-BCRC-002 | bit30 ERROR_FLAG | `tc_dll_rx_errflag` | `tb/vibe/tests/tc_dll_rx_errflag.sv` | MAPPED |
| TP-MGMT-001 | Port Reset cmd=3 | `tc_port_rst_via_cfg` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-MGMT-002 | device reset cmd=4 clears CNA | `tc_device_rst_via_cfg` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-MGMT-003 | CNA endpoint terminate | `tc_cna_ep` | `tb/vibe/tests/tc_cna_ep.sv` | MAPPED |
| TP-MGMT-004 | mgmt bypass FIFO no xbar | `tc_mgmt_byp` | `tb/vibe/tests/tc_mgmt_byp.sv` | MAPPED |
| TP-MGMT-005 | lmsm_go pulse cmd=5 | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-MGMT-006 | mgmt wrapper + rst_ctl | `tc_mgmt` | `tb/vibe/tests/tc_mgmt.sv` | MAPPED |
| TP-IRQ-001 | G1 → irq_logic | `tc_rt_shortest_irq_logic` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-IRQ-002 | irq_logic sticky until clr/rst | `tc_rt_irq_logic_sticky` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-IRQ-003 | OR of §15 sources | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-004 | Packet Length Error irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-005 | deadlock drop irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-006 | DL Protocol Error irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-007 | DL Retry Error irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-008 | RX AFIFO overflow irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-VL-001 | VL RR among non-empty VOQs | `tc_vl_rr` | `tb/vibe/tests/tc_vl_rr.sv` | MAPPED |
| TP-VL-002 | VL0–15 hardware present | `tc_vl_rr_0_15` | `tb/vibe/tests/tc_vl_rr_0_15.sv` | MAPPED |
| TP-VL-003 | flow key {CFG,src,dest,VL} | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-FECN-001 | FECN rewrite vs watermark | `tc_fecn_mark` | `tb/vibe/tests/tc_fecn_mark.sv` | MAPPED |
| TP-FECN-002 | not CAQM | `tc_neg_absent_features` | `tb/vibe/tests/tc_neg_absent_features.sv` | NEG |
| TP-NW-001 | LinkReady in nw_adapt ready | `tc_nw_adapt_linkready` | `tb/vibe/tests/tc_nw_adapt_linkready.sv` | MAPPED |
| TP-NW-002 | NW pkt → PMA TX | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-NW-003 | NW pkt PMA loopback | `tc_nw_pkt_pma_loopback` | `tb/vibe/tests/tc_nw_pkt_pma_loopback.sv` | MAPPED |
| TP-PKT-001 | oversize length drop | `tc_pkt_len_err_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-PKT-002 | legal length 20..4300 | `tc_pkt_len_legal_16_4300` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-PKT-003 | SAF hold until EOP | `tc_saf_full_pkt` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-QDL-001 | QDLWS absent | `tc_neg_qdlws` | `tb/vibe/tests/tc_neg_qdlws.sv` | NEG |
| TP-NEG-001 | QDLWS scan_absent | `tc_neg_qdlws` | `tb/vibe/tests/tc_neg_qdlws.sv` | NEG |
| TP-NEG-002 | Exact Route absent | `tc_neg_exact_route` | `tb/vibe/tests/tc_neg_exact_route.sv` | NEG |
| TP-NEG-003 | Port CNA absent | `tc_neg_port_cna` | `tb/vibe/tests/tc_neg_port_cna.sv` | NEG |
| TP-NEG-004 | cut-through absent (SAF only) | `tc_neg_cut_through` | `tb/vibe/tests/tc_neg_cut_through.sv` | NEG |
| TP-NEG-005 | UBFM absent | `tc_neg_ubfm` | `tb/vibe/tests/tc_neg_ubfm.sv` | NEG |
| TP-NEG-006 | hi_FEC_BER absent | `tc_neg_hi_fec_ber` | `tb/vibe/tests/tc_neg_hi_fec_ber.sv` | NEG |
| TP-NEG-007 | Probe / Dijkstra absent | `tc_neg_probe` | `tb/vibe/tests/tc_neg_probe.sv` | NEG |
| TP-NEG-008 | Dijkstra / shortest-path absent | `tc_neg_dijkstra` | `tb/vibe/tests/tc_neg_dijkstra.sv` | NEG |
| TP-AM-001 | AMCTL TX eBCH-16 | `tc_pcs_amctl` | `tb/vibe/tests/tc_pcs_amctl.sv` | MAPPED |
| TP-AM-002 | AMCTL RX lock per lane | `tc_pcs_rx_amctl` | `tb/vibe/tests/tc_pcs_rx_amctl.sv` | MAPPED |
| TP-AM-003 | eBCH-16 LUT | `tc_ebch16_lut` | `tb/vibe/tests/tc_ebch16_lut.sv` | MAPPED |
| TP-AM-004 | AMCTL confirm / unlock N | `tc_lmsm_vlock` | `tb/vibe/tests/tc_lmsm_vlock.sv` | MAPPED |
| TP-HOLE-001 | Max Index unpublished | `tc_hole_max_index` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-002 | extra IRQ pins unpublished | `tc_hole_extra_irq_pins` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-003 | extra reset pins unpublished | `tc_hole_extra_rst_pins` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-004 | CNA default unpublished | `tc_hole_cna_default` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-005 | lmsm_go source unpublished | `tc_hole_lmsm_go_source` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-006 | package pins unpublished | `tc_hole_package_pins` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-007 | RXEQ_Optimize unpublished | `tc_hole_rxeq_optimize` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-008 | Change_Speed unpublished | `tc_hole_change_speed` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-009 | polarity/lane-swap unpublished | `tc_hole_polarity_laneswap` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-010 | Fig 3-28 missing arcs unpublished | `tc_hole_fig328_arcs` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-011 | credit underflow unpublished | `tc_hole_credit_underflow` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-012 | optical unpublished | `tc_hole_optical` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
