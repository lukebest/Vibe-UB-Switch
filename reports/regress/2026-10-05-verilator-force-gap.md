# Verilator Force 缺口日间分析 — 2026-10-05

**这是日间分析笔记，不是新回归，不是 1/3，不是 4/3，不是签核。**
不要记成 **4/3**，也不要重开 3 次计数，也不要把本日算成新系列的 **1/3**。
**不是签核。**
**stock Icarus 连续全绿系列 STOPPED（Decision I）。** 2/3 **does not start**。
PR122 1/3 PASS 是历史记录，不是本日。
**Path B HOLD。** Freeze **UNFROZEN**。本日 **未** 重钉 freeze。
**Remaining tip-align: none。** 勿自造叶子。
**≠1/3 ≠4/3 ≠signoff。** **F1 `ovf_l` 未动。** 无 ECO。无新 GitHub issue。

本 PR **只新增本文件**。**未** 覆盖昨夜闸后健康
[`reports/regress/2026-10-05.md`](2026-10-05.md)（PR347；量测 checkout `39293e01`）。
**未** 改 `tb/` / `rtl/` / `include/` / `docs/SPEC.md` / `pycircuit/` / `Makefile` / checkers。
本 PR **不挑选修复、不改 testbench**。可选 TB 侧修法只列选项，**未实现**。

## Pin / tip

| Item | Value |
|------|--------|
| 分析写在 | `origin/main` HEAD `0a70480536b6c0b44ef1a10ecf533860b718da52`（与 assign 时 expected tip **相同**；Accept PR347 闸后夜间健康 + PR346 lint+CDC，reports-only） |
| 昨夜量测 checkout | `39293e0189c277bb50e7c6b6a851c41ff6dc8582`（PR345 lint+CDC；数字经 PR347 进 main） |
| 产品 DUT 叶子 | `42ad05ca59f8614c739d5f5cb98100e2d0253216`（stage-87 `vibe_rst_ctl` tip-align） |
| `git diff 42ad05ca...HEAD -- rtl/` | **EMPTY** |
| `git diff 42ad05ca...HEAD -- include/` | **EMPTY** |
| Freeze | **UNFROZEN**。历史 pin `302ac943` **VOID as current**。本日 **未** 重钉 |
| Path B | **HOLD** |
| Remaining tip-align | **none**（勿自造叶子） |
| Open draft | 写本笔记时 `gh`/GitHub open PR = **none**。**未** overlay 任何 draft |
| 本日是否重跑全回归 | **否**。机制可由已合入报告 + TB 源码 + wrap 叶子对照命名，未改源码去“做绿” |

main **未** 相对 expected tip `0a704805` 前进。产品叶子仍是 `42ad05ca`。

## 本题范围

primary uvm-python 门 `make -C tb/vibe sim`（`Makefile` `SIM ?= verilator`）上
已知的 4 条 Verilator Force **TOOL** fail：

- `tc_port_smoke`
- `tc_nw_pkt_to_pma_tx`
- `tc_nw_pkt_pma_loopback`
- `tc_top_smoke`

昨夜 [`2026-10-05.md`](2026-10-05.md) 在 tip `39293e01` 上量到：
Verilator **PASS 198 / FAIL 4，exit 2**；
`make -C tb/vibe sim SIM=icarus` **203/0**（loopback **100/100**）；
stock `sim-icarus` **124/124**。
本日不重跑，不改这些数字。

## 源文件原话（先引，再判断）

PR119 / README 的 Force 说法当作 **非绑定假说**。下面只引原文，本日结论另写。

### `tb/vibe/pyuvm/README.md`（Gate status）

> Icarus (`SIM=icarus`) is the complete no-xvlog gate. Verilator is the
> fabric/unit baseline (`--timing`); port/top hierarchical `Force` of LMSM
> lock does not take effect under Verilator 5.020 + cocotb 1.9.2 VPI, so
> those two stay Icarus.

同文件表：

| Bucket | Icarus | Verilator |
|--------|--------|-----------|
| `port` (smoke / TX / 100-pkt loopback) | PASS 100/100 | compile OK; LMSM Force bring-up does not reach ACTIVE |
| `top` (`tc_top_smoke`) | PASS | not scored (same Force path) |

README **没有** 写 `AttributeError` / `u_peer` 缺 `u_lmsm`。
它把 port 与 top 都归到同一条 Force 路径，并写明 Verilator 上 **not scored**。

### PR119（https://github.com/lukebest/Vibe-UB-Switch/pull/119）

PR 正文 vs old 124-bucket 表：

