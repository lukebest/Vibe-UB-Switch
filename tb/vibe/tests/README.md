# Named TP-0.3 testcases

Each name is the gate identifier. G1 TCs are unchanged. One TC per remaining
MUST TP where the RTL implements it. Negatives are explicit absent-feature TCs.

## Suite (`make suite`) — 26 TCs

| Test | TP / AS |
|------|---------|
| `tc_rt00_per_flow_rr_fwd` | RT=00 per-flow RR |
| `tc_rt01_per_packet_rr_fwd` | RT=01 per-packet RR |
| `tc_rt10_must_drop` | TP-RT-003 |
| `tc_rt11_must_drop` | TP-RT-004 |
| `tc_rt_shortest_unimpl_count` | G1 counter |
| `tc_rt_shortest_irq_logic` | G1 irq |
| `tc_rt_irq_logic_sticky` | AS §10 sticky |
| `tc_rt_no_rewrite` | G1 no RT rewrite |
| `tc_rt10_not_as_rt00` | G1 not treat-as-00 |
| `tc_rt_counter_32b_sat` | sat 32'hFFFF_FFFF |
| `tc_cfg_identity_guid_class` | AS §10 GUID/class |
| `tc_default_rt_all0_port0` | default → port 0 |
| `tc_pkt_len_err_drop` | oversize drop |
| `tc_cfg6_term_vs_fwd` | CFG6 term vs fwd |
| `tc_saf_full_pkt` | SAF |
| `tc_icrc_transit_no_recompute` | transit no ICRC |
| `tc_cfg3_fwd` / `tc_cfg4_fwd` / `tc_cfg5_fwd` / `tc_cfg7_fwd` / `tc_cfg9_fwd` | CFG forward |
| `tc_cfg_reserved_fwd` | CFG 1,2,8,10,15 forward |
| `tc_cfg0_fabric_no_special` | CFG0 terminate is DLL, not fabric |
| `tc_port_rst_via_cfg` | Port Reset cmd=4'h3 W1C `data[0]==1` (data[0]==0 must not reset) |
| `tc_device_rst_via_cfg` | device reset cmd=4 |
| `tc_pkt_len_legal_16_4300` | legal 20 B / 4300 B (16 B not LPH-representable) |

## Units (`make units`)

PHY/U26, FEC T=4/T=2/bypass + dual enc, AMCTL, eBCH-16, scramble, G1 window,
cw2beat, PMA 512b + 922 MHz, LMSM Idle→Discovery, DLL SM, BCRC, retry 256,
GBN, ACK replay, credit 1024-**cell** BP (G7; filename `tc_credit_1024_flit_bp`
is historical), credit timeout 1 µs, VOQ
deadlock 1 µs (**separate**), AFIFO occ≥10, CFG0 no-credit, VL0–15 RR, ICRC
unit, DLL TX CFG0, mgmt bypass, rst_sync, RS decoder, named negatives
(QDLWS / Exact Route / Port CNA / cut-through / UBFM / hi_FEC_BER / Probe /
Dijkstra). Overlay B: `tc_phy_nw_dll_512b` requires NW `data[511:0]`.

`tc_credit_1024_hole` scores the same 1023→1024 **cell** `bp_nw` as
`tc_credit_1024_flit_bp` (G7 closed as cell).

## NW packet → PMA (`make units`)

| Test | TP / AS |
|------|---------|
| `tc_nw_pkt_to_pma_tx` | TP-PHY-009/010/018: legal NW/LPH on NW `data[511:0]` → score PMA `txdata[511:0]`. **FAIL vs `d6549521`:** DUT NW pin is still 640 (Overlay B not wired). |
| `tc_nw_pkt_pma_loopback` | TP-PHY-012: recover LPH+payload on NW `data[511:0]` after PMA loopback. **FAIL vs `d6549521`:** same 512-vs-640 width. LPH values unchanged if Overlay B lands. |

Select one suite test: `make -C tb/vibe suite TC=tc_rt10_must_drop`
