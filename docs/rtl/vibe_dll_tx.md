# vibe_dll_tx

DLL TX pack (AS-0.1.2 / FS-0.2.7 overlay B). Decision I
stage-34 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(eighth DLL helper under `pycircuit/dll/`, after `vibe_bcrc`
/ `vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm`) under the pycircuit → rtl flow.
512b NW byte stream → 20B flits with cross-beat remainder
(64B beat, 20B flit, rem 4B). Emit one 640b beat (4 flits
+ BCRC in last 32b) when a group is ready. Short EOP that
leaves `fq_n % 4 != 0` is Null-padded to the next 4-flit
group (UB T2 / AS T1). Credit consume counts data flits
only. CFG0 does not consume credit. Self-contained (no
child instances). Eighth DLL leaf after `vibe_bcrc` /
`vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_tx.py` |
| Product SV | `rtl/dll/vibe_dll_tx.sv` |
| Instantiator | `vibe_dll` (`u_tx`); unit TC (`tc_dll_tx_cfg0`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `dfa505a6` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `link_up` | in | 0: clear rem / pkt / `fq_n` / `dll_pcs_vld` |
| `status_up` | in | NW accept requires up |
| `credit_low` | in | backpressure NW |
| `bp_pending` | in | pending ≥ 1024 cell |
| `drop_data` | in | REQ\|WAIT dropping data |
| `can_send` | in | retry / SM allow |
| `replay` | in | emit `{replay_flit, 480'0}` |
| `replay_flit[159:0]` | in | retry-buffer flit |
| `send_idle` | in | AMCTL Idle; `is_null` |
| `send_req` | in | AMCTL Req; `is_retry` |
| `send_ack` | in | AMCTL Ack; `is_retry` |
| `nw_dll_data[511:0]` | in | 64B NW beat |
| `nw_dll_vld` | in | NW beat valid |
| `nw_dll_ready` | out | combo accept (up, not BP, `fq_occ <= 4`) |
| `dll_pcs_data[639:0]` | out | 4-flit PCS beat + BCRC |
| `dll_pcs_vld` | out | PCS beat valid |
| `dll_pcs_ready` | in | PCS accept |
| `wr_en` | out | data emit to retry buf (`emitting`) |
| `wr_flit[159:0]` | out | `fq[0]` |
| `is_null` | out | combo `send_idle` |
| `is_retry` | out | combo `send_req \|\| send_ack` |
| `consume_flits[9:0]` | out | `{7'b0, n_flits}` this accept |
| `consume_vld` | out | `nw_dll_vld && nw_dll_ready` |
| `consume_cfg0` | out | SOP CFG0 (does not consume credit) |

`include "vibe_ub_params.vh"` for `VIBE_BCRC_POLY`.
`include "vibe_ub_fn.vh"` for `vibe_nw512_flit0` /
`vibe_pkt_bytes` / `vibe_lph_cfg`. This is **not** PCS
tx / rx tops (later stages), **not** `vibe_dll` top, and
**not** `vibe_fabric` top. Stage-1..33 leaves are left
intact. Does **not** instantiate children.

## Flow

Combo ready / emit / consume plus one async-low sequential
and a combo `fq_nxt` pack. State: `rem_lj[159:0]` /
`rem_b[4:0]` / `pkt_act` / `pkt_left[15:0]` / 8-deep
`fq[159:0]` / `fq_n[3:0]` / `dll_pcs_data[639:0]` /
`dll_pcs_vld`.

LPH is `vibe_nw512_flit0` = `nw_dll_data[511:352]`.
`emitting` when `fq_n >= 4` and the PCS slot is free and
not AMCTL/replay. `nw_dll_ready` when link/status up, not
credit-low / pending / drop / replay / AMCTL, `can_send`,
and `fq_occ <= 4`. Accept packs leftover rem || valid NW
bytes in a 672b window, pushes 0–4 flits, and on EOP
Null-pads to a 4-flit group. A ready group emits
`{fq[0], fq[1], fq[2], fq[3][159:32], crc_w}` with CRC30
init all-1s (same poly as `vibe_bcrc`; no invert; last
32b `{1'b0, 1'b0, crc3}`). Idle/Req/Ack emit a zero 640b
beat; replay emits `{replay_flit, 480'0}`. CFG0 SOP
pulses `consume_cfg0` so credit cells stay 0.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_tx
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`vibe_ub_params.vh` / `vibe_ub_fn.vh`, 512b→20B rem pack,
4-flit + BCRC emit, EOP Null-pad, and CFG0 skip stay.
Ports / TX match stock (header-only vs stock). Official
`.vlt` is not expanded.
