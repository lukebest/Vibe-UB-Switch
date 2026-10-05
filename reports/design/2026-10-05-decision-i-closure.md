# Decision I 收口审计 — 2026-10-05

只读 git 量测。本文件是 reports-only。不重钉 freeze。不开 issue。不改 RTL。

## 1. 头表

| 项 | 量测 |
|----|------|
| 日期 | 2026-10-05（Asia/Shanghai） |
| 量测 main tip | `0a704805`（`0a70480536b6c0b44ef1a10ecf533860b718da52`）。`Accept PR347: 闸后夜间健康 2026-10-05 (reports-only)`。与任务预期 tip 一致：其父 `f4181fa` = Accept PR346 nightly lint+CDC 2026-10-05（reports-only），再上一笔产品叶子仍是 `42ad05ca`。 |
| 产品 RTL 叶子 | `42ad05ca`（`42ad05ca59f8614c739d5f5cb98100e2d0253216`）。`stage-87 tip-align: vibe_rst_ctl (Decision I UNFROZEN)`。提交正文写 last tip-align leaf / tip-align leaf wave done。 |
| `git diff 42ad05ca...HEAD -- rtl/ include/` | **EMPTY** |
| 书面 freeze | **UNFROZEN**（Decision I）。历史 pin `302ac943`（`302ac943c3737c288f3af6c4857bb3a9b1683a26`）**VOID as current**。依据：`docs/CHANGELOG.md` 最近 freeze 相关条（2026-09-30 CR-PMA-IDLE-PRBS31）仍写 UNFROZEN / Not a freeze re-pin；`docs/STATUS.md` 最后改动 `5dd4186` 写 UNFROZEN / VOID as current；本树 49 个 `rtl/**/*.sv` 头或脚均写 Decision I UNFROZEN。 |
| Path B | **HOLD**。同上书面来源；叶子提交正文写 Path B HOLD。 |
| 剩余 tip-align | **无**。叶子提交正文：last tip-align leaf；wave done。叶子之后 9 个 tip 提交只动 `tb/` / `docs/` / `reports/`，`rtl/` 无再提交。`docs/STATUS.md` 写 remaining tip-align: none。本仓库无另一份未完成 tip-align 队列。 |

量测时 `origin/main` = HEAD = `0a704805`。工作区干净。

`docs/STATUS.md` 仍把 HEAD 写成 `6ffcaf92`，相对本 tip **文档过期**；其中产品叶子 `42ad05ca` 仍与量测一致。

`rtl/**/*.sv` 计数：**49**（`find rtl -name '*.sv'`）。`include/` 仅 `include/vibe_ub_switch_regs.h`，相对叶子 EMPTY。

相对历史 pin：`git diff --shortstat 302ac943...HEAD -- rtl/` = `49 files changed, 391 insertions(+), 72 deletions(-)`。`-- include/` EMPTY。不把 MATCHES 或 NON-EMPTY 当成当前 freeze。

## 2. 全量 `rtl/**/*.sv`

每文件一行。来源只取文件自己写的 `GENERATED/HAND-FINISHED from …`；未写则记手写。PR 号只在该文件末提交说明里出现时抄入，不从 STATUS 补。

