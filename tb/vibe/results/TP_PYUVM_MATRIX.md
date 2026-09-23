# TP-0.3 ↔ pyuvm (Python) coverage matrix

Docs/results audit only. **Python column is authoritative.**
Stock SV / `tb/vibe/tests/tc_*.sv` / SV UVM (`tb/vibe/uvm/pkg/*.svh`) alone does **not** count as HAS.

This document is **not** 1/3, **not** 4/3, **not** freeze, **not** signoff.

## Sources

- Official IDs (159): [`docs/Vibe-UB-Switch-testpoints.md`](../../../docs/Vibe-UB-Switch-testpoints.md) / [`TP-0.3.md`](TP-0.3.md)
- Existing SV/UVM-biased matrix (re-checked, not copied): [`TP_TC_MATRIX.md`](TP_TC_MATRIX.md)
- Python gate: `tb/vibe/pyuvm/` (`catalog*.py`, `entry_*.py`, `vibe_uvm/tests/*.py`)
- Regenerator: `tb/vibe/scripts/gen_tp_pyuvm_matrix.py`
- Checkout tip audited: `5087843d0f4c4375a75f01c841d1b80b5229550a` (`origin/main`)

## Method

1. Enumerate the locked TP-0.3 ID set (FS-0.2.7 / AS-0.1.2).
2. Discover actual Python TCs: `class tc_*` / fab `_one()` factories / `static_tests.py` PASS/HOLE names / `scan_official_neg.RULES`.
3. HAS = a pyuvm TC exists that corresponds to the official rule (same identifier as `TP_TC_MATRIX.md`, or an in-file PASS alias).
4. GAP = no such Python TC. Icarus/SV-UVM presence is noted only as the miss.
5. Decision-I leaf TCs (`tc_vibe_afifo`, `tc_vibe_sync2`, `tc_vibe_rst_sync`) cover **only that leaf**. They are listed in the appendix and are **not** used to mark full-chip official TPs as HAS.

## Totals

| | count |
|---|------:|
| Official testpoints (TP-0.3) | **159** |
| HAS Python TC | **159** |
| GAP (no corresponding Python TC) | **0** |

N=159 / M=159 / G=0. Do not read this as a gate fraction, freeze, or signoff.

## GAP list

None.

## HAS by Python scope (not a gate)

| scope | HAS count |
|-------|----------:|
| fab-suite | 27 |
| port-sim | 4 |
| static | 29 |
| static-neg | 6 |
| unit-sim | 93 |

Scope is where the Python TC lives. A unit-sim or static-neg TC can still be the project's designated scorer for a chip-level rule (same convention as `TP_TC_MATRIX.md`). Leaf-only Decision-I TCs are excluded from HAS.

## Full matrix

