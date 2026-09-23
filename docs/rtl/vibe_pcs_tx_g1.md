# vibe_pcs_tx_g1

PCS TX G1 (AS-0.1 §5 T2). Decision I stage-19
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_tx` `u_g1`) under the pycircuit →
rtl flow. Collect 6 flits / 960b FEC window (640b = 4 flits →
1.5 beats + 320b rem). Idle Null Block fill when `link_up`.
Self-contained (no child instances). After stage-17
`vibe_pcs_tx_fec` / stage-18 `vibe_pcs_rx_fec`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_tx_g1.py` |
| Product SV | `rtl/pcs/vibe_pcs_tx_g1.sv` |
| Instantiator | `vibe_pcs_tx` (`u_g1`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `24f7239a` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `link_up` | in | 1: accept ingress and idle-Null fill |
| `in_data[639:0]` | in | 640b = 4 flits from DLL |
| `in_vld` | in | beat available |
| `in_ready` | out | combo `link_up && (!have \|\| win_ready) && !((nflit >= 4) && rem_vld)` |
| `win_data[959:0]` | out | combo `acc` (6-flit / 960b FEC window) |
| `win_vld` | out | combo `have` |
| `win_ready` | in | downstream accept |

No parameters. This is **not** tx / rx tops (later
stages). Stage-1..18 leaves are left intact. Does **not**
instantiate FEC / pack / scramble.

## Flow

One always block plus combo ready / window. State:
`rem[319:0]` / `rem_vld` / `nflit` (0,2,4,6) / `acc` /
`have`. `NULL_FLIT = 160'd0` (CFG=0, CLENGTH=0).

Accept a 640b beat when `in_vld && in_ready`. Fresh window
(`nflit==0` or `have && win_ready`) parks 4 flits in
`acc[959:320]` and waits (`nflit=4`). A second beat while
`nflit==4` writes `acc[319:0] = in_data[639:320]`, keeps
`in_data[319:0]` in `rem` / `rem_vld`, and raises `have`.
`rem_vld && !have` completes the leftover 2 flits with 4
Nulls. Idle while `link_up && win_ready`: a parked 4-flit
window gets 2 Nulls; an empty window gets 6 Nulls.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_tx_g1
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo ready /
window, rem leftover, Null fill, and the collect body stay.
Ports / G1 match stock (header-only vs stock). Official `.vlt`
is not expanded.
