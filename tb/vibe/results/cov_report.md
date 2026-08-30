# Verilator coverage (vibe_*.sv only)

Honest tool output. FSM = line hits on state `case`/`if` (no VCS FSM engine).

| Module | Line hit/tot | Line % | Toggle hit/tot | Toggle % |
|--------|-------------:|-------:|---------------:|---------:|
| `vibe_afifo.sv` | 10/11 | 90.9 | 29/374 | 7.8 |
| `vibe_bcrc.sv` | 19/20 | 95.0 | 161/458 | 35.2 |
| `vibe_cfg_space.sv` | 6/12 | 50.0 | 41/264 | 15.5 |
| `vibe_dll_credit.sv` | 31/64 | 48.4 | 86/420 | 20.5 |
| `vibe_dll_retry_ack_sm.sv` | 8/14 | 57.1 | 10/51 | 19.6 |
| `vibe_dll_retry_buf.sv` | 8/10 | 80.0 | 39/420 | 9.3 |
| `vibe_dll_retry_req_sm.sv` | 8/21 | 38.1 | 12/60 | 20.0 |
| `vibe_dll_rx.sv` | 13/18 | 72.2 | 17/536 | 3.2 |
| `vibe_dll_sm.sv` | 11/16 | 68.8 | 11/13 | 84.6 |
| `vibe_dll_tx.sv` | 9/16 | 56.2 | 39/551 | 7.1 |
| `vibe_ebch16.sv` | 11/66 | 16.7 | 30/42 | 71.4 |
| `vibe_fecn_mark.sv` | 0/0 | 0.0 | 15/49 | 30.6 |
| `vibe_gear_128_160.sv` | 12/12 | 100.0 | 58/714 | 8.1 |
| `vibe_gear_160_128.sv` | 12/12 | 100.0 | 45/556 | 8.1 |
| `vibe_icrc.sv` | 11/12 | 91.7 | 54/78 | 69.2 |
| `vibe_lmsm.sv` | 18/72 | 25.0 | 23/65 | 35.4 |
| `vibe_mgmt_byp.sv` | 6/7 | 85.7 | 6/16 | 37.5 |
| `vibe_nw_adapt.sv` | 0/0 | 0.0 | 13/13 | 100.0 |
| `vibe_pcs_scramble.sv` | 13/13 | 100.0 | 304/511 | 59.5 |
| `vibe_pcs_tx_amctl.sv` | 2/5 | 40.0 | 78/152 | 51.3 |
| `vibe_pcs_tx_cw2beat.sv` | 9/9 | 100.0 | 8/8 | 100.0 |
| `vibe_pcs_tx_fec.sv` | 58/87 | 66.7 | 157/573 | 27.4 |
| `vibe_pcs_tx_g1.sv` | 15/16 | 93.8 | 11/12 | 91.7 |
| `vibe_pma_bnd.sv` | 7/8 | 87.5 | 50/2056 | 2.4 |
| `vibe_port_sel.sv` | 14/17 | 82.4 | 36/139 | 25.9 |
| `vibe_rs128_120_dec.sv` | 13/13 | 100.0 | 14/88 | 15.9 |
| `vibe_rs128_120_enc.sv` | 19/24 | 79.2 | 180/477 | 37.7 |
| `vibe_rst_ctl.sv` | 13/15 | 86.7 | 14/32 | 43.8 |
| `vibe_rst_sync.sv` | 3/3 | 100.0 | 4/4 | 100.0 |
| `vibe_sync2.sv` | 3/3 | 100.0 | 13/17 | 76.5 |
| `vibe_vl_rr.sv` | 7/8 | 87.5 | 36/36 | 100.0 |
| `vibe_voq_egr.sv` | 15/16 | 93.8 | 15/270 | 5.6 |
| `vibe_xbar.sv` | 24/30 | 80.0 | 18/72 | 25.0 |
| **TOTAL implemented vibe_*** | **408/650** | **62.8** | **1627/9127** | **17.8** |

## RTL files with no coverage records

- `vibe_cna_ep.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_dll.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_fabric.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_irq_agg.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_mgmt.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_rx.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_rx_amctl_lock.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_rx_deskew.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_rx_fec.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_rx_unpack.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_tx.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_pcs_tx_pack.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_port.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_route_lu.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_saf_ing.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_ub_switch.sv` — no stimulus in Verilator clusters (or not elaborated)

## Uncovered bins (first 80)

- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[100]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[101]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[102]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[103]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[104]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[105]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[106]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[107]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[108]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[109]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[10]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[110]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[111]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[112]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[113]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[114]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[115]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[116]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[117]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[118]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[119]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[11]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[120]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[121]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[122]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[123]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[124]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[125]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[126]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[127]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[128]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[129]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[12]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[130]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[131]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[132]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[133]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[134]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[135]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[136]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[137]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[138]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[139]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[13]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[140]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[141]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[142]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[143]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[144]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[145]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[146]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[147]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[148]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[149]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[14]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[150]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[151]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[152]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[153]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[154]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[155]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[156]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[157]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[158]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[159]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[15]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[16]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[17]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[18]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[19]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[20]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[21]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[22]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[23]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[24]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[25]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[26]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[27]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[28]`
- `toggle /workspace/rtl/cdc/vibe_afifo.sv:10 wdata[29]`
- … 7662 more (see annotate/ and cov_raw.txt)

## Classification (honest; gate 100% of implemented `vibe_*` **not** met)

**Tool:** Verilator 5.020 `--coverage-line --coverage-toggle`. Custom C++ main
writes `coverage.dat` (fixes prior `--binary`+$finish gap). `-Wno-BLKLOOPINIT`
on `vibe_route_lu` (RTL freeze). **No FSM engine** — FSM = line hits on state
`case`/`if`.

**Collected:** 36 unit clusters (including `vibe_xbar`). Full `vibe_suite`
Verilator bind **did not finish** (g++/cc1plus ~7 GB RSS on VOQ age loops).
Those modules still ran under Icarus.

| Class | What |
|-------|------|
| **100% line (this run)** | gear_160_128, gear_128_160, pcs_scramble, pcs_tx_cw2beat, rs128_120_dec, rst_sync, sync2 |
| **Combo-only (0 line points)** | `vibe_fecn_mark`, `vibe_nw_adapt` — toggle is the metric (`nw_adapt` toggle 100%) |
| **Wide-bus toggle miss** | PMA 512b, AFIFO/gear/DLL 160b+ datapaths — unused data-bit patterns, **not dead code** |
| **Missing Verilator stimulus** | fabric/top/SAF/route_lu/cna_ep/irq/mgmt, full PCS RX/TX wrappers, `vibe_dll`/`vibe_port` — suite cluster OOM |
| **Timer / unused SM** | LMSM post-Discovery (ms timers), retry WAIT/RETRAIN/ERROR, credit ovf/port_rst — **missing stimulus** |
| **Dead / non-goal** | Probe, Dijkstra, QDLWS, Exact Route, cut-through, UBFM, hi_FEC_BER — **not in RTL** |

Do not treat 62.8% / 17.8% as 100%. Numbers are tool output.

