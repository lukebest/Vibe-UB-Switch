# vibe_gear_160_128

TX 160→128 residue gearbox (AS-0.1 §5 T7). Decision I stage-6
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer gear
used by `vibe_port` `u_g0`..`u_g3`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.** 4×160 = 5×128.

| | |
|---|---|
| Python | `pycircuit/cdc/vibe_gear_160_128.py` |
| Product SV | `rtl/cdc/vibe_gear_160_128.sv` |
| Instantiator | `vibe_port` (`u_g0`..`u_g3`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `cb4549f` / freeze `302ac943`. Ready/valid on both sides.
Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | TX read-domain clock (`txclk` in `vibe_port`) |
| `rst_n` | in | TX-domain async active-low |
| `in_vld` | in | 160b beat available |
| `in_ready` | out | combo `can_load && (rbits != 4)` |
| `in_data[159:0]` | in | PMA / TX 160b beat |
| `out_vld` | out | combo `hold_vld` |
| `out_ready` | in | consumer takes the 128b hold |
| `out_data[127:0]` | out | combo `hold` |

`can_load` is combo `!hold_vld || out_ready`. No parameters. This is
**not** `vibe_gear_128_160` (RX 128→160; stage-5).

## Flow

One always block plus combo ready/valid. `rbits` is 0..4
(0/32/64/96/128 bits valid in `res`). Beats 0..3 take 160, emit 128,
and park the leftover in `res`. When `rbits==4` the parked 128 is
emitted **without** taking a new input (`in_ready` is low).
`hold_vld` clears when the consumer takes; a same-cycle accept or
residue flush sets it again. Single-clock ratio — **not** a CDC cell
(used before TX AFIFO in the TX domain).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_gear_160_128
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo `in_ready`,
and the residue `case (rbits)` body stay.
