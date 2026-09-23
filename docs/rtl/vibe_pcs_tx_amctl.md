# vibe_pcs_tx_amctl

AMCTL 40 symbol/lane, eBCH-16 (AS-0.1 §5). Decision I
stage-10 pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_tx_pack` `u_am0`..`u_am3`) under the
pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_tx_amctl.py` |
| Product SV | `rtl/pcs/vibe_pcs_tx_amctl.sv` |
| Instantiator | `vibe_pcs_tx_pack` (`u_am0`..`u_am3`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `92adf9b` / freeze `302ac943`. Combo assemble. Reset
pin stays **async active-low** `rst_n` (pack wires it; the combo
body does not sample `clk` / `rst_n` / `sdf_period`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`); unused in combo body |
| `rst_n` | in | dest-domain async active-low pin; unused in combo body |
| `link_up` | in | `ack = req && link_up` |
| `sdf_period` | in | 1 = 640-symbol data period (pack owns the timer) |
| `lane_id[1:0]` | in | AMCTL.LID (physical=logical this rev) |
| `req` | in | request the 40-symbol word |
| `ack` | out | combo `req && link_up` |
| `amctl_40B[319:0]` | out | 40 symbols (BODY / END / LID / CTRL_TYPE / CTRL_DETAIL) |

No parameters. This is **not** `vibe_pcs_tx` / pack / FEC / RS /
rx (later stages). Stage-7 `vibe_pcs_scramble`, stage-8
`vibe_ebch16`, and stage-9 `vibe_pcs_tx_cw2beat` are left intact.

## Flow

Seven `vibe_ebch16` instances (combo LUT): CW3/8/9/10/21/22/28.
`always @*` `case (lane_id)` picks LID: lane 0 `{CW3,CW3}`, lane 1
`{CW3,CW8}`, lane 2 `{CW3,CW9}`, default `{CW3,CW10}` (`lid1` is
always CW3). Concat is BODY `{3{CW21,CW28}}` (12 symbols), END
`{CW22,CW22}` (4), LID `{lid1,lid0,lid1,lid0}` (8), CTRL_TYPE
Link Width `{CW8,CW9,CW8,CW9}` (8), CTRL_DETAIL x4 SDF
`{CW10,CW22,CW10,CW22}` (8). Insertion period (640 after SDF /
512 otherwise) lives in `vibe_pcs_tx_pack`, not this leaf.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_tx_amctl
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so the `vibe_ebch16` instances, combo
LID `case`, and 40-symbol assemble body stay.
