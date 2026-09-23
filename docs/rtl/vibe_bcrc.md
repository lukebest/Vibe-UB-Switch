# vibe_bcrc

DLL BCRC CRC30 (AS-0.1 §12). Decision I stage-20
pyCircuit leaf. Re-homes pre-Decision I stock RTL (first
DLL helper under `pycircuit/dll/`) under the pycircuit →
rtl flow. CRC30 init all-1s; no invert. bit31 reserved,
bit30 `ERROR_FLAG`. Self-contained (no child instances).
First DLL leaf after PCS leaf cells (stage-1..19).
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_bcrc.py` |
| Product SV | `rtl/dll/vibe_bcrc.sv` |
| Instantiator | Unit TB (`u_bcrc`); `vibe_dll_tx` inlines the same CRC30 |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `1e57f2a5` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `start` | in | reload CRC30 to all-1s (wins over `in_vld`) |
| `in_vld` | in | eat one 160b flit |
| `in_flit[159:0]` | in | DLL flit (LSB first through `crc30_step`) |
| `last` | in | this flit ends the block; emit `crc_word` / `done` |
| `error_flag` | in | packed into bit30 of `crc_word` |
| `crc_word[31:0]` | out | `{1'b0, error_flag, crc[29:0]}` (no invert) |
| `done` | out | 1-cycle pulse on the last-flit NBA |

No parameters. This is **not** PCS tx / rx tops (later
stages) and **not** the rest of DLL. Stage-1..19 leaves
are left intact. Does **not** instantiate children.
`include "vibe_ub_params.vh"` for `VIBE_BCRC_POLY`.

## Flow

One always block plus `crc30_step`. State: `crc[29:0]`
(init `{30{1'b1}}`) / `crc_word` / `done`.

`start` reloads all-1s. Else `in_vld` walks 160 bits
LSB-first: `t = {c[28:0], 1'b0} ^ ({30{c[29]^b}} & POLY)`.
On `last`, `crc_word <= {1'b0, error_flag, t}` and `done`
is a 1-cycle pulse (`done <= 0` every cycle, last-wins 1).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_bcrc
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`VIBE_BCRC_POLY`, `crc30_step`, and the 160-bit eat loop
stay. Ports / CRC30 match stock (header-only vs stock).
Official `.vlt` is not expanded.
