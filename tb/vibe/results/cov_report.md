# Verilator coverage (vibe_*.sv only)

Honest tool output. FSM = line hits on state `case`/`if` (no VCS FSM engine).

| Module | Line hit/tot | Line % | Toggle hit/tot | Toggle % |
|--------|-------------:|-------:|---------------:|---------:|
| `vibe_afifo.sv` | 11/11 | 100.0 | 70/374 | 18.7 |
| `vibe_bcrc.sv` | 10/10 | 100.0 | 108/229 | 47.2 |
| `vibe_cfg_space.sv` | 12/12 | 100.0 | 183/264 | 69.3 |
| `vibe_cna_ep.sv` | 6/6 | 100.0 | 33/69 | 47.8 |
| `vibe_dll.sv` | 0/0 | 0.0 | 30/437 | 6.9 |
| `vibe_dll_credit.sv` | 16/16 | 100.0 | 112/122 | 91.8 |
| `vibe_dll_retry_ack_sm.sv` | 14/14 | 100.0 | 26/51 | 51.0 |
| `vibe_dll_retry_buf.sv` | 10/10 | 100.0 | 60/420 | 14.3 |
| `vibe_dll_retry_req_sm.sv` | 21/21 | 100.0 | 38/60 | 63.3 |
| `vibe_dll_rx.sv` | 18/18 | 100.0 | 25/536 | 4.7 |
| `vibe_dll_sm.sv` | 14/14 | 100.0 | 13/13 | 100.0 |
| `vibe_dll_tx.sv` | 16/16 | 100.0 | 80/551 | 14.5 |
| `vibe_ebch16.sv` | 33/33 | 100.0 | 21/21 | 100.0 |
| `vibe_fabric.sv` | 27/27 | 100.0 | 150/712 | 21.1 |
| `vibe_fecn_mark.sv` | 0/0 | 0.0 | 20/49 | 40.8 |
| `vibe_gear_128_160.sv` | 12/12 | 100.0 | 58/714 | 8.1 |
| `vibe_gear_160_128.sv` | 12/12 | 100.0 | 45/556 | 8.1 |
| `vibe_icrc.sv` | 12/12 | 100.0 | 68/78 | 87.2 |
| `vibe_irq_agg.sv` | 5/5 | 100.0 | 14/35 | 40.0 |
| `vibe_lmsm.sv` | 64/72 | 88.9 | 63/65 | 96.9 |
| `vibe_mgmt.sv` | 0/0 | 0.0 | 28/187 | 15.0 |
| `vibe_mgmt_byp.sv` | 7/7 | 100.0 | 8/16 | 50.0 |
| `vibe_nw_adapt.sv` | 0/0 | 0.0 | 13/13 | 100.0 |
| `vibe_pcs_rx.sv` | 9/9 | 100.0 | 1309/1960 | 66.8 |
| `vibe_pcs_rx_amctl_lock.sv` | 19/19 | 100.0 | 304/304 | 100.0 |
| `vibe_pcs_rx_deskew.sv` | 12/12 | 100.0 | 1296/1308 | 99.1 |
| `vibe_pcs_rx_fec.sv` | 19/19 | 100.0 | 27/34 | 79.4 |
| `vibe_pcs_rx_unpack.sv` | 12/12 | 100.0 | 650/654 | 99.4 |
| `vibe_pcs_scramble.sv` | 13/13 | 100.0 | 359/511 | 70.3 |
| `vibe_pcs_tx.sv` | 0/0 | 0.0 | 1296/1941 | 66.8 |
| `vibe_pcs_tx_amctl.sv` | 5/5 | 100.0 | 152/152 | 100.0 |
| `vibe_pcs_tx_cw2beat.sv` | 9/9 | 100.0 | 8/8 | 100.0 |
| `vibe_pcs_tx_fec.sv` | 28/28 | 100.0 | 126/191 | 66.0 |
| `vibe_pcs_tx_g1.sv` | 16/16 | 100.0 | 11/12 | 91.7 |
| `vibe_pcs_tx_pack.sv` | 17/17 | 100.0 | 501/678 | 73.9 |
| `vibe_pma_bnd.sv` | 4/4 | 100.0 | 43/1028 | 4.2 |
| `vibe_port.sv` | 6/6 | 100.0 | 44/4201 | 1.0 |
| `vibe_port_sel.sv` | 17/17 | 100.0 | 52/139 | 37.4 |
| `vibe_route_lu.sv` | 10/10 | 100.0 | 27/76 | 35.5 |
| `vibe_rs128_120_dec.sv` | 13/13 | 100.0 | 74/88 | 84.1 |
| `vibe_rs128_120_enc.sv` | 8/8 | 100.0 | 158/159 | 99.4 |
| `vibe_rst_ctl.sv` | 15/15 | 100.0 | 20/32 | 62.5 |
| `vibe_rst_sync.sv` | 3/3 | 100.0 | 4/4 | 100.0 |
| `vibe_saf_ing.sv` | 16/16 | 100.0 | 43/85 | 50.6 |
| `vibe_sync2.sv` | 3/3 | 100.0 | 17/17 | 100.0 |
| `vibe_ub_switch.sv` | 0/0 | 0.0 | 35/292 | 12.0 |
| `vibe_vl_rr.sv` | 8/8 | 100.0 | 36/36 | 100.0 |
| `vibe_voq_egr.sv` | 16/16 | 100.0 | 38/270 | 14.1 |
| `vibe_xbar.sv` | 30/30 | 100.0 | 40/72 | 55.6 |
| **TOTAL implemented vibe_*** | **628/636** | **98.7** | **7936/19824** | **40.0** |

## Uncovered LINE points

- `line /workspace/rtl/lmsm/vibe_lmsm.sv:101 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:102 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:103 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:104 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:105 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:106 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:107 case`
- `line /workspace/rtl/lmsm/vibe_lmsm.sv:108 case`

## Uncovered toggle bins (first 40; not the line gate)

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
- … 11848 more (see annotate/ and cov_raw.txt)

Classification: see `CHECKER_AUDIT.md` / `COVERAGE_HOLES.md`.
Wide-bus toggle miss is unused data-bit patterns (not dead).
Waive only Probe/Dijkstra/QDLWS/Exact Route/UBFM — those are
**not in RTL** (AS-0.1 non-goals). Do not waive missing stimulus.
Suite Verilator bind OOM on VOQ — use per-module clusters.

