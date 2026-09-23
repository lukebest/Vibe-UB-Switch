# vibe_voq_egr

Fabric egress VOQ (AS-0.1 §8/§14). Decision I
stage-31 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(fifth fabric helper under `pycircuit/fabric/`, after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel`) under the pycircuit → rtl flow. VOQ
32 flit/VL/egress. Deadlock timeout 1 µs from enqueue
(`age = VIBE_US_CYC`). Self-contained (no child
instances). Fifth fabric leaf after `vibe_fecn_mark` /
`vibe_vl_rr` / `vibe_route_lu` / `vibe_port_sel`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_voq_egr.py` |
| Product SV | `rtl/fabric/vibe_voq_egr.sv` |
| Instantiator | `vibe_fabric` (`g_egr.u_voq`); unit TC (`tc_voq_rd`, `tc_deadlock_timeout_1us`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `8ec96a2a` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; clears `deadlock_*` + `wptr`/`rptr` |
| `wr_vl[3:0]` | in | enqueue VL |
| `wr_en` | in | enqueue this cycle (needs `wr_ready`) |
| `wr_data[511:0]` | in | flit written at `wptr[wr_vl][4:0]` |
| `wr_sop` | in | SOP flag stored with the flit |
| `wr_eop` | in | EOP flag stored with the flit |
| `wr_ready` | out | combo `occ < DEPTH` for `wr_vl` |
| `rd_vl[3:0]` | in | dequeue VL |
| `rd_en` | in | dequeue this cycle |
| `rd_data[511:0]` | out | combo `mem[rd_vl][rptr[rd_vl][4:0]]` |
| `rd_sop` | out | combo SOP at the read slot |
| `rd_eop` | out | combo EOP at the read slot |
| `nonempty[15:0]` | out | combo `wptr[v] != rptr[v]` |
| `occ_vl0[5:0]` | out | combo `wptr[0] - rptr[0]` |
| `deadlock_drop` | out | 1-cycle pulse when a VL times out |
| `deadlock_cnt[31:0]` | out | increments on deadlock drop |

Parameter `DEPTH` default 32. This is **not** PCS tx / rx
tops (later stages), **not** remaining DLL wraps
(`vibe_dll_tx`, dll top), and **not** `vibe_fabric` top.
Does **not** migrate `vibe_saf_ing` / `vibe_xbar`.
Stage-1..30 leaves are left intact. Does **not**
instantiate children. `include "vibe_ub_params.vh"`
(stock; `VIBE_US_CYC` is 1250).

## Flow

Combo plus one async-low sequential. Combo:
`occ = wptr[wr_vl] - rptr[wr_vl]`; `wr_ready = occ <
DEPTH`; `rd_data/rd_sop/rd_eop` from
`mem/sopm/eopm[rd_vl][rptr[rd_vl][4:0]]`;
`occ_vl0 = wptr[0] - rptr[0]`; `nonempty[v] =
(wptr[v] != rptr[v])`.

State: `wptr[0:15]` / `rptr[0:15]` (6-bit),
`mem[0:15][0:DEPTH-1]` (512b), `sopm` / `eopm`,
`age[0:15][0:DEPTH-1]` (11-bit), `deadlock_drop`,
`deadlock_cnt[31:0]`. Integers `v` / `j` for the
loops. Mem / sop / eop / age are **not** cleared on
reset.

`!rst_n` → `deadlock_drop=0`, `deadlock_cnt=0`, every
`wptr[v]=0` / `rptr[v]=0`. Else `deadlock_drop <= 0`.
On `wr_en && wr_ready`: write the slot, `age =
VIBE_US_CYC[10:0]`, `wptr+1`. On `rd_en`:
`rptr[rd_vl]+1`. Every nonzero `age` counts down.
If nonempty and `age[v][rptr[v][4:0]]==0`: `rptr+1`,
pulse `deadlock_drop`, `deadlock_cnt+1`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_voq_egr
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, 16 VL ×
DEPTH mem + sop/eop/age, combo `wr_ready` / `rd_*` /
`nonempty` / `occ_vl0`, and the 1 µs deadlock timeout
stay. Ports / behavior match stock (header-only vs
stock). Official `.vlt` is not expanded.
