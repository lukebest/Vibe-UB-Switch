# vibe_pcs_tx_cw2beat

1024b codeword as two 512b beats (AS-0.1 §5 T4). Decision I
stage-9 pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_tx` `u_cw`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_tx_cw2beat.py` |
| Product SV | `rtl/pcs/vibe_pcs_tx_cw2beat.sv` |
| Instantiator | `vibe_pcs_tx` (`u_cw`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `c8804c0` / freeze `302ac943`. Ready/valid on both sides.
Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `cw_data[1023:0]` | in | FEC 1024b codeword |
| `cw_vld` | in | codeword available |
| `cw_ready` | out | combo `!have_hi && !have_lo` |
| `beat_data[511:0]` | out | combo `have_hi ? hi : lo` |
| `beat_vld` | out | combo `have_hi or have_lo` |
| `beat_ready` | in | consumer takes the 512b beat |

No parameters. This is **not** `vibe_pcs_tx` / amctl / pack / FEC /
RS / rx (later stages). Stage-7 `vibe_pcs_scramble` and stage-8
`vibe_ebch16` are left intact.

## Flow

One always block plus combo ready/valid. Accept (`cw_vld && cw_ready`)
parks `cw_data[1023:512]` in `hi` and `cw_data[511:0]` in `lo`, and
sets both `have_hi` and `have_lo`. Consume (`beat_vld && beat_ready`)
clears `have_hi` first (high beat), then `have_lo` (low beat).
`cw_ready` and `beat_vld` are mutually exclusive in stock — a new
codeword is taken only when both halves are empty.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_tx_cw2beat
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, combo ready/valid,
and the 1024→2×512 split body stay.