> `port` smoke / `tc_nw_pkt_to_pma_tx` / 100-pkt loopback | **PASS** (loopback **100/100**) | elaborates after PCS input-default strip; LMSM `Force` does **not** reach ACTIVE — not scored
>
> `top` (`tc_top_smoke`) | **PASS** | not scored (same Force path)

工具钉：Icarus 12.0 + cocotb 1.9.2 + uvm-python 0.4.0；Verilator 5.020 `--timing`。
PR119 **没有** 引用 `u_peer contains no object named u_lmsm`。
它把 4 条里的 port×3 + top 都写成 Verilator **not scored**，Icarus **PASS**。

### 昨夜闸后健康 [`2026-10-05.md`](2026-10-05.md)（量测 `39293e01`）

命令摘要：

> FAIL tc_port_smoke / tc_nw_pkt_to_pma_tx / tc_nw_pkt_pma_loopback / tc_top_smoke
> TOTAL_PASS_LINES=198 TOTAL_FAIL_LINES=4
> 失败原因：LMSM/DLL did not reach ACTIVE（Force am_locked）；top: u_peer 无 u_lmsm
> = PR119 已记录的 Verilator TOOL，不是 DUT

失败列表原文：

> 现象：`LMSM/DLL did not reach ACTIVE/NRM`（stimulus = `lmsm_go` +
> `Force am_locked=1111`）；`tc_nw_pkt_to_pma_tx` / `tc_nw_pkt_pma_loopback`
> 为 `stimulus : link bring-up` / `actual : 0`；top 另有
> `AttributeError: u_peer contains no object named u_lmsm`。
> **TOOL** — PR119 / `tb/vibe/pyuvm/README.md` 已写明：Verilator 5.020 +
> cocotb 1.9.2 VPI 下 hierarchical `Force` 不进 ACTIVE；port/top **not scored**。
> 同 4 条在 `SIM=icarus` **PASS**（loopback **100/100**），stock Icarus 亦 **PASS**。
> **不是 DUT mismatch。不因此开 issue。**

同夜 Icarus complete：`SIM_UVM_ICARUS_EXIT=0`，`TOTAL_PASS_LINES=203` / `TOTAL_FAIL_LINES=0`，
`tc_port_smoke PASS`；`tc_nw_pkt_pma_loopback PASS 100/100`；`tc_top_smoke PASS`。
stock Icarus：`tc_port_smoke PASS`；`tc_nw_pkt_pma_loopback` `tx_n=100 rx_n=100`；
`tc_top_smoke PASS`。

### TB 源码（本日只读，未改）

`tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py` `VibePortBase.bringup_link`：

```text
hier(d, "u_p.u_lmsm.am_locked").value = Force(0xF)
hier(d, "u_p.u_lmsm.lid_bad").value = Force(0)
… lmsm_go 脉冲 …
等最多 64 拍 u_p.link_ready && status_up
再 Force u_p.u_dll.u_crd.cells / u_p.u_lmsm.st=9
```

三条 port TC 都走同一 `bringup_link`。失败时 **尚未** 打 GOLDEN 包：

- `tc_port_smoke` expected：`link_ready=1 status_up=1`；actual：`LMSM/DLL did not reach ACTIVE/NRM`
- `tc_nw_pkt_to_pma_tx` / `tc_nw_pkt_pma_loopback` expected：`link_ready`；actual：`0`；stimulus：`link bring-up`

`tb/vibe/pyuvm/vibe_uvm/tests/switch_tests.py` `tc_top_smoke` 在 CNA 写完后立刻：

```text
hier(d, "u_peer.u_lmsm.am_locked") 等路径 .value = Force(0xF)
```

`hdl.py` 的 `hier()` 用 `getattr` 走点路径。`u_peer` 上没有 `u_lmsm` 时，
这里会在 `tb_fail` 之前抛 `AttributeError`，与昨夜原文一致。

对照：Decision I wrap 叶子 **故意不用** 这条 Force。
`unit_lmsm_wrap.py` 写：

> Icarus exposes u_lmsm; Verilator 5.020 VPI may not.

`unit_port_wrap.py` / `unit_ub_switch_wrap.py`：**Prefer observe over Force** /
**without Force**。昨夜这三条 wrap 在 Verilator **PASS**
（≠ `tc_port_smoke` / ≠ `tc_top_smoke`）。

## 本日结论（非绑定）

我同意把这 4 条记成 **TOOL，不是 DUT 红**。依据不是“PR119 说过”，而是：

1. **同一产品叶子、同一套 checker**，uvm-python Icarus 与 stock Icarus 已 PASS
   （昨夜实测；loopback 100/100）。DUT 在能 Force / 能看见层次的仿真器上走通 PMA 环回与 G1 irq。
