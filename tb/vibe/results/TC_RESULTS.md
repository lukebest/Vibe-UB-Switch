# TC results (this PR)

Simulator: Icarus Verilog 12.0. TB does not modify `rtl/`. FS-0.2.4 G7:
credit threshold 1024 is **flit**. Old `tb/ub_*` not run.

**Counts:** suite 26 + units 47 + top 1 = **74 named TCs**. Static `make neg`
scan: 9 PASS. **Icarus: all PASS (0 FAIL).**

## Suite (`make suite`) — 26/26 PASS

| Test | Result |
|------|--------|
| tc_rt00_per_flow_rr_fwd | PASS |
| tc_rt01_per_packet_rr_fwd | PASS |
| tc_rt10_must_drop (TP-RT-003) | PASS |
| tc_rt11_must_drop (TP-RT-004) | PASS |
| tc_rt_shortest_unimpl_count | PASS |
| tc_rt_shortest_irq_logic | PASS |
| tc_rt_irq_logic_sticky | PASS |
| tc_rt_no_rewrite | PASS |
| tc_rt10_not_as_rt00 | PASS |
| tc_rt_counter_32b_sat | PASS |
| tc_cfg_identity_guid_class | PASS |
| tc_default_rt_all0_port0 | PASS |
| tc_pkt_len_err_drop | PASS (16 B unreachable; 1-flit clamp=20 B) |
| tc_cfg6_term_vs_fwd | PASS |
| tc_saf_full_pkt | PASS |
| tc_icrc_transit_no_recompute | PASS |
| tc_cfg3_fwd | PASS |
| tc_cfg4_fwd | PASS |
| tc_cfg5_fwd | PASS |
| tc_cfg7_fwd | PASS |
| tc_cfg9_fwd | PASS |
| tc_cfg_reserved_fwd | PASS |
| tc_cfg0_fabric_no_special | PASS (DLL terminates CFG0) |
| tc_port_rst_via_cfg | PASS |
| tc_device_rst_via_cfg | PASS |
| tc_pkt_len_legal_16_4300 | PASS |

`SUITE pass=26 fail=0 ran=26`

## Units (`make units`) — 47/47 PASS

| Test | Result | Notes |
|------|--------|-------|
| tc_cfg0_term_not_fabric | PASS | DLL `cfg0_hit`, no `nw_vld` |
| tc_icrc_txrx_vs_transit | PASS | unit CRC; `cna_ep` has no `vibe_icrc` (NOTE) |
| tc_vl_rr | PASS | VL0/VL2 |
| tc_vl_rr_0_15 | PASS | all 16 VLs |
| tc_credit_1024_hole | PASS | G7 closed; see flit_bp |
| tc_credit_1024_flit_bp | PASS | 1023 no BP; 1024 `bp_nw`+`force_crd_ack`; no `/n` |
| tc_credit_timeout_1us | PASS | 1250 `clk_fab` → `proto_err` |
| tc_deadlock_timeout_1us | PASS | separate VOQ age 1 µs |
| tc_cfg0_no_credit | PASS | `is_cfg0` does not add cells |
| tc_dll_tx_cfg0 | PASS | TX+credit cells stay 0 |
| tc_dll_sm_states | PASS | Dis→Parm→Crd→Nrm; LinkUp=0→Dis |
| tc_bcrc_crc30 | PASS | bit31=0 bit30=ERROR_FLAG |
| tc_retry_buf_256 | PASS | free=256; Null/Retry skip; ovf proto_err |
| tc_retry_req_gbn | PASS | start_retry → REQ drop_data |
| tc_retry_ack_replay | PASS | start_ack leaves NORMAL |
| tc_afifo_afull10 | PASS | occ≥10 |
| tc_gear_160_128 | PASS | 4×160 → 5×128 |
| tc_gear_128_160 | PASS | 5×128 → 4×160 |
| tc_phy_u26_chain | PASS | gears + PMA slice |
| tc_pma_512b_slice | PASS | [127:0]=lane0 |
| tc_pma_922mhz | PASS | T=1085 ps |
| tc_pcs_tx_g1_window | PASS | 960b window |
| tc_pcs_fec_bypass | PASS | two cw beats |
| tc_pcs_fec_dual_enc | PASS | T=4 both encoders start |
| tc_pcs_fec_t2 | PASS | T=2 both encoders start |
| tc_pcs_cw2beat | PASS | 1024→2×512 |
| tc_pcs_amctl | PASS | nonzero 40-symbol |
| tc_pcs_scramble | PASS | en=0 pass-through |
| tc_ebch16_lut | PASS | sel0=0000 sel1=0A6F |
| tc_lmsm_idle_discovery | PASS | Idle→Discovery, not Probe |
| tc_rst_port_device | PASS | port pulse vs device hold |
| tc_fecn_mark | PASS | Mode=100 occ≥24 |
| tc_nw_adapt_linkready | PASS | LinkReady + mgmt pri |
| tc_mgmt_byp | PASS | 16×640 hold |
| tc_rst_sync | PASS | async assert, sync deassert |
| tc_rs_dec_syndrome | PASS | 128 symbols → done |
| tc_neg_absent_features | PASS | LMSM subset |
| tc_identity_cfg_space | PASS | |
| tc_xbar_unit | PASS | iverilog 640b `out_data` X |
| tc_neg_qdlws / exact_route / port_cna / cut_through / ubfm / hi_fec_ber / probe / dijkstra | PASS | |

## Top / static neg

| Test | Result |
|------|--------|
| tc_top_smoke | PASS |
| scan_absent (9 identifiers) | PASS |

## Failures (do not patch RTL)

None on this Icarus run. If a later TC fails, record name / stimulus /
expected vs actual / hier / `make -C tb/vibe …`.

## Coverage (Verilator 5.020, honest)

Custom C++ main writes `coverage.dat`. `-Wno-BLKLOOPINIT` (not an RTL patch).
36 unit clusters merged (incl. `vibe_xbar`). Full suite+VOQ Verilator compile
**OOM** (~7 GB); Icarus suite still ran those TCs.

| | Hit/tot | % |
|--|--------:|--:|
| **Line (`vibe_*.sv`)** | **408/650** | **62.8** |
| **Toggle** | **1627/9127** | **17.8** |
| **FSM** | (no VCS FSM engine; use line on state `case`) | |

100% of implemented `vibe_*` **not** achieved. See `tb/vibe/results/cov_report.md`
for per-module table, uncovered bins, and dead vs missing-stimulus notes.
