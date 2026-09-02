# TP-0.3 ↔ testcase matrix (official IDs only)

Source: [`TP-0.3.md`](TP-0.3.md) — 159 official IDs.
Planned names in column 2 of that table may not exist as files;
this matrix points at the TC that **scores that rule**.

Verdict: **MAPPED** existing TC scores this official rule;
**ADDED** new TC this pass; **HOLE** unknown not invented;
**NEG** absent-feature / scan.

SHELL→REAL (same 159 IDs): `tc_port_smoke` scores PMA lane-pack + RX LPH
(TP-PHY-001). `tc_pcs_tx` / `tc_pcs_rx` score `lane_vld` / `dll_vld` vs golden.
`tc_fabric_line_holes` scores CFG6 hit + TP-RT-013 sat (not a hole punch).
`tc_neg_official` greps `rtl/vibe_*.sv` (one PASS per official NEG after clean).
`tc_credit_1024_hole` is a thin 1023→1024 `bp_nw` wrapper (G7 closed;
TP-HOLE-G7 / TP-CRD-004 stay on `tc_credit_1024_flit_bp`).
`tc_top_smoke` drives a real RT=10 packet on `rxdata_0` and scores `irq_logic`.
`tc_tp_holes` remains HOLE documentation — do not invent Max Index / pins.

Counts: MAPPED=106 ADDED=16 HOLE=9 NEG=28 (sum=159)

