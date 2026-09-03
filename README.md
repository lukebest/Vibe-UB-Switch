# Vibe-UB-Switch

4-port independent Unified Bus (UB) 2.0 switch RTL for ASIC, Entity 0, Ports 0–3.

**This branch supersedes the prior `rtl/` and `tb/` trees.** Those sources are void: do not use their signal names, queue depths, SCNA-compare routing, 640-bit-as-flit, README depth 8, or CDC ready formulas. Verification owns testbenches; this revision does not add testcases.

Architecture: [`docs/Vibe-UB-Switch-architecture-spec.md`](docs/Vibe-UB-Switch-architecture-spec.md) (AS-0.1).  
Function behavior for this rev: **FS-0.2.3** + AS-0.1 (function-spec true source is not in this repo and is not modified here).  
Public protocol reference: https://www.unifiedbus.com (UB 2.0).

## Locked subset

- Fabric store-and-forward. Flit = 20 bytes (never 640-bit).
- Routing: `CFG0_ROUTE_TABLE` dest → 4-bit egress bitmap. Default all-0 → port 0.
- **G1 (mandatory, FS-0.2.3 + AS-0.1):** RT=10 and RT=11 **DROP** the packet. `rt_shortest_unimpl` is a **32-bit saturating** counter (does not wrap). The drop also sets sticky `irq_logic`. No extra IRQ pins. No Dijkstra, no treat-as-RT=00, no RT rewrite.
- RT=00 per-flow sticky RR; RT=01 per-packet RR. Flow key `{CFG, src, dest, VL}`.
- U26 width chain + G1/G2 gearbox. Per-lane gray-pointer AFIFO CDC 1.25 GHz ↔ 922 MHz.
- LMSM (this-rev subset), DLL SM, `RETRY_REQ_SM`, `RETRY_ACK_SM`, AMCTL lock per lane.
- Product PMA: `txdata[511:0]`, `txclk`, `rxdata[511:0]`, `rxclk`. No extra handshake, no PMA ready.

## Clocks and pins

| Signal | Role |
|--------|------|
| `clk_fab` | 1.25 GHz fabric / DLL / PCS digital / LMSM / mgmt |
| `txclk_*` / `rxclk_*` | per-port independent 922 MHz |
| `txdata_*` / `rxdata_*` | 512-bit PMA; `[127:0]`=lane0 … `[511:384]`=lane3 |
| `cfg_wr_*` | static write (`vld`/`ready`, `cmd`/`idx`/`data`) |
| `irq_logic` | sticky active-high OR of observable errors |
| `rst_n` | logical reset |

`cfg_wr_cmd` (4 bits): 0=CNA, 1=route entry, 2=Default bitmap, 3=Port Reset (RW1C per port), 4=device reset, 5=pulse `lmsm_go`; others ignore.

## Module tree (landed)

```
vibe_ub_switch
├── port[3:0]
│   ├── pma_bnd
│   ├── afifo_tx[3:0], afifo_rx[3:0]
│   ├── pcs_tx (g1, fec dual RS(128,120)+interleave, scramble, amctl insert, pack G2)
│   ├── pcs_rx (amctl_lock x4, unpack, descramble, fec decode, deskew)
│   ├── lmsm
│   ├── dll (dll_sm, dll_tx, dll_rx, dll_credit, retry_buf, retry_req_sm, retry_ack_sm)
│   └── nw_adapt
├── fabric (saf_ing[3:0], route_lu, port_sel, xbar, voq_egr[3:0] x16 VL, vl_rr[3:0], fecn_mark[3:0])
└── mgmt (cfg_space, cna_ep, irq_agg, rst_ctl)
```

No UBFM, no CAQM, no NPI filter datapath, no Transport/Transaction/Function endpoint, no analog PMA (Gray/precoding/SerDes).

## Landed RTL files

