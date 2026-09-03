## Acceptance + classification (do not chase LINE 100%)

Gate (芯片开发PM): **LINE ≥95% + waiver**. This merge: **702/727 = 96.6% PASS**.
FSM = line on state `case`/`if`. Toggle miss = unused wide-bus bits (not the gate).
Functional coverage = official **159 TPs** (`TP_TC_MATRIX.md`): 122 MAPPED/ADDED +
28 NEG scored; 9 HOLE = freeze SPEC **非目标 / waiver**. **Published FUNC = 100%.**

HOLE nine (非目标 / waiver): TP-HOLE-G2, G3, G4, G5, G6, G8, G9, 010, 012.

Every uncovered LINE (`COVERAGE_HOLES.md`):

| File:line | Class |
|-----------|--------|
| `vibe_lmsm.sv:101–108` | **TOOL** (`tmr_load`; 设计 agreed) |
| `vibe_pcs_rx_amctl_lock.sv:55–58` | **TOOL** (`dec_lid` inline) |
| `vibe_dll_tx.sv:151, 155, 159` | **TOOL** (pad combo settles) |
| `vibe_dll_tx.sv:98 if` | **WAIVER / 防御** — `val_b==0` shift defense; not DUT dead |
| `vibe_dll_tx.sv:144 else` | **WAIVER / 防御** — `n_flits==0` rem < 20 B; not DUT dead |
| `vibe_pcs_tx_g1.sv:51 else` | **TB空洞 — WAIVE** (not cheap) |
| `vibe_pcs_rx.sv:181, 182, 194, 198, 207, 211` | **TB空洞 — WAIVE** (rem/pend; not cheap) |

AS-0.1 / freeze SPEC 非目标: Probe / Dijkstra / QDLWS / Exact Route / UBFM + HOLE nine.
Suite Verilator bind OOM on VOQ — per-module clusters. Port/top 0 records (OOM).