| TP | rule (short) | pyuvm | TC name | file | scope | note |
|----|--------------|-------|---------|------|-------|------|
| TP-ID-001 | 软件可识别为独立 UB Switch（GUID Type / Class Code） | **HAS** | `tc_identity_cfg_space` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-ID-002 | 本实例仅 Entity 0，Port 0..3，N_PORTS=4 | **HAS** | `tc_id_nports_entity0` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-ID-003 | 必须实现 CFG0_PORT_BASIC / PORT_CAP / ROUTE_TABLE | **HAS** | `tc_identity_cfg_space` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-ID-004 | 无 UBFM 实例 | **HAS** | `tc_neg_ubfm` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-ID-005 | 协议只跟 UB Base 2.0 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-ID-006 | 附录 D 超出已点名子集暂不实现 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-PHY-001 | 每端口全双工 TX+RX | **HAS** | `tc_port_smoke` | `tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py` | port-sim |  |
| TP-PHY-002 | 每端口固定 x4 对称 | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-PHY-003 | 仅 Mode-2 PAM4 106.25G | **HAS** | `tc_identity_cfg_space` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-PHY-004 | TX 侧全部车道同频 | **HAS** | `tc_pma_922mhz` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-005 | 光通路不实现 | **HAS** | `tc_neg_no_optical` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-PHY-006 | Flit 20 字节；640b 是 DLL↔PCS 窗，不是 flit | **HAS** | `tc_pkt_len_legal_16_4300` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-PHY-007 | pcs_pma_txdata/pma_pcs_rxdata[511:0] @922MHz 无额外握手 | **HAS** | `tc_pma_512b_slice` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-PHY-008 | NW↔DLL 仅 data[511:0] @1.25GHz（vld/ready） | **HAS** | `tc_phy_nw_dll_512b` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-PHY-009 | FEC 1024b = 两拍 512 | **HAS** | `tc_pcs_cw2beat` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-010 | 4×160 AFIFO → 4×128=512（640b 在 DLL↔PCS） | **HAS** | `tc_phy_u26_chain` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-011 | TX 可逐级向 NW 反压 | **HAS** | `tc_nw_pkt_to_pma_tx` | `tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py` | port-sim |  |
| TP-PHY-012 | RX 为 TX 逆过程；NW 脚 data[511:0] 上回收 LPH | **HAS** | `tc_nw_pkt_pma_loopback` | `tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py` | port-sim |  |
| TP-PHY-013 | FEC T=4/T=2/bypass 双编码交织 | **HAS** | `tc_pcs_fec_dual_enc` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-014 | 不实现 hi_FEC_BER | **HAS** | `tc_neg_hi_fec_ber` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-PHY-015 | >T 失败→DLL 重传，失败→Retrain | **HAS** | `tc_fec_fail_gbn` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-PHY-016 | AMCTL eBCH-16 54640/32 LTB | **HAS** | `tc_pcs_amctl` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-017 | AMCTL/EEIB 不扰，LTB 扰，种子 LID | **HAS** | `tc_pcs_scramble` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-PHY-018 | lane0=[127:0]..lane3=[511:384] | **HAS** | `tc_nw_pkt_to_pma_tx` | `tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py` | port-sim |  |
| TP-PHY-019 | 只 BCRC | **HAS** | `tc_bcrc_crc30` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-PHY-020 | 训练完前不得向 DLL 业务 flit | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-001 | reset / port_rst → Link_Idle | **HAS** | `tc_lmsm_idle_discovery` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-LMSM-002 | lmsm_go：Idle → Discovery | **HAS** | `tc_lmsm_idle_discovery` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-LMSM-003 | Discovery 锁定 x4 / 106.25G | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-004 | LMSM 定时器（10µs/2ms/24ms/48ms…） | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-005 | Config.Active / Check / Confirm | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-006 | Send_NullBlock → Link_Active | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-007 | Link_Active：LinkUp + LinkReady | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-008 | Retrain 不改速率 | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-009 | EQ.*（若 Config 协商 EQ） | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-010 | lane0 fail → Retrain，不降宽 | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-011 | 未实现 Fig 3-28 / Probe / RXEQ / Change_Speed 弧 | **HAS** | `tc_neg_absent_features` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-LMSM-012 | AMCTL lock 参与 LMSM | **HAS** | `tc_lmsm_vlock` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-LMSM-013 | 不车道对调 / 极性训练 | **HAS** | `tc_neg_absent_features` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-LMSM-014 | Send_NullBlock 8 个 DLTB 后 Active | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-DLL-001 | Disabled / Param_Init / Credit_Init / Normal | **HAS** | `tc_dll_sm_states` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-DLL-002 | LinkUp==0 → 永远 Disabled | **HAS** | `tc_dll_sm_states` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-DLL-003 | entity rst 不得单独强制 Disabled | **HAS** | `tc_dll_sm_states` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-DLL-004 | DLLDP >32 flit 拆 ≤16×≤32 | **HAS** | `tc_dll` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_dll.py` | unit-sim | full vibe_dll; scores >32-flit split ≤16×≤32 (not leaf SM/credit/retry/rx/tx) |
| TP-DLL-005 | BCRC CRC30 + ERROR_FLAG 字段 | **HAS** | `tc_bcrc_crc30` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-DLL-006 | CFG0 DLLCB 不耗 data credit | **HAS** | `tc_cfg0_no_credit` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-DLL-007 | 同 VL FCFS | **HAS** | `tc_vl_rr` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-DLL-008 | 协商失败用官方默认；VL1–15 硬件仍可用 | **HAS** | `tc_vl_rr_0_15` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-CRD-001 | consume ceil(flits/n)，n 默认 8 | **HAS** | `tc_credit_grain_n` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CRD-002 | max 65535 cells，再加 → fc_ovf | **HAS** | `tc_credit_grain_n` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CRD-003 | 无 DLLDP 但 pending → Crd_Ack | **HAS** | `tc_credit_1024_flit_bp` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-CRD-004 | pending≥1024 cell → 反压 NW + Crd_Ack（不是 flit，不×n） | **HAS** | `tc_credit_1024_flit_bp` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-CRD-005 | credit return 超时 1µs → proto_err | **HAS** | `tc_credit_timeout_1us` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CRD-006 | RX buf overflow → irq | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CRD-007 | FC overflow → irq | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CRD-008 | 不发明 credit underflow 错误码 | **HAS** | `tc_credit_no_underflow` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-001 | FEC/BCRC fail → Go-Back-N | **HAS** | `tc_retry_req_gbn` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-002 | retry_buf 深度 256 | **HAS** | `tc_retry_buf_256` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-003 | 不得为 512-flit DP 扩 retry_buf | **HAS** | `tc_retry_buf_256` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-004 | RETRY_REQ_SM | **HAS** | `tc_retry_req_gbn` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-005 | NUM_RETRY=15 / NUM_PHY_REINIT=4 | **HAS** | `tc_retry_wait_retrain` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-006 | WAIT 超时合法范围（参数 1µs–10s） | **HAS** | `tc_retry_wait_retrain` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-007 | RETRY_ACK_SM 回放 | **HAS** | `tc_retry_ack_replay` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-008 | RETRAIN / ERROR 分类 | **HAS** | `tc_retry_wait_retrain` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-009 | NumFreeBuf 溢出 → DL Protocol Error | **HAS** | `tc_retry_buf_256` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-010 | ERROR 等 Port/device reset | **HAS** | `tc_retry_req_gbn` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RTY-011 | LinkUp=0 未完成 DP pad0+ERROR_FLAG | **HAS** | `tc_dll_rx_errflag` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RT-001 | RT=00 per-flow sticky RR | **HAS** | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-002 | RT=01 per-packet RR | **HAS** | `tc_rt01_per_packet_rr_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-003 | RT=10 DROP | **HAS** | `tc_rt10_must_drop` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-004 | RT=11 DROP | **HAS** | `tc_rt11_must_drop` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-005 | rt_shortest_unimpl +1 | **HAS** | `tc_rt_shortest_unimpl_count` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-006 | G1 置 irq_logic | **HAS** | `tc_rt_shortest_irq_logic` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-007 | irq_logic sticky | **HAS** | `tc_rt_irq_logic_sticky` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-008 | 不得改写 RT | **HAS** | `tc_rt_no_rewrite` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-009 | RT=10 不得当 RT=00 | **HAS** | `tc_rt10_not_as_rt00` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-010 | RT=11 不得当 RT=01 | **HAS** | `tc_rt_g1_official` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim | PASS line inside tc_rt_g1_official (not a standalone class); matrix SV name `tc_rt11_not_as_rt01` |
| TP-RT-011 | 不得 Dijkstra / shortest-path | **HAS** | `tc_neg_dijkstra` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-RT-012 | G1 在 route_lu/port_sel 检测 | **HAS** | `tc_rt_g1_official` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RT-013 | 计数器 32b 饱和 | **HAS** | `tc_rt_counter_32b_sat` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RT-014 | 即使唯一 bitmap 也 DROP | **HAS** | `tc_rt_g1_official` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RT-015 | 走 default 仍 DROP | **HAS** | `tc_rt_g1_official` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RT-016 | G1 drop 不是 DL Protocol Error | **HAS** | `tc_rt_g1_official` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RT-017 | 所有 ingress 端口都检测 G1 | **HAS** | `tc_rt_shortest_unimpl_count` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-NW-001 | 路由表项仅 [3:0] nibble | **HAS** | `tc_route_lu` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-NW-002 | default 全 0 → port 0 | **HAS** | `tc_default_rt_all0_port0` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-NW-003 | bitmap AND Status_Up；port0 Down → drop+count | **HAS** | `tc_p0_down_drop` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-NW-004 | 无 Exact Route | **HAS** | `tc_neg_exact_route` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-NW-005 | 无 Port CNA | **HAS** | `tc_neg_port_cna` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static-neg |  |
| TP-NW-006 | 无 flood/broadcast | **HAS** | `tc_p0_down_drop` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-NW-007 | 包长 16–4300 B | **HAS** | `tc_pkt_len_legal_16_4300` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-NW-008 | 无 UPI / Port IP 路由 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NW-009 | lookup index = dest（表深参数） | **HAS** | `tc_route_lu` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-NW-010 | per-flow vs per-packet 分流 | **HAS** | `tc_rt00_per_flow_rr_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-001 | CFG0 在 DLL 终结，不进 fabric | **HAS** | `tc_cfg0_term_not_fabric` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CFG-002 | CFG 3/4/5/7/9 与 reserved 转发 | **HAS** | `tc_cfg_fwd_class` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-003 | CFG6 DCNA==已写 CNA 终结 | **HAS** | `tc_cfg6_term_vs_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-004 | CFG6 NLP=1 或 opc 0x10 targeting us 终结 | **HAS** | `tc_cfg6_term_vs_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-005 | 其余 CFG6 FORWARD | **HAS** | `tc_cfg6_term_vs_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-006 | CNA 未写不得用上电默认匹配 | **HAS** | `tc_cfg6_term_vs_fwd` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-CFG-007 | CNA 16-bit 不是 24-bit | **HAS** | `tc_cna_16bit` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-ICRC-001 | 发送端计算 ICRC | **HAS** | `tc_icrc_txrx_vs_transit` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-ICRC-002 | 接收端 ICRC fail → drop/irq | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-ICRC-003 | transit 不得重算 ICRC | **HAS** | `tc_icrc_transit_no_recompute` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-ICRC-004 | CFG9 无 ICRC，转发 | **HAS** | `tc_cfg9_no_icrc` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-VL-001 | VL0–15 硬件可用 | **HAS** | `tc_vl_rr_0_15` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-VL-002 | egress 非空 VOQ 间 RR | **HAS** | `tc_vl_rr` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-VL-003 | 无 SL | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-FECN-001 | CCI.Mode 3'b100/010 才改写 FECN | **HAS** | `tc_fecn_mark` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-FECN-002 | 不是 CAQM | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-QOS-001 | NPI 关闭 / 无 NPI 过滤 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-QOS-002 | VOQ deadlock 1µs drop | **HAS** | `tc_deadlock_timeout_1us` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-FAB-001 | SAF，无 cut-through | **HAS** | `tc_saf_full_pkt` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-FAB-002 | down 端口无 DLLDP | **HAS** | `tc_xbar_unit` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-FAB-003 | 4 端口转发；mgmt bypass 不进 xbar | **HAS** | `tc_mgmt_byp` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-FAB-004 | 无 hop/qdepth MUST | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-FAB-005 | xbar 一包一 grant，冲突 RR | **HAS** | `tc_xbar_unit` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-MGMT-001 | 静态写 vld/ready 接口 | **HAS** | `tc_identity_cfg_space` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-MGMT-002 | CFG6 子集 RW（CNA/route/default/rst/go） | **HAS** | `tc_identity_cfg_space` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-MGMT-003 | CNA 全端口 capture（本 CNA） | **HAS** | `tc_cna_ep` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-RST-001 | Port Reset 只动该端口 | **HAS** | `tc_port_rst_via_cfg` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-RST-002 | device reset 清 RW / CNA unwritten | **HAS** | `tc_device_rst_via_cfg` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-IRQ-001 | 仅 irq_logic 一脚 | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-IRQ-002 | §15 必须事件映射 | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-IRQ-003 | 无 hotplug IRQ | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-IF-001 | LinkReady 参与 vld/ready | **HAS** | `tc_nw_adapt_linkready` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-IF-002 | 每端口 txclk/rxclk 独立 | **HAS** | `tc_pma_922mhz` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-IF-003 | PMA 无额外握手名 | **HAS** | `tc_pma_512b_slice` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-IF-004 | mgmt bypass 从 ingress TX 注入 | **HAS** | `tc_mgmt_byp` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CDC-001 | 每 lane gray AFIFO | **HAS** | `tc_afifo_afull10` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-CDC-002 | reset sync | **HAS** | `tc_rst_sync` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-TIM-001 | Retrain 定时器 | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-TIM-002 | credit 1µs 与 VOQ deadlock 1µs 独立 | **HAS** | `tc_timers_indep` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-TIM-003 | clk_fab 与 txclk/rxclk 双时钟 | **HAS** | `tc_pma_922mhz` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py` | unit-sim |  |
| TP-ERR-001 | Retrain 源（lane0 / retry / LID） | **HAS** | `tc_lmsm_walk` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-ERR-002 | §15 可观察错误名 | **HAS** | `tc_irq_agg` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py` | unit-sim |  |
| TP-ERR-003 | 无 attack 类需求 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-001 | 无 Transport/Transaction/Function endpoint | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-002 | 无 UMMU | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-003 | 无 UBoE | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-004 | CFG9 不作本端 home 终结 | **HAS** | `tc_cfg9_no_icrc` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-NEG-005 | 无模拟 PMA（Gray/预编码/SerDes） | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-006 | 无秘密 IP 核 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-007 | 无 host CSR 总线脚 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-008 | 无片外 APB/AXI/I2C/JTAG | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-009 | 不以旧 README 数字为准 | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-010 | 无第五端口 | **HAS** | `tc_id_nports_entity0` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-NEG-011 | 无 FS-7 bundle | **HAS** | `tc_neg_official` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G2 | 路由表 Max Index 未发布 | **HAS** | `tc_hole_g2_route_max` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G3 | 额外 IRQ 脚名未发布 | **HAS** | `tc_hole_g3_irq_pin` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G4 | 额外 reset 脚名未发布 | **HAS** | `tc_hole_g4_reset_pin` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G5 | 上电 CNA 默认未发布 | **HAS** | `tc_hole_g5_cna_poweron` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G6 | lmsm_go 来源未发布 | **HAS** | `tc_hole_g6_lmsm_go_src` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G7 | G7 已关闭：1024 单位是 cell | **HAS** | `tc_credit_1024_flit_bp` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py` | unit-sim |  |
| TP-HOLE-G8 | 封装脚未发布 | **HAS** | `tc_hole_g8_package_pins` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-G9 | RXEQ 张力/Optimize 未发布 | **HAS** | `tc_hole_g9_rxeq_tension` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-010 | 性能数字未发布 | **HAS** | `tc_hole_010_perf` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |
| TP-HOLE-011 | G1 不是 hole（已实现 DROP+count+irq） | **HAS** | `tc_rt10_must_drop` | `tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py` | fab-suite |  |
| TP-HOLE-012 | 计数器位宽不是 FS-must，不得发明产品宽度 | **HAS** | `tc_hole_012_counter_width` | `tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py` | static |  |

