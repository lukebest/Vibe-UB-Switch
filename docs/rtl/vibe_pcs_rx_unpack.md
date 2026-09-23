# vibe_pcs_rx_unpack

PCS RX unpack (AS-0.1 §6 inverse G2). Decision I stage-15
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_rx` `u_un`) under the pycircuit →
rtl flow. Continues the RX path after stage-13 deskew and
stage-14 amctl_lock; inverse of TX `vibe_pcs_tx_pack`
(5×512 ↔ 4×640). **No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_rx_unpack.py` |
| Product SV | `rtl/pcs/vibe_pcs_rx_unpack.sv` |
| Instantiator | `vibe_pcs_rx` (`u_un`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `ebd1671` / freeze `302ac943`. Four 160b lanes
plus AMCTL skip / gap. Reset stays **async active-low**
(`or negedge rst_n`). Stock `am_gap = 1'b0` default stays
(Verilator `UNSUPPORTED` on input defaults is pre-existing;
pins are always connected at instantiate).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `lane0`..`lane3[159:0]` | in | per-lane 160b (post-deskew) |
| `lane_vld` | in | beat available |
| `am0`..`am3` | in | per-lane AMCTL mark; skipped |
| `am_gap` | in | one-cycle group reset of `n` (default `1'b0`) |
| `beat_data[511:0]` | out | combo `acc[511:0]` |
| `beat_vld` | out | combo `have` |
| `beat_ready` | in | downstream accept |

No parameters. This is **not** FEC wrap / pack / g1 / tx /
rx tops (later stages). Stage-7 `vibe_pcs_scramble`,
stage-8 `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`,
stage-10 `vibe_pcs_tx_amctl`, stage-11 `vibe_rs128_120_enc`,
stage-12 `vibe_rs128_120_dec`, stage-13 `vibe_pcs_rx_deskew`,
and stage-14 `vibe_pcs_rx_amctl_lock` are left intact.

## Flow

One always block plus combo `beat_vld` / `beat_data`.
`din = {lane3, lane2, lane1, lane0}` (640b). `take` is
`lane_vld && !(am0|am1|am2|am3) && !am_gap && !nxt_full`.
Fill writes `nxt[640*n +: 640]` for `n=0..2`. `n==3`
completes `{din, nxt[1919:0]}` (2560b) into `acc` when
that buffer is free, else parks the group in `nxt` /
`nxt_full`. Emit shifts one 512 when `have && beat_ready`;
the last beat (`e==0`) swaps `nxt` in or clears `have`.
`am_gap` resets `n` only — an in-flight 5×512 drain is
kept. Dual-buffer so the next 4×640 is accepted while
emitting; a single acc that dropped ingress while `have`
permanently slipped 512 pairing vs TX pack.

`vibe_pcs_rx` ties `am0`..`am3` to 0 (deskew already
drops AMCTL) and drives `am_gap` as the one-cycle
AMCTL-pair reset.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_rx_unpack
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`am_gap = 1'b0` default, combo `beat_vld` / `beat_data`,
and the dual-buffer body stay. Ports / unpack match stock
(header-only vs stock).
