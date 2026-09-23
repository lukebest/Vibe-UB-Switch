# vibe_dll_retry_ack_sm

DLL RETRY_ACK_SM (AS-0.1 §12). Decision I
stage-24 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(fifth DLL helper under `pycircuit/dll/`, after `vibe_bcrc`
/ `vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx`) under
the pycircuit → rtl flow. NORMAL / ACK (1 Idle + 32 Ack
then replay `RdPtr=RcvPtr` until `WrPtr`). Self-contained
(no child instances). Fifth DLL leaf after `vibe_bcrc` /
`vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_retry_ack_sm.py` |
| Product SV | `rtl/dll/vibe_dll_retry_ack_sm.sv` |
| Instantiator | `vibe_dll` (`u_ack`); unit TC (`tc_retry_ack_replay`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `0b0a82db` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | force `ST_N` / clear burst and `rd_ptr` |
| `start_ack` | in | NORMAL → ACK (`burst=0`, Idle) |
| `wr_ptr[7:0]` | in | replay stop (`rd_ptr == wr_ptr`) |
| `rcv_ptr[7:0]` | in | replay start (`rd_ptr <= rcv_ptr` at ACK done) |
| `state[2:0]` | out | combo `st` (`0` NORMAL / `1` ACK / `2` replay) |
| `send_idle` | out | combo `(st==ST_A) && (burst==0)` |
| `send_ack` | out | combo `(st==ST_A) && (burst!=0)` |
| `replay` | out | combo `st == ST_P` |
| `rd_ptr[7:0]` | out | combo `rp` (set to `rcv_ptr` then +1) |

No parameters. This is **not** PCS tx / rx tops (later
stages) and **not** remaining DLL wraps (`retry_buf`,
`retry_req_sm`, `vibe_dll_tx`, dll top). Stage-1..23
leaves are left intact. Does **not** instantiate children.

## Flow

One always block plus combo decode. State: `st[2:0]`
(init `ST_N`), `burst[5:0]`, `rp[7:0]`.

`!rst_n` / `port_rst` → `ST_N`, `burst=0`, `rp=0`. Else
`ST_N` + `start_ack` → `ST_A` with `burst=0` (1 Idle).
Then `burst` 1..32 (32 Ack). At `burst==32` enter `ST_P`
with `rp<=rcv_ptr`. Replay increments `rp` until
`rp==wr_ptr`, then back to `ST_N`. Default (illegal `st`)
→ `ST_N`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_retry_ack_sm
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
NORMAL / ACK (1 Idle + 32 Ack) then replay
`RdPtr=RcvPtr` until `WrPtr` stay. Ports / behavior
match stock (header-only vs stock). Official `.vlt` is
not expanded.
