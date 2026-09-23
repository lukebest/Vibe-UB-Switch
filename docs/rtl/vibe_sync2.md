# vibe_sync2

2-FF dest-domain synchronizer (AS-0.1 §7). Decision I stage-3
pyCircuit leaf. Re-homes pre-Decision I stock RTL (same-layer CDC
used by `vibe_afifo`) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/cdc/vibe_sync2.py` |
| Product SV | `rtl/cdc/vibe_sync2.sv` |
| Instantiator | `vibe_afifo` (`u_r2w`, `u_w2r`, `W=5`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `7cf680f` / freeze `302ac943`. No ready/valid. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | dest-domain clock |
| `rst_n` | in | dest-domain async active-low |
| `d[W-1:0]` | in | unsynchronized input (gray in `vibe_afifo`) |
| `q[W-1:0]` | out | 2-FF dest-domain sample |

Parameter: `W` (default 5). Product AFIFO instantiates `#(.W(5))`.

## Flow

One always block: `q1 <= d; q <= q1`. Both stages clear to 0 on
`!rst_n`. This is a same-layer multi-bit 2-FF cell for gray pointers;
it is **not** `vibe_rst_sync` and **not** gear.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_sync2
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n` and the 2-FF body stay.