2. Verilator 失败点在 **bring-up**，GOLDEN / irq 还没打。这不是 lane-pack / LPH / G1 对不上。
3. TB 刺激是层次 `Force am_locked=1111` + `lmsm_go`，再 Force `st=9` / credit cells。
   wrap 叶子改成 **只观察管脚、不 Force LMSM 内部** 后，同一 Verilator 5.020 上 **PASS**。
4. `tc_top_smoke` 另有 **VPI 层次缺失**：`u_peer` 没有 `u_lmsm`。这是工具句柄问题，不是 RTL 少实例。
5. 默认 `make sim` 仍跑这 4 条并 `exit=2`。README/PR119 的 “not scored” 是 **验收口径**，
   不是 Makefile 已经跳过。昨夜把 exit=2 记入报告、**不** 静默改 primary 命令——本日沿用。

仍非绑定的部分：本日 **没有** 在 Verilator 上 dump VPI 对象表，也没有单步看 Force 后
`am_locked` 读回值。因此“Force 静默不生效”与“层次根本不可写”对 port×3 还没在本日拆开。
现有证据更支持 **工具/VPI**，不支持 **DUT mismatch**：

- 若 DUT 在 Verilator `--timing` 下真坏，198 条里的 LMSM/PCS/DLL/port wrap 不该全绿，
  Icarus 同 checker 也不该绿。
- 若只是 64 拍不够，Icarus 用同一 64 拍就能 ACTIVE；更弱。

**不要** 把这 4 条当成新 DUT issue。**不要** 因此开 issue。**不要** ECO `rtl/`。
**不要** 动 F1 `ovf_l`。

## 四条 TC（中文）

共同前提：产品叶子 `42ad05ca`；`rtl/` / `include/` 相对 HEAD **EMPTY**。
Icarus 两侧昨夜已 PASS。分类 **TOOL** 的理由见上，每条只补本 TC 的 expected / actual。

### `tc_port_smoke`（TP-PHY-001）

| | |
|--|--|
| 刺激 | `bringup_link`：`lmsm_go` + `Force u_p.u_lmsm.am_locked=1111` / `lid_bad=0`，再 Force cells / `st=9`，然后打 GOLDEN_TX 并看 PMA 环回 |
| Verilator expected | `link_ready=1` 且 `status_up=1`，再 `nw_dll_data===GOLDEN_TX`，环回 `nw_fab_data===GOLDEN_TX` |
| Verilator actual | bring-up 失败：`LMSM/DLL did not reach ACTIVE/NRM`。GOLDEN / PMA 未跑到 |
| 为何 TOOL 不是 DUT | 失败在 Force 链接建立，不是 GOLDEN 比对。Icarus uvm-python 与 stock Icarus **PASS**。wrap `tc_vibe_port`（observe，不 Force ACTIVE）Verilator **PASS** |
| Icarus | uvm-python complete **PASS**；stock **PASS** |

### `tc_nw_pkt_to_pma_tx`（TP-PHY-011 / 018）

| | |
|--|--|
| 刺激 | 同一 `bringup_link`，再打 GOLDEN_TX，看 `pcs_pma_txdata` 非 0 |
| Verilator expected | `link_ready`；之后 PMA pack 非 0 |
| Verilator actual | `stimulus : link bring-up` / `actual : 0`（`u_p.u_lmsm`）。未到 PMA 计分 |
| 为何 TOOL 不是 DUT | 与 `tc_port_smoke` 同一 Force 路径、同一 bring-up 失败。Icarus 两侧 **PASS**。不是 DUT lane-pack 错 |
| Icarus | uvm-python complete **PASS**；stock **PASS** |

### `tc_nw_pkt_pma_loopback`（TP-PHY-012）

| | |
|--|--|
| 刺激 | `bringup_link(cells=512, hold_pend=True)`，再 100 个 unique SOP |
| Verilator expected | `link_ready`；然后 **100/100** 顺序回收 |
| Verilator actual | 同样死在 `link bring-up` / `actual : 0`。100 包未发出 |
| 为何 TOOL 不是 DUT | 失败在链接，不是 100 包比对。Icarus uvm-python **PASS 100/100**；stock `tx_n=100 rx_n=100`、`am_lock_end=1111`、`saw_fec_fail=0` |
| Icarus | uvm-python complete **PASS 100/100**；stock **PASS** |

### `tc_top_smoke`

