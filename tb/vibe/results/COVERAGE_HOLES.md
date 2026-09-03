# Coverage close-out — SHA `25eb085e` (PR14 TB)

Acceptance (芯片开发PM): **code coverage ≥95% + waiver**; **functional coverage 100%**.
**Do not chase LINE 100%.** Specs unchanged. **Zero `rtl/` commits.**

RTL under test: PR13 SHA **`25eb085e`** (sim-only overlay). Tool: Verilator **5.020**.
FSM = line hits on state `case`/`if` (no VCS FSM engine).

## Verdict

| Gate | Result |
|------|--------|
| Code LINE ≥95% | **PASS — 702/727 = 96.6%** |
| Code + classified waiver | **PASS** — every remaining LINE is TOOL / WAIVER-防御 / TB空洞-waived |
| Functional (official 159 TPs) | **100% of published/implementable TPs** — see below |
| LINE 100% | **not a goal** |

| Metric | Hit/tot | % |
|--------|--------:|--:|
| **LINE** | **702/727** | **96.6** |
| **TOGGLE** | **9528/17230** | **55.3** |
| **FSM** | (none) | use LINE on state `case`/`if` |

Toggle <100% is wide-bus unused bit patterns (not the LINE gate).

Combo wrappers (`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`,
`vibe_pcs_tx`) are **0/0** line (toggle only) — not a LINE miss.
`vibe_port` / `vibe_ub_switch`: 0 records (port/top cluster OOM). Children
clustered. **`vibe_suite` never bound** (VOQ OOM).

## Functional coverage 100%

No SystemVerilog `covergroup` in this TB. Functional coverage **is** the locked
**159 official TP-0.3 IDs** (`TP-0.3.md` / `TP_TC_MATRIX.md`). Do not invent IDs.

| Class | Count | Status |
|-------|------:|--------|
| MAPPED + ADDED (scored by a TC) | 122 | hit |
| NEG (absent-feature / scan) | 28 | hit (must-not-exist) |
| HOLE (freeze SPEC **非目标** / 未发布) | 9 | **waiver / 非目标** |
| **Sum** | **159** | |

HOLE nine (Xia: go into freeze SPEC as **非目标**; keep waived):

| ID | Note |
|----|------|
| TP-HOLE-G2 | 路由表 Max Index 未发布 — **非目标 / waiver** |
| TP-HOLE-G3 | 额外 IRQ 脚名未发布 — **非目标 / waiver** |
| TP-HOLE-G4 | 额外 reset 脚名未发布 — **非目标 / waiver** |
| TP-HOLE-G5 | 上电 CNA 默认未发布 — **非目标 / waiver** |
| TP-HOLE-G6 | lmsm_go 来源未发布 — **非目标 / waiver** |
| TP-HOLE-G8 | 封装脚未发布 — **非目标 / waiver** |
| TP-HOLE-G9 | RXEQ 张力/Optimize 未发布 — **非目标 / waiver** |
| TP-HOLE-010 | 性能数字未发布 — **非目标 / waiver** |
| TP-HOLE-012 | 计数器位宽不是 FS-must — **非目标 / waiver** |

`tc_tp_holes` documents them; do not invent. Implemented-feature bins: **122/122**.
Official NEG: **28/28**. HOLE nine: **非目标 / waiver**. **Published FUNC = 100%.**

Suite 27/27, units 85/85, neg 10/10 (Overlay B TB). `tc_top_smoke` **PASSED**
vs SHA `25eb085e` after PR13 Null-pad. G1 is also scored on the fabric cluster.

## Every uncovered LINE — classified

25 LINE points at 0. None are open TB work under the new bar.

### TOOL (waiver — not DUT / not TB)

| File:line | Why |
|-----------|-----|
| `vibe_lmsm.sv:101–108` | `tmr_load` function case arms. Caller `st_n != st` **is hit**. Verilator 5.020 instruments before `__Vfunc_…s = st_n`. 设计 agreed **TOOL**. |
| `vibe_pcs_rx_amctl_lock.sv:55–58` | `dec_lid` function arms. `tc_pcs_rx_amctl` already sends cw3/cw8/cw9/cw10/else. Same 5.020 inline class as `tmr_load`. |
| `vibe_dll_tx.sv:151, 155, 159 if` | EOP Null-pad (`25eb085e`). Three combo `if (fq_n_nxt[1:0] != 0)` settle to 0; Verilator records the **final** condition. 1/2/3-flit EOP was sent. |

### WAIVER / 防御 (设计: not DUT dead to fix)

Legal 20 B granules cannot hit these arms. They stay as defensive
guards — **not** DUT死代码. Do not patch `rtl/`.

| File:line | What | Class |
|-----------|------|--------|
| `vibe_dll_tx.sv:98 if` | `val_b==0` shift defense | **WAIVER / 防御** |
| `vibe_dll_tx.sv:144 else` | `n_flits==0` when rem < 20 B | **WAIVER / 防御** |

### TB空洞 — waived (not cheap to close; do not chase LINE 100%)

| File:line | Why 0 | Waiver |
|-----------|-------|--------|
| `vibe_pcs_tx_g1.sv:51 else` | second 640 while `nflit==4`. Isolated two-beat + `win_ready=0` still 0. | **WAIVE** — LINE already ≥95% |
| `vibe_pcs_rx.sv:181 elsif, :182 if/else` | `pend_vld` / null-pend | **WAIVE** — needs pend stall; `tc_pcs_rx` is AM + one beat |
| `vibe_pcs_rx.sv:194 else, :198 if` | low-320 pad vs rem | **WAIVE** |
| `vibe_pcs_rx.sv:207 else, :211 if` | rem is non-null second 640 | **WAIVE** |

Cheap TB holes from the first `25eb085e` pass **were filled** (`dll_rx` 22/22,
`fabric` 48/48, unpack/fec 100%, dll_tx rem/multi-beat). Remaining TB zeros
are inverse-G1 rem/pend shapes — not worth another LINE hunt.

## AS-0.1 non-goals (not in RTL — not LINE bins)

| Feature | Waiver |
|---------|--------|
| Probe LMSM | not implemented (`width_fail` tied 0) |
| Dijkstra / shortest-path | RT=10/11 DROP |
| QDLWS / Exact Route / UBFM | not implemented |

## Cov script (TB only)

Verilator 5.020 `%Error-UNSUPPORTED` on `input … = 1'b0`. `-Wno-UNSUPPORTED`
is not a valid warning name. Script strips defaults into
`tb/vibe/cov/out/rtl_nodedef`. Does not modify or commit `rtl/`.
