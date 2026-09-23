# vibe_dll_retry_req_sm

DLL RETRY_REQ_SM (AS-0.1 §12). Decision I
stage-26 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(seventh DLL helper under `pycircuit/dll/`, after `vibe_bcrc`
/ `vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf`) under
the pycircuit → rtl flow. NORMAL / REQ (1 Idle + burst
Req) / WAIT (`RETRY_WAIT_CYC`, default 12500) / RETRAIN /
ERROR. `VIBE_NUM_RETRY` / `VIBE_NUM_PHY_REINIT` from
`vibe_ub_params.vh`. Self-contained (no child instances).
Seventh DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx` / `vibe_dll_retry_ack_sm` /
`vibe_dll_retry_buf`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_retry_req_sm.py` |
| Product SV | `rtl/dll/vibe_dll_retry_req_sm.sv` |
| Instantiator | `vibe_dll` (`u_req`); unit TCs (`tc_retry_req_gbn`, `tc_retry_wait_retrain`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `1891dec0` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | force `ST_N` / clear retry, phy, burst (not `wtmr`) |
| `device_rst` | in | same clear as `port_rst` |
| `start_retry` | in | NORMAL → REQ (`burst=0`, Idle); FEC/BCRC Go-Back-N |
| `phy_retrain` | in | at REQ burst done → RETRAIN |
| `wait_done_ack` | in | WAIT → NORMAL |
| `state[2:0]` | out | combo `st` (`0` NORMAL / `1` REQ / `2` WAIT / `3` RETRAIN / `4` ERROR) |
| `drop_data` | out | combo `(st==ST_Q) || (st==ST_W)` |
| `retrain_req` | out | combo `st == ST_R` |
| `retry_error` | out | combo `st == ST_E` |
| `send_idle` | out | combo `(st==ST_Q) && (burst==0)` |
| `send_req` | out | combo `(st==ST_Q) && (burst!=0)` |
| `send_cnt[4:0]` | out | combo `burst[4:0]` |

Parameter `RETRY_WAIT_CYC` default 12500 (10 µs). This is
**not** PCS tx / rx tops (later stages) and **not**
remaining DLL wraps (`vibe_dll_tx`, dll top). Stage-1..25
leaves are left intact. Does **not** instantiate children.
`include "vibe_ub_params.vh"` (stock; `VIBE_NUM_RETRY` 15,
`VIBE_NUM_PHY_REINIT` 4).

## Flow

One always block plus combo decode. State: `st[2:0]`
(init `ST_N`), `num_retry[3:0]`, `num_phy[2:0]`,
`wtmr[23:0]`, `burst[5:0]`.

`!rst_n` → `ST_N`, counters 0, `wtmr=0`, `burst=0`.
`port_rst || device_rst` → same except `wtmr` stays
(stock). Else `ST_N` + `start_retry` → `ST_Q` with
`burst=0` (1 Idle). Then `burst` 1..32 (Req). At
`burst==32` increment `num_retry`; if
`num_retry+1==VIBE_NUM_RETRY` or `phy_retrain` enter
`ST_R`, else `ST_W` with `wtmr<=RETRY_WAIT_CYC`. WAIT:
`wait_done_ack` → `ST_N`; `wtmr==0` → `ST_Q` with
`burst=0`; else `wtmr-1`. RETRAIN increments `num_phy`;
`num_phy+1==VIBE_NUM_PHY_REINIT` → `ST_E` else `ST_N`.
ERROR waits Port / device reset. Default (illegal `st`)
→ `ST_N`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_retry_req_sm
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
NORMAL / REQ (1 Idle + burst Req) / WAIT
(`RETRY_WAIT_CYC`) / RETRAIN / ERROR stay. Ports /
behavior match stock (header-only vs stock). Official
`.vlt` is not expanded.
