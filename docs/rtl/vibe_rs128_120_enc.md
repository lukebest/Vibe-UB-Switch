# vibe_rs128_120_enc

Systematic RS(128,120) encoder over GF(256) (AS-0.1 §5 T3 /
UB 2.0 §3.2.2). Decision I stage-11 pyCircuit leaf. Re-homes
pre-Decision I stock RTL (same-layer PCS FEC building block used
by `vibe_pcs_tx_fec` `u_enc_a` / `u_enc_b`) under the pycircuit →
rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_rs128_120_enc.py` |
| Product SV | `rtl/pcs/vibe_rs128_120_enc.sv` |
| Instantiator | `vibe_pcs_tx_fec` (`u_enc_a` / `u_enc_b`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `984e3b9` / freeze `302ac943`. One message symbol per
accepted cycle. Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `start` | in | clear LFSR (`r0`..`r7`, `cnt`) and set `busy` |
| `in_vld` | in | message symbol available |
| `in_sym[7:0]` | in | one GF(256) message symbol |
| `in_ready` | out | combo `busy && (cnt < 8'd120)` |
| `done` | out | 1-cycle pulse after the 120th accepted symbol |
| `parity[63:0]` | out | combo `{r7,r6,r5,r4,r3,r2,r1,r0}` (p7..p0) |

No parameters. This is **not** `vibe_pcs_tx_fec` / pack / g1 / tx
wrap / rx / decoder (later stages). Stage-7 `vibe_pcs_scramble`,
stage-8 `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`, and stage-10
`vibe_pcs_tx_amctl` are left intact.

## Flow

One always block plus combo ready / parity. `start` (if/else
priority) zeros the 8-symbol LFSR and `cnt`, and sets `busy`.
While `busy && in_vld && in_ready`, feedback `fb = in_sym ^ r7`
updates the registers with Table 3-2 generator coefficients
(`G0..G7` = 24 / 200 / 173 / 239 / 54 / 81 / 11 / 255) via
`vibe_gf256_mul` from `vibe_ub_fn.vh`:

`r0 <= mul(fb,G0)`, `r1 <= r0 ^ mul(fb,G1)`, …, `r7 <= r6 ^ mul(fb,G7)`.

The 120th accepted symbol (`cnt==119`) drops `busy` and pulses
`done`. T=2 encoding produces the same 8 parity symbols.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_rs128_120_enc
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`vibe_ub_fn.vh` include, `vibe_gf256_mul` LFSR step, and combo
`in_ready` / `parity` stay.
