# Vibe-UB-Switch — project status

| Item | Value |
|------|--------|
| Project | Vibe-UB-Switch |
| Snapshot date | **2026-09-08** (Asia/Shanghai) |
| `origin/main` HEAD | `473df7a4` — nightly lint+CDC 2026-09-08 / PR46 (`473df7a4e658ab435fbf0d4f9eb5d23c4b9817b8`) |
| RTL freeze SHA | `1ed4d350` (`1ed4d35006848e6275e93d9bd2fc4e7f7af348f1`) — CR-B ports; supersedes `32a7f5e0` for ports. Merge PR51 `777865f0` |
| `git diff 1ed4d350 -- rtl/` | **empty** vs new freeze (ports landed). Old `32a7f5e0` superseded for ports. |
| SPEC | **SPEC-0.1** — status **已冻结** (PR28, 2026-09-03, human approved; aligned RTL `32a7f5e0`) |
| FPGA / proto | **Deferred** — no FPGA tree, no board bring-up in this repo |

This file is an in-repo snapshot for 芯片开发PM. Numbers below are copied from committed reports. **No WNS/TNS/slack is stated** because none exists in-repo.

This snapshot follows PR46 (`473df7a4`, nightly lint+CDC 2026-09-08). Prior: PR45 health regress 2026-09-08 merged at `9a52f3e9`; PR44 evening STATUS was at `95f1f731` (that snapshot referenced HEAD `2e177e8d`). RTL freeze for ports is now `1ed4d350` (PR51 merge `777865f0`); old `32a7f5e0` superseded for ports. Decision **E** remains path **B**; decision **F** remains **F1**.

**CR-B RTL ports landed** at `1ed4d350` (PR51 merge `777865f0`). Luke chose Option B on 2026-09-08 Asia/Shanghai: `{src}_{dst}_{meaning}` (`dll` not `dl`). Formal record [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md); inventory [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md). 3/3 greens **voided**. F1 unchanged. SPEC functional body is not rewritten here.

---

## 1. Four gates

| Gate | Result | Evidence |
|------|--------|----------|
| SPEC freeze | **PASS** | [`docs/SPEC.md`](SPEC.md) header / intro / §18: **已冻结**, 2026-09-03, RTL `32a7f5e0`. PR28. |
| Lint | **PASS** | [`reports/lint/2026-09-08.md`](../reports/lint/2026-09-08.md): **0** `%Error-*`, **0** new `file:line:rule` keys vs 2026-09-07. DUT `32a7f5e0`. |
| Verification (consecutive green) | **PASS — 3/3 CLOSED** (2026-09-03) | [`reports/regress/2026-09-03.md`](../reports/regress/2026-09-03.md) / [`-run2.md`](../reports/regress/2026-09-03-run2.md) / [`-run3.md`](../reports/regress/2026-09-03-run3.md). Do **not** count nightly health as 4/3. |
| Impl signoff | **NOT PASS** | [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep`. Luke chose **path B** (2026-09-05) and **F1** (2026-09-07). PLAN stays historical. Directory stays PLAN + keepers. Methodology QoR still [`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md) — **no top netlist**, **no WNS/TNS**. Do not claim signoff. |

Post-gate nightly health (not a new consecutive-green series): [`reports/regress/2026-09-08.md`](../reports/regress/2026-09-08.md) — **PASS**. LINE **708/737 = 96.1%**; functional **159 TP 100%** (9 HOLE = SPEC §非目标). Explicitly **not** a 4/3 count.

FPGA is **not** a fifth gate. It is deferred.

---

## 2. Module × stage

Legend: **done** = locked / present at freeze SHA; **PASS** = committed gate or health check; **debt** = known, waived or frozen, not an ECO; **not started** / **NOT PASS** / **deferred** as written.

