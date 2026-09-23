# vibe_vl_rr

Fabric VL round-robin (AS-0.1 §8). Decision I
stage-28 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(second fabric helper under `pycircuit/fabric/`, after
`vibe_fecn_mark`) under the pycircuit → rtl flow. RR among
non-empty VOQs of an egress; FCFS within VL; no SL. On
`grant && valid` advance `rr` to `vl_sel+1`. Reset clears
`rr`. Self-contained (no child instances). Second fabric
leaf after `vibe_fecn_mark`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_vl_rr.py` |
| Product SV | `rtl/fabric/vibe_vl_rr.sv` |
| Instantiator | `vibe_fabric` (`u_rr` in `g_egr`); unit TCs (`tc_vl_rr`, `tc_vl_rr_0_15`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `450ed1c2` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; clears `rr` |
| `nonempty[15:0]` | in | VOQ occupancy one-hot-or-more per VL |
| `grant` | in | consume current `vl_sel`; advance `rr` when `valid` |
| `vl_sel[3:0]` | out | combo first nonempty VL from `rr` (wrap 16) |
| `valid` | out | combo `\|nonempty` |

This is **not** PCS tx / rx tops (later stages) and **not**
remaining DLL wraps (`vibe_dll_tx`, dll top). Stage-1..27
leaves are left intact. Does **not** instantiate children.
No SL. FCFS within VL is the VOQ, not this leaf.

## Flow

One combo always block plus one async-low sequential.
State: `rr[3:0]` (init 0). Combo temps: `pick[3:0]`,
`p[3:0]`, integer `n`.

`valid = |nonempty`. Scan `p = rr` then `p+1` (4-bit wrap)
for 16 steps; first `nonempty[p]` wins as `pick`.
`vl_sel = pick` (stays `rr` if none).

`!rst_n` → `rr=0`. Else `grant && valid` →
`rr <= vl_sel + 1`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_vl_rr
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the stock
combo for-loop pick, and `grant && valid` advance stay.
Ports / behavior match stock (header-only vs stock). Official
`.vlt` is not expanded.
