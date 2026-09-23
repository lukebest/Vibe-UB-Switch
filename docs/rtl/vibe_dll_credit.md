# vibe_dll_credit

DLL credit / backpressure / 1µs timeout (AS-0.1 §12 /
FS-0.2.6). Decision I stage-21 pyCircuit leaf. Re-homes
pre-Decision I stock RTL (second DLL helper under
`pycircuit/dll/`, after `vibe_bcrc`) under the pycircuit →
rtl flow. Consume `ceil(DLLDP_flits/n)` (n default 8);
pending is a cell count; thresh 1024 → `bp_nw` + force
Crd_Ack. CFG0 does not consume. Timeout 1µs → `proto_err`.
No credit underflow code. Self-contained (no child
instances). Second DLL leaf after `vibe_bcrc`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_credit.py` |
| Product SV | `rtl/dll/vibe_dll_credit.sv` |
| Instantiator | `vibe_dll` (`u_crd`); unit TCs (`u_crd`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `ad36bf66` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | clears `cells` / `pend` / `to` (not `proto_err` / `fc_ovf`) |
| `link_up` | in | 0: same clear as `port_rst` |
| `grain_n[7:0]` | in | 1,2,4,...,128; default 8 |
| `consume_vld` | in | consume this cycle (skipped when `is_cfg0`) |
| `consume_flits[9:0]` | in | raw DLLDP flits; converted via `ceil_div` |
| `is_cfg0` | in | CFG0 DLLCB does not consume credit |
| `credit_ret` | in | Crd_Ack return (already cells) |
| `credit_ret_n[15:0]` | in | returned cell count (not raw flits) |
| `pending[15:0]` | out | combo `pend` (cell count) |
| `credit_low` | out | combo `cells == 0` |
| `force_crd_ack` | out | combo `pend >= thresh` or `!consume_vld && pend != 0` |
| `bp_nw` | out | combo `pend >= VIBE_CREDIT_THRESH` (1024) |
| `proto_err` | out | 1µs timeout while `pend != 0` |
| `fc_ovf` | out | 17-bit `cells` sum overflow (saturate 65535) |

No parameters. This is **not** PCS tx / rx tops (later
stages) and **not** the rest of DLL wraps. Stage-1..20
leaves are left intact. Does **not** instantiate children.
`include "vibe_ub_params.vh"` for `VIBE_CREDIT_THRESH` and
`VIBE_US_CYC`.

## Flow

One always block plus `ceil_div` and combo pending /
thresh. State: `cells[15:0]` / `pend[15:0]` / `to[10:0]` /
`proto_err` / `fc_ovf`.

`ceil_div`: `n==0` → 0; else
`({1'b0, flits} + {9'd0, n} - 17'd1) / {9'd0, n}`. Consume
uses `ceil_div({6'd0, consume_flits}, grain_n)` when
`consume_vld && !is_cfg0`. Credit return adds
`credit_ret_n` cells (already grain). `pend >= 1024` raises
`bp_nw` and `force_crd_ack`. A consume or return reloads
`to` to `VIBE_US_CYC` (1250 @ 1.25 GHz). Else while
`pend != 0`, `to` counts down; `to==0` sets `proto_err`.
`cells` saturates and sets `fc_ovf` on a 17-bit sum
`> 65535`. There is no credit underflow subtract.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_credit
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`VIBE_CREDIT_THRESH` / `VIBE_US_CYC`, `ceil_div`, CFG0 skip,
cell-count return, thresh backpressure, and the 1µs timeout
stay. Ports / credit match stock (header-only vs stock).
Official `.vlt` is not expanded.