| Module | Spec | RTL | DV | Impl | Proto |
|--------|------|-----|----|------|-------|
| top (`vibe_ub_switch`) | SPEC-0.1 **已冻结**; AS-0.1 | Frozen `32a7f5e0` | `tc_top_smoke` 1/1; 3/3 CLOSED; nightly health PASS | **NOT PASS** — top not mapped (slang OOM / not invoked). Path B: do **not** chase top-level map / STA | FPGA **deferred** |
| port / PMA / AFIFO | SPEC §15 + AS §3–5 | Frozen (`vibe_port`, `vibe_pma_bnd`, `vibe_afifo`) | Covered by suite/units; CDC data path through AFIFO | Leaf QoR mapped (`pma_bnd`, `afifo`, gears). Not a chip netlist | FPGA **deferred** |
| DLL / NW | SPEC §2 + AS §4 | Frozen (`vibe_dll*`, `vibe_nw_adapt`) | Covered by suite/units; LINE waivers in `COVERAGE_HOLES.md` | Leaf QoR mapped; `vibe_dll_retry_buf` flattened `$mem` artifact | FPGA **deferred** |
| PCS / LMSM | SPEC §15 + AS §4–5 | Frozen (`vibe_pcs_*`, `vibe_lmsm`) | Covered; LMSM `tmr_load` TOOL waiver | Leaf QoR mapped (RS left as written) | FPGA **deferred** |
| fabric / xbar / mgmt | SPEC §2 + AS §4 | Frozen | Suite 27/27; fabric G1/routing TPs | **NOT mapped**: xbar unroll, fabric/mgmt slang fail, `voq_egr` timeout. Lint debt: xbar **LATCH×2**, fabric **UNOPTFLAT×2** | FPGA **deferred** |
| CFG / headers | SPEC + register-map + RDL | Frozen (`vibe_cfg_space`, `include/vibe_ub_switch_regs.h`) | PR22/PR25 4-bit + RW1C checkers on main | `vibe_cfg_space` Yosys `proc_dff` FAIL — tool, RTL not rewritten | FPGA **deferred** |
| CDC | AS CDC + SPEC clocks | Frozen (`vibe_sync2`, `vibe_afifo`, `vibe_rst_sync`; gears not CDC) | Nightly [`reports/cdc/2026-09-08.md`](../reports/cdc/2026-09-08.md): 0 CDC-ERROR; **CDC-WARN** `vibe_port.sv:244` `ovf_l` (unchanged vs 2026-09-07 / 2026-09-04 baseline). **F1** — permanent frozen WARN/waiver | CDC leaves mapped. WARN is permanent frozen waiver under **F1**; not ECO | FPGA **deferred** |
| Signoff package | SPEC §16: QoR is **not** a SPEC must | N/A (no RTL ECO for signoff) | N/A | **NOT PASS** — path **B** chosen; Sky130 scripts/docs only; OpenSTA **not run**; no `sta_wns_tns.rpt`; do not run tapeout flow | FPGA **deferred** |

---

## 3. Open issues / PRs

| Item | Count | As of |
|------|------:|--------|
| Open GitHub issues | **0** | 2026-09-08, `lukebest/Vibe-UB-Switch` |
| Closed GitHub issues | **0** | same |
| Open GitHub PRs | **0** | same (`origin/main` `473df7a4`) |

No issue was opened from lint, CDC, or nightly health. Known debts stay in [`docs/RISKS.md`](RISKS.md), not as fake signoff gaps.

---

## 4. Next actions

1. **Path B chosen** (Luke, 2026-09-05 Asia/Shanghai; human **decision E**). Keep Sky130 scripts/docs only. Do **not** chase top-level map / STA. [`reports/signoff/`](../reports/signoff/) stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. See [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). PLAN-2026-09-04 stays historical.
2. **Freeze watch** — new RTL freeze is `1ed4d350` (PR51 `777865f0`). Old `32a7f5e0` superseded for ports. Keep `git diff 1ed4d350 -- rtl/` empty except via CR. F1 unchanged. 3/3 greens voided.
3. **`ovf_l` decided F1** (Luke, 2026-09-07 Asia/Shanghai; human **decision F**). Permanent frozen CDC-WARN/waiver at `rtl/port/vibe_port.sv:244`. F1 unchanged (no ECO). No issue. Not a signoff hole. See [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md).
4. **CR-B RTL ports landed** at `1ed4d350` (merge `777865f0`). 3/3 voided; new series only after reports against `1ed4d350`. F1 unchanged. Verification re-gate still pending. No signoff claim. Path B still **NOT PASS**. See [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md).

Do not reopen consecutive-green as 4/3. Do not hand-write WNS/TNS.
