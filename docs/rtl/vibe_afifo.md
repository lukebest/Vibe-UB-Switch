# vibe_afifo

Per-lane gray-pointer async FIFO (AS-0.1 §7). First pyCircuit leaf after
Decision I unfroze RTL `302ac943`.

| | |
|---|---|
| Python | `pycircuit/cdc/vibe_afifo.py` |
| Product SV | `rtl/cdc/vibe_afifo.sv` |
| Instantiators | `vibe_port` TX×4 (`W=160`) and RX×4 (`W=128`) |
| SPEC / CR-B | Unchanged. Internal leaf; no `{src}_{dst}_{meaning}` ports |

## Ports (product)

Same as freeze `302ac943`. Do not invent ready/valid names.

| Port | Dir | Notes |
|------|-----|--------|
| `wclk` | in | write clock |
| `wrst_n` | in | write-domain async active-low |
| `wen` | in | write when `wen && !wfull` |
| `wdata[W-1:0]` | in | default `W=160` |
| `wfull` | out | `wocc == DEPTH` |
| `almost_full` | out | `wocc >= VIBE_AFIFO_AFULL_OCC` (10) |
| `wocc[4:0]` | out | `wbin - gray2bin(rgray synced to wclk)` |
| `rclk` | in | read clock |
| `rrst_n` | in | read-domain async active-low |
| `ren` | in | pop when `ren && !rempty` |
| `rdata[W-1:0]` | out | combo `mem[rbin[3:0]]` |
| `rempty` | out | `rbin == gray2bin(wgray synced to rclk)` |

Parameters: `W` (default 160), `DEPTH` (product 16, pointer 5 bits).
`DEPTH != 16` is not a product configuration.

## Flow

Write domain: binary `wbin` → gray → `vibe_sync2` into read domain.
Read domain: binary `rbin` → gray → `vibe_sync2` into write domain.
Occupancy and `almost_full` are write-domain only. RAM write is `wclk`;
read is combinational; memory is not reset.

`vibe_port` uses `almost_full` on TX and `wfull` on RX overflow. `ovf_l`
(F1) is **not** in this module — do not ECO it from this leaf.

## Regenerate

```bash
make -C pycircuit vibe_afifo
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low reset and `vibe_sync2` stay.
