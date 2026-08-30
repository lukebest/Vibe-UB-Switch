# Remaining Verilator LINE points (`vibe_*.sv`)

Gate: unique source LINE on implemented `vibe_*.sv`. Last merge: **618/638 = 96.9%**
(was 408/650 = 62.8% on a smaller elaborate set). Combo-only wrappers
(`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`, `vibe_pcs_tx`,
`vibe_ub_switch`) contribute **0/0** line points.

Clusters: per-module / small groups. **`vibe_suite` is never bound** (VOQ OOM).

## Waivers (non-goals — not in RTL; AS-0.1)

No line to waive. Static `scan_absent.sh` + `tc_neg_*`:

| Feature | Spec | Waiver |
|---|---|---|
| Probe LMSM state | AS-0.1 §11 this-rev subset | not implemented (`width_fail` tied 0, x4-only) |
| Dijkstra / shortest-path | AS-0.1 G1 | not implemented (RT=10/11 DROP) |
| QDLWS | AS-0.1 | not implemented |
| Exact Route | AS-0.1 | not implemented |
| UBFM | AS-0.1 | not implemented |

Do **not** waive missing stimulus.

## Remaining LINE (20) — not waived

### RTL-dead (predicate cannot be true; Verilator `CMPCONST` / SAF)

| Line | Reason | Spec |
|---|---|---|
| `vibe_dll_credit.sv:56` | `cells + ceil_div > 16'd65535` is 16-bit; never true. `%Warning-CMPCONST`. | FS-0.2.4 credit; overflow sticky intended, width makes it dead. **Not patched.** |
| `vibe_dll_sm.sv:36 else` | `ST_DIS && !link_up` inside `else` after `if (!link_up)` already took Disabled. | AS-0.1 §12 |
| `vibe_fabric.sv:185 if` | single-beat CFG6 term (`saf_sop && saf_eop`). SAF does not present a 1-beat packet (`done` only on beat 2+). | AS-0.1 §8 SAF + §9 CFG6 |

### Tool: `tmr_load` function case (8)

`vibe_lmsm.sv:101–108` — automatic function case arms. Caller `st_n != st` **is** hit
(Idle→Disc→CFG→NULL→ACTIVE→RTR and EQ). Verilator 5.020 does not attribute LINE
to those function `case` items. **Not a non-goal. Not waived.**

### Missing Verilator stimulus (not Icarus)

Icarus `tc_lmsm_walk` walks these via `force tmr` (PASS). `--cc` force of `tmr`
often does not affect combo `tmr==0` in the same window.

| Line | Branch | Why still open |
|---|---|---|
| `vibe_lmsm.sv:56` | Disc.C `tmr==0` | 48 ms or force not taken in `--cc` |
| `vibe_lmsm.sv:58 if/else` | Disc.C `lid_bad` / stay | one-cycle Disc.C window |
| `vibe_lmsm.sv:70` | CFG_C `eq_negotiated` | 2 ms window / `--cc` timing |
| `vibe_lmsm.sv:75 else` | EQ_A hold (`tmr!=0`) | 24 ms |
| `vibe_lmsm.sv:85/86` | RTR_A `tmr==0` / stay | 24 ms / force |
| `vibe_dll_rx.sv:61` | `!link_up && have` ERROR_FLAG pad | `--cc` `have` consumed same slot |
| `vibe_pcs_tx_fec.sv:96 else` | bypass `emit_b` second CW | handshake NBA in `--cc` |

24/48/64 ms waits are not used (cluster run timeout). That is **missing stim**, not a waiver.

## Combo-only (0 line points)

Elaborated in clusters; no executable line bins. Toggle exists. Not a LINE miss.
