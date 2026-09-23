# vibe_pcs_rx_amctl_lock

PCS RX AMCTL lock per lane (AS-0.1 §6 / §14). Decision I
stage-14 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(same-layer PCS cell used by `vibe_pcs_rx` `u_l0`..`u_l3`)
under the pycircuit → rtl flow. Continues the RX path after
stage-13 deskew; pairs with stage-10 `vibe_pcs_tx_amctl`.
Hunt on RAW 160b (AMCTL is not scrambled). Factory
physical=logical (U24): no lane swap. **No SPEC / CR-B
semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_rx_amctl_lock.py` |
| Product SV | `rtl/pcs/vibe_pcs_rx_amctl_lock.sv` |
| Instantiator | `vibe_pcs_rx` (`u_l0`..`u_l3`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `263aec6` / freeze `302ac943`. One 160b lane.
Reset stays **async active-low** (`or negedge rst_n`).
Stock include `vibe_ub_params.vh` stays
(`VIBE_AMCTL_CONFIRM_N` = `VIBE_AMCTL_UNLOCK_N` = 3).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `in_vld` | in | beat available |
| `in_data[159:0]` | in | RAW 160b (pre-descramble) |
| `locked` | out | 3 AMCTL detections then locked |
| `lid[1:0]` | out | decoded AMCTL.LID {0,1,2,3} |
| `lid_bad` | out | sticky; LID not {0,1,2,3} (U24) |
| `is_amctl` | out | combo `in_vld && (match_pair \|\| match_w0 \|\| match_w1)` |
| `sdf` | out | 1-cycle pulse when pair CTRL_DETAIL is x4 SDF |
| `edf` | out | 1-cycle pulse when pair is not SDF |

No parameters. This is **not** FEC wrap / pack / g1 / tx /
rx tops / unpack (later stages). Stage-7 `vibe_pcs_scramble`,
stage-8 `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`,
stage-10 `vibe_pcs_tx_amctl`, stage-11 `vibe_rs128_120_enc`,
stage-12 `vibe_rs128_120_dec`, and stage-13
`vibe_pcs_rx_deskew` are left intact.

## Flow

Seven `vibe_ebch16` instances (combo LUT): CW3/8/9/10/21/22/28.
`is_amctl` is combo so descramble `en=!is_amctl` sees the same
beat (pass-through AMCTL). Hunt with 1-beat slip: word0 of TX
AMCTL is BODY at `[159:144]` plus END `{CW22,CW22}` at
`[63:32]`; a pair match also accepts the legacy END slot at
`in_data[127:112]`. Word1 (CTRL_TYPE Link-Width + CTRL_DETAIL
x4 SDF) is marked so a slip still skips it. Three detections
(`CONFIRM_N=3`) then `locked`. TX-layout lock is sticky
through data; `UNLOCK_N` only for legacy pair-slot hunt
(unit TB). LID CW3/8/9/10 → 0/1/2/3; anything else sets
`lid_bad` and does not swap lanes (U24).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_rx_amctl_lock
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`vibe_ub_params.vh` include, the `vibe_ebch16` instances,
combo `is_amctl`, and the hunt / confirm / unlock body stay.
Ports / hunt / lock match stock (header-only vs stock).
