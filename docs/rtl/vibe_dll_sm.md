# vibe_dll_sm

DLL link SM (AS-0.1 §12). Decision I stage-22
pyCircuit leaf. Re-homes pre-Decision I stock RTL (third
DLL helper under `pycircuit/dll/`, after `vibe_bcrc` /
`vibe_dll_credit`) under the pycircuit → rtl flow.
Disabled when `LinkUp==0`. Entity reset must not force
Disabled via `rst` alone beyond async `rst_n` /
`port_rst`. States Disabled → Param → Credit → Normal.
`dll_error` → Disabled. `status_up` when Normal.
Self-contained (no child instances). Third DLL leaf
after `vibe_bcrc` / `vibe_dll_credit`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_sm.py` |
| Product SV | `rtl/dll/vibe_dll_sm.sv` |
| Instantiator | `vibe_dll` (`u_sm`); unit TC (`tc_dll_sm_states`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `39d3aa1d` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | force `ST_DIS` (entity rst is **not** this pin) |
| `link_up` | in | 0: force `ST_DIS` (AS-0.1 §12) |
| `param_ok` | in | Param → Credit |
| `credit_ok` | in | Credit → Normal |
| `dll_error` | in | force `ST_DIS` from any state |
| `state[1:0]` | out | combo `st` (`0` DIS / `1` PARM / `2` CRD / `3` NRM) |
| `status_up` | out | combo `st == ST_NRM` |
| `disabled` | out | combo `st == ST_DIS` |

No parameters. This is **not** PCS tx / rx tops (later
stages) and **not** remaining DLL wraps (`retry_*`,
tx/rx, dll top). Stage-1..21 leaves are left intact.
Does **not** instantiate children.

## Flow

One always block plus combo decode. State: `st[1:0]`
(init `ST_DIS`).

`!rst_n` / `port_rst` / `!link_up` / `dll_error` →
`ST_DIS`. Else `ST_DIS` → `ST_PARM` → (`param_ok`)
`ST_CRD` → (`credit_ok`) `ST_NRM`. Default (including
`ST_NRM`) holds Normal. There is **no** entity-reset
pin on this SM.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_sm
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
Disabled-on-`LinkUp==0`, no entity-rst pin, the
Disabled → Param → Credit → Normal walk, `dll_error` →
Disabled, and `status_up` in Normal stay. Ports /
behavior match stock (header-only vs stock).
Official `.vlt` is not expanded.
