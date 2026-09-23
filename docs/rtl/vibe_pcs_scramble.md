# vibe_pcs_scramble

PCS LTB/DLL scramble (AS-0.1 §5 / UB 3.2.2.4). Decision I stage-7
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer PCS
cell used by `vibe_pcs_tx` `u_s0`..`u_s3` and `vibe_pcs_rx`
`u_d0`..`u_d3`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_scramble.py` |
| Product SV | `rtl/pcs/vibe_pcs_scramble.sv` |
| Instantiator | `vibe_pcs_tx` (`u_s0`..`u_s3`); `vibe_pcs_rx` (`u_d0`..`u_d3`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `5087843` / freeze `302ac943`. No ready. Fire is
`in_vld`. Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `lane_id[1:0]` | in | AMCTL.LID (physical=logical this rev) |
| `seed_load` | in | load `{19'd1, lane_id, 2'b01}` |
| `en` | in | 0 = pass-through (AMCTL/EEIB); LFSR does not advance |
| `in_vld` | in | 160b beat available |
| `in_data[159:0]` | in | LTB / DLL beat |
| `out_vld` | out | registered `in_vld` |
| `out_data[159:0]` | out | `en ? (in_data ^ xmask) : in_data` when `in_vld` |

No parameters. This is **not** `vibe_pcs_tx` / rx / FEC / RS
(later stages). Same poly + seed as PMA PRBS23 (issue #115).

## Flow

Combo `xmask[159:0]` is LFSR[0] after 0..159 steps of
`{s[21:0], s[22] ^ s[17]}`. Reset seed is `{21'd0, 2'b01}`.
`seed_load` writes `{19'd1, lane_id, 2'b01}`. On `in_vld && en`
the LFSR advances 160 steps from the **current** state; if
`seed_load` is also high that cycle, NBA last-wins is the
advance (stock). `en=0` (AMCTL/EEIB) passes `in_data` and
does not step the LFSR.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_scramble
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo `xmask`,
and the seed / pass-through body stay.
