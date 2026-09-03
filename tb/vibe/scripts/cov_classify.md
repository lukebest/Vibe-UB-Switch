## Acceptance + classification (do not chase LINE 100%)

Gate (芯片开发PM): **LINE ≥95% + waiver**. This merge: **702/727 = 96.6% PASS**.
FSM = line on state `case`/`if`. Toggle miss = unused wide-bus bits (not the gate).
Functional coverage = official **159 TPs** (`TP_TC_MATRIX.md`): 122 MAPPED/ADDED +
28 NEG scored; 9 HOLE (FS unpublished) waived. **Published FUNC = 100%.**

Every uncovered LINE (`COVERAGE_HOLES.md`):

| File:line | Class |
|-----------|--------|
| `vibe_lmsm.sv:101–108` | **TOOL** (`tmr_load`; 设计 agreed) |
| `vibe_pcs_rx_amctl_lock.sv:55–58` | **TOOL** (`dec_lid` inline) |
| `vibe_dll_tx.sv:151, 155, 159` | **TOOL** (pad combo settles) |
| `vibe_dll_tx.sv:98 if` | **DUT死代码** — `val_b==0`; 设计; do not patch rtl/ |
| `vibe_dll_tx.sv:144 else` | **DUT死代码** — `n_flits==0`; 设计; do not patch rtl/ |
| `vibe_pcs_tx_g1.sv:51 else` | **TB空洞 — WAIVE** (not cheap) |
| `vibe_pcs_rx.sv:181, 182, 194, 198, 207, 211` | **TB空洞 — WAIVE** (rem/pend; not cheap) |

AS-0.1 non-goals (not in RTL): Probe / Dijkstra / QDLWS / Exact Route / UBFM.
Suite Verilator bind OOM on VOQ — per-module clusters. Port/top 0 records (OOM).
