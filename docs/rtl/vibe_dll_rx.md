# vibe_dll_rx

DLL RX unpack (AS-0.1.2 / FS-0.2.7 overlay B). Decision I
stage-23 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(fourth DLL helper under `pycircuit/dll/`, after `vibe_bcrc`
/ `vibe_dll_credit` / `vibe_dll_sm`) under the pycircuit →
rtl flow. 640b PCS → 4 flits, unBCRC, pack to 512b NW with
remainder. LPH is the first 160b flit. After EOP drop
intra-group leftover. CFG0 terminate. FEC/BCRC fail →
Go-Back-N. `dll_rxbuf` = 1024 flit/VL. `start_ack` tied 0
as stock. Self-contained (no child instances). Fourth DLL
leaf after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_rx.py` |
| Product SV | `rtl/dll/vibe_dll_rx.sv` |
| Instantiator | `vibe_dll` (`u_rx`); unit TCs (`tc_cfg0_term_not_fabric`, `tc_dll_rx_errflag`, `tc_fec_fail_gbn`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `7543c944` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`). Parameter
`RXBUF` default 1024.

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | clear have / vld / cfg0 / pkt / byte lane |
| `link_up` | in | 0: same clear; leftover → abort NW beat |
| `fec_fail` | in | combo `start_retry`; stock also clears `bcrc_fail` |
| `pcs_dll_data[639:0]` | in | 4-flit PCS beat |
| `pcs_dll_vld` | in | PCS beat valid |
| `pcs_dll_ready` | out | combo: CFG0 or idle lane when `link_up` |
| `dll_nw_data[511:0]` | out | packed 512b NW beat |
| `dll_nw_vld` | out | NW beat valid |
| `dll_nw_ready` | in | NW accept |
| `cfg0_hit` | out | CFG0 terminate (does not enter fabric) |
| `cfg0_data[639:0]` | out | captured CFG0 beat |
| `bcrc_fail` | out | pulsed 0 each cycle (stock); `start_retry` ORs it |
| `start_retry` | out | combo `fec_fail \|\| bcrc_fail` (Go-Back-N) |
| `rx_ovf` | out | `wptr[vl] - rptr[vl] >= RXBUF` |
| `start_ack` | out | tied `1'b0` as stock |

`include "vibe_ub_fn.vh"` for `vibe_lph_cfg` / `vibe_lph_vl`
/ `vibe_pkt_bytes`. This is **not** PCS tx / rx tops (later
stages) and **not** remaining DLL wraps (`retry_*`,
`vibe_dll_tx`, dll top). Stage-1..22 leaves are left intact.
Does **not** instantiate children.

## Flow

One always block plus combo ready / retry / emit size.
State: `have` / `hold[639:0]` / `by_lj[1279:0]` / `by_n[7:0]`
/ `pkt_act` / `pkt_left[15:0]` / 16-VL `wptr` / `rptr`
(unused `rbuf` kept as stock).

LPH is `pcs_dll_data[639:480]`. CFG0 (`cfg==0`) terminates
and does not pack. Else occupancy `>= RXBUF` sets `rx_ovf`;
otherwise the 640b beat is held and `wptr[vl] += 4`. When
`have && by_n <= 80`, OR-pack `{hold, 640'b0}` at byte
offset `by_n`. Emit a 512b NW beat when the declared packet
has ≥64B (or a last beat ≤64B) and the NW is ready. After
EOP, drop intra-group leftover (Null pad + BCRC tail) so it
cannot prefix the next SOP. `!link_up` with leftover emits
`{by_lj[1279:800], 1'b0, 1'b1, 30'd0}`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_rx
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`vibe_ub_fn.vh`, `RXBUF=1024`, 640b→4-flit unBCRC pack,
LPH-first, EOP leftover drop, CFG0 terminate, FEC/BCRC
Go-Back-N, and tied `start_ack` stay. Ports / RX match
stock (header-only vs stock). Official `.vlt` is not
expanded.
