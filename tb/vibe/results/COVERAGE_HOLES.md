# Remaining Verilator LINE points (`vibe_*.sv`)

RTL under test: **PR13 SHA `25eb085e`** (sim-only overlay; this branch does not
commit `rtl/`). Tool: Verilator **5.020**.
FSM = line hits on state `case`/`if` (no VCS FSM engine).

## Numbers (final merge this PR)

| Metric | Hit/tot | % |
|--------|--------:|--:|
| **LINE** | **702/727** | **96.6** |
| **TOGGLE** | **9528/17230** | **55.3** |
| **FSM** | (none) | use LINE on state `case`/`if` |

First pass (before TB fill, some clusters dark): LINE 621/651 = 95.4%,
TOGGLE 4992/14508 = 34.4%. Denominator grew when `vibe_pcs_rx` / unpack / fec
elaborated (input-default strip + TX sources on the pcs_rx cluster).

Combo-only wrappers (`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`,
`vibe_pcs_tx`) contribute **0/0** line points (toggle only). Not a LINE miss.

`vibe_port` / `vibe_ub_switch`: **0 records** — port/top clusters compile
`rc=1` (OOM / 180 s). Same class as suite-VOQ skip. Wrappers; children are
clustered. Not DUT dead.

**`vibe_suite` is never bound** (VOQ OOM).

## Hittable LINE now 100% except classified leftovers

Filled this PR (were TB holes on the first `25eb085e` pass):

| Path | Stim |
|---|---|
| `vibe_dll_rx` ovf / leftover / need_hdr | `tc_cfg0_term_not_fabric` → **22/22** |
| `vibe_dll_tx` rem / n_flits≥2,3,4 / multi-beat `:208` | `tc_dll_tx_cfg0` 2/3/16-flit |
| `vibe_fabric` `:246/:248` xbar + CFG6/sat | `tc_fabric_line_holes` RT=00 → **48/48** |
| `vibe_pcs_tx_g1` `:65` 4-flit idle Nulls | `tc_pcs_tx_g1_window` |
| `vibe_pcs_rx_unpack` / `_fec` am_gap + dual-buf | those TCs → **16/16**, **18/18** |

## Uncovered LINE — classification

### TOOL (not a hole) — `tmr_load` `:101–108`

`vibe_lmsm.sv:101–108` function case arms. Caller
`if (st_n != st) tmr <= tmr_load(...)` **is hit**. Verilator 5.020 instruments
the case-cover tree before `__Vfunc_…s = st_n` (selector still 0).
`no_inline` for functions is **Unsupported** on 5.020. 设计 agreed: do not
count as DUT or TB. Still present on this SHA.

### TOOL (not a hole) — `dec_lid` `:55–58`

`vibe_pcs_rx_amctl_lock.sv:55–58` function arms. `tc_pcs_rx_amctl` already
sends cw3 / cw8 / cw9 / cw10 / else (`lid` scores 0/1/3 + `lid_bad`).
`--inline-mult 0` did not make the arms take LINE. Same 5.020 function-inline
class as `tmr_load`.

### TOOL — EOP Null-pad combo ifs `:151/:155/:159`

`vibe_dll_tx.sv` (`25eb085e` pad). Three sequential
`if (fq_n_nxt[1:0] != 0)` in one `always @*`. After the pads settle,
`fq_n_nxt[1:0]==0`, so Verilator records the **final** condition as false.
1/2/3-flit EOP packets were sent (`tc_dll_tx_cfg0`); the pad logic runs
(group becomes 4 flits). Not DUT dead. Do not patch RTL for the tool.

### DUT dead (legal 20 B packets) — FAIL-style for 设计

Do **not** patch RTL from TB. These arms cannot fire given
`vibe_pkt_bytes` ≥ 20 and `pkt_act && pkt_left==0` never holding.

| File:line | Unreachable | TCs already tried |
|---|---|---|
| `vibe_dll_tx.sv:98 if` | `val_b==0` in the rem/NW pack combo. `val_b = min(cur_left, 64)`; SOP leftover is always ≥ 20 B. Zero-data beat still decl_flits=1 → 20 B. | `tc_dll_tx_cfg0` CFG0, CFG3 1/2/3/16-flit, all-zero NW beat |
| `vibe_dll_tx.sv:144 else` | `n_flits==0` while `nw_vld && nw_ready`. `n_flits = (rem_b+val_b)/20`; rem+val never < 20 on 20 B granules. | same as above |

### TB remaining (not DUT)

| File:line | Why still 0 | Tried |
|---|---|---|
| `vibe_pcs_tx_g1.sv:51 else` | `nflit==4` rem-complete of a second 640b. Idle `:65` steals the window unless `win_ready` is held 0; Verilator still 0 on that sequence. | `tc_pcs_tx_g1_window` isolated 4-flit + idle; two beats with `win_ready=0` between |
| `vibe_pcs_rx.sv:181 elsif, :182 if/else` | `pend_vld` emit / null-pend drop | `tc_pcs_rx` AM lock + one legal DLL beat (35/42). No pend-held + null window. |
| `vibe_pcs_rx.sv:194 else, :198 if` | low-320 pad vs rem (`pad_null` / `!pad_null`) | same TC; single 4-flit+Null window only |
| `vibe_pcs_rx.sv:207 else, :211 if` | rem is non-null second 640 of a multi-beat packet | same TC; no 1.5-beat rem continuation |

Those `vibe_pcs_rx` arms are inverse-G1 remainder / Null-pad. Filling them needs
a second 640 after a non-null rem (or a pend stall), not an RTL change.

## Waivers (non-goals — not in RTL; AS-0.1)

| Feature | Spec | Waiver |
|---|---|---|
| Probe LMSM state | AS-0.1 §11 this-rev subset | not implemented (`width_fail` tied 0, x4-only) |
| Dijkstra / shortest-path | AS-0.1 G1 | not implemented (RT=10/11 DROP) |
| QDLWS | AS-0.1 | not implemented |
| Exact Route | AS-0.1 | not implemented |
| UBFM | AS-0.1 | not implemented |

Toggle <100% is wide-bus unused bit patterns (not the LINE gate).

## Cov script notes (TB only)

- Verilator 5.020: `%Error-UNSUPPORTED` on `input … = 1'b0`. `-Wno-UNSUPPORTED`
  is **not a valid warning name** (aborts every cluster). Script copies `rtl/`
  to `tb/vibe/cov/out/rtl_nodedef` and strips those defaults. **Does not
  modify or commit `rtl/`.**
- `// Verilator:` comments are pragmas — do not use that spelling in TB notes.
