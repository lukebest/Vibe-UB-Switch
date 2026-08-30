# Named TP-0.3 testcases

Each name is the gate identifier. Implementation:

| Test | TP / AS | Where it runs |
|------|---------|----------------|
| `tc_rt00_per_flow_rr_fwd` | RT=00 per-flow RR | `make suite` |
| `tc_rt01_per_packet_rr_fwd` | RT=01 per-packet RR | `make suite` |
| `tc_rt10_must_drop` | TP-RT-003 | `make suite` |
| `tc_rt11_must_drop` | TP-RT-004 | `make suite` |
| `tc_rt_shortest_unimpl_count` | G1 counter | `make suite` |
| `tc_rt_shortest_irq_logic` | G1 irq | `make suite` |
| `tc_rt_irq_logic_sticky` | AS §10 sticky | `make suite` |
| `tc_rt_no_rewrite` | G1 no RT rewrite | `make suite` |
| `tc_rt10_not_as_rt00` | G1 not treat-as-00 | `make suite` |
| `tc_rt_counter_32b_sat` | sat 32'hFFFF_FFFF | `make suite` |
| `tc_cfg_identity_guid_class` | AS §10 GUID/class | `make suite` + `units` |
| `tc_default_rt_all0_port0` | default → port 0 | `make suite` |
| `tc_pkt_len_err_drop` | 16..4300 | `make suite` |
| `tc_cfg0_term_not_fabric` | CFG0 terminate | `make units` |
| `tc_cfg6_term_vs_fwd` | CFG6 term vs fwd | `make suite` |
| `tc_icrc_txrx_vs_transit` | ICRC §13 | `make units` + suite transit |
| `tc_vl_rr` | VL RR | `make units` |
| `tc_saf_full_pkt` | SAF | `make suite` |
| `tc_credit_1024_hole` | credit unit HOLE | `make units` |
| `tc_neg_absent_features` | Probe/QDLWS/… | `make units` + `make neg` |
| `tc_top_smoke` | top pins + hier probe | `make top` |

Select one suite test: `make -C tb/vibe suite TC=tc_rt10_must_drop`