| 路径 | 模块 | 来源 | 最后改动该文件的提交 | tip-align |
|------|------|------|----------------------|-----------|
| `rtl/cdc/vibe_afifo.sv` | `vibe_afifo` | `pycircuit/cdc/vibe_afifo.py` | `7491081` (#264) — Decision I stage-52: vibe_afifo tip-align (CDC header/docs; body identical) (#264) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 4dc6ce77. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/cdc/vibe_gear_128_160.sv` | `vibe_gear_128_160` | `pycircuit/cdc/vibe_gear_128_160.py` | `f9bcfc1` (#268) — stage-54: vibe_gear_128_160 tip-align (header/docs only) (#268) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip a7a39eb3. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/cdc/vibe_gear_160_128.sv` | `vibe_gear_160_128` | `pycircuit/cdc/vibe_gear_160_128.py` | `22ac0e6` (#270) — stage-55: vibe_gear_160_128 tip-align (header/docs only) (#270) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip b0ee1880. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/cdc/vibe_rst_sync.sv` | `vibe_rst_sync` | `pycircuit/cdc/vibe_rst_sync.py` | `6a6252c` (#266) — Decision I stage-53: vibe_rst_sync tip-align (CDC header/docs; body identical) (#266) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 31647057. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/cdc/vibe_sync2.sv` | `vibe_sync2` | `pycircuit/cdc/vibe_sync2.py` | `35a3b65` (#262) — Decision I stage-51: vibe_sync2 tip-align (CDC header/docs) (#262) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 00647c9e. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_bcrc.sv` | `vibe_bcrc` | `pycircuit/dll/vibe_bcrc.py` | `1c08861` — stage-69: vibe_bcrc tip-align (header/docs) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 8ad2e351. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll.sv` | `vibe_dll` | `pycircuit/dll/vibe_dll.py` | `3930701` — stage-77 tip-align: vibe_dll wrap (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 4520441a. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_credit.sv` | `vibe_dll_credit` | `pycircuit/dll/vibe_dll_credit.py` | `cc4bcf6` (#302) — stage-70 tip-align vibe_dll_credit (LIVE_FREEZE) (#302) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 2ef95a43. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_retry_ack_sm.sv` | `vibe_dll_retry_ack_sm` | `pycircuit/dll/vibe_dll_retry_ack_sm.py` | `39a453f` (#308) — stage-73: vibe_dll_retry_ack_sm tip-align (header/docs) (#308) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 002d054d. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_retry_buf.sv` | `vibe_dll_retry_buf` | `pycircuit/dll/vibe_dll_retry_buf.py` | `73f1f70` — stage-74 tip-align: vibe_dll_retry_buf (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip eac12a8b. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_retry_req_sm.sv` | `vibe_dll_retry_req_sm` | `pycircuit/dll/vibe_dll_retry_req_sm.py` | `152bf1f` — stage-75 tip-align: vibe_dll_retry_req_sm (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 4f701bd1. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_rx.sv` | `vibe_dll_rx` | `pycircuit/dll/vibe_dll_rx.py` | `d921297` (#306) — stage-72: vibe_dll_rx tip-align (header/docs) (#306) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip e76523bf. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_sm.sv` | `vibe_dll_sm` | `pycircuit/dll/vibe_dll_sm.py` | `8f527a4` (#304) — stage-71 tip-align vibe_dll_sm (LIVE_FREEZE) (#304) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 551b6647. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/dll/vibe_dll_tx.sv` | `vibe_dll_tx` | `pycircuit/dll/vibe_dll_tx.py` | `20b3cfb` — stage-76 tip-align: vibe_dll_tx (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 780018d2. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_fabric.sv` | `vibe_fabric` | `pycircuit/fabric/vibe_fabric.py` | `deef6ad` — Decision I stage-46: vibe_fabric wrap (pyCircuit header/handfinish) | not a tip-align leaf。`git log --grep=tip-align -- rtl/fabric/vibe_fabric.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip 1ce79bfe. Decision I UNFROZEN. Path B hold.` |
| `rtl/fabric/vibe_fecn_mark.sv` | `vibe_fecn_mark` | `pycircuit/fabric/vibe_fecn_mark.py` | `b01dd07` (#323) — stage-80 tip-align: vibe_fecn_mark (#323) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 2c607719. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_port_sel.sv` | `vibe_port_sel` | `pycircuit/fabric/vibe_port_sel.py` | `d7a3322` (#329) — stage-83 vibe_port_sel tip-align (header/docs) (#329) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 637175ee. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_route_lu.sv` | `vibe_route_lu` | `pycircuit/fabric/vibe_route_lu.py` | `9a27b3b` (#327) — stage-82 vibe_route_lu tip-align (header/docs) (#327) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 5f082040. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_saf_ing.sv` | `vibe_saf_ing` | `pycircuit/fabric/vibe_saf_ing.py` | `a2bf040` — stage-85 tip-align: vibe_saf_ing (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 4c08425b. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_vl_rr.sv` | `vibe_vl_rr` | `pycircuit/fabric/vibe_vl_rr.py` | `c2a93d6` (#325) — stage-81 tip-align: vibe_vl_rr (#325) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 78000930. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_voq_egr.sv` | `vibe_voq_egr` | `pycircuit/fabric/vibe_voq_egr.py` | `8a14a21` — stage-84 tip-align: vibe_voq_egr (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 62f97739. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/fabric/vibe_xbar.sv` | `vibe_xbar` | `pycircuit/fabric/vibe_xbar.py` | `2436316` — stage-86 tip-align: vibe_xbar (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 0f453ed6. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/lmsm/vibe_lmsm.sv` | `vibe_lmsm` | `pycircuit/lmsm/vibe_lmsm.py` | `cd71b1d` — Decision I stage-49: vibe_lmsm wrap (pyCircuit header/handfinish) | not a tip-align leaf。`git log --grep=tip-align -- rtl/lmsm/vibe_lmsm.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip eb452e32 (RTL same as f8ed45ac). Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_cfg_space.sv` | `vibe_cfg_space` | `pycircuit/mgmt/vibe_cfg_space.py` | `2e62370` (#236) — stage-42: vibe_cfg_space pyCircuit (mgmt leaf) (#236) | not a tip-align leaf。`git log --grep=tip-align -- rtl/mgmt/vibe_cfg_space.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip 6f790520. Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_cna_ep.sv` | `vibe_cna_ep` | `pycircuit/mgmt/vibe_cna_ep.py` | `048bbbd` (#234) — stage-41: vibe_cna_ep pyCircuit (mgmt leaf) (#234) | not a tip-align leaf。`git log --grep=tip-align -- rtl/mgmt/vibe_cna_ep.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip cf64951b. Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_irq_agg.sv` | `vibe_irq_agg` | `pycircuit/mgmt/vibe_irq_agg.py` | `cf64951` (#233) — Decision I stage-40: vibe_irq_agg (pyCircuit leaf) (#233) | not a tip-align leaf。`git log --grep=tip-align -- rtl/mgmt/vibe_irq_agg.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip 7dbac272. Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_mgmt.sv` | `vibe_mgmt` | `pycircuit/mgmt/vibe_mgmt.py` | `1ce79bf` (#249) — Decision I stage-45: vibe_mgmt wrap (pyCircuit header/handfinish) (#249) | not a tip-align leaf。`git log --grep=tip-align -- rtl/mgmt/vibe_mgmt.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip 72e53573 / 7924cf44. Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_mgmt_byp.sv` | `vibe_mgmt_byp` | `pycircuit/mgmt/vibe_mgmt_byp.py` | `afcc216` (#230) — Decision I stage-39: vibe_mgmt_byp (pyCircuit leaf) (#230) | not a tip-align leaf。`git log --grep=tip-align -- rtl/mgmt/vibe_mgmt_byp.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip 23718d19. Decision I UNFROZEN. Path B hold.` |
| `rtl/mgmt/vibe_rst_ctl.sv` | `vibe_rst_ctl` | `pycircuit/mgmt/vibe_rst_ctl.py` | `42ad05c` — stage-87 tip-align: vibe_rst_ctl (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 2262044e. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/nw/vibe_icrc.sv` | `vibe_icrc` | `pycircuit/nw/vibe_icrc.py` | `ba992a4` — stage-78 tip-align: vibe_icrc (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 6dd82499. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/nw/vibe_nw_adapt.sv` | `vibe_nw_adapt` | `pycircuit/nw/vibe_nw_adapt.py` | `56c848b` — stage-79 tip-align: vibe_nw_adapt (Decision I UNFROZEN) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 8c0057ab. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_ebch16.sv` | `vibe_ebch16` | `pycircuit/pcs/vibe_ebch16.py` | `1eeeb21` (#274) — stage-57: vibe_ebch16 tip-align (header/docs only) (#274) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 80ff14af. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_rx.sv` | `vibe_pcs_rx` | `pycircuit/pcs/vibe_pcs_rx.py`（戳在 `endmodule` 后，不在文件头） | `f8ed45a` — Decision I stage-48: vibe_pcs_rx wrap (pyCircuit header/handfinish) | not a tip-align leaf。`git log --grep=tip-align -- rtl/pcs/vibe_pcs_rx.sv` 空。末提交是 wrap/leaf/CR。横幅 L224 `Product ports match tip 3365182d. Decision I UNFROZEN. Path B hold.` |
| `rtl/pcs/vibe_pcs_rx_amctl_lock.sv` | `vibe_pcs_rx_amctl_lock` | `pycircuit/pcs/vibe_pcs_rx_amctl_lock.py` | `2da59ef` — stage-65 vibe_pcs_rx_amctl_lock tip-align (header/docs) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip ed0f7c47. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_rx_deskew.sv` | `vibe_pcs_rx_deskew` | `pycircuit/pcs/vibe_pcs_rx_deskew.py` | `7e37f84` — stage-66: vibe_pcs_rx_deskew tip-align (header/docs) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 77f9a460. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_rx_fec.sv` | `vibe_pcs_rx_fec` | `pycircuit/pcs/vibe_pcs_rx_fec.py` | `ff6d5a9` — stage-68: vibe_pcs_rx_fec tip-align (header/docs) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip d3a3275b. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_rx_unpack.sv` | `vibe_pcs_rx_unpack` | `pycircuit/pcs/vibe_pcs_rx_unpack.py` | `262586e` — stage-67: vibe_pcs_rx_unpack tip-align (header/docs) | done。末提交即 tip-align。横幅 L3 `Product ports and behavior match tip 0c167477. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_scramble.sv` | `vibe_pcs_scramble` | `pycircuit/pcs/vibe_pcs_scramble.py` | `0941719` (#272) — stage-56: vibe_pcs_scramble tip-align (header/docs only) (#272) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip bc6839d8. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_tx.sv` | `vibe_pcs_tx` | `pycircuit/pcs/vibe_pcs_tx.py` | `3365182` — Decision I stage-47: vibe_pcs_tx wrap (pyCircuit header/handfinish) | not a tip-align leaf。`git log --grep=tip-align -- rtl/pcs/vibe_pcs_tx.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip deef6adc. Decision I UNFROZEN. Path B hold.` |
| `rtl/pcs/vibe_pcs_tx_amctl.sv` | `vibe_pcs_tx_amctl` | `pycircuit/pcs/vibe_pcs_tx_amctl.py` | `cba47f2` (#278) — stage-59: vibe_pcs_tx_amctl tip-align (header/docs only) (#278) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 963aab5d. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_tx_cw2beat.sv` | `vibe_pcs_tx_cw2beat` | `pycircuit/pcs/vibe_pcs_tx_cw2beat.py` | `d7194f5` (#276) — stage-58: vibe_pcs_tx_cw2beat tip-align (header/docs only) (#276) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 938f23f1. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_tx_fec.sv` | `vibe_pcs_tx_fec` | `pycircuit/pcs/vibe_pcs_tx_fec.py` | `38da155` — stage-63 vibe_pcs_tx_fec tip-align (header/docs) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 6fa0ff52. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_tx_g1.sv` | `vibe_pcs_tx_g1` | `pycircuit/pcs/vibe_pcs_tx_g1.py` | `fe4ecbe` (#280) — stage-60: vibe_pcs_tx_g1 tip-align (header/docs only) (#280) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip 6119e4db. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_pcs_tx_pack.sv` | `vibe_pcs_tx_pack` | `pycircuit/pcs/vibe_pcs_tx_pack.py` | `417b2d7` — stage-64 vibe_pcs_tx_pack tip-align (header/docs) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip ad3a7165. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_rs128_120_dec.sv` | `vibe_rs128_120_dec` | `pycircuit/pcs/vibe_rs128_120_dec.py` | `027dfe4` — stage-62 vibe_rs128_120_dec tip-align (header/docs) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip c1f7d49b. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pcs/vibe_rs128_120_enc.sv` | `vibe_rs128_120_enc` | `pycircuit/pcs/vibe_rs128_120_enc.py` | `5d92881` (#282) — stage-61: vibe_rs128_120_enc tip-align (header/docs only) (#282) | done。末提交即 tip-align。横幅 L4 `Product ports and behavior match tip b30e59fd. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.` |
| `rtl/pma/vibe_pma_bnd.sv` | `vibe_pma_bnd` | `pycircuit/pma/vibe_pma_bnd.py` | `7dbac27` (#231) — rtl: PMA pin-idle PRBS31 (CR-PMA-IDLE-PRBS31) (#231) | not a tip-align leaf。`git log --grep=tip-align -- rtl/pma/vibe_pma_bnd.sv` 空。末提交是 wrap/leaf/CR。横幅 L4 `Product ports match tip afcc2162. Decision I UNFROZEN. Path B hold.` |
| `rtl/port/vibe_port.sv` | `vibe_port` | `pycircuit/port/vibe_port.py` | `4b2eefe` (#260) — Decision I stage-50: vibe_port tip-align (header/docs) (#260) | done。末提交即 tip-align。横幅 L3 `Product ports match tip 4cff3a53 (RTL same as cd71b1d0). Decision I UNFROZEN. Path B hold.` |
| `rtl/top/vibe_ub_switch.sv` | `vibe_ub_switch` | `pycircuit/top/vibe_ub_switch.py` | `7924cf4` (#244) — Decision I stage-44: vibe_ub_switch wrap (pyCircuit header/handfinish) (#244) | not a tip-align leaf。`git log --grep=tip-align -- rtl/top/vibe_ub_switch.sv` 空。末提交是 wrap/leaf/CR。横幅 L3 `Product ports match tip cb644804 / 260dc6db. Decision I UNFROZEN. Path B hold.` |

tip-align = **done** 的 38 个：末提交说明含 tip-align。

tip-align = **not a tip-align leaf** 的 11 个（`git log --grep=tip-align -- <file>` 皆空，故不是排队中的未做叶子）：

- wrap（pyCircuit header/handfinish）：`vibe_ub_switch` `7924cf4`；`vibe_mgmt` `1ce79bf`；`vibe_fabric` `deef6ad`；`vibe_pcs_tx` `3365182`；`vibe_pcs_rx` `f8ed45a`；`vibe_lmsm` `cd71b1d`。
- mgmt 产品叶子（未再有 tip-align 提交）：`vibe_mgmt_byp` `afcc216`；`vibe_irq_agg` `cf64951`；`vibe_cna_ep` `048bbbd`；`vibe_cfg_space` `2e62370`。
- CR 改体、不是 tip-align：`vibe_pma_bnd` `7dbac27` CR-PMA-IDLE-PRBS31 (#231)。

本审计没有 unknown 行：每个文件都能从末提交说明或横幅定性。

## 3. 非 pyCircuit 生成模块（手写或其他）

**空。**

49/49 个 `rtl/**/*.sv` 都写了 `GENERATED/HAND-FINISHED from pycircuit/…`。没有文件头（或页脚）未写生成路径、需要记成手写的模块。

版式例外（仍算 pyCircuit 来源，不进本清单）：`rtl/pcs/vibe_pcs_rx.sv` 第 1 行是 `// AS-0.1 §6: …`（blame `984e3b9f`，2026-08-29 原注释），生成戳在 L222–227（blame `f8ed45ac` stage-48 wrap）。

## 4. 是否具备重钉 freeze 的条件

本审计使用的条件（任务给定，按本树量测）：

1. 产品 RTL 相对叶子稳定。
2. 无未合入的 RTL diff。
3. tip-align 队列为空。
4. 无待做 ECO。
5. 书面 freeze 仍是 UNFROZEN。

量测：

| 条件 | 结果 | 证据 |
|------|------|------|
| 1 产品 RTL vs 叶子 | 成立 | `git diff 42ad05ca...HEAD -- rtl/ include/` EMPTY |
| 2 无开放 RTL diff | 成立 | 同上 EMPTY。写本文件前工作区干净。写本文件前 `gh pr list --state open` 空、`gh issue list --state open` 空（本 draft 尚未开） |
| 3 tip-align 队列空 | 成立 | 见 §1「剩余 tip-align = 无」。11 个非 tip-align 文件是 wrap / 产品叶子 / CR，不是未做队列 |
| 4 无待做 ECO | 成立 | F1 `ovf_l` 仍是 CDC WARN，不是 ECO。`reports/cdc/2026-10-05.md`：CDC-WARN×1 = `vibe_port.sv:246`，`|ovf_l` 采样仍在 `:252`。blame：`:246`/`:252` = `984e3b9f`，`:238–241` = `6eedb84d`。Decision I / tip-align 未改该体。无 open issue |
| 5 书面仍 UNFROZEN | 成立 | CHANGELOG 2026-09-30、STATUS `5dd4186`、SV 头/脚均写 UNFROZEN；历史 pin `302ac943` VOID as current |

结论：就本树这五条，量测均为成立。是否重钉 freeze 是 Luke 的决定。本审计不重钉，也不开新的 1/3。

## 5. 明确不声称

- 不是 1/3。
- 不是 4/3。
- 不是签核。
- Path B **HOLD**。
- F1 `ovf_l` **未动**（仍 CDC WARN，不 ECO、不改 `vibe_port` 体）。
- stock Icarus 连续全绿系列 **STOPPED**（Decision I）。不把 PR122 历史 1/3 或其后健康报告续成新 1/3。
- 历史 pin `302ac943` 不是当前 freeze。

