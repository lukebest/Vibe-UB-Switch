# vibe_pcs_rx_fec

PCS RX FEC wrap (AS-0.1 §6). Decision I stage-18
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_rx` `u_fec`) under the pycircuit →
rtl flow. Assemble 2×512 → RS syndrome check / bypass; `fec_fail`
on fail; `am_gap` drops a leftover half-CW. Inline syndromes
(same Horner as stage-12 `vibe_rs128_120_dec`); does **not**
instantiate the decoder. Pairs with stage-17 `vibe_pcs_tx_fec`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_rx_fec.py` |
| Product SV | `rtl/pcs/vibe_pcs_rx_fec.sv` |
| Instantiator | `vibe_pcs_rx` (`u_fec`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `b7233f49` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`). Stock
`am_gap = 1'b0` default stays on **line 14** (Verilator
`UNSUPPORTED` on input defaults is pre-existing; official
`.vlt` already waives that line; pins are always connected
at instantiate).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `fec_mode[2:0]` | in | `VIBE_FEC_T4` / `T2` / `BYPASS` (`3'b010` / `3'b001` / `3'b000`) |
| `beat_data[511:0]` | in | 512b codeword half |
| `beat_vld` | in | beat available |
| `beat_ready` | out | combo `!win_vld` (ready while the window is free) |
| `win_data[959:0]` | out | 960b message window (`{hi, beat_data[511:64]}`) |
| `win_vld` | out | window available (clean CW or bypass) |
| `win_ready` | in | downstream accept |
| `am_gap` | in | 1: drop half-CW so 1024b does not straddle AMCTL (default `1'b0`) |
| `fec_fail` | out | 1-cycle pulse when `!bypass` and any syndrome is nonzero |

No parameters. This is **not** g1 / tx / rx tops (later
stages). Stage-1..17 leaves are left intact. Does **not**
instantiate `vibe_rs128_120_dec`.

## Flow

One always block plus combo ready / `{hi, beat_data}` /
`rs_syndromes`. Collect the first 512b into `hi` /
`have_hi`. The second beat forms a 1024b CW. One-shot
syndromes over all 128 symbols (idle zeros must not hide a
later overwrite). Bypass (`fec_mode == VIBE_FEC_BYPASS`) or
`syn == 0` emits the 960b window. Else `fec_fail`; the CW is
still consumed so pairing stays on the 2×512 grid. A failed
CW must not become a 960 for inverse G1 / DLL.

`am_gap` clears `have_hi` (hunt and locked). TX inserts AM
only between 5×512 groups; a leftover first-half must not
straddle that gap.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_rx_fec
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the inline
syndrome functions, combo ready, `am_gap` on waived line 14,
and the collect / check / emit body stay. Ports / RX FEC wrap
match stock (header-only vs stock). Official `.vlt` is
not expanded.
