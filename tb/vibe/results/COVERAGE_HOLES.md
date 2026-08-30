# Remaining Verilator LINE points (`vibe_*.sv`)

Gate: unique source LINE on implemented `vibe_*.sv`. Last merge: **626/638 = 98.1%**
(was 618/638 = 96.9%, originally 408/650 = 62.8%). Combo-only wrappers
(`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`, `vibe_pcs_tx`,
`vibe_ub_switch`) contribute **0/0** line points.

Clusters: per-module / small groups. **`vibe_suite` is never bound** (VOQ OOM).

**100% of TB-hittable lines.** No remaining missing-stimulus LINE. The 12
uncovered points are dead RTL (4) or Verilator 5.020 tool (8). **Not waived.**
Do not claim 100% of 638 by dropping those bins.

## Waivers (non-goals — not in RTL; AS-0.1)

No line to waive. Static `scan_absent.sh` + `tc_neg_*`:

| Feature | Spec | Waiver |
|---|---|---|
| Probe LMSM state | AS-0.1 §11 this-rev subset | not implemented (`width_fail` tied 0, x4-only) |
| Dijkstra / shortest-path | AS-0.1 G1 | not implemented (RT=10/11 DROP) |
| QDLWS | AS-0.1 | not implemented |
| Exact Route | AS-0.1 | not implemented |
| UBFM | AS-0.1 | not implemented |

Do **not** waive missing stimulus. There is none left on LINE.

## Remaining LINE (12) — not waived

### RTL-dead (predicate cannot be true) — list for 设计

| Line | Reason | Spec |
|---|---|---|
| `vibe_dll_credit.sv:56 if` | `cells + ceil_div > 16'd65535` is 16-bit; never true. `%Warning-CMPCONST`. | FS-0.2.4 credit; overflow sticky intended, width makes it dead. **Not patched.** |
| `vibe_dll_sm.sv:36 else` | `ST_DIS && !link_up` inside `else` after `if (!link_up)` already took Disabled. | AS-0.1 §12 |
| `vibe_fabric.sv:185 if` | single-beat CFG6 term (`saf_sop && saf_eop`). SAF does not present a 1-beat packet (`done` only on beat 2+). | AS-0.1 §8 SAF + §9 CFG6 |
| `vibe_pcs_tx_fec.sv:96 else` | bypass `else if (cw_ready \|\| !cw_vld)` is nested under `have0 && have1 && bypass && !cw_vld`. `!(cw_ready \|\| !cw_vld)` requires `cw_vld`, which contradicts the outer `!cw_vld`. `tc_pcs_fec_emitb` takes the else-if body (`96 if`). | AS-0.1 §5 T3 bypass |

TB cannot hit these. Leave uncovered. Do not waive.

### Tool: `tmr_load` function case (8)

`vibe_lmsm.sv:101–108` — automatic function case arms. Caller `st_n != st` **is**
hit (Idle→Disc→CFG→NULL→ACTIVE→RTR and EQ). Every load value is executed.

Workarounds tried (no `rtl/` edit):

| Attempt | Result on Verilator 5.020 |
|---|---|
| `--coverage-line` (already on) | case points exist, stay 0 |
| `--inline-mult 0 --public --public-flat-rw` | function emitted as `__Vfunc_…tmr_load` |
| `.vlt` `no_inline -function tmr_load` | **Unsupported: no_inline for tasks** |
| `$c` poke of `u_l__DOT__tmr` | C++ name is `vlSelf->tc_lmsm_cc__DOT__u_l__DOT__tmr` |
| park via `force st`/`tmr` | hits combo elsifs; does not increment function case LINE |

Generated C++ instruments the case-cover tree **before** `__Vfunc_…s = st_n`
(the selector is still 0). Only `default` (`:109`) increments. **Tool, not a
non-goal, not waived.** Inlining the case into the sequential `always` (RTL
edit) would make the arms visible.

## Closed this revision (were missing `--cc` stim)

| Line | How `--cc` samples it |
|---|---|
| `vibe_lmsm.sv:56 elsif` | park Disc.C + `force tmr=1` then RTL decrement |
| `vibe_lmsm.sv:58 if/else` | park Disc.C, `lid_bad` / partial lock `4'b0111` |
| `vibe_lmsm.sv:70 elsif` | park CFG_C with `force tmr=0` (1-cycle if `tmr!=0`) |
| `vibe_lmsm.sv:75 else` | park EQ_P/EQ_A with `tmr!=0` |
| `vibe_lmsm.sv:85/86` | park RTR_A `!all_lock`, then expire |
| `vibe_dll_rx.sv:61 if` | drop `link_up` on the negedge of the 1-cycle `have` window (`tc_dll_rx_errflag`) |

Icarus `tc_lmsm_walk` already walked several of these via `force tmr=0`. That
is not enough for `--cc` (stale `st_n` after a 1-cycle state; force-to-0 races
`tmr_load`).

## Combo-only (0 line points)

Elaborated in clusters; no executable line bins. Toggle exists. Not a LINE miss.
