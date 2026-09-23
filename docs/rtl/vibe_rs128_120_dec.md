# vibe_rs128_120_dec

RS(128,120) syndrome-check decoder over GF(256) (AS-0.1 §6).
Decision I stage-12 pyCircuit leaf. Re-homes pre-Decision I stock
RTL (same-layer PCS FEC building block; paired with stage-11
`vibe_rs128_120_enc`) under the pycircuit → rtl flow.
`vibe_pcs_rx_fec` uses the same Horner recurrence in one shot
(not an instance). **No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_rs128_120_dec.py` |
| Product SV | `rtl/pcs/vibe_rs128_120_dec.sv` |
| Instantiator | unit TCs (`tc_rs_dec_syndrome`); same recurrence inlined in `vibe_pcs_rx_fec` |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `984e3b9` / freeze `302ac943`. One codeword symbol per
accepted cycle. Reset stays **async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / PCS digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `start` | in | clear syndromes (`s0`..`s7`, `cnt`) and set `busy` |
| `in_vld` | in | codeword symbol available |
| `in_sym[7:0]` | in | one GF(256) codeword symbol |
| `in_ready` | out | combo `busy && (cnt < 8'd128)` |
| `done` | out | 1-cycle pulse after the 128th accepted symbol |
| `fec_fail` | out | 1-cycle pulse when any next-syndrome is nonzero |
| `data_out[959:0]` | out | packed `msg[0]`..`msg[119]` (`msg[0]` is MSB) |

No parameters. This is **not** `vibe_pcs_rx_fec` / pack / g1 / tx
wrap / rx / amctl_lock / deskew / unpack (later stages). Stage-7
`vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
`vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, and stage-11
`vibe_rs128_120_enc` are left intact.

## Flow

One always block plus combo ready / next-syndromes. `start` (if/else
priority) zeros the 8 syndromes and `cnt`, and sets `busy`.
While `busy && in_vld && in_ready`, Horner updates

`ns0 = s0 ^ in_sym`, `ns1 = gf_mul2(s1) ^ in_sym`,
`ns2 = mul(s2,4) ^ in_sym`, …, `ns7 = mul(s7,128) ^ in_sym`

via `vibe_gf256_mul` from `vibe_ub_fn.vh` (and local `gf_mul2` for
`α^1`). Message symbols (`cnt < 120`) land in `msg[cnt]`. The 128th
accepted symbol (`cnt==127`) drops `busy`, pulses `done`, sets
`fec_fail` from `|{ns0..ns7}` (last symbol included), and packs
`msg[0]` as the first symbol (MSB of `data_out`). T=2 check is
syndrome-only.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_rs128_120_dec
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, the
`vibe_ub_fn.vh` include, combo next-syndromes, `msg[0:119]` pack,
and combo `in_ready` stay. Ports / syndrome path / `data_out` pack
match stock. Reset of `msg[0:119]` is unrolled NBA
`msg[i] <= 8'd0` (same zeros as the stock reset `for`; Icarus-legal
and Verilator 5.020 `BLKLOOPINIT` / `BLKSEQ` clean).
