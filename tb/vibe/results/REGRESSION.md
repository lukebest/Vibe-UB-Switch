# TP-0.3 regression (Icarus gate)

Compiled **TB** on `cursor/vibe-tb-g1-6065` against **PR4 HEAD rtl** (sim-only checkout; not committed).

Matrix IDs are the **official 159** in [`TP-0.3.md`](TP-0.3.md). No reconstructed `TP-FEC-*`, `TP-CFG-008..012`, or `TP-HOLE-001..009`.

| Item | Value |
|------|--------|
| RTL compiled SHA | `7a4abe2f1832603b52b5ae36c65f5b580c942661` |
| RTL ref | `origin/cursor/as01-rtl-82c7` (PR #4 lineage; merge of PR #5) |
| Gate | `make -C tb/vibe sim` (suite + units + top + neg) |
| `SIM_EXIT` | **0** |
| `summarize.sh` | **TOTAL_PASS_LINES=162  TOTAL_FAIL_LINES=0** (excl. `cov.log`; leftover `tc_credit.log` removed) |
| Suite | **27/27 PASS** (`SUITE_RESULT PASS`; includes `tc_cfg_fwd_class`) |
| Units | **all `run1` files PASS** (`fail_n=0`) |
| Top | `PASS tc_top_smoke` |
| Neg scan | 10/10 PASS (incl. `neg_optical`) |

Checkers were **not** weakened. G1 still DROP + `rt_shortest_unimpl` + sticky `irq_logic`. Credit threshold **1024 is flit**. Credit 1 µs and VOQ deadlock 1 µs are independent. CFG6 three terminate classes else FORWARD. CNA is **16-bit**.

## SHELL → REAL (this pass)

Seven former shells now compare stimulus / expected / actual / hier and can FAIL. `tc_tp_holes` stays HOLE documentation (no invented Max Index / pin / CNA default).

| TC | Result vs `7a4abe2` |
|----|---------------------|
| `tc_port_smoke` | PASS — PMA lane-pack + RX LPH (TP-PHY-001) |
| `tc_pcs_tx` | PASS — `lane_vld` + golden lanes |
| `tc_pcs_rx` | PASS — TX→RX T=4 `dll_vld` + LPH |
| `tc_fabric_line_holes` | PASS — CFG6 hit + G1 sat |
| `tc_neg_official` | PASS — 19 official NEG scans + summary (rtl grep) |
| `tc_credit_1024_hole` | PASS — 1023→1024 `bp_nw` (G7 closed) |
| `tc_top_smoke` | PASS — RT=10 on `rxdata_0` → `irq_logic` |

Optional: `tc_credit_no_underflow` PASS; `tc_timers_indep` PASS.

## FAIL list (handoff to 设计)

**None.** No Icarus `FAIL` block in suite, units, top, or `scan_absent` for this SHA.

There is no stimulus / expected / actual / hier / reproduce block to quote. If a later RTL drop cannot implement a MUST TP, the existing TC must FAIL with that print — do not patch RTL from this TB branch.

Stale `tb/vibe/results/cov.log` (Verilator coverage, not part of `make sim`) still contains historical FAIL lines and is **excluded**.

## Official remaps (kept TCs)

| TC | Official TP | Notes |
|----|-------------|--------|
| `tc_p0_down_drop` | TP-NW-003 (also TP-NW-006) | port0 Down → drop+count; no flood |
| `tc_cfg9_no_icrc` | TP-ICRC-004 (also TP-NEG-004) | CFG9 no ICRC; forward |
| `tc_fec_fail_gbn` | TP-PHY-015 | `fec_fail` → `start_retry`; TP-RTY-001 → `tc_retry_req_gbn` |
| `tc_tp_holes` | TP-HOLE-G2..G6, G8, G9, 010, 012 | split PASS notes; G7/011 mapped elsewhere |
| `tc_neg_no_optical` | TP-PHY-005 | optical absent |

## New MUST TCs this pass (all PASS vs `7a4abe2`)

| TC | Official TP | Notes |
|----|-------------|--------|
| `tc_id_nports_entity0` | TP-ID-002 / TP-NEG-010 | N_PORTS=4; no fifth port |
| `tc_cna_16bit` | TP-CFG-007 | write `00ABCDEF` → `cna=16'hCDEF` |
| `tc_rt_g1_official` | TP-RT-010/012/014/015/016 | RT=11 not as 01; unique/default still DROP |
| `tc_credit_grain_n` | TP-CRD-001/002 | n=8 → +1 cell; sat 65535 → `fc_ovf` |
| `tc_credit_no_underflow` | TP-CRD-008 | scan + return-without-consume |
| `tc_timers_indep` | TP-TIM-002 | credit expiry must not set VOQ drop |
| `tc_neg_official` | TP-NEG-* / ID-005/006 / … | `scan_official_neg.py` on `vibe_*.sv` |
| `tc_cfg_fwd_class` | TP-CFG-002 | suite: CFG 3/4/5/7/9 + reserved fwd |

## Notable existing TCs vs this SHA

| TC | Result |
|----|--------|
| `tc_nw_pkt_to_pma_tx` | PASS |
| `tc_nw_pkt_pma_loopback` | PASS |
| `tc_rt10_must_drop` / `tc_rt11_must_drop` | PASS |
| `tc_rt_irq_logic_sticky` | PASS (official TP-RT-007) |
| `tc_cfg6_term_vs_fwd` | PASS |
| `tc_credit_1024_flit_bp` | PASS (official TP-HOLE-G7 closed) |

## Reproduce

```bash
git fetch origin cursor/as01-rtl-82c7
git checkout origin/cursor/as01-rtl-82c7 -- rtl
git restore --staged rtl
make -C tb/vibe sim
# restore TB-branch rtl before any commit:
git checkout HEAD -- rtl
```

## Matrix

See [`TP_TC_MATRIX.md`](TP_TC_MATRIX.md) vs [`TP-0.3.md`](TP-0.3.md): **ID sets equal, 159/159**.
Verdicts: MAPPED=106, ADDED=16, HOLE=9, NEG=28.
