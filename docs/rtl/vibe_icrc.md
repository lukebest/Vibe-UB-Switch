# vibe_icrc

NW ICRC CRC32 (AS-0.1 §13). Decision I stage-36
pyCircuit leaf. Re-homes pre-Decision I stock RTL (first
NW helper under `pycircuit/nw/`) under the pycircuit →
rtl flow. CRC32 poly `0x04C11DB7` init `0xFFFFFFFF`;
per-byte bit reverse then reverse+invert. Self-contained
(no child instances). First NW leaf after PCS/CDC/DLL/
fabric leaves (stage-1..35).
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/nw/vibe_icrc.py` |
| Product SV | `rtl/nw/vibe_icrc.sv` |
| Instantiator | Unit TB (`u_icrc`); intended for `cna_ep` (sender/receiver) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `186dde4e` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / NW digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `start` | in | reload CRC32 to all-1s (wins over `in_vld`) |
| `in_vld` | in | eat one byte |
| `in_byte[7:0]` | in | next byte (`vibe_rev8` then `step8`) |
| `last` | in | this byte ends the block; emit `crc_out` / `done` |
| `crc_out[31:0]` | out | `~vibe_rev32(step8(crc, in_byte))` |
| `done` | out | 1-cycle pulse on the last-byte NBA |

No parameters. This is **not** PCS tx / rx tops (later
stages), **not** `vibe_port` / `vibe_ub_switch` tops, and
**not** other NW stubs (`vibe_nw_adapt`) or `vibe_fabric`
top. Stage-1..35 leaves are left intact.
Does **not** instantiate children.
`include "vibe_ub_params.vh"` for `VIBE_ICRC_POLY`.
`include "vibe_ub_fn.vh"` for `vibe_rev8` / `vibe_rev32`.
Transit has **no** ICRC unit.

## Flow

One always block plus `step8`. State: `crc[31:0]`
(init `32'hFFFF_FFFF`) / `crc_out` / `done`.

`start` reloads all-1s. Else `in_vld` walks 8 bits of
`vibe_rev8(in_byte)` MSB-first:
`t = {c[30:0], 1'b0} ^ ({32{c[31]^br[7-k]}} & POLY)`.
On `last`, `crc_out <= ~vibe_rev32(step8(crc, in_byte))`
and `done` is a 1-cycle pulse (`done <= 0` every cycle,
last-wins 1).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_icrc
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`VIBE_ICRC_POLY`, `vibe_rev8` / `vibe_rev32`, and
`step8` stay. Ports / CRC32 match stock (header-only vs
stock). Official `.vlt` is not expanded.
