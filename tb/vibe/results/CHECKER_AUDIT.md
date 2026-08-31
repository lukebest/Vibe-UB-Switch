# Checker audit — `tb/vibe` vs FS-0.2.4 + AS-0.1

Audit of every named checker in `tb/vibe`. Spec is **FS-0.2.4** (credit, timeouts, G7) and **AS-0.1** (CFG6, ICRC, G1 RT=10/11, negatives). Old README / `tb/ub_*` are **void**. RTL is frozen (`rtl/` not patched).

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

## Credit (FS-0.2.4 / G7 closed)

Threshold **1024 is FLIT**. Pending path `pend += credit_ret_n` with **no divide-by-n**. Consume path may `ceil_div` by `grain_n` (cell accounting) — that is **not** the G7 unit.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_credit_1024_flit_bp` | `pending=1023` + 1 return → `credit_low`/`bp_nw`; 2-flit return does **not** `ceil_div` | OK |
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

## NW packet → PMA `txdata[511:0]` (FS-0.2.4 §1.4 / U26, AS-0.1 TX path)

Product boundary: `txdata[511:0]`, no extra handshake; `[127:0]=lane0` … `[511:384]=lane3`.

Previously missing: `tc_port_smoke` drives one `fab_tx` beat and never scores `txdata`. `tc_top_smoke` notes no packet BFM. PHY units use synthetic DLL/lane patterns.

| Checker | Spec | Verdict |
|---|---|---|
| `tc_nw_pkt_to_pma_tx` | TP-PHY-009/010/018: legal RT=00 NW beat accepted, then `txdata` contents | **ADDED** — bring-up: `lmsm_go` + hierarchical `force am_locked=1111` / `lid_bad=0` (peer AM) and one-cycle `force cells=64` (peer credit; power-on `credit_low` would otherwise block `nw_ready`). Scores: (1) `fab_tx_ready` handshake; (2) injected LPH on `u_p.pcs_tx_d` (DLL wrap; BCRC may replace `[31:0]`); (3) every `p_txv` beat `txdata=={lane3,lane2,lane1,lane0}`; (4) TB-only `vibe_pcs_tx` (DUT `fec_mode=T=4`, not bypass — RTL hardcodes `VIBE_FEC_T4`) + AFIFO + `vibe_gear_160_128` + pack vs DUT `txdata` (AMCTL in both). |
| `tc_nw_pkt_pma_loopback` | TP-PHY-012: TX→PMA→RX inverse, NW packet on `fab_rx` | **ADDED** — same DUT/packet; `rxdata=txdata`. Scores LPH (CFG/RT/SCNA/DCNA) **and** payload `[479:32]` (not just `fab_rx_vld`). |

DUT cannot be put in FEC bypass without an `rtl/` edit (`assign fec_mode = VIBE_FEC_T4`). Golden uses T=4. If either TC FAILs after bring-up, that is an RTL gap (verification does not patch `rtl/`).

---

## Unit checkers (PHY / DLL / FEC / LMSM / retry)

All OK vs FS-0.2.4 / AS-0.1 as previously locked (FEC T=4/T=2/bypass, AMCTL, BCRC, VL0–15 RR, retry 256, GBN, AFIFO, named negatives). New stimulus TCs (`tc_lmsm_walk`, `tc_retry_wait_retrain`, PCS RX wrappers, SAF/route/cna/irq/mgmt clusters) **add coverage**, they do not change the locked rules.

---

## Summary

| Verdict | Count |
|---|---|
| OK | 30+ (suite + units + static) |
| FIXED | 2 families: G1 `expect_drop_only`; CFG6 terminate-class completeness |
