# vibe_pcs_tx_fec

PCS TX FEC wrap (AS-0.1 §5 T3). Decision I stage-17
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS cell used by `vibe_pcs_tx` `u_fec`) under the pycircuit →
rtl flow. Two interleaved RS(128,120); T=4 default / T=2 /
bypass. Instantiates stage-11 `vibe_rs128_120_enc` ×2.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_pcs_tx_fec.py` |
| Product SV | `rtl/pcs/vibe_pcs_tx_fec.sv` |
| Instantiator | `vibe_pcs_tx` (`u_fec`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `ee5e8f4` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `fec_mode[2:0]` | in | `VIBE_FEC_T4` / `T2` / `BYPASS` (`3'b010` / `3'b001` / `3'b000`) |
| `win_data[959:0]` | in | 960b message window (120 symbols) |
| `win_vld` | in | window available |
| `win_ready` | out | combo `!have1` (ready while a slot is free) |
| `cw_data[1023:0]` | out | 1024b codeword (960b + 8 parity) |
| `cw_vld` | out | codeword available |
| `cw_ready` | in | downstream accept |

No parameters. This is **not** RX FEC wrap / g1 / tx / rx
tops (later stages). Stage-1..16 leaves are left intact.

## Flow

One always block plus combo ready / symbol slices. Two
`vibe_rs128_120_enc` instances (`u_enc_a` / `u_enc_b`). Collect
`w0` then `w1`. `win_ready = !have1` stays 1 on the w1 accept
so G1 drops the window.

Encode (`fec_mode != VIBE_FEC_BYPASS`): on the second window,
pulse `enc_a_start` / `enc_b_start` and run both encoders in
parallel (`enc_*_vld = enc_go`, `enc_*_sym = w*[959-8*sym_cnt -: 8]`).
120 symbols; `enc_a_done && enc_b_done` forms
`cwa = {w0, par_a}` / `cwb = {w1, par_b}` and sets `pair_done`.
Emit `cwa` then `cwb` while `!cw_vld`; the second emit clears
`have0` / `have1` / `pair_done`. T=2 encoding produces the
same 8 parity symbols (mode pin only).

Bypass (`fec_mode == VIBE_FEC_BYPASS`): skip encoder, still
6-flit (two-window) align. Emit `{w0, 64'd0}` then
`{w1, 64'd0}`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pcs_tx_fec
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`vibe_rs128_120_enc` instances, combo ready / symbol slices,
and the collect / encode / bypass / emit body stay. Ports /
FEC wrap match stock (header-only vs stock). Official `.vlt` is
not expanded.
