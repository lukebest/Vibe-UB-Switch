# vibe_saf_ing

Fabric store-and-forward ingress (AS-0.1 §8). Decision I
stage-32 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(sixth fabric helper under `pycircuit/fabric/`, after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel` / `vibe_voq_egr`) under the pycircuit → rtl
flow. Do not present to xbar until EOP / full declared
length. Length not in 16–4300 B → Packet Length Error,
drop, irq. Self-contained (no child instances). Sixth
fabric leaf after `vibe_fecn_mark` / `vibe_vl_rr` /
`vibe_route_lu` / `vibe_port_sel` / `vibe_voq_egr`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_saf_ing.py` |
| Product SV | `rtl/fabric/vibe_saf_ing.sv` |
| Instantiator | `vibe_fabric` (`g_saf.u_saf`); unit TC (`tc_saf_ing`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `d8fdf91f` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; clears pointers / assemble state / `len_err` |
| `in_data[511:0]` | in | ingress NW beat |
| `in_vld` | in | beat valid this cycle (needs `in_ready`) |
| `in_ready` | out | combo `(wptr+1) != rptr` |
| `pkt_data[511:0]` | out | combo `mem[rptr]` |
| `pkt_vld` | out | combo `done && (rptr != wptr)` |
| `pkt_ready` | in | downstream accept |
| `pkt_sop` | out | combo `pkt_vld && (rptr==0 \|\| beat_cnt==0)` |
| `pkt_eop` | out | combo `pkt_vld && (rptr+1 == wptr)` |
| `pkt_bytes[15:0]` | out | combo declared byte count |
| `len_err` | out | 1-cycle pulse on Packet Length Error |

Parameter `DEPTH` default 128. This is **not** PCS tx / rx
tops (later stages), **not** remaining DLL wraps
(`vibe_dll_tx`, dll top), and **not** `vibe_fabric` top.
Does **not** migrate `vibe_xbar`.
Stage-1..31 leaves are left intact. Does **not**
instantiate children. `include "vibe_ub_params.vh"` and
`include "vibe_ub_fn.vh"` (stock; `VIBE_PKT_LEN_MIN` /
`VIBE_PKT_LEN_MAX` are 16 / 4300).

## Flow

Combo plus one async-low sequential. Combo:
`in_ready = (wptr+1) != rptr`; `pkt_vld = done &&
(rptr != wptr)`; `pkt_data = mem[rptr]`; `pkt_sop` /
`pkt_eop` as above; `pkt_bytes = bytes`; header temps
`plen = vibe_lph_plength(vibe_nw512_flit0(in_data))`,
`dflits = vibe_decl_flits(plen)` (combo `always @*`,
not sequential blocking — BLKSEQ).

State: `wptr` / `rptr` / `beat_cnt` / `decl_beats`
(7-bit), `bytes[15:0]`, `assembling`, `done`,
`len_err`, `mem[0:DEPTH-1]` (512b). Mem is **not**
cleared on reset.

`!rst_n` → pointers / `beat_cnt` / `decl_beats` /
`bytes` / `assembling` / `done` / `len_err` = 0.
Else `len_err <= 0`. On `in_vld && in_ready`: write
`mem[wptr]`, `wptr+1`. SOP (`!assembling`): load
`decl_beats` / `bytes = dflits*20` / `beat_cnt=1`.
If `(dflits*20)` not in 16–4300: pulse `len_err`,
clear `assembling`, rewind `wptr` to `rptr`. Else if
declared beats == 1: complete on SOP (`done`). Mid
beats: `beat_cnt+1`; last beat sets `done`. On
`pkt_vld && pkt_ready`: `rptr+1`; EOP clears `done`
and both pointers.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_saf_ing
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, DEPTH
mem, combo `in_ready` / `pkt_*`, header temps, and the
16–4300 B Packet Length Error drop stay. Ports /
behavior match stock (header-only vs stock). Official
`.vlt` is not expanded.
