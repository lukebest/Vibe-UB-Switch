# vibe_port_sel

Fabric port select (AS-0.1 §2/§8). Decision I
stage-30 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(fourth fabric helper under `pycircuit/fabric/`, after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu`) under
the pycircuit → rtl flow. `available = bitmap & status_up`
(forced 0 if `drop_g1`). Empty after filter → Default;
Default all-0 → port 0 bitmap `4'b0001`; AND with
`status_up`. If still empty → drop + increment
`drop_down_cnt`, no flood. RT=00: per-flow sticky RR;
flow slot `fidx=vl` (compact); sticky table `[0:15]`.
RT=01 (else): per-packet RR via `rr`. `pick_rr(bm, start)`
walks 4 ports from start. Self-contained (no child
instances). Fourth fabric leaf after `vibe_fecn_mark` /
`vibe_vl_rr` / `vibe_route_lu`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_port_sel.py` |
| Product SV | `rtl/fabric/vibe_port_sel.sv` |
| Instantiator | `vibe_fabric` (`u_ps`, `g_rt.u_psi`); unit TC (`tc_p0_down_drop`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `3e647231` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; clears outputs + `rr` + sticky |
| `bitmap[3:0]` | in | route-table egress bitmap |
| `status_up[3:0]` | in | DLL Status_Up per port |
| `default_bm[3:0]` | in | Default bitmap when filter is empty |
| `rt[1:0]` | in | `2'b00` sticky RR; else per-packet RR |
| `drop_g1` | in | force `avail=0` (G1); drop, no `drop_down_cnt` |
| `sel_vld` | in | select valid this cycle |
| `cfg[3:0]` | in | product flow-key port (compact slot is `vl`) |
| `src[15:0]` | in | product flow-key port (compact slot is `vl`) |
| `dest[15:0]` | in | product flow-key port (compact slot is `vl`) |
| `vl[3:0]` | in | compact sticky slot `fidx` |
| `egr[1:0]` | out | selected egress port |
| `drop` | out | 1-cycle pulse when empty after filter / G1 |
| `drop_down_cnt[31:0]` | out | increments on empty-after-filter (not G1) |

This is **not** PCS tx / rx tops (later stages), **not**
remaining DLL wraps (`vibe_dll_tx`, dll top), and **not**
`vibe_fabric` top. Does **not** migrate `vibe_voq_egr` /
`vibe_saf_ing` / `vibe_xbar`. Stage-1..29 leaves are left
intact. Does **not** instantiate children. No flood.

## Flow

Combo plus one async-low sequential. Combo: `fidx=vl`;
`avail = drop_g1 ? 0 : (bitmap & status_up)`; empty →
`(default_bm==0 ? 4'b0001 : default_bm) & status_up` as
`use_bm`. `pick_rr(bm, start)` walks 4 ports from `start`.

State: `egr[1:0]`, `drop`, `drop_down_cnt[31:0]`,
`rr[1:0]`, `sticky[0:15]` (2-bit, init 0). Integer `k`
for the reset loop.

`!rst_n` → `egr=0`, `drop=0`, `drop_down_cnt=0`,
`rr=0`, every `sticky[k]=0`. Else `drop <= 0`. On
`sel_vld`: if `drop_g1 || use_bm==0` pulse `drop`; if
not `drop_g1` and `use_bm==0` increment
`drop_down_cnt` (no flood). Else if `rt==2'b00`: keep
`sticky[fidx]` when that port is in `use_bm`, else
`pick_rr` and write the sticky slot. Else: `egr =
pick_rr(use_bm, rr)` and `rr <= pick + 1`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_port_sel
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the stock
`pick_rr` walk, sticky / per-packet RR, and Default /
port-0 / drop+count stay. Ports / behavior match stock
(header-only vs stock). Official `.vlt` is not expanded.