| Path | Module |
|------|--------|
| `rtl/top/vibe_ub_switch.sv` | `vibe_ub_switch` |
| `rtl/port/vibe_port.sv` | `vibe_port` |
| `rtl/pma/vibe_pma_bnd.sv` | `vibe_pma_bnd` |
| `rtl/cdc/vibe_sync2.sv` | `vibe_sync2` |
| `rtl/cdc/vibe_afifo.sv` | `vibe_afifo` |
| `rtl/cdc/vibe_rst_sync.sv` | `vibe_rst_sync` |
| `rtl/cdc/vibe_gear_160_128.sv` | `vibe_gear_160_128` |
| `rtl/cdc/vibe_gear_128_160.sv` | `vibe_gear_128_160` |
| `rtl/pcs/vibe_ebch16.sv` | `vibe_ebch16` |
| `rtl/pcs/vibe_rs128_120_enc.sv` | `vibe_rs128_120_enc` |
| `rtl/pcs/vibe_rs128_120_dec.sv` | `vibe_rs128_120_dec` |
| `rtl/pcs/vibe_pcs_scramble.sv` | `vibe_pcs_scramble` |
| `rtl/pcs/vibe_pcs_tx_g1.sv` | `vibe_pcs_tx_g1` |
| `rtl/pcs/vibe_pcs_tx_fec.sv` | `vibe_pcs_tx_fec` |
| `rtl/pcs/vibe_pcs_tx_cw2beat.sv` | `vibe_pcs_tx_cw2beat` |
| `rtl/pcs/vibe_pcs_tx_amctl.sv` | `vibe_pcs_tx_amctl` |
| `rtl/pcs/vibe_pcs_tx_pack.sv` | `vibe_pcs_tx_pack` |
| `rtl/pcs/vibe_pcs_tx.sv` | `vibe_pcs_tx` |
| `rtl/pcs/vibe_pcs_rx_amctl_lock.sv` | `vibe_pcs_rx_amctl_lock` |
| `rtl/pcs/vibe_pcs_rx_unpack.sv` | `vibe_pcs_rx_unpack` |
| `rtl/pcs/vibe_pcs_rx_deskew.sv` | `vibe_pcs_rx_deskew` |
| `rtl/pcs/vibe_pcs_rx_fec.sv` | `vibe_pcs_rx_fec` |
| `rtl/pcs/vibe_pcs_rx.sv` | `vibe_pcs_rx` |
| `rtl/lmsm/vibe_lmsm.sv` | `vibe_lmsm` |
| `rtl/dll/vibe_bcrc.sv` | `vibe_bcrc` |
| `rtl/dll/vibe_dll_sm.sv` | `vibe_dll_sm` |
| `rtl/dll/vibe_dll_credit.sv` | `vibe_dll_credit` |
| `rtl/dll/vibe_dll_retry_buf.sv` | `vibe_dll_retry_buf` |
| `rtl/dll/vibe_dll_retry_req_sm.sv` | `vibe_dll_retry_req_sm` |
| `rtl/dll/vibe_dll_retry_ack_sm.sv` | `vibe_dll_retry_ack_sm` |
| `rtl/dll/vibe_dll_tx.sv` | `vibe_dll_tx` |
| `rtl/dll/vibe_dll_rx.sv` | `vibe_dll_rx` |
| `rtl/dll/vibe_dll.sv` | `vibe_dll` |
| `rtl/nw/vibe_nw_adapt.sv` | `vibe_nw_adapt` |
| `rtl/nw/vibe_icrc.sv` | `vibe_icrc` |
| `rtl/fabric/vibe_saf_ing.sv` | `vibe_saf_ing` |
| `rtl/fabric/vibe_route_lu.sv` | `vibe_route_lu` |
| `rtl/fabric/vibe_port_sel.sv` | `vibe_port_sel` |
| `rtl/fabric/vibe_xbar.sv` | `vibe_xbar` |
| `rtl/fabric/vibe_voq_egr.sv` | `vibe_voq_egr` |
| `rtl/fabric/vibe_vl_rr.sv` | `vibe_vl_rr` |
| `rtl/fabric/vibe_fecn_mark.sv` | `vibe_fecn_mark` |
| `rtl/fabric/vibe_fabric.sv` | `vibe_fabric` |
| `rtl/mgmt/vibe_cfg_space.sv` | `vibe_cfg_space` |
| `rtl/mgmt/vibe_cna_ep.sv` | `vibe_cna_ep` |
| `rtl/mgmt/vibe_irq_agg.sv` | `vibe_irq_agg` |
| `rtl/mgmt/vibe_rst_ctl.sv` | `vibe_rst_ctl` |
| `rtl/mgmt/vibe_mgmt_byp.sv` | `vibe_mgmt_byp` |
| `rtl/mgmt/vibe_mgmt.sv` | `vibe_mgmt` |
| `rtl/common/vibe_ub_params.vh` | parameters (FS-must vs architecture-chosen) |
| `rtl/common/vibe_ub_fn.vh` | header extract / gray / GF(256) helpers |

## Parameters

**FS-must:** retry_buf 256; credit threshold 1024; credit/deadlock timeout 1 µs; `NUM_RETRY` 15; `NUM_PHY_REINIT` 4.

**Architecture-chosen (parameters, not product Max Index):** AFIFO 16; `dll_rxbuf` 1024 flit/VL; `saf_ing` 128×640b; VOQ 32 flit/VL/egress; mgmt bypass 16×640b; `FECN_WM=24`; `AMCTL_CONFIRM_N=UNLOCK_N=3`; `ROUTE_TABLE_DEPTH` default 256.

## Compile (syntax check)

```bash
iverilog -g2012 -I rtl/common -o /tmp/vibe_ub_switch.vvp \
  rtl/common/*.vh rtl/cdc/*.sv rtl/pma/*.sv rtl/pcs/*.sv rtl/lmsm/*.sv \
  rtl/dll/*.sv rtl/nw/*.sv rtl/fabric/*.sv rtl/mgmt/*.sv rtl/port/*.sv \
  rtl/top/vibe_ub_switch.sv
```

Prior `tb/` (`ub_*`) remains in-tree but does not target this RTL and is not a source of behavior. Do not run it as the gate.

## Verification (new `tb/vibe`)

G1 and TP-0.3 tests live under `tb/vibe/`. They do **not** modify `rtl/`.
`rt_shortest_unimpl` is probed hierarchically (`u_fab.rt_shortest_unimpl`); it is not a top port.

```bash
make -C tb/vibe sim              # suite + units + top + absent-feature scan
make -C tb/vibe suite            # fabric + port_sel G1/routing
make -C tb/vibe suite TC=tc_rt10_must_drop
scripts/sim/run_vibe.sh sim
```

See `tb/vibe/README.md`. Icarus Verilog 12 (`iverilog`/`vvp`) is the functional simulator.

## Implementation flow (Sky130 bring-up)

Yosys / ORFS (`sky130hd`) / OpenSTA **scaffold** lives under
`scripts/synth/` (sibling of `scripts/sim/`). This is methodology
bring-up, not a production-node signoff: Sky130 cannot close the FS
1.25 GHz fabric clock, and current RTL is not frozen. The flow does
not edit `rtl/`. See [`scripts/synth/README.md`](scripts/synth/README.md).

```bash
make -C scripts/synth help
make -C scripts/synth synth-smoke    # leaf vibe_sync2, when Yosys is installed
```
