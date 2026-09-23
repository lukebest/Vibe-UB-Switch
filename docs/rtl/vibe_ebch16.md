# vibe_ebch16

eBCH-16 codeword LUT (AS-0.1 §5 / UB 3.2.4.1 Table 3-5). Decision I
stage-8 pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer
PCS helper used by `vibe_pcs_tx_amctl` and `vibe_pcs_rx_amctl_lock`)
under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pcs/vibe_ebch16.py` |
| Product SV | `rtl/pcs/vibe_ebch16.sv` |
| Instantiator | `vibe_pcs_tx_amctl`; `vibe_pcs_rx_amctl_lock` |
| SPEC / CR-B | Unchanged. Internal leaf; no clocks/resets |

## Ports (product)

Same as tip `9f86cba` / freeze `302ac943`. Combo LUT. No clock.
No ready.

| Port | Dir | Notes |
|------|-----|--------|
| `cw_sel[4:0]` | in | Table 3-5 index (0..30); 31 is default |
| `cw[15:0]` | out | eBCH-16 codeword |

No parameters. This is **not** `vibe_pcs_tx` / rx / FEC / RS /
amctl (later stages). Stage-7 `vibe_pcs_scramble` is left intact.

## Flow

One `always @*` `case (cw_sel)`: sel 0..30 emit Table 3-5
(`16'h0000` … `16'hF590`); default is `16'hFFFF`. Same-layer
PCS helper — **not** a CDC cell.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_ebch16
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so the combo `case (cw_sel)` LUT stays.
