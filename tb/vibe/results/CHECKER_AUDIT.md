# Checker audit — `tb/vibe` vs FS-0.2.7 / AS-0.1.2

Audit of every named checker in `tb/vibe`. Spec is **FS-0.2.7 / AS-0.1.2** (Overlay B: NW `data[511:0]`; 640b is DLL↔PCS; credit **1024 = cell**) plus locked G1 / CFG6 / ICRC. Old README / `tb/ub_*` are **void**. RTL is frozen (`rtl/` not patched).

Verdict: **OK** = checker already scored the locked rule. **FIXED** = checker was wrong or incomplete vs spec and was corrected in this revision.

---

## G1 — RT=10/11 DROP + 32-bit sat + sticky irq_logic

| Checker | Spec | Verdict |
|---|---|---|
| `tc_rt00_per_flow_rr_fwd` | AS-0.1: RT=00 per-flow RR **forward** | OK |
| `tc_rt01_per_packet_rr_fwd` | AS-0.1: RT=01 per-packet RR **forward** | OK |
| `tc_rt10_must_drop` | AS-0.1 G1: RT=10 **DROP**, not shortest-path, not alias 00 | **FIXED** — `expect_drop_only` used to PASS on drop even if `rt_shortest_unimpl` did not increment (dead `if (counter !== cnt+1)` after `pass`). Now requires increment (or sat) **and** no egress. |
| `tc_rt11_must_drop` | same, RT=11 | **FIXED** (same helper) |
| `tc_rt_shortest_unimpl_count` | increment-per-event, 32-bit `+1` | OK |
| `tc_rt_shortest_irq_logic` | `irq_logic` after first RT=10/11 | OK |
| `tc_rt_irq_logic_sticky` | sticky until static `cfg_wr` / reset | OK |
| `tc_rt_no_rewrite` | drop, do **not** rewrite RT to 00/01 | OK |
| `tc_rt10_not_as_rt00` | RT=10 is **not** treated as RT=00 | OK |
| `tc_rt_counter_32b_sat` | 32-bit saturate at `32'hFFFF_FFFF` | OK |

No Dijkstra / shortest-path TC exists (correct: non-goal). Detector is `port_sel` (`g1_comb`) → `vibe_irq_agg`.

---

## CFG6 terminate vs FORWARD (AS-0.1 §9)

Terminate **only** if: (a) 本CNA = statically written CNA **and** DCNA==mgmt CNA; (b) NLP=1 enumerate (even if DCNA ≠ us); (c) opcode `0x10` **targeting this device**. Else **FORWARD**. Power-on CNA unwritten must not match.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_cfg6_term_vs_fwd` | AS-0.1 §9 three-way terminate + else FORWARD | **FIXED** — previously only scored 本CNA terminate + generic else-FORWARD. Now scores NLP=1 terminate, opc `0x10` targeting-us terminate, opc `0x10` not-targeting FORWARD, CNA-unwritten no-match, and fabric `x_in_v=1` on non-term CFG6. |
| `tc_cfg3/4/5/7/9_fwd` | non-6 CFG classes FORWARD (no terminate-class) | OK |
| `tc_cfg_reserved_fwd` | reserved CFG FORWARD | OK |
| `tc_cfg0_fabric_no_special` | CFG0 terminate is **DLL**, fabric does not special-case | OK |
| `tc_cfg_identity_guid_class` | identity GUID class (CFG=0010) | OK |

---

## Credit (FS-0.2.6 / 0.2.7 / G7 closed)

Threshold **1024 is CELL**. Official unit is cell; this instance does **not** convert 1024 into 1024×n flit. `credit_ret_n` is already cells. Consume path may `ceil_div` by `grain_n` (cell accounting from flits) — that is **not** the G7 threshold unit.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_credit_1024_flit_bp` | `pending=1023` cell + 1 return → `bp_nw` at 1024 cell (filename historical) | **FIXED** — score is cell, not flit |
| `tc_credit_1024_hole` | same 1023→1024 cell `bp_nw` | **FIXED** |
| `tc_cfg0_no_credit` | CFG0 does not consume | OK |

---

## Timeouts are **separate** (both 1 µs = 1250 cyc @ 1.25 GHz)

| Checker | Spec | Verdict |
|---|---|---|
| `tc_credit_timeout_1us` | credit-return timeout 1 µs (`VIBE_US_CYC`) | OK — distinct DUT (`vibe_dll_credit`) |
| `tc_deadlock_timeout_1us` | VOQ deadlock 1 µs — **separate** timer (`vibe_voq_egr.age`) | OK |

They must not share a counter or a single TB event. They do not.

---

## ICRC (AS-0.1 §13)

