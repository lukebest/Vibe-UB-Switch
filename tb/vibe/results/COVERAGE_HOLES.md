# Remaining Verilator LINE points (`vibe_*.sv`)

Gate: unique source LINE on implemented `vibe_*.sv`.
RTL under test: **PR13 SHA `25eb085e`** (sim-only overlay; this branch does not commit `rtl/`).
Tool: Verilator **5.020**. FSM = line hits on state `case`/`if` (no VCS FSM engine).

## First pass (before TB fill) — LINE **621/651 = 95.4%**, TOGGLE **4992/14508 = 34.4%**

Combo-only wrappers (`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`,
`vibe_pcs_tx`, `vibe_ub_switch`) contribute **0/0** line points.

Clusters: per-module / small groups. **`vibe_suite` is never bound** (VOQ OOM).

`pcs_rx` / `pcs_rx_unpack` / `pcs_rx_fec` / `port` / `top` produced **0 records**
this pass: Verilator 5.020 `%Error-UNSUPPORTED` on default input values
(`link_up=1'b0`, `am_gap=1'b0`) and `%Error-ASSIGNIN` on `force u_lmsm.*`
without `--public-flat-rw`. Script now has `-Wno-UNSUPPORTED` and port/top
`--public-flat-rw`. Those modules are **not** DUT dead — tool/cluster setup.

## First-pass uncovered LINE — classification

| File:line | Class | Why / stim |
|---|---|---|
| `vibe_lmsm.sv:101–108` | **TOOL** | `tmr_load` function case arms. Caller `st_n != st` is hit. Verilator 5.020 instruments before selector bind. 设计 agreed not a hole. |
| `vibe_pcs_rx_amctl_lock.sv:55–58` | **TOOL** (re-check) | `dec_lid` function arms. `tc_pcs_rx_amctl` already sends cw3/cw8/cw9/cw10/else. Same inline class; cluster now `--inline-mult 0`. |
| `vibe_dll_tx.sv:94 else` | **TB hole → filled** | `rem_b != 0`. 16-flit / 5-beat packet in `tc_dll_tx_cfg0`. |
| `vibe_dll_tx.sv:98 if` | **DUT dead?** | `val_b==0`. `vibe_pkt_bytes` clamps to ≥20 B. Zero-data beat still SOP=20 B. Tried; sequential invariant `pkt_act && pkt_left==0` never holds. |
| `vibe_dll_tx.sv:144 else` | **DUT dead?** | `n_flits==0` while packing. Legal packets are 20 B granules; `rem+val` never <20. |
| `vibe_dll_tx.sv:145–147 if` | **TB hole → filled** | `n_flits>=2,3,4`. 2-flit / 3-flit / 16-flit (rem=16+val=64) in `tc_dll_tx_cfg0`. |
| `vibe_dll_tx.sv:150 else, 151/155/159 if` | **TB hole → filled** | EOP Null-pad (`25eb085e`) + continuation. 1/2/3-flit pad + 16-flit multi-beat. |
| `vibe_dll_tx.sv:208 else` | **TB hole → filled** | `cur_left > val_b`. 16-flit continuation beats. |
| `vibe_dll_rx.sv:100 if` | **TB hole → filled** | `rx_ovf`. Prior burst dropped on `!pcs_ready`. Now 12 ready-gated 1-flit, RXBUF=32. |
| `vibe_dll_rx.sv:118 else` | **TB hole → filled** | leftover > emit. 5-flit declared length, one 640b beat. |
| `vibe_dll_rx.sv:128 if` | **TB hole → filled** | `need_hdr && !can_emit`. Stall `nw_ready` after first emit, send second SOP. |
| `vibe_fabric.sv:246,248` | **TB hole → filled** | `xb_v&&xb_sop` / `egr_sop`. Prior clusters were G1/CFG6 only. `tc_fabric_line_holes` now RT=00 dest=5 → port0. |
| `vibe_pcs_tx_g1.sv:51 else` | **TB hole → filled** | second 640b while `nflit==4`. Two back-to-back beats. |
| `vibe_pcs_tx_g1.sv:65 elsif` | **TB hole → filled** | idle complete of a 4-flit window. One beat then idle. |

Toggle <100% is wide-bus unused bit patterns (not the LINE gate).

## Waivers (non-goals — not in RTL; AS-0.1)

| Feature | Spec | Waiver |
|---|---|---|
| Probe LMSM state | AS-0.1 §11 this-rev subset | not implemented (`width_fail` tied 0, x4-only) |
| Dijkstra / shortest-path | AS-0.1 G1 | not implemented (RT=10/11 DROP) |
| QDLWS | AS-0.1 | not implemented |
| Exact Route | AS-0.1 | not implemented |
| UBFM | AS-0.1 | not implemented |

## Tool only: `tmr_load` `:101–108`

Automatic function case arms. Caller `if (st_n != st) tmr <= tmr_load(...)` **is**
hit. Verilator 5.020 instruments the case-cover tree before `__Vfunc_…s = st_n`
(selector still 0). `no_inline` for functions is **Unsupported** on 5.020.
Leave as 0; report separately. Not DUT / not TB.

Second-pass numbers (after this TB fill, overlay `25eb085e`) replace the
first-pass totals in `cov_summary.txt` / `cov_report.md`.
