# vibe_rst_sync

Async-assert / sync-deassert reset into a destination clock
(AS-0.1 §3). Decision I stage-4 pyCircuit leaf. Re-homes
pre-Decision I stock RTL (same-layer CDC used by `vibe_port`
`u_txrst` / `u_rxrst`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/cdc/vibe_rst_sync.py` |
| Product SV | `rtl/cdc/vibe_rst_sync.sv` |
| Instantiator | `vibe_port` (`u_txrst` / `u_rxrst`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `49421f9` / freeze `302ac943`. No ready/valid. Reset stays
**async assert on `rst_n_in`**, **sync release into `clk`**.

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | dest-domain clock |
| `rst_n_in` | in | async active-low assert (source / logical reset) |
| `rst_n_out` | out | dest-domain reset, sync deassert (2-FF) |

No parameters.

## Flow

One always block: async `!rst_n_in` clears `r1` and `rst_n_out` to 0.
On dest clocks after release: `r1 <= 1'b1; rst_n_out <= r1`. This is a
same-layer 2-FF reset cell; it is **not** `vibe_sync2` and **not** gear.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_rst_sync
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n_in` and the 2-FF body stay.
