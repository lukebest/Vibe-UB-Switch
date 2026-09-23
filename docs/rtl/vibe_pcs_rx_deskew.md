# vibe_pcs_rx_deskew

PCS RX AMCTL deskew (AS-0.1 §6). Decision I stage-13 pyCircuit
leaf. Re-homes pre-Decision I stock RTL (same-layer PCS cell used
by `vibe_pcs_rx` `u_dsk`) under the pycircuit → rtl flow. Factory
physical=logical (U24): no lane swap. **No SPEC / CR-B semantic
change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_rx_deskew.py` |
| Product SV | `rtl/pcs/vibe_pcs_rx_deskew.sv` |
| Instantiator | `vibe_pcs_rx` (`u_dsk`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `ebd1671` / freeze `302ac943`. Four 160b lanes plus
per-lane AMCTL marks. Reset stays **async active-low**
(`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `in0`..`in3[159:0]` | in | per-lane 160b (post-descramble) |
| `in_vld` | in | beat available |
| `am0`..`am3` | in | per-lane AMCTL mark for this beat |
| `out0`..`out3[159:0]` | out | pass-through `in0`..`in3` |
| `out_vld` | out | combo `in_vld && !(am0\|am1\|am2\|am3)` |
| `aligned` | out | combo `saw0 & saw1 & saw2 & saw3` |

No parameters. This is **not** FEC wrap / pack / g1 / tx / rx
tops / amctl_lock / unpack (later stages). Stage-7
`vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
`vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, stage-11
`vibe_rs128_120_enc`, and stage-12 `vibe_rs128_120_dec` are left
intact.

## Flow

One always block plus combo aligned / valid / pass-through. On
`in_vld`, hunt FIFOs `f0`..`f3[wptr]` store the beat, `am*_r`
tracks the previous marker, and `wptr` advances. The first AMCTL
160b on a lane (`amX && !amX_r`) latches `aX <= wptr` and sets
`sawX`. `aligned` rises once every lane has seen that first
marker. Factory physical=logical: data passes during hunt
(lock/aligned come later). AMCTL is still dropped so unpack sees
a gap between 4×640 groups. FIFO pointers only record first-AMCTL
lock; feeding them as `out` would leak the second AMCTL 160b into
the 512b stream after each marker. FIFO contents are **not**
reset.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_rx_deskew
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo
`aligned` / `out_vld`, pass-through `out0`..`out3`, first-AMCTL
lock pointers, and un-reset hunt FIFOs stay. Ports / hunt /
pass-through match stock (header-only vs stock).
