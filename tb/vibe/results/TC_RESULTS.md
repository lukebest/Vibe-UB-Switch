# TC results (this PR)

Simulator: Icarus Verilog 12.0. TB does not modify `rtl/`. Rebased onto
`5be17592` (PR1: qualify fabric `cfg6_hit` with CFG6 terminate). Old `tb/ub_*` not run.

## Minimum / G1 (must) — re-run after rebase: all PASS

| Test | Result | Notes |
|------|--------|-------|
| tc_rt00_per_flow_rr_fwd | PASS | `vibe_port_sel`+`vibe_route_lu`; fabric `x_in_v` |
| tc_rt01_per_packet_rr_fwd | PASS | port_sel per-packet RR |
| tc_rt10_must_drop (TP-RT-003) | PASS | fabric drop, no egr |
| tc_rt11_must_drop (TP-RT-004) | PASS | fabric drop, no egr |
| tc_rt_shortest_unimpl_count | PASS | hier `u_fab.rt_shortest_unimpl` 0→1→2 |
| tc_rt_shortest_irq_logic | PASS | `irq_logic` after RT=10 |
| tc_rt_irq_logic_sticky | PASS | sticky; clr cfg_wr_cmd=7 and device rst |
| tc_rt_no_rewrite | PASS | no RT rewrite on drop path |
| tc_rt10_not_as_rt00 | PASS | RT=00 → egr=2; RT=10 drop; fabric `x_in_v=0` |
| tc_rt_counter_32b_sat | PASS | force-preload FFFFFFFE → FFFFFFFF, no wrap |
| tc_cfg_identity_guid_class | PASS | GUID 0x3, Class 0x0300, CNA write |
| tc_default_rt_all0_port0 | PASS | default → port 0 |
| tc_pkt_len_err_drop | PASS | oversize 4480 B → len_err+irq; &lt;16 B unreachable (1-flit clamp) |

## Extra locked / hole / negative

| Test | Result | Notes |
|------|--------|-------|
| tc_cfg0_term_not_fabric | PASS | `vibe_dll_rx` CFG0 → cfg0_hit, no `nw_vld` |
| tc_cfg6_term_vs_fwd | **PASS** (after `5be17592`) | Expected unchanged. See re-run below. |
| tc_icrc_txrx_vs_transit | PASS | unit CRC; cna_ep has no `vibe_icrc` (NOTE); transit SAF header unchanged |
| tc_icrc_transit_no_recompute | PASS | suite |
| tc_vl_rr | PASS | VL0/VL2 walk |
| tc_saf_full_pkt | PASS | no `saf_v` after 1 of 2 beats |
| tc_credit_1024_hole | PASS | threshold 1024; **unit cell vs flit is HOLE** |
| tc_neg_absent_features | PASS | lmsm_go → Discovery, not Probe |
| scan_absent (QDLWS/Exact Route/Port CNA/SCNA/cut-through/UBFM/hi_FEC_BER/Probe/Dijkstra) | PASS | |
| tc_xbar_unit | PASS | dest/grant work; **640b `out_data` is X in Icarus** |
| tc_top_smoke | PASS | pins, cfg CNA, hier `dut.u_fab.rt_shortest_unimpl==0` |
| tc_identity_cfg_space | PASS | unit cfg_space |

## tc_cfg6_term_vs_fwd re-run (`5be17592`)

```
make -C tb/vibe suite TC=tc_cfg6_term_vs_fwd
```

Expected (unchanged): cna_ep terminate when DCNA==written CNA (`consume`/`reply`);
not terminate when DCNA!=CNA; fabric CFG6 that must forward has `x_in_v=1`
(not excluded by `cfg6_hit`).

Actual: **PASS**

| Signal | Value |
|--------|--------|
| `u_fab.cfg6_hit` | `0000` |
| `u_fab.x_in_v` | `0001` |
| `u_mgmt.cfg6_consume` | `0000` |
| `cna_written` / `cna` | `0` / `0000` (post-reset; DCNA=`0x2222`, NLP=0) |

Suite after rebase: `pass=16 fail=0`.

## Coverage

Not faked. Icarus has no coverage. Verilator `--coverage` did not complete (see `tb/vibe/cov/README.md`).
