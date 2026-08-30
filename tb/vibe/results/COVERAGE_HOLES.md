# Remaining Verilator LINE points (`vibe_*.sv`)

Gate: unique source LINE on implemented `vibe_*.sv`. Last merge: **628/636 = 98.7%**
after rebase onto RTL `79ac9592` (was 626/638 = 98.1% before that RTL cleanup).
Combo-only wrappers (`vibe_dll`, `vibe_fecn_mark`, `vibe_mgmt`, `vibe_nw_adapt`,
`vibe_pcs_tx`, `vibe_ub_switch`) contribute **0/0** line points.

Clusters: per-module / small groups. **`vibe_suite` is never bound** (VOQ OOM).

**100% of remaining hittable LINE.** The only uncovered bins are `tmr_load`
`:101–108` (tool). **Not a coverage hole** — the caller `st_n != st` is hit.
Do not waive; do not treat as missing stim.

## Newly live paths (RTL `79ac9592`) — all HIT

| Path | Stim | Module LINE |
|---|---|---|
| Credit 17-bit `cells_sum > 65535` | `tc_credit_1024_flit_bp` 70×1023 grain=1 | `vibe_dll_credit.sv` **16/16** |
| `ST_DIS → Param` | `tc_dll_sm_states` `link_up` + 2 posedge | `vibe_dll_sm.sv` **14/14** |
| SAF 1-beat `sop&&eop` / fabric CFG6 `:185` | `tc_saf_ing` + `tc_fabric_line_holes` 1-flit 本CNA | `vibe_saf_ing.sv` **16/16**, `vibe_fabric.sv` **27/27** |
| FEC bypass `else` (tautology removed) | `tc_pcs_fec_emitb` | `vibe_pcs_tx_fec.sv` **28/28** |

## Waivers (non-goals — not in RTL; AS-0.1)

No line to waive. Static `scan_absent.sh` + `tc_neg_*`:

| Feature | Spec | Waiver |
|---|---|---|
| Probe LMSM state | AS-0.1 §11 this-rev subset | not implemented (`width_fail` tied 0, x4-only) |
| Dijkstra / shortest-path | AS-0.1 G1 | not implemented (RT=10/11 DROP) |
| QDLWS | AS-0.1 | not implemented |
| Exact Route | AS-0.1 | not implemented |
| UBFM | AS-0.1 | not implemented |

## Tool only (not a hole): `tmr_load` `:101–108`

Automatic function case arms. Caller `if (st_n != st) tmr <= tmr_load(...)` **is**
hit. Verilator 5.020 instruments the case-cover tree before `__Vfunc_…s = st_n`
(selector still 0). `no_inline` for functions is **Unsupported** on 5.020.
RTL `79ac9592` did not change `tmr_load`. Leave as 0; report separately.

## Combo-only (0 line points)

Elaborated in clusters; no executable line bins. Toggle exists. Not a LINE miss.