Compute/check as **sender/receiver**. Transit does **not** recompute.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_icrc` (unit) | `vibe_icrc` compute + check | OK |
| `tc_icrc_transit_no_recompute` | fabric has **no** `vibe_icrc` instance | OK (static + runtime) |
| `scan_absent.sh` / `tc_no_icrc_on_transit` | same | OK |

**RTL gap (not a TB miss):** `vibe_cna_ep` does not instantiate `vibe_icrc` (echo only). Recorded; RTL frozen.

---

## Default table / negatives (AS-0.1)

| Checker | Spec | Verdict |
|---|---|---|
| `tc_default_rt_all0_port0` | power-on table all-0 → **port 0** | OK |
| `tc_no_scna` / `scan_absent` | no SCNA / Port CNA | OK |
| `tc_no_exact_route` | no Exact Route | OK |
| `tc_no_cut_through` | store-and-forward only | OK |
| `tc_no_ubfm` | no UBFM | OK |
| `tc_no_probe` | no Probe (LMSM Idle→Discovery on `lmsm_go`) | OK |
| `tc_no_dijkstra` | no Dijkstra | OK |
| `tc_saf_full_pkt` | SAF: full packet then one grant | OK |
| `tc_pkt_len_legal_16_4300` / `tc_pkt_len_err_drop` | 16–4300 B; oversize drop | OK |
| `tc_port_rst_via_cfg` / `tc_device_rst_via_cfg` | mgmt reset | OK |

---

## NW packet → PMA `txdata[511:0]` (FS-0.2.7 Overlay B / AS-0.1.2)

Product boundary: `txdata[511:0]`, no extra handshake; `[127:0]=lane0` … `[511:384]=lane3`.

Previously missing: `tc_port_smoke` drives one `fab_tx` beat and never scores `txdata`. `tc_top_smoke` notes no packet BFM. PHY units use synthetic DLL/lane patterns.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_nw_pkt_to_pma_tx` | TX NW→DLL: accepted beat `dll_tx_data[511:0] === GOLDEN_TX`; then PMA pack | **FIXED** — unique 512b GOLDEN (not a 640 slice, no LPH extract). Width≠512 cannot PASS. |
| `tc_nw_pkt_pma_loopback` | E2E: inject GOLDEN_TX; recover `fab_rx_data[511:0] === GOLDEN_TX` | **FIXED** — full 512-bit compare. `fec_fail=0` / `am_locked` supporting only. |
| `tc_phy_nw_dll_512b` | TX `dll_tx===GOLDEN_TX` and RX `fab_rx===GOLDEN_RX` | **FIXED** — beat-by-beat 512b content both directions. Width gate kept; PASS illegal without content. |
| `tc_nw_adapt_linkready` | Same 512b TX+RX GOLDEN + LinkReady / mgmt pri | **FIXED** — content compare always attempted. |

DUT cannot be put in FEC bypass without an `rtl/` edit (`assign fec_mode = VIBE_FEC_T4`). Golden uses T=4.

GOLDEN is a unique 512-bit constant (`vibe_tb_nw512.svh`) with SOP LPH at `[511:352]` (设计). Checkers score full 512 bits **and** CFG/RT/SCNA/DCNA from that 160b window (not README `[511:496]`). A 640-bit DUT pin cannot PASS. Overlay RTL for sim only; do not patch `rtl/`.

---

## Unit checkers (PHY / DLL / FEC / LMSM / retry)

All OK vs FS-0.2.4 / AS-0.1 as previously locked (FEC T=4/T=2/bypass, AMCTL, BCRC, VL0–15 RR, retry 256, GBN, AFIFO, named negatives). New stimulus TCs (`tc_lmsm_walk`, `tc_retry_wait_retrain`, PCS RX wrappers, SAF/route/cna/irq/mgmt clusters) **add coverage**, they do not change the locked rules.

---

## SHELL → REAL (seven files; official 159 IDs unchanged)

Each of these can FAIL with stimulus / expected / actual / hier. No `$display("PASS")` after a wait with `fail` stuck 0. No NOTE-then-PASS when the score missed. HOLE TCs in `tc_tp_holes` stay documentation.

| Checker | Was | Now |
|---|---|---|
| `tc_port_smoke` (TP-PHY-001) | one `fab_tx` beat, never scored `txdata` | TX `dll_tx===GOLDEN_TX`; RX `fab_rx===GOLDEN_TX` after PMA loopback. PMA pack supporting. |
| `tc_pcs_tx` | PASS if no `lane_vld` | FAIL if no `lane_vld` after legal dll + `link_up`. Lane words vs second `vibe_pcs_tx` golden (bypass). |
| `tc_pcs_rx` | force `wv`/`win`/`remv`; `fail` never set | TX→RX T=4 (port pin). Score `dll_vld` + LPH vs injected pack. No coverage-only force as pass. |
| `tc_fabric_line_holes` | coverage stimulus, FAIL=0 | CFG6 1-beat + 2-beat `cfg6_hit[0]`; G1 sat `FFFFFFFE`→`FFFFFFFF` then stay. |
| `tc_neg_official` | 19 PASS, no RTL scan | `scan_official_neg.py` → include; FAIL if forbidden id in `vibe_*.sv` code. One PASS per official NEG after clean scan. |
| `tc_credit_1024_hole` | NOTE+PASS stub | Same 1023→1024 **cell** `bp_nw` as `tc_credit_1024_flit_bp` (G7 closed as cell). |
| `tc_phy_nw_dll_512b` | (new Overlay B) | FAIL if `$bits(fab_tx_data)!==512`. Compiles against 640 DUT; FAIL goes to 设计. |
| `tc_top_smoke` | reset/CNA only, no packet BFM | Peer encodes RT=10 onto `rxdata_0`; score top `irq_logic`. FAIL if no packet / no irq (no NOTE skip). |

Optional (same pass): `tc_credit_no_underflow` scans `vibe_dll_credit` for underflow tokens + exercises return-without-consume. `tc_timers_indep` instantiates credit + VOQ; credit expiry must not set VOQ drop.

---

## Summary

| Verdict | Count |
|---|---|
| OK | 30+ (suite + units + static) |
| FIXED | 2 families: G1 `expect_drop_only`; CFG6 terminate-class completeness |
| ADDED | `tc_phy_nw_dll_512b` 512b TX+RX GOLDEN + SOP LPH `[511:352]` |
| FIXED | all five Overlay-B content TCs **PASS** vs `a3ecec9f` |
| SHELL→REAL | seven files above; checkers not weakened |
