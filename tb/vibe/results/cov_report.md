# Verilator coverage (vibe_*.sv only)

Honest tool output. FSM = line hits on state `case`/`if` (no VCS FSM engine).

| Module | Line hit/tot | Line % | Toggle hit/tot | Toggle % |
|--------|-------------:|-------:|---------------:|---------:|
| `vibe_afifo.sv` | 11/11 | 100.0 | 70/374 | 18.7 |
| `vibe_bcrc.sv` | 10/10 | 100.0 | 102/229 | 44.5 |
| `vibe_cfg_space.sv` | 12/12 | 100.0 | 64/264 | 24.2 |
| `vibe_cna_ep.sv` | 6/6 | 100.0 | 44/229 | 19.2 |
| `vibe_dll.sv` | 0/0 | 0.0 | 20/437 | 4.6 |
| `vibe_dll_credit.sv` | 16/16 | 100.0 | 137/155 | 88.4 |
| `vibe_dll_retry_ack_sm.sv` | 14/14 | 100.0 | 26/51 | 51.0 |
| `vibe_dll_retry_buf.sv` | 10/10 | 100.0 | 48/420 | 11.4 |
| `vibe_dll_retry_req_sm.sv` | 21/21 | 100.0 | 38/60 | 63.3 |
| `vibe_dll_rx.sv` | 22/22 | 100.0 | 45/604 | 7.5 |
| `vibe_dll_sm.sv` | 14/14 | 100.0 | 13/13 | 100.0 |
| `vibe_dll_tx.sv` | 46/51 | 90.2 | 523/1873 | 27.9 |
| `vibe_ebch16.sv` | 33/33 | 100.0 | 21/21 | 100.0 |
| `vibe_fabric.sv` | 48/48 | 100.0 | 161/732 | 22.0 |
| `vibe_fecn_mark.sv` | 0/0 | 0.0 | 21/49 | 42.9 |
| `vibe_gear_128_160.sv` | 12/12 | 100.0 | 58/714 | 8.1 |
| `vibe_gear_160_128.sv` | 12/12 | 100.0 | 45/556 | 8.1 |
| `vibe_icrc.sv` | 12/12 | 100.0 | 68/78 | 87.2 |
| `vibe_irq_agg.sv` | 5/5 | 100.0 | 14/35 | 40.0 |
| `vibe_lmsm.sv` | 64/72 | 88.9 | 62/65 | 95.4 |
| `vibe_mgmt.sv` | 0/0 | 0.0 | 27/187 | 14.4 |
| `vibe_mgmt_byp.sv` | 7/7 | 100.0 | 8/16 | 50.0 |
| `vibe_nw_adapt.sv` | 0/0 | 0.0 | 13/13 | 100.0 |
| `vibe_pcs_rx.sv` | 35/42 | 83.3 | 1818/1985 | 91.6 |
| `vibe_pcs_rx_amctl_lock.sv` | 18/22 | 81.8 | 416/472 | 88.1 |
| `vibe_pcs_rx_deskew.sv` | 12/12 | 100.0 | 1162/1312 | 88.6 |
| `vibe_pcs_rx_fec.sv` | 18/18 | 100.0 | 74/77 | 96.1 |
| `vibe_pcs_rx_unpack.sv` | 16/16 | 100.0 | 582/660 | 88.2 |
| `vibe_pcs_scramble.sv` | 13/13 | 100.0 | 511/511 | 100.0 |
| `vibe_pcs_tx.sv` | 0/0 | 0.0 | 1881/1941 | 96.9 |
| `vibe_pcs_tx_amctl.sv` | 5/5 | 100.0 | 152/152 | 100.0 |
| `vibe_pcs_tx_cw2beat.sv` | 9/9 | 100.0 | 8/8 | 100.0 |
| `vibe_pcs_tx_fec.sv` | 24/24 | 100.0 | 173/175 | 98.9 |
| `vibe_pcs_tx_g1.sv` | 16/17 | 94.1 | 11/12 | 91.7 |
| `vibe_pcs_tx_pack.sv` | 17/17 | 100.0 | 619/680 | 91.0 |
| `vibe_pma_bnd.sv` | 5/5 | 100.0 | 43/1028 | 4.2 |
| `vibe_port_sel.sv` | 17/17 | 100.0 | 49/139 | 35.3 |
| `vibe_route_lu.sv` | 10/10 | 100.0 | 25/76 | 32.9 |
| `vibe_rs128_120_dec.sv` | 13/13 | 100.0 | 14/152 | 9.2 |
| `vibe_rs128_120_enc.sv` | 8/8 | 100.0 | 158/159 | 99.4 |
| `vibe_rst_ctl.sv` | 15/15 | 100.0 | 20/32 | 62.5 |
| `vibe_rst_sync.sv` | 3/3 | 100.0 | 4/4 | 100.0 |
| `vibe_saf_ing.sv` | 16/16 | 100.0 | 42/85 | 49.4 |
| `vibe_sync2.sv` | 3/3 | 100.0 | 17/17 | 100.0 |
| `vibe_vl_rr.sv` | 8/8 | 100.0 | 36/36 | 100.0 |
| `vibe_voq_egr.sv` | 16/16 | 100.0 | 39/270 | 14.4 |
| `vibe_xbar.sv` | 30/30 | 100.0 | 46/72 | 63.9 |
| **TOTAL implemented vibe_*** | **702/727** | **96.6** | **9528/17230** | **55.3** |

## RTL files with no coverage records

- `vibe_port.sv` — no stimulus in Verilator clusters (or not elaborated)
- `vibe_ub_switch.sv` — no stimulus in Verilator clusters (or not elaborated)

## Uncovered LINE points

- `line /workspace/tb/vibe/cov/out/rtl_nodedef/dll/vibe_dll_tx.sv:144 else`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/dll/vibe_dll_tx.sv:151 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/dll/vibe_dll_tx.sv:155 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/dll/vibe_dll_tx.sv:159 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/dll/vibe_dll_tx.sv:98 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:101 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:102 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:103 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:104 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:105 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:106 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:107 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/lmsm/vibe_lmsm.sv:108 case`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:181 elsif`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:182 else`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:182 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:194 else`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:198 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:207 else`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx.sv:211 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx_amctl_lock.sv:55 elsif`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx_amctl_lock.sv:56 elsif`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx_amctl_lock.sv:57 elsif`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_rx_amctl_lock.sv:58 if`
- `line /workspace/tb/vibe/cov/out/rtl_nodedef/pcs/vibe_pcs_tx_g1.sv:51 else`

## Uncovered toggle bins (first 40; not the line gate)

- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[100]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[101]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[102]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[103]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[104]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[105]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[106]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[107]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[108]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[109]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[110]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[111]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[112]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[113]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[114]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[115]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[116]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[117]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[118]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[119]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[120]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[121]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[122]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[123]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[124]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[125]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[126]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[127]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[128]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[129]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[130]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[131]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[132]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[133]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[134]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[135]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[136]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[137]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[138]`
- `toggle /workspace/tb/vibe/cov/out/rtl_nodedef/cdc/vibe_afifo.sv:10 wdata[139]`
- … 7662 more (see annotate/ and cov_raw.txt)

Classification: see `CHECKER_AUDIT.md` / `COVERAGE_HOLES.md`.
Wide-bus toggle miss is unused data-bit patterns (not dead).
Waive only Probe/Dijkstra/QDLWS/Exact Route/UBFM — those are
**not in RTL** (AS-0.1 non-goals). Do not waive missing stimulus.
Suite Verilator bind OOM on VOQ — use per-module clusters.

