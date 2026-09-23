# vibe_gear_128_160

RX 128→160 dual-residue gearbox (AS-0.1 §6/§7). Decision I stage-5
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer gear
used by `vibe_port` `u_rg0`..`u_rg3`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.** 5×128 = 4×160.

| | |
|---|---|
| Python | `pycircuit/cdc/vibe_gear_128_160.py` |
| Product SV | `rtl/cdc/vibe_gear_128_160.sv` |
| Instantiator | `vibe_port` (`u_rg0`..`u_rg3`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `195d380` / freeze `302ac943`. Ready/valid on both sides.
Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | dest-domain clock (`clk_fab` in `vibe_port`) |
| `rst_n` | in | dest-domain async active-low |
| `in_vld` | in | 128b beat available |
| `in_ready` | out | combo `!hold_vld \|\| out_ready` |
| `in_data[127:0]` | in | RX AFIFO read data |
| `out_vld` | out | combo `hold_vld` |
| `out_ready` | in | consumer takes the 160b hold |
| `out_data[159:0]` | out | combo `hold` |

No parameters. This is **not** `vibe_gear_160_128` (TX 160→128; later stage).

## Flow

One always block plus combo ready/valid. `phase` counts 0..4 inputs
in a 5-beat group. Phase 0 parks 128 in `res_a`. Phases 1..4 emit 160
(`{new bits, leftover}`) and park the unused tail in `res_a` / `res_b`.
`hold_vld` clears when the consumer takes; a same-cycle accept in
phases 1..4 sets it again. Single-clock ratio — **not** a CDC cell
(used after RX AFIFO in the dest domain).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_gear_128_160
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo `in_ready`,
and the dual-residue `case (phase)` body stay.