| TP | rule (short) | TC name | file | verdict |
|----|--------------|---------|------|---------|
| TP-ID-001 | 软件可识别为独立 UB Switch（GUID Type / Class Code） | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-002 | 本实例仅 Entity 0，Port 0..3，N_PORTS=4 | `tc_id_nports_entity0` | `tb/vibe/tests/tc_id_nports_entity0.sv` | ADDED |
| TP-ID-003 | 必须实现 CFG0_PORT_BASIC / PORT_CAP / ROUTE_TABLE | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-ID-004 | 无 UBFM 实例 | `tc_neg_ubfm` | `tb/vibe/tests/tc_neg_ubfm.sv` | NEG |
| TP-ID-005 | 协议只跟 UB Base 2.0 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-ID-006 | 附录 D 超出已点名子集暂不实现 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-PHY-001 | 每端口全双工 TX+RX | `tc_port_smoke` | `tb/vibe/tests/tc_port_smoke.sv` | MAPPED |
| TP-PHY-002 | 每端口固定 x4 对称 | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-PHY-003 | 仅 Mode-2 PAM4 106.25G | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-PHY-004 | TX 侧全部车道同频 | `tc_pma_922mhz` | `tb/vibe/tests/tc_pma_922mhz.sv` | MAPPED |
| TP-PHY-005 | 光通路不实现 | `tc_neg_no_optical` | `tb/vibe/tests/tc_neg_no_optical.sv` | NEG |
| TP-PHY-006 | Flit 20 字节，不得把 640b 当 flit | `tc_pkt_len_legal_16_4300` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-PHY-007 | txdata/rxdata[511:0] @922MHz 无额外握手 | `tc_pma_512b_slice` | `tb/vibe/tests/tc_pma_512b_slice.sv` | MAPPED |
| TP-PHY-008 | NW↔DLL 640b @1.25GHz | `tc_nw_adapt_linkready` | `tb/vibe/tests/tc_nw_adapt_linkready.sv` | MAPPED |
| TP-PHY-009 | FEC 1024b = 两拍 512 | `tc_pcs_cw2beat` | `tb/vibe/tests/tc_pcs_cw2beat.sv` | MAPPED |
| TP-PHY-010 | 4×160 AFIFO → 4×128=512 | `tc_phy_u26_chain` | `tb/vibe/tests/tc_phy_u26_chain.sv` | MAPPED |
| TP-PHY-011 | TX 可逐级向 NW 反压 | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-PHY-012 | RX 为 TX 逆过程 | `tc_nw_pkt_pma_loopback` | `tb/vibe/tests/tc_nw_pkt_pma_loopback.sv` | MAPPED |
| TP-PHY-013 | FEC T=4/T=2/bypass 双编码交织 | `tc_pcs_fec_dual_enc` | `tb/vibe/tests/tc_pcs_fec_dual_enc.sv` | MAPPED |
| TP-PHY-014 | 不实现 hi_FEC_BER | `tc_neg_hi_fec_ber` | `tb/vibe/tests/tc_neg_hi_fec_ber.sv` | NEG |
| TP-PHY-015 | >T 失败→DLL 重传，失败→Retrain | `tc_fec_fail_gbn` | `tb/vibe/tests/tc_fec_fail_gbn.sv` | ADDED |
| TP-PHY-016 | AMCTL eBCH-16 54640/32 LTB | `tc_pcs_amctl` | `tb/vibe/tests/tc_pcs_amctl.sv` | MAPPED |
| TP-PHY-017 | AMCTL/EEIB 不扰，LTB 扰，种子 LID | `tc_pcs_scramble` | `tb/vibe/tests/tc_pcs_scramble.sv` | MAPPED |
| TP-PHY-018 | lane0=[127:0]..lane3=[511:384] | `tc_nw_pkt_to_pma_tx` | `tb/vibe/tests/tc_nw_pkt_to_pma_tx.sv` | MAPPED |
| TP-PHY-019 | 只 BCRC | `tc_bcrc_crc30` | `tb/vibe/tests/tc_bcrc_crc30.sv` | MAPPED |
| TP-PHY-020 | 训练完前不得向 DLL 业务 flit | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-001 | reset / port_rst → Link_Idle | `tc_lmsm_idle_discovery` | `tb/vibe/tests/tc_lmsm_idle_discovery.sv` | MAPPED |
| TP-LMSM-002 | lmsm_go：Idle → Discovery | `tc_lmsm_idle_discovery` | `tb/vibe/tests/tc_lmsm_idle_discovery.sv` | MAPPED |
| TP-LMSM-003 | Discovery 锁定 x4 / 106.25G | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-004 | LMSM 定时器（10µs/2ms/24ms/48ms…） | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-005 | Config.Active / Check / Confirm | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-006 | Send_NullBlock → Link_Active | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-007 | Link_Active：LinkUp + LinkReady | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-008 | Retrain 不改速率 | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-009 | EQ.*（若 Config 协商 EQ） | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-010 | lane0 fail → Retrain，不降宽 | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-LMSM-011 | 未实现 Fig 3-28 / Probe / RXEQ / Change_Speed 弧 | `tc_neg_absent_features` | `tb/vibe/tests/tc_neg_absent_features.sv` | NEG |
| TP-LMSM-012 | AMCTL lock 参与 LMSM | `tc_lmsm_vlock` | `tb/vibe/tests/tc_lmsm_vlock.sv` | MAPPED |
| TP-LMSM-013 | 不车道对调 / 极性训练 | `tc_neg_absent_features` | `tb/vibe/tests/tc_neg_absent_features.sv` | NEG |
| TP-LMSM-014 | Send_NullBlock 8 个 DLTB 后 Active | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-DLL-001 | Disabled / Param_Init / Credit_Init / Normal | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-002 | LinkUp==0 → 永远 Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-003 | entity rst 不得单独强制 Disabled | `tc_dll_sm_states` | `tb/vibe/tests/tc_dll_sm_states.sv` | MAPPED |
| TP-DLL-004 | DLLDP >32 flit 拆 ≤16×≤32 | `tc_dll` | `tb/vibe/tests/tc_dll.sv` | MAPPED |
| TP-DLL-005 | BCRC CRC30 + ERROR_FLAG 字段 | `tc_bcrc_crc30` | `tb/vibe/tests/tc_bcrc_crc30.sv` | MAPPED |
| TP-DLL-006 | CFG0 DLLCB 不耗 data credit | `tc_cfg0_no_credit` | `tb/vibe/tests/tc_cfg0_no_credit.sv` | MAPPED |
| TP-DLL-007 | 同 VL FCFS | `tc_vl_rr` | `tb/vibe/tests/tc_vl_rr.sv` | MAPPED |
| TP-DLL-008 | 协商失败用官方默认；VL1–15 硬件仍可用 | `tc_vl_rr_0_15` | `tb/vibe/tests/tc_vl_rr_0_15.sv` | MAPPED |
| TP-CRD-001 | consume ceil(flits/n)，n 默认 8 | `tc_credit_grain_n` | `tb/vibe/tests/tc_credit_grain_n.sv` | ADDED |
| TP-CRD-002 | max 65535 cells，再加 → fc_ovf | `tc_credit_grain_n` | `tb/vibe/tests/tc_credit_grain_n.sv` | ADDED |
| TP-CRD-003 | 无 DLLDP 但 pending → Crd_Ack | `tc_credit_1024_flit_bp` | `tb/vibe/tests/tc_credit_1024_flit_bp.sv` | MAPPED |
| TP-CRD-004 | pending≥1024 flit → 反压 NW + Crd_Ack | `tc_credit_1024_flit_bp` | `tb/vibe/tests/tc_credit_1024_flit_bp.sv` | MAPPED |
| TP-CRD-005 | credit return 超时 1µs → proto_err | `tc_credit_timeout_1us` | `tb/vibe/tests/tc_credit_timeout_1us.sv` | MAPPED |
| TP-CRD-006 | RX buf overflow → irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-CRD-007 | FC overflow → irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-CRD-008 | 不发明 credit underflow 错误码 | `tc_credit_no_underflow` | `tb/vibe/tests/tc_credit_no_underflow.sv` | ADDED |
| TP-RTY-001 | FEC/BCRC fail → Go-Back-N | `tc_retry_req_gbn` | `tb/vibe/tests/tc_retry_req_gbn.sv` | MAPPED |
| TP-RTY-002 | retry_buf 深度 256 | `tc_retry_buf_256` | `tb/vibe/tests/tc_retry_buf_256.sv` | MAPPED |
| TP-RTY-003 | 不得为 512-flit DP 扩 retry_buf | `tc_retry_buf_256` | `tb/vibe/tests/tc_retry_buf_256.sv` | MAPPED |
| TP-RTY-004 | RETRY_REQ_SM | `tc_retry_req_gbn` | `tb/vibe/tests/tc_retry_req_gbn.sv` | MAPPED |
| TP-RTY-005 | NUM_RETRY=15 / NUM_PHY_REINIT=4 | `tc_retry_wait_retrain` | `tb/vibe/tests/tc_retry_wait_retrain.sv` | MAPPED |
| TP-RTY-006 | WAIT 超时合法范围（参数 1µs–10s） | `tc_retry_wait_retrain` | `tb/vibe/tests/tc_retry_wait_retrain.sv` | MAPPED |
| TP-RTY-007 | RETRY_ACK_SM 回放 | `tc_retry_ack_replay` | `tb/vibe/tests/tc_retry_ack_replay.sv` | MAPPED |
| TP-RTY-008 | RETRAIN / ERROR 分类 | `tc_retry_wait_retrain` | `tb/vibe/tests/tc_retry_wait_retrain.sv` | MAPPED |
| TP-RTY-009 | NumFreeBuf 溢出 → DL Protocol Error | `tc_retry_buf_256` | `tb/vibe/tests/tc_retry_buf_256.sv` | MAPPED |
| TP-RTY-010 | ERROR 等 Port/device reset | `tc_retry_req_gbn` | `tb/vibe/tests/tc_retry_req_gbn.sv` | MAPPED |
| TP-RTY-011 | LinkUp=0 未完成 DP pad0+ERROR_FLAG | `tc_dll_rx_errflag` | `tb/vibe/tests/tc_dll_rx_errflag.sv` | MAPPED |
| TP-RT-001 | RT=00 per-flow sticky RR | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-002 | RT=01 per-packet RR | `tc_rt01_per_packet_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-003 | RT=10 DROP | `tc_rt10_must_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-004 | RT=11 DROP | `tc_rt11_must_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-005 | rt_shortest_unimpl +1 | `tc_rt_shortest_unimpl_count` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-006 | G1 置 irq_logic | `tc_rt_shortest_irq_logic` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-007 | irq_logic sticky | `tc_rt_irq_logic_sticky` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-008 | 不得改写 RT | `tc_rt_no_rewrite` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-009 | RT=10 不得当 RT=00 | `tc_rt10_not_as_rt00` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-010 | RT=11 不得当 RT=01 | `tc_rt11_not_as_rt01` | `tb/vibe/tests/tc_rt_g1_official.sv` | ADDED |
| TP-RT-011 | 不得 Dijkstra / shortest-path | `tc_neg_dijkstra` | `tb/vibe/tests/tc_neg_dijkstra.sv` | NEG |
| TP-RT-012 | G1 在 route_lu/port_sel 检测 | `tc_rt_g1_official` | `tb/vibe/tests/tc_rt_g1_official.sv` | ADDED |
| TP-RT-013 | 计数器 32b 饱和 | `tc_rt_counter_32b_sat` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RT-014 | 即使唯一 bitmap 也 DROP | `tc_rt_g1_official` | `tb/vibe/tests/tc_rt_g1_official.sv` | ADDED |
| TP-RT-015 | 走 default 仍 DROP | `tc_rt_g1_official` | `tb/vibe/tests/tc_rt_g1_official.sv` | ADDED |
| TP-RT-016 | G1 drop 不是 DL Protocol Error | `tc_rt_g1_official` | `tb/vibe/tests/tc_rt_g1_official.sv` | ADDED |
| TP-RT-017 | 所有 ingress 端口都检测 G1 | `tc_rt_shortest_unimpl_count` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-NW-001 | 路由表项仅 [3:0] nibble | `tc_route_lu` | `tb/vibe/tests/tc_route_lu.sv` | MAPPED |
| TP-NW-002 | default 全 0 → port 0 | `tc_default_rt_all0_port0` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-NW-003 | bitmap AND Status_Up；port0 Down → drop+count | `tc_p0_down_drop` | `tb/vibe/tests/tc_p0_down_drop.sv` | ADDED |
| TP-NW-004 | 无 Exact Route | `tc_neg_exact_route` | `tb/vibe/tests/tc_neg_exact_route.sv` | NEG |
| TP-NW-005 | 无 Port CNA | `tc_neg_port_cna` | `tb/vibe/tests/tc_neg_port_cna.sv` | NEG |
| TP-NW-006 | 无 flood/broadcast | `tc_p0_down_drop` | `tb/vibe/tests/tc_p0_down_drop.sv` | ADDED |
| TP-NW-007 | 包长 16–4300 B | `tc_pkt_len_legal_16_4300` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-NW-008 | 无 UPI / Port IP 路由 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NW-009 | lookup index = dest（表深参数） | `tc_route_lu` | `tb/vibe/tests/tc_route_lu.sv` | MAPPED |
| TP-NW-010 | per-flow vs per-packet 分流 | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-001 | CFG0 在 DLL 终结，不进 fabric | `tc_cfg0_term_not_fabric` | `tb/vibe/tests/tc_cfg0_term_not_fabric.sv` | MAPPED |
| TP-CFG-002 | CFG 3/4/5/7/9 与 reserved 转发 | `tc_cfg_fwd_class` | `tb/vibe/env/vibe_suite.sv` | ADDED |
| TP-CFG-003 | CFG6 DCNA==已写 CNA 终结 | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-004 | CFG6 NLP=1 或 opc 0x10 targeting us 终结 | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-005 | 其余 CFG6 FORWARD | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-006 | CNA 未写不得用上电默认匹配 | `tc_cfg6_term_vs_fwd` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-CFG-007 | CNA 16-bit 不是 24-bit | `tc_cna_16bit` | `tb/vibe/tests/tc_cna_16bit.sv` | ADDED |
| TP-ICRC-001 | 发送端计算 ICRC | `tc_icrc_txrx_vs_transit` | `tb/vibe/tests/tc_icrc_txrx_vs_transit.sv` | MAPPED |
| TP-ICRC-002 | 接收端 ICRC fail → drop/irq | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-ICRC-003 | transit 不得重算 ICRC | `tc_icrc_transit_no_recompute` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-ICRC-004 | CFG9 无 ICRC，转发 | `tc_cfg9_no_icrc` | `tb/vibe/tests/tc_cfg9_no_icrc.sv` | ADDED |
| TP-VL-001 | VL0–15 硬件可用 | `tc_vl_rr_0_15` | `tb/vibe/tests/tc_vl_rr_0_15.sv` | MAPPED |
| TP-VL-002 | egress 非空 VOQ 间 RR | `tc_vl_rr` | `tb/vibe/tests/tc_vl_rr.sv` | MAPPED |
| TP-VL-003 | 无 SL | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-FECN-001 | CCI.Mode 3'b100/010 才改写 FECN | `tc_fecn_mark` | `tb/vibe/tests/tc_fecn_mark.sv` | MAPPED |
| TP-FECN-002 | 不是 CAQM | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-QOS-001 | NPI 关闭 / 无 NPI 过滤 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-QOS-002 | VOQ deadlock 1µs drop | `tc_deadlock_timeout_1us` | `tb/vibe/tests/tc_deadlock_timeout_1us.sv` | MAPPED |
| TP-FAB-001 | SAF，无 cut-through | `tc_saf_full_pkt` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-FAB-002 | down 端口无 DLLDP | `tc_xbar_unit` | `tb/vibe/tests/tc_xbar_unit.sv` | MAPPED |
| TP-FAB-003 | 4 端口转发；mgmt bypass 不进 xbar | `tc_mgmt_byp` | `tb/vibe/tests/tc_mgmt_byp.sv` | MAPPED |
| TP-FAB-004 | 无 hop/qdepth MUST | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-FAB-005 | xbar 一包一 grant，冲突 RR | `tc_xbar_unit` | `tb/vibe/tests/tc_xbar_unit.sv` | MAPPED |
| TP-MGMT-001 | 静态写 vld/ready 接口 | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-MGMT-002 | CFG6 子集 RW（CNA/route/default/rst/go） | `tc_identity_cfg_space` | `tb/vibe/tests/tc_identity_cfg_space.sv` | MAPPED |
| TP-MGMT-003 | CNA 全端口 capture（本 CNA） | `tc_cna_ep` | `tb/vibe/tests/tc_cna_ep.sv` | MAPPED |
| TP-RST-001 | Port Reset 只动该端口 | `tc_port_rst_via_cfg` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-RST-002 | device reset 清 RW / CNA unwritten | `tc_device_rst_via_cfg` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-IRQ-001 | 仅 irq_logic 一脚 | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-002 | §15 必须事件映射 | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-IRQ-003 | 无 hotplug IRQ | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-IF-001 | LinkReady 参与 vld/ready | `tc_nw_adapt_linkready` | `tb/vibe/tests/tc_nw_adapt_linkready.sv` | MAPPED |
| TP-IF-002 | 每端口 txclk/rxclk 独立 | `tc_pma_922mhz` | `tb/vibe/tests/tc_pma_922mhz.sv` | MAPPED |
| TP-IF-003 | PMA 无额外握手名 | `tc_pma_512b_slice` | `tb/vibe/tests/tc_pma_512b_slice.sv` | MAPPED |
| TP-IF-004 | mgmt bypass 从 ingress TX 注入 | `tc_mgmt_byp` | `tb/vibe/tests/tc_mgmt_byp.sv` | MAPPED |
| TP-CDC-001 | 每 lane gray AFIFO | `tc_afifo_afull10` | `tb/vibe/tests/tc_afifo_afull10.sv` | MAPPED |
| TP-CDC-002 | reset sync | `tc_rst_sync` | `tb/vibe/tests/tc_rst_sync.sv` | MAPPED |
| TP-TIM-001 | Retrain 定时器 | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-TIM-002 | credit 1µs 与 VOQ deadlock 1µs 独立 | `tc_timers_indep` | `tb/vibe/tests/tc_timers_indep.sv` | ADDED |
| TP-TIM-003 | clk_fab 与 txclk/rxclk 双时钟 | `tc_pma_922mhz` | `tb/vibe/tests/tc_pma_922mhz.sv` | MAPPED |
| TP-ERR-001 | Retrain 源（lane0 / retry / LID） | `tc_lmsm_walk` | `tb/vibe/tests/tc_lmsm_walk.sv` | MAPPED |
| TP-ERR-002 | §15 可观察错误名 | `tc_irq_agg` | `tb/vibe/tests/tc_irq_agg.sv` | MAPPED |
| TP-ERR-003 | 无 attack 类需求 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-001 | 无 Transport/Transaction/Function endpoint | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-002 | 无 UMMU | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-003 | 无 UBoE | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-004 | CFG9 不作本端 home 终结 | `tc_cfg9_no_icrc` | `tb/vibe/tests/tc_cfg9_no_icrc.sv` | NEG |
| TP-NEG-005 | 无模拟 PMA（Gray/预编码/SerDes） | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-006 | 无秘密 IP 核 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-007 | 无 host CSR 总线脚 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-008 | 无片外 APB/AXI/I2C/JTAG | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-009 | 不以旧 README 数字为准 | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-NEG-010 | 无第五端口 | `tc_id_nports_entity0` | `tb/vibe/tests/tc_id_nports_entity0.sv` | NEG |
| TP-NEG-011 | 无 FS-7 bundle | `tc_neg_official` | `tb/vibe/tests/tc_neg_official.sv` | NEG |
| TP-HOLE-G2 | 路由表 Max Index 未发布 | `tc_hole_g2_route_max` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G3 | 额外 IRQ 脚名未发布 | `tc_hole_g3_irq_pin` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G4 | 额外 reset 脚名未发布 | `tc_hole_g4_reset_pin` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G5 | 上电 CNA 默认未发布 | `tc_hole_g5_cna_poweron` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G6 | lmsm_go 来源未发布 | `tc_hole_g6_lmsm_go_src` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G7 | G7 已关闭：1024 单位是 flit | `tc_credit_1024_flit_bp` | `tb/vibe/tests/tc_credit_1024_flit_bp.sv` | MAPPED |
| TP-HOLE-G8 | 封装脚未发布 | `tc_hole_g8_package_pins` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-G9 | RXEQ 张力/Optimize 未发布 | `tc_hole_g9_rxeq_tension` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-010 | 性能数字未发布 | `tc_hole_010_perf` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
| TP-HOLE-011 | G1 不是 hole（已实现 DROP+count+irq） | `tc_rt10_must_drop` | `tb/vibe/env/vibe_suite.sv` | MAPPED |
| TP-HOLE-012 | 计数器位宽不是 FS-must，不得发明产品宽度 | `tc_hole_012_counter_width` | `tb/vibe/tests/tc_tp_holes.sv` | HOLE |
