# Vibe-UB-Switch — project status

| Item | Value |
|------|--------|
| Project | Vibe-UB-Switch |
| Snapshot date | **2026-09-04 evening** (Asia/Shanghai) |
| `origin/main` HEAD | `b6904159` — Merge PR32: docs(signoff) PLAN-2026-09-04 |
| RTL freeze SHA | `32a7f5e0` (`32a7f5e0c3f04762aa27dae73b000e55773195da`) |
| `git diff 32a7f5e0 -- rtl/` | **empty** — no `rtl/` functional diff vs freeze SHA (docs/reports only after PR30) |
| SPEC | **SPEC-0.1** — status **已冻结** (PR28, 2026-09-03, human approved; aligned RTL `32a7f5e0`) |
| FPGA / proto | **Deferred** — no FPGA tree, no board bring-up in this repo |

This file is an in-repo snapshot for 芯片开发PM. Numbers below are copied from committed reports. **No WNS/TNS/slack is stated** because none exists in-repo.

Earlier the same day: PR31 (STATUS/RISKS) landed at `a3c8a331`. This evening snapshot follows PR32.

---

## 1. Four gates

| Gate | Result | Evidence |
|------|--------|----------|
| SPEC freeze | **PASS** | [`docs/SPEC.md`](SPEC.md) header / intro / §18: **已冻结**, 2026-09-03, RTL `32a7f5e0`. PR28. |
| Lint | **PASS** | [`reports/lint/2026-09-04.md`](../reports/lint/2026-09-04.md): **0** `%Error-*`, **0** new `file:line:rule` keys vs prior committed log. DUT `32a7f5e0`. |
| Verification (consecutive green) | **PASS — 3/3 CLOSED** (2026-09-03) | [`reports/regress/2026-09-03.md`](../reports/regress/2026-09-03.md) / [`-run2.md`](../reports/regress/2026-09-03-run2.md) / [`-run3.md`](../reports/regress/2026-09-03-run3.md). Do **not** count nightly health as 4/3. |
| Impl signoff | **NOT PASS** | [`reports/signoff/`](../reports/signoff/) now has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep`. PLAN is **proposal only**, not signoff. Methodology QoR still [`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md) — **no top netlist**, **no WNS/TNS**. |

Post-gate nightly health (not a new consecutive-green series): [`reports/regress/2026-09-04.md`](../reports/regress/2026-09-04.md) — **PASS**. LINE **708/737 = 96.1%**; functional **159 TP 100%** (9 HOLE = SPEC §非目标). Explicitly **not** a 4/3 count.

FPGA is **not** a fifth gate. It is deferred.

---

## 2. Module × stage

Legend: **done** = locked / present at freeze SHA; **PASS** = committed gate or health check; **debt** = known, waived or frozen, not an ECO; **not started** / **NOT PASS** / **deferred** as written.

| Module | Spec | RTL | DV | Impl | Proto |
|--------|------|-----|----|------|-------|
| top (`vibe_ub_switch`) | SPEC-0.1 **已冻结**; AS-0.1 | Frozen `32a7f5e0` | `tc_top_smoke` 1/1; 3/3 CLOSED; nightly health PASS | **NOT PASS** — top not mapped (slang OOM / not invoked) | FPGA **deferred** |
| port / PMA / AFIFO | SPEC §15 + AS §3–5 | Frozen (`vibe_port`, `vibe_pma_bnd`, `vibe_afifo`) | Covered by suite/units; CDC data path through AFIFO | Leaf QoR mapped (`pma_bnd`, `afifo`, gears). Not a chip netlist | FPGA **deferred** |
| DLL / NW | SPEC §2 + AS §4 | Frozen (`vibe_dll*`, `vibe_nw_adapt`) | Covered by suite/units; LINE waivers in `COVERAGE_HOLES.md` | Leaf QoR mapped; `vibe_dll_retry_buf` flattened `$mem` artifact | FPGA **deferred** |
| PCS / LMSM | SPEC §15 + AS §4–5 | Frozen (`vibe_pcs_*`, `vibe_lmsm`) | Covered; LMSM `tmr_load` TOOL waiver | Leaf QoR mapped (RS left as written) | FPGA **deferred** |
| fabric / xbar / mgmt | SPEC §2 + AS §4 | Frozen | Suite 27/27; fabric G1/routing TPs | **NOT mapped**: xbar unroll, fabric/mgmt slang fail, `voq_egr` timeout. Lint debt: xbar **LATCH×2**, fabric **UNOPTFLAT×2** | FPGA **deferred** |
| CFG / headers | SPEC + register-map + RDL | Frozen (`vibe_cfg_space`, `include/vibe_ub_switch_regs.h`) | PR22/PR25 4-bit + RW1C checkers on main | `vibe_cfg_space` Yosys `proc_dff` FAIL — tool, RTL not rewritten | FPGA **deferred** |
| CDC | AS CDC + SPEC clocks | Frozen (`vibe_sync2`, `vibe_afifo`, `vibe_rst_sync`; gears not CDC) | First structural baseline [`reports/cdc/2026-09-04.md`](../reports/cdc/2026-09-04.md): 0 CDC-ERROR; **CDC-WARN** `vibe_port.sv:244` `ovf_l` | CDC leaves mapped. WARN is frozen, not ECO | FPGA **deferred** |
| Signoff package | SPEC §16: QoR is **not** a SPEC must | N/A (no RTL ECO for signoff) | N/A | **NOT PASS** — PLAN is proposal only; OpenSTA **not run**; no `sta_wns_tns.rpt` | FPGA **deferred** |

---

## 3. Open issues / PRs

| Item | Count | As of |
|------|------:|--------|
| Open GitHub issues | **0** | 2026-09-04 evening, `lukebest/Vibe-UB-Switch` |
| Closed GitHub issues | **0** | same |
| Open GitHub PRs | **0** | same (`origin/main`) |

No issue was opened from lint, CDC, or nightly health. Known debts stay in [`docs/RISKS.md`](RISKS.md), not as fake signoff gaps.

---

## 4. Next actions

1. **Luke / PM choose path A/B/C** — from [`reports/signoff/PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md). Human **decision E**. PLAN landed; until a path is chosen: do not run tapeout flow, do not claim signoff. Default suggestion remains path A (Sky130 100 MHz bring-up). Impl gate stays **NOT PASS**.
2. **Freeze watch** — keep `git diff 32a7f5e0 -- rtl/` empty. Interface / function change after SPEC-0.1 **已冻结** needs a change request.
3. **`ovf_l` stays decision F** — frozen CDC-WARN; no ECO; not a fake signoff gap.

Do not reopen consecutive-green as 4/3. Do not hand-write WNS/TNS.
