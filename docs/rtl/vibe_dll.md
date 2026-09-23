# vibe_dll

DLL structural top (AS-0.1 §12). Decision I stage-35
pyCircuit hierarchy wrap. Re-homes pre-Decision I stock RTL
(first DLL structural top under `pycircuit/dll/`, after the
eight DLL leaves `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx` / `vibe_dll_retry_ack_sm` /
`vibe_dll_retry_buf` / `vibe_dll_retry_req_sm` /
`vibe_dll_tx`) under the pycircuit → rtl flow. Instantiates
already-migrated children: `vibe_dll_sm u_sm`,
`vibe_dll_credit u_crd`, `vibe_dll_retry_buf u_rbuf`,
`vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(...)) u_req`,
`vibe_dll_retry_ack_sm u_ack`, `vibe_dll_tx u_tx`,
`vibe_dll_rx u_rx`. Wrap-local combo:
`proto_err = crd_proto | buf_proto`, `fc_ovf = crd_ovf`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll.py` |
| Product SV | `rtl/dll/vibe_dll.sv` |
| Instantiator | `vibe_port` (later); unit TC (`tc_dll`) |
| SPEC / CR-B | Unchanged. Structural top; clocks/resets exempt |

## Ports (product)

Same as tip `5b071097` / freeze `302ac943`. Reset stays
**async active-low** on the children (`or negedge rst_n`).
This wrap has no sequential of its own.

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low (children) |
| `port_rst` | in | port entity reset (SM / credit / retry / RX) |
| `device_rst` | in | device reset (`u_req`) |
| `link_up` | in | 0: children clear / SM Disabled |
| `fec_fail` | in | RX Go-Back-N |
| `nw_dll_data[511:0]` | in | 64B NW beat to TX |
| `nw_dll_vld` | in | NW beat valid |
| `nw_dll_ready` | out | TX combo accept |
| `dll_nw_data[511:0]` | out | RX unpacked NW beat |
| `dll_nw_vld` | out | RX NW valid |
| `dll_nw_ready` | in | NW accept |
| `dll_pcs_data[639:0]` | out | TX 4-flit PCS beat |
| `dll_pcs_vld` | out | TX PCS valid |
| `dll_pcs_ready` | in | PCS accept |
| `pcs_dll_data[639:0]` | in | RX PCS beat |
| `pcs_dll_vld` | in | RX PCS valid |
| `pcs_dll_ready` | out | RX PCS accept |
| `status_up` | out | SM Normal |
| `disabled` | out | SM Disabled |
| `retrain_req` | out | REQ_SM RETRAIN |
| `retry_error` | out | REQ_SM ERROR |
| `proto_err` | out | `crd_proto \| buf_proto` |
| `fc_ovf` | out | credit `fc_ovf` |
| `rx_ovf` | out | RX overflow |
| `cfg0_hit` | out | CFG0 terminate |
| `cfg0_data[639:0]` | out | CFG0 beat |

Parameter `RETRY_WAIT_CYC` default 12500 (passed to
`u_req`). This is **not** PCS tx / rx tops (later
stages) and **not** `vibe_fabric` top. Stage-1..34
leaves are left intact. Instantiates the seven DLL
children listed above (does **not** instantiate
`vibe_bcrc`; TX inlines CRC30).

## Flow

Structural wrap only. Interconnect nets: SM state,
credit / retry / TX / RX handshakes, replay flit /
pointers, consume / CFG0, start_retry / start_ack.
Ties: `param_ok=1`, `credit_ok=1`, `grain_n=8`,
`credit_ret_n=1`, `send_size=4`, `ack_rel=0`,
`rel_size=0`, `phy_retrain=0`, `wait_done_ack=0`.
`u_req.send_cnt` and `u_ack.send_idle` are open.
`dll_error` is `retry_error || proto_err`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so the stock hierarchy
(instances / nets / ties / wrap assigns) stays. Ports /
instances match stock (header-only vs stock). Official
`.vlt` is not expanded.
