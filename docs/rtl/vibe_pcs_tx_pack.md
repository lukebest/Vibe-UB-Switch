# vibe_pcs_tx_pack

PCS TX pack (AS-0.1 §5 T5 G2). Decision I stage-16
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_tx` `u_pack`) under the pycircuit →
rtl flow. Inverse of stage-15 `vibe_pcs_rx_unpack`
(5×512 ↔ 4×640). Instantiates stage-10 `vibe_pcs_tx_amctl`
×4. **No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_tx_pack.py` |
| Product SV | `rtl/pcs/vibe_pcs_tx_pack.sv` |
| Instantiator | `vibe_pcs_tx` (`u_pack`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `ee5e8f4` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `sdf_period` | in | 1 = 640-symbol AMCTL data period |
| `afifo_afull` | in | backpressure (almost_full) |
| `beat_data[511:0]` | in | 512b beat |
| `beat_vld` | in | beat available |
| `beat_ready` | out | combo `!afifo_afull && lane_ready && (am_phase==0) && !pack_vld` |
| `lane0`..`lane3[159:0]` | out | per-lane 160b (AMCTL or packed 640) |
| `lane_vld` | out | combo `(am_phase!=0) \|\| pack_vld` |
| `lane_ready` | in | downstream accept |
| `am_word` | out | combo `am_phase!=0` |

No parameters. This is **not** FEC wrap / g1 / tx / rx tops
(later stages). Stage-1..15 leaves are left intact.

## Flow

One always block plus combo ready / valid / lane mux. Four
`vibe_pcs_tx_amctl` instances (`u_am0`..`u_am3`, `lane_id` 0..3,
`link_up=1`). AMCTL timer is 640 symbols after SDF / 512
otherwise (`insert_am = sym_cnt >= period`). `am_phase` 0=data,
1=AM high 160b/lane, 2=AM low 160b/lane. Start AM only when
`am_phase==0 && !pack_vld && !completing` so a finishing 4×640
emits before AMCTL (keeps RX 1024b pairs on even beats).

Take (`beat_vld && beat_ready`) writes `pack[512*acc_n +: 512]`.
`acc_n==4` completes 2560b, sets `pack_vld`, and resets
`acc_n` / `emit_idx`. Emit one 640 (4×160) when
`pack_vld && lane_ready && am_phase==0 && !afifo_afull`; the
last word (`emit_idx==3`) clears `pack_vld`. `sym_cnt` advances
by 16 symbols/lane per accepted beat unless `insert_am`.
`afifo_afull` / `lane_ready` backpressure both data and AM.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_tx_pack
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`vibe_pcs_tx_amctl` instances, combo ready/valid / lane mux,
and the timer / pack / emit body stay. Ports / pack / AMCTL
insert match stock (header-only vs stock). Official `.vlt` is
not expanded.
