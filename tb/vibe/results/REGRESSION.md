# TP-0.3 regression (Icarus gate)

Compiled **TB** on `cursor/vibe-tb-g1-6065` against **PR4 HEAD rtl** (sim-only checkout; not committed).

| Item | Value |
|------|--------|
| RTL compiled SHA | `7a4abe2f1832603b52b5ae36c65f5b580c942661` |
| RTL ref | `origin/cursor/as01-rtl-82c7` (PR #4 lineage; commit message: merge of PR #5) |
| Gate | `make -C tb/vibe sim` (suite + units + top + neg) |
| `SIM_EXIT` | **0** |
| `summarize.sh` | **TOTAL_PASS_LINES=134  TOTAL_FAIL_LINES=0** (excl. `cov.log`) |
| Suite | **26/26 PASS** (`SUITE_RESULT PASS`) |
| Units | **all `run1` files PASS** (`fail_n=0`; includes new hole/gap TCs) |
| Top | `PASS tc_top_smoke` |
| Neg scan | 10/10 PASS (incl. new `neg_optical`) |

Checkers were **not** weakened. G1 still DROP + `rt_shortest_unimpl` + sticky `irq_logic`. Credit threshold **1024 is flit**. Credit 1 µs and VOQ deadlock 1 µs are independent. CFG6 three terminate classes else FORWARD.

## FAIL list (handoff to 设计)

**None.** No Icarus `FAIL` block in suite, units, top, or `scan_absent` for this SHA.

There is no stimulus / expected / actual / hier / reproduce block to quote. If a later RTL drop cannot implement a MUST TP, the existing TC must FAIL with that print — do not patch RTL from this TB branch.

Stale `tb/vibe/results/cov.log` (Verilator coverage, not part of `make sim`) still contains historical FAIL lines and is **excluded**.

## New TCs this pass (all PASS vs `7a4abe2`)

| TC | TP | Notes |
|----|----|--------|
| `tc_p0_down_drop` | TP-FAB-004 | default all-0 → port 0; port 0 Down → drop+count |
| `tc_cfg9_no_icrc` | TP-CFG-011 / TP-ICRC-003 | CFG9 no ICRC; CCI/LBF unchanged; forward |
| `tc_fec_fail_gbn` | TP-FEC-005 | `fec_fail` → `start_retry` |
| `tc_tp_holes` | TP-HOLE-001..012 | PASS + NOTE; no invented values |
| `tc_neg_no_optical` | NEG companion | optical absent |

## Notable existing TCs vs this SHA

| TC | Result |
|----|--------|
| `tc_nw_pkt_to_pma_tx` | PASS |
| `tc_nw_pkt_pma_loopback` | PASS — `fab_rx` LPH+payload; `am_lock_end=1111`; `saw_fec_fail=0` |
| `tc_rt10_must_drop` / `tc_rt11_must_drop` | PASS |
| `tc_cfg6_term_vs_fwd` | PASS |

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

See `TP_TC_MATRIX.md`: **159/159** TPs. Verdicts: MAPPED=130, ADDED=4, HOLE=12, NEG=13.
