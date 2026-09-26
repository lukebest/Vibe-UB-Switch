# vibe_nw_adapt

NW 512b vld/ready adapter (AS-0.1 §3/§5 T0 / §8 /
FS-0.2.7). Decision I stage-37 pyCircuit leaf. Re-homes
pre-Decision I stock RTL (second NW helper under
`pycircuit/nw/`, after stage-36 `vibe_icrc`) under the
pycircuit → rtl flow. Combo: LinkReady in ready (U21);
mgmt reply injects on ingress TX before `nw_adapt_tx`,
priority over VOQ. Self-contained (no child instances).
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/nw/vibe_nw_adapt.py` |
| Product SV | `rtl/nw/vibe_nw_adapt.sv` |
| Instantiator | `vibe_port` (`u_nw`); unit TC (`tc_nw_adapt_linkready`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets unused in combo body |

## Ports (product)

Same as tip `2b4a8408` / freeze `302ac943`. Combo. Reset
pin stays **async active-low** `rst_n` (port wires it; the
combo body does not sample `clk` / `rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / NW digital clock (`clk_fab`); unused in combo body |
| `rst_n` | in | dest-domain async active-low pin; unused in combo body |
| `link_ready` | in | LinkReady in ready / vld (U21) |
| `fab_nw_data[511:0]` | in | FAB → NW (VOQ egress) |
| `fab_nw_vld` | in | VOQ beat valid |
| `fab_nw_ready` | out | `link_ready && nw_dll_ready && !mgmt_nw_vld` |
| `mgmt_nw_data[511:0]` | in | mgmt → NW inject (priority) |
| `mgmt_nw_vld` | in | mgmt beat valid |
| `mgmt_nw_ready` | out | `link_ready && nw_dll_ready` |
| `nw_dll_data[511:0]` | out | `mgmt_nw_vld ? mgmt_nw_data : fab_nw_data` |
| `nw_dll_vld` | out | `link_ready && (mgmt_nw_vld \|\| fab_nw_vld)` |
| `nw_dll_ready` | in | DLL TX ready |
| `dll_nw_data[511:0]` | in | DLL → NW |
| `dll_nw_vld` | in | DLL RX valid |
| `dll_nw_ready` | out | `nw_fab_ready` |
| `nw_fab_data[511:0]` | out | `dll_nw_data` (SAF ingress) |
| `nw_fab_vld` | out | `dll_nw_vld` |
| `nw_fab_ready` | in | fabric ingress ready |

No parameters. This is **not** PCS tx / rx tops (later
stages), **not** `vibe_port` / `vibe_ub_switch` tops, and
**not** other NW helpers or `vibe_fabric` top. Stage-1..36
leaves are left intact.
Does **not** instantiate children.

## Flow

Combo assigns only. TX mux: mgmt wins over VOQ when
`mgmt_nw_vld`. Both TX readies and `nw_dll_vld` require
`link_ready`. RX is a wire-through (`dll_nw_*` ↔ `nw_fab_*`).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_nw_adapt
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so the combo mux / ready tree
stays. Ports / behavior match stock (header-only vs
stock). Official `.vlt` is not expanded.
