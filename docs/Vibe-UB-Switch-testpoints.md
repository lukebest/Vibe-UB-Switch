# TP-0.3 official test points (159)

Locked ID set (FS-0.2.7 / AS-0.1.2). Do not invent `TP-FEC-*` or `TP-CFG-008`..`012`.
Column 2 is the planned name (file may differ).
Overlay B: NW↔DLL is `data[511:0]`; 640b window is DLL↔PCS. 1024 credit = cell.

| ID | planned_name | rule |
|----|--------------|------|
| TP-ID-001 | `tc_id_guid_class` | 软件可识别为独立 UB Switch（GUID Type / Class Code） |
| TP-ID-002 | `tc_id_nports_entity0` | 本实例仅 Entity 0，Port 0..3，N_PORTS=4 |
| TP-ID-003 | `tc_id_cfg0_model` | 必须实现 CFG0_PORT_BASIC / PORT_CAP / ROUTE_TABLE |
| TP-ID-004 | `tc_id_no_ubfm` | 无 UBFM 实例 |
| TP-ID-005 | `tc_id_spec_2_0_only` | 协议只跟 UB Base 2.0 |
| TP-ID-006 | `tc_id_appendix_d_subset` | 附录 D 超出已点名子集暂不实现 |
| TP-PHY-001 | `tc_phy_fullduplex` | 每端口全双工 TX+RX |
| TP-PHY-002 | `tc_phy_x4_symmetric` | 每端口固定 x4 对称 |
| TP-PHY-003 | `tc_phy_mode2_106p25` | 仅 Mode-2 PAM4 106.25G |
| TP-PHY-004 | `tc_phy_tx_lanes_same_freq` | TX 侧全部车道同频 |
| TP-PHY-005 | `tc_phy_no_optical` | 光通路不实现 |
| TP-PHY-006 | `tc_phy_flit_20b` | Flit 20 字节；640b 是 DLL↔PCS 窗，不是 flit |
| TP-PHY-007 | `tc_phy_pma_pcs_boundary` | txdata/rxdata[511:0] @922MHz 无额外握手 |
| TP-PHY-008 | `tc_phy_nw_dll_512b` | NW↔DLL 仅 data[511:0] @1.25GHz（vld/ready） |
| TP-PHY-009 | `tc_phy_tx_fec_1024_two_beats` | FEC 1024b = 两拍 512 |
| TP-PHY-010 | `tc_phy_tx_4x160_afifo_4x128` | 4×160 AFIFO → 4×128=512（640b 在 DLL↔PCS） |
| TP-PHY-011 | `tc_phy_tx_backpressure_chain` | TX 可逐级向 NW 反压 |
| TP-PHY-012 | `tc_phy_rx_inverse_chain` | RX 为 TX 逆过程；NW 脚 data[511:0] 上回收 LPH |
| TP-PHY-013 | `tc_phy_fec_modes_interleave` | FEC T=4/T=2/bypass 双编码交织 |
| TP-PHY-014 | `tc_phy_no_hi_fec_ber` | 不实现 hi_FEC_BER |
| TP-PHY-015 | `tc_phy_fec_decode_retry_retrain` | >T 失败→DLL 重传，失败→Retrain |
| TP-PHY-016 | `tc_phy_amctl_period` | AMCTL eBCH-16 54640/32 LTB |
| TP-PHY-017 | `tc_phy_scrambler_scope` | AMCTL/EEIB 不扰，LTB 扰，种子 LID |
| TP-PHY-018 | `tc_phy_txdata_lane_slice_arch` | lane0=[127:0]..lane3=[511:384] |
| TP-PHY-019 | `tc_phy_dll_bcrc_only` | 只 BCRC |
| TP-PHY-020 | `tc_phy_no_payload_before_train` | 训练完前不得向 DLL 业务 flit |
| TP-LMSM-001 | `tc_lmsm_idle` | reset / port_rst → Link_Idle |
| TP-LMSM-002 | `tc_lmsm_discovery` | lmsm_go：Idle → Discovery |
| TP-LMSM-003 | `tc_lmsm_x4_106g` | Discovery 锁定 x4 / 106.25G |
| TP-LMSM-004 | `tc_lmsm_timers` | LMSM 定时器（10µs/2ms/24ms/48ms…） |
| TP-LMSM-005 | `tc_lmsm_config` | Config.Active / Check / Confirm |
| TP-LMSM-006 | `tc_lmsm_nullblock` | Send_NullBlock → Link_Active |
| TP-LMSM-007 | `tc_lmsm_link_active` | Link_Active：LinkUp + LinkReady |
| TP-LMSM-008 | `tc_lmsm_retrain_no_speed` | Retrain 不改速率 |
| TP-LMSM-009 | `tc_lmsm_eq` | EQ.*（若 Config 协商 EQ） |
| TP-LMSM-010 | `tc_lmsm_lane0_retrain` | lane0 fail → Retrain，不降宽 |
| TP-LMSM-011 | `tc_lmsm_unimpl_arcs` | 未实现 Fig 3-28 / Probe / RXEQ / Change_Speed 弧 |
| TP-LMSM-012 | `tc_lmsm_amctl_lock` | AMCTL lock 参与 LMSM |
| TP-LMSM-013 | `tc_lmsm_no_lane_reverse` | 不车道对调 / 极性训练 |
| TP-LMSM-014 | `tc_lmsm_8_dltb` | Send_NullBlock 8 个 DLTB 后 Active |
| TP-DLL-001 | `tc_dll_four_states` | Disabled / Param_Init / Credit_Init / Normal |
| TP-DLL-002 | `tc_dll_linkup0_disabled` | LinkUp==0 → 永远 Disabled |
| TP-DLL-003 | `tc_dll_entity_rst_not_disabled` | entity rst 不得单独强制 Disabled |
| TP-DLL-004 | `tc_dll_dp_split` | DLLDP >32 flit 拆 ≤16×≤32 |
| TP-DLL-005 | `tc_dll_bcrc_fields` | BCRC CRC30 + ERROR_FLAG 字段 |
| TP-DLL-006 | `tc_dll_cb_no_credit` | CFG0 DLLCB 不耗 data credit |
| TP-DLL-007 | `tc_dll_same_vl_fcfs` | 同 VL FCFS |
| TP-DLL-008 | `tc_dll_autoneg_defaults` | 协商失败用官方默认；VL1–15 硬件仍可用 |
| TP-CRD-001 | `tc_crd_cell_n_default8` | consume ceil(flits/n)，n 默认 8 |
| TP-CRD-002 | `tc_crd_max_65535` | max 65535 cells，再加 → fc_ovf |
| TP-CRD-003 | `tc_crd_ack_no_dp` | 无 DLLDP 但 pending → Crd_Ack |
| TP-CRD-004 | `tc_crd_1024_cell_bp` | pending≥1024 cell → 反压 NW + Crd_Ack（不是 flit，不×n） |
| TP-CRD-005 | `tc_crd_1us_timeout` | credit return 超时 1µs → proto_err |
| TP-CRD-006 | `tc_crd_rxbuf_ovf` | RX buf overflow → irq |
| TP-CRD-007 | `tc_crd_fc_ovf` | FC overflow → irq |
| TP-CRD-008 | `tc_crd_no_underflow` | 不发明 credit underflow 错误码 |
| TP-RTY-001 | `tc_rty_gbn` | FEC/BCRC fail → Go-Back-N |
| TP-RTY-002 | `tc_rty_buf_256` | retry_buf 深度 256 |
| TP-RTY-003 | `tc_rty_not_grow_512` | 不得为 512-flit DP 扩 retry_buf |
| TP-RTY-004 | `tc_rty_req_sm` | RETRY_REQ_SM |
| TP-RTY-005 | `tc_rty_thresh_15_4` | NUM_RETRY=15 / NUM_PHY_REINIT=4 |
| TP-RTY-006 | `tc_rty_wait_range` | WAIT 超时合法范围（参数 1µs–10s） |
| TP-RTY-007 | `tc_rty_ack_sm` | RETRY_ACK_SM 回放 |
| TP-RTY-008 | `tc_rty_error_classes` | RETRAIN / ERROR 分类 |
| TP-RTY-009 | `tc_rty_numfreebuf_ovf` | NumFreeBuf 溢出 → DL Protocol Error |
| TP-RTY-010 | `tc_rty_wait_port_dev_rst` | ERROR 等 Port/device reset |
| TP-RTY-011 | `tc_rty_error_flag_saf` | LinkUp=0 未完成 DP pad0+ERROR_FLAG |
| TP-RT-001 | `tc_rt00_per_flow_rr` | RT=00 per-flow sticky RR |
| TP-RT-002 | `tc_rt01_per_packet_rr` | RT=01 per-packet RR |
| TP-RT-003 | `tc_rt10_must_drop` | RT=10 DROP |
| TP-RT-004 | `tc_rt11_must_drop` | RT=11 DROP |
| TP-RT-005 | `tc_rt_shortest_unimpl_count` | rt_shortest_unimpl +1 |
| TP-RT-006 | `tc_rt_shortest_irq_logic` | G1 置 irq_logic |
| TP-RT-007 | `tc_rt_irq_logic_sticky` | irq_logic sticky |
| TP-RT-008 | `tc_rt_no_rewrite` | 不得改写 RT |
| TP-RT-009 | `tc_rt10_not_as_rt00` | RT=10 不得当 RT=00 |
| TP-RT-010 | `tc_rt11_not_as_rt01` | RT=11 不得当 RT=01 |
| TP-RT-011 | `tc_rt_no_dijkstra` | 不得 Dijkstra / shortest-path |
| TP-RT-012 | `tc_rt_detect_in_port_sel` | G1 在 route_lu/port_sel 检测 |
| TP-RT-013 | `tc_rt_counter_32b_sat` | 计数器 32b 饱和 |
| TP-RT-014 | `tc_rt10_unique_bm_drop` | 即使唯一 bitmap 也 DROP |
| TP-RT-015 | `tc_rt10_on_default_drop` | 走 default 仍 DROP |
| TP-RT-016 | `tc_rt10_not_proto_err` | G1 drop 不是 DL Protocol Error |
| TP-RT-017 | `tc_rt_all_ingress_ports` | 所有 ingress 端口都检测 G1 |
| TP-NW-001 | `tc_nw_route_nibble` | 路由表项仅 [3:0] nibble |
| TP-NW-002 | `tc_nw_default_all0_port0` | default 全 0 → port 0 |
| TP-NW-003 | `tc_nw_bitmap_and_up` | bitmap AND Status_Up；port0 Down → drop+count |
| TP-NW-004 | `tc_nw_no_exact_route` | 无 Exact Route |
| TP-NW-005 | `tc_nw_no_port_cna` | 无 Port CNA |
| TP-NW-006 | `tc_nw_no_flood` | 无 flood/broadcast |
| TP-NW-007 | `tc_nw_pkt_len_16_4300` | 包长 16–4300 B |
| TP-NW-008 | `tc_nw_no_upi_port_ip` | 无 UPI / Port IP 路由 |
| TP-NW-009 | `tc_nw_lookup_index` | lookup index = dest（表深参数） |
| TP-NW-010 | `tc_nw_per_flow_vs_packet` | per-flow vs per-packet 分流 |
| TP-CFG-001 | `tc_cfg0_term_dll` | CFG0 在 DLL 终结，不进 fabric |
| TP-CFG-002 | `tc_cfg_fwd_class` | CFG 3/4/5/7/9 与 reserved 转发 |
| TP-CFG-003 | `tc_cfg6_cna_term` | CFG6 DCNA==已写 CNA 终结 |
| TP-CFG-004 | `tc_cfg6_nlp_opc_term` | CFG6 NLP=1 或 opc 0x10 targeting us 终结 |
| TP-CFG-005 | `tc_cfg6_other_fwd` | 其余 CFG6 FORWARD |
| TP-CFG-006 | `tc_cfg6_no_default_cna` | CNA 未写不得用上电默认匹配 |
| TP-CFG-007 | `tc_cfg_cna_16bit` | CNA 16-bit 不是 24-bit |
| TP-ICRC-001 | `tc_icrc_tx_compute` | 发送端计算 ICRC |
| TP-ICRC-002 | `tc_icrc_rx_fail_drop` | 接收端 ICRC fail → drop/irq |
| TP-ICRC-003 | `tc_icrc_transit_no_recompute` | transit 不得重算 ICRC |
| TP-ICRC-004 | `tc_icrc_cfg9_no_icrc` | CFG9 无 ICRC，转发 |
| TP-VL-001 | `tc_vl_0_15_usable` | VL0–15 硬件可用 |
| TP-VL-002 | `tc_vl_inter_rr` | egress 非空 VOQ 间 RR |
| TP-VL-003 | `tc_vl_no_sl` | 无 SL |
| TP-FECN-001 | `tc_fecn_cci_modes` | CCI.Mode 3'b100/010 才改写 FECN |
| TP-FECN-002 | `tc_fecn_no_caqm` | 不是 CAQM |
| TP-QOS-001 | `tc_qos_npi_disabled` | NPI 关闭 / 无 NPI 过滤 |
| TP-QOS-002 | `tc_qos_deadlock_1us` | VOQ deadlock 1µs drop |
| TP-FAB-001 | `tc_fab_saf_no_cutthrough` | SAF，无 cut-through |
| TP-FAB-002 | `tc_fab_no_dp_when_down` | down 端口无 DLLDP |
| TP-FAB-003 | `tc_fab_4port_mgmt_byp` | 4 端口转发；mgmt bypass 不进 xbar |
| TP-FAB-004 | `tc_fab_no_hop_qdepth_must` | 无 hop/qdepth MUST |
| TP-FAB-005 | `tc_fab_xbar_one_pkt_rr` | xbar 一包一 grant，冲突 RR |
| TP-MGMT-001 | `tc_mgmt_static_wr_if` | 静态写 vld/ready 接口 |
| TP-MGMT-002 | `tc_mgmt_cfg6_subset_rw` | CFG6 子集 RW（CNA/route/default/rst/go） |
| TP-MGMT-003 | `tc_mgmt_cna_all_ports_capture` | CNA 全端口 capture（本 CNA） |
| TP-RST-001 | `tc_rst_port_scope` | Port Reset 只动该端口 |
| TP-RST-002 | `tc_rst_device_scope` | device reset 清 RW / CNA unwritten |
| TP-IRQ-001 | `tc_irq_logic_pin` | 仅 irq_logic 一脚 |
| TP-IRQ-002 | `tc_irq_must_events_map` | §15 必须事件映射 |
| TP-IRQ-003 | `tc_irq_no_hotplug` | 无 hotplug IRQ |
| TP-IF-001 | `tc_if_linkready_vld_ready` | LinkReady 参与 vld/ready |
| TP-IF-002 | `tc_if_clk_independent` | 每端口 txclk/rxclk 独立 |
| TP-IF-003 | `tc_if_pma_no_handshake` | PMA 无额外握手名 |
| TP-IF-004 | `tc_if_mgmt_bypass_inject` | mgmt bypass 从 ingress TX 注入 |
| TP-CDC-001 | `tc_cdc_gray_afifo_per_lane` | 每 lane gray AFIFO |
| TP-CDC-002 | `tc_cdc_reset_sync` | reset sync |
| TP-TIM-001 | `tc_tim_retrain_timers` | Retrain 定时器 |
| TP-TIM-002 | `tc_tim_two_1us_indep` | credit 1µs 与 VOQ deadlock 1µs 独立 |
| TP-TIM-003 | `tc_tim_dual_clock` | clk_fab 与 txclk/rxclk 双时钟 |
| TP-ERR-001 | `tc_err_retrain_sources` | Retrain 源（lane0 / retry / LID） |
| TP-ERR-002 | `tc_err_named_observable` | §15 可观察错误名 |
| TP-ERR-003 | `tc_err_no_attack_req` | 无 attack 类需求 |
| TP-NEG-001 | `tc_neg_no_transport_ep` | 无 Transport/Transaction/Function endpoint |
| TP-NEG-002 | `tc_neg_no_ummu` | 无 UMMU |
| TP-NEG-003 | `tc_neg_no_uboe` | 无 UBoE |
| TP-NEG-004 | `tc_neg_no_cfg9_home` | CFG9 不作本端 home 终结 |
| TP-NEG-005 | `tc_neg_no_analog_pma` | 无模拟 PMA（Gray/预编码/SerDes） |
| TP-NEG-006 | `tc_neg_no_secret_ip` | 无秘密 IP 核 |
| TP-NEG-007 | `tc_neg_no_host_csr` | 无 host CSR 总线脚 |
| TP-NEG-008 | `tc_neg_no_offchip_mgmt` | 无片外 APB/AXI/I2C/JTAG |
| TP-NEG-009 | `tc_neg_no_readme_numbers` | 不以旧 README 数字为准 |
| TP-NEG-010 | `tc_neg_no_fifth_port` | 无第五端口 |
| TP-NEG-011 | `tc_neg_no_fs7_bundle` | 无 FS-7 bundle |
| TP-HOLE-G2 | `tc_hole_g2_route_max` | 路由表 Max Index 未发布 |
| TP-HOLE-G3 | `tc_hole_g3_irq_pin` | 额外 IRQ 脚名未发布 |
| TP-HOLE-G4 | `tc_hole_g4_reset_pin` | 额外 reset 脚名未发布 |
| TP-HOLE-G5 | `tc_hole_g5_cna_poweron` | 上电 CNA 默认未发布 |
| TP-HOLE-G6 | `tc_hole_g6_lmsm_go_src` | lmsm_go 来源未发布 |
| TP-HOLE-G7 | `tc_hole_g7_closed_cell` | G7 已关闭：1024 单位是 cell |
| TP-HOLE-G8 | `tc_hole_g8_package_pins` | 封装脚未发布 |
| TP-HOLE-G9 | `tc_hole_g9_rxeq_tension` | RXEQ 张力/Optimize 未发布 |
| TP-HOLE-010 | `tc_hole_010_perf` | 性能数字未发布 |
| TP-HOLE-011 | `tc_hole_011_g1_not_hole` | G1 不是 hole（已实现 DROP+count+irq） |
| TP-HOLE-012 | `tc_hole_012_counter_width` | 计数器位宽不是 FS-must，不得发明产品宽度 |