## Appendix — Decision-I leaf Python TCs (not full-chip cover)

These exist under `tb/vibe/pyuvm` and score **only** their leaf DUT. They must not be used to close official full-chip TPs (TP-CDC-001 / TP-CDC-002 / TP-IF-* / etc.).

| TC | file | leaf |
|----|------|------|
| `tc_vibe_afifo` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_afifo.py` | `vibe_afifo` |
| `tc_vibe_sync2` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_sync2.py` | `vibe_sync2` |
| `tc_vibe_rst_sync` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_rst_sync.py` | `vibe_rst_sync` |

Official TP-CDC-001 is scored (if HAS) by `tc_afifo_afull10`, not `tc_vibe_afifo`.
Official TP-CDC-002 is scored (if HAS) by `tc_rst_sync`, not `tc_vibe_rst_sync`.
There is no official TP whose designated scorer is `tc_vibe_sync2`.

## Appendix — catalogued Python TCs not used as a TP scorer

Present in `catalog*.py` / tests but not the designated scorer for any official TP-0.3 ID (helpers, extra PCS/DLL leaves, suite umbrella). Not a defect by itself.

| TC |
|----|
| `tc_cfg0_fabric_no_special` |
| `tc_cfg3_fwd` |
| `tc_cfg4_fwd` |
| `tc_cfg5_fwd` |
| `tc_cfg7_fwd` |
| `tc_cfg9_fwd` |
| `tc_cfg_identity_guid_class` |
| `tc_cfg_reserved_fwd` |
| `tc_credit_1024_hole` |
| `tc_dll_tx_cfg0` |
| `tc_ebch16_lut` |
| `tc_gear_128_160` |
| `tc_gear_160_128` |
| `tc_lmsm_cc` |
| `tc_mgmt` |
| `tc_pcs_fec_bypass` |
| `tc_pcs_fec_emitb` |
| `tc_pcs_fec_t2` |
| `tc_pcs_rx_amctl` |
| `tc_pcs_rx_deskew` |
| `tc_pcs_rx_fec` |
| `tc_pcs_rx_unpack` |
| `tc_pcs_tx_g1_window` |
| `tc_pcs_tx_pack` |
| `tc_pkt_len_err_drop` |
| `tc_rs_dec_syndrome` |
| `tc_rst_port_device` |
| `tc_saf_ing` |
| `tc_vibe_gear_128_160` |
| `tc_voq_rd` |

## Appendix — still Icarus/SV-only (not Python-sim)

From `tb/vibe/pyuvm/README.md` (re-checked against `vibe_uvm/tests/`):

| name | Python? | note |
|------|---------|------|
| `tc_dll` | **yes** | full-stack wrapper; **TP-DLL-004** >32-flit split ≤16×≤32 |
| `tc_pcs_rx` (full stack) | **no** | no official TP maps only to this name; leaf PCS RX units exist |
| `tc_pcs_tx` (full stack) | **no** | no official TP maps only to this name; leaf PCS TX units exist |

---

Handoff: 验证 → 芯片开发PM. Audit only. Leave open. Do not merge as a gate.