| | |
|--|--|
| 刺激 | CNA=1 后 `Force u_peer.u_lmsm.am_locked` 与 DUT `g_port[0/1].u_port.u_lmsm.*`，`plgo` / cfg `lmsm_go`，再 Force cells / `st=9`，peer 打 RT=10，看 `irq_logic` |
| Verilator expected | peer `link_ready && status_up`，DUT port0 `link_up=1`，peer 接受 RT=10，`irq_logic=1` |
| Verilator actual | 昨夜另记 `AttributeError: u_peer contains no object named u_lmsm`（`hier()` 在 Force 时炸掉）。即使绕过这句，后续仍是同一条 Force ACTIVE 路径 |
| 为何 TOOL 不是 DUT | `u_peer` 在 RTL 里有 `u_lmsm`；缺的是 Verilator 5.020 VPI 句柄。Icarus 两侧 **PASS**（含 G1 `irq_logic`）。wrap `tc_vibe_ub_switch`（不 Force、不走 peer PMA）Verilator **PASS**，且 **不是** 本 TC |
| Icarus | uvm-python complete **PASS**；stock **PASS** |

## 可选修复（仅 TB / 工具；未实现）

本 PR **不挑选** 下列任何一项，也 **不改** testbench。只给芯片开发PM 看工作量。
全部 **禁止** 动 `rtl/` / `include/` / F1 `ovf_l`。

| 选项 | 工作量 | 要改什么 | 能做什么 / 不能做什么 |
|------|--------|----------|------------------------|
| A. Verilator 上对这 4 条 **skip / not-scored**，让默认 `make sim` exit 0 | **small** | `tb/vibe/pyuvm/run_gate.py`（以及如需要 `catalog.py` 的 port/top 列表）。README 口径已是 not scored | 只消 exit=2。**不** 让 Verilator 真正打 PMA 环回 / G1。验收仍应看 `SIM=icarus` |
| B. 接住 `AttributeError` / bring-up False，打成 TOOL skip 而不是 FAIL | **small** | `port_tests.py` / `switch_tests.py` 的 `tb_fail` 与 `hier()` 调用 | top 不再炸 Python。**不** 进 ACTIVE，**不** 打 GOLDEN |
| C. 把 `am_locked` / `lid_bad` / `st` / credit cells **拍到 cocotb wrapper 顶层网**，Force 顶层而不是 `u_p.u_lmsm.*` / `u_peer.u_lmsm.*` | **medium** | `tb/vibe/pyuvm/tb/` 里 port / switch wrapper `.v`，再改 `port_tests.py` / `switch_tests.py` 路径。同类先例：512b flatten、`tc_vibe_lmsm` wrap-local nets | 可能绕过 “`u_peer` 无 `u_lmsm`”。**不保证** Verilator Force 对拍出来的网生效（cov 已有 ASSIGNIN Force skip） |
| D. 丢掉 Force，改成 **管脚观察 bring-up**（`lmsm_go` + 等 PMA/PRBS 真 AM lock），对齐 wrap 叶子 | **medium** | `VibePortBase.bringup_link` 与 `tc_top_smoke` 前半。多半要加长超时、接真实 AMCTL/idle | 与 `tc_vibe_lmsm` / `tc_vibe_port` 同一哲学。风险：stock/pyuvm Icarus 用 Force 就是因为全路径 lock 慢或不稳；可能拖垮 Icarus 绿 |
| E. 升级 Verilator（及/或 cocotb），让层次 VPI Force 对嵌套实例生效 | **large** | 环境钉（现 Verilator **5.020**、cocotb **1.9.2**），不是 RTL。可能要动 venv pin | 若成功，4 条可在默认 `SIM=verilator` 计分。回归面大：`--timing`、其他 Force（DLL cells、LMSM unit）都要重验 |

没有 “只改一行就让 4 条在 Verilator 上计分” 的选项。
A/B 是记账；C/D 是 TB；E 是工具链。

## 本日明确不做

- **不** 挑选 A–E，**不** 改 testbench，**不** 改 Makefile。
- **不** 重跑 `make -C tb/vibe sim` / `sim SIM=icarus` / `sim-icarus` / `cov`。
- **不** 覆盖 `2026-10-05.md` 或任何已有报告。
- **不** 开 GitHub issue。**不** ECO。**不** 动 F1 `ovf_l`。
- **不** 重钉 freeze。**不** 自造 tip-align 叶子。
- **不** 把本笔记算成新回归 / 1/3 / 4/3 / 签核。
- stock Icarus 连续全绿保持 **STOPPED**。Path B 保持 **HOLD**。

## 验收口径

**≠1/3 ≠4/3 ≠signoff。**

本文件是给芯片开发PM 的日间分析。聊天 PASS 不算验收。
进仓后 PM 即时验。Handoff: 验证 → 芯片开发PM。Leave merge for PM。
