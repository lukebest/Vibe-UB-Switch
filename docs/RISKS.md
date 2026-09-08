# Vibe-UB-Switch — risks

| Item | Value |
|------|--------|
| Snapshot date | **2026-09-08** (Asia/Shanghai) |
| `origin/main` HEAD | `3fc359b8` (PR58 merge) |
| RTL freeze SHA | `1ed4d350` (`1ed4d35006848e6275e93d9bd2fc4e7f7af348f1`) — rename head; **same role as old `32a7f5e0`**. PR51 `777865f0` is merge-trace only. Old freeze `32a7f5e0` is **VOID**. |
| Companion | [`docs/STATUS.md`](STATUS.md) |

Facts only. **No WNS, TNS, or slack numbers** — OpenSTA was not run; [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep` (PLAN is historical proposal; E is path **B**; F is **F1**; not signoff); [`reports/synth/timing_summary.rpt`](../reports/synth/timing_summary.rpt) is `STATUS: not_run`. Coverage for the renamed DUT is the committed 3/3 report: [`reports/regress/2026-09-08-crb-3of3.md`](../reports/regress/2026-09-08-crb-3of3.md) — **124/124**, LINE **708/737 = 96.1%**, functional **159/159**, **0 fail**. 1/3 remains [`reports/regress/2026-09-08-crb-1of3.md`](../reports/regress/2026-09-08-crb-1of3.md). 2/3 remains [`reports/regress/2026-09-08-crb-2of3.md`](../reports/regress/2026-09-08-crb-2of3.md).

---

## Top risks

| # | Risk | Owner | Status |
|---|------|--------|--------|
| 1 | **No mapped top / no STA / Sky130 × 1.25 GHz.** Top `vibe_ub_switch` was not mapped (full-chip slang elaborate OOM / unroll; Verilog frontend cannot parse unpacked-array ports on `vibe_fabric`). OpenSTA not installed / not run. Sky130 HD **cannot close** FS `clk_fab` 1.25 GHz. That is a **process / node risk**, not a missing signoff file. Path **B** (2026-09-05): do **not** chase top-level map / STA on Sky130. | Impl + 芯片开发PM | **OPEN** — accepted under path B **hold**. Methodology QoR only ([`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md)). Not tapeout. |
| 2 | **`ovf_l` CDC-WARN.** `rtl/port/vibe_port.sv`: 1-cycle `rxclk` sticky/pulse OR-reduction of `ovf_l`, then 2-FF into `clk_fab` as `afifo_ovf`. No pulse stretcher / req-ack. A single-cycle overflow can be missed (1.25 GHz ↔ 922 MHz). Data path is AFIFO-protected. CR-B did **not** ECO this path. **Not a fake signoff gap.** **Not blocking** the rename. | Design + 芯片开发PM | **OPEN** — **F1** unchanged, non-blocking. Permanent frozen WARN/waiver. Prior nightly [`reports/cdc/2026-09-08.md`](../reports/cdc/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). Record: [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md). |
| 3 | **xbar LATCH × 2 + fabric UNOPTFLAT × 2.** Verilator `-Wall` debt recorded under the voided freeze (`vibe_xbar.sv` combo `req`/`win`; `vibe_fabric` ready/valid combo loops). Waived in [`reports/lint/WAIVERS.md`](../reports/lint/WAIVERS.md). Not re-measured on `1ed4d350`. Not an ECO. | Design | **OPEN** — known lint debt. Do not chase as CR-B fallout. |
| 4 | **Missing STATUS / RISKS** (PM cannot see gates / debts in-repo). | Docs / 芯片开发PM | **CLOSED** — files exist on main (PR31 `a3c8a331`). |
| 5 | **CR-B TB lag.** Design **landed** at freeze `1ed4d350` (`rtl/` only; ports `{src}_{dst}_{meaning}`). PR51 `777865f0` is merge-trace only. TB rename **landed** (PR54). New consecutive-green series is **CLOSED (3/3)**: [`reports/regress/2026-09-08-crb-3of3.md`](../reports/regress/2026-09-08-crb-3of3.md) — **124/124**, LINE **708/737 = 96.1%**, functional **159/159**, **0 fail**. Series: [`1of3`](../reports/regress/2026-09-08-crb-1of3.md) + [`2of3`](../reports/regress/2026-09-08-crb-2of3.md) + [`3of3`](../reports/regress/2026-09-08-crb-3of3.md) all vs freeze `1ed4d350`. Old consecutive greens **3/3** (2026-09-03 run1/2/3 vs `32a7f5e0`) remain **VOID**. This is **not** 4/3 of the old series and **not** nightly health. Chat PASS does **not** count. | Verification + 芯片开发PM | **CLOSED** — TB rename + new 3/3 complete. SPEC-0.2 naming frozen (PR50). Xia CHANGELOG/SPEC pin **done** (PR52, freeze `1ed4d350`). Record: [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md). |

---

## Pending human decisions

| ID | Decision | Why it is blocked | Default until decided |
|----|----------|-------------------|------------------------|
| **E** | **Signoff next-gate definition.** **DECIDED 2026-09-05 (Asia/Shanghai): path B.** Keep Sky130 scripts/docs only. Do not chase top-level map / STA. `reports/signoff/` stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. Path B **hold** after CR-B. RTL freeze pin `1ed4d350`. | Not blocked — Luke chose **B**. PLAN ([`reports/signoff/PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md)) stays historical. Record: [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). Methodology QoR is explicitly **not** tapeout; SPEC §16 says QoR is **not** a SPEC must | **Decided: B.** Do not run tapeout flow. Do not claim signoff. Do not invent WNS/TNS. Do not treat Sky130 1.25 GHz fail as a missing file. Do not chase mapped top / STA on this node. |
| **F** | **`ovf_l` disposition.** **DECIDED 2026-09-07 (Asia/Shanghai): F1.** Permanently record `ovf_l` CDC-WARN as frozen WARN/waiver. No ECO. No issue. Not a signoff hole. **Unchanged / non-blocking** for CR-B (rename commit did not ECO `ovf_l`). | Not blocked — Luke chose **F1**. Record: [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md). | **Decided: F1.** Permanent frozen WARN/waiver. Leave `ovf_l` as-is. Do not ECO. Do not open an issue. Do not call it a signoff hole. |
| **G** | **Interface naming.** **DECIDED 2026-09-08 (Asia/Shanghai): Option B.** Formal CR + full rename to `{src}_{dst}_{meaning}` (`dll` not `dl`). SPEC-0.2 naming **frozen** (PR50). Design **landed** (freeze `1ed4d350`; PR51 merge `777865f0` is trace only). Xia CHANGELOG/SPEC pin **done** (PR52). TB rename **landed** (PR54). New series **3/3 CLOSED** (1/3 + 2/3 + 3/3 vs freeze `1ed4d350`). No functional width/protocol change. F1 (`ovf_l`) still stands — no ECO. | Not blocked on the decision. **Verification landed.** Only Path B **hold** / impl signoff **NOT PASS** remains. Inventory: [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md). Record: [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md). | **Decided: B.** Design + Xia pin + TB rename + new 3/3 **CLOSED**. Old 2026-09-03 3/3 stays **VOID**. Chat PASS does not count; not nightly / not 4/3 of the old series. Path B still **NOT PASS**. |

No other human decisions are listed here. CFG6 payload packing remains **未知** (SPEC / register-map); that is a documented unknown, not a new risk row.

---

## What this file does not claim

- No chip area, utilization, or die size (block µm² in the synth report are stdcell-only / flattened artifacts).
- No Sky130 or any-node WNS/TNS/slack.
- No FPGA schedule (proto is deferred; see STATUS).
- No coverage / LINE / TP numbers beyond the committed 1/3, 2/3, and 3/3 reports ([`reports/regress/2026-09-08-crb-3of3.md`](../reports/regress/2026-09-08-crb-3of3.md): **124/124**, LINE **708/737 = 96.1%**, functional **159/159**, **0 fail**; 1/3 remains [`reports/regress/2026-09-08-crb-1of3.md`](../reports/regress/2026-09-08-crb-1of3.md); 2/3 remains [`reports/regress/2026-09-08-crb-2of3.md`](../reports/regress/2026-09-08-crb-2of3.md)).
- Old consecutive greens **3/3** (2026-09-03 vs `32a7f5e0`) are **VOID**. Do not count them. Do not count chat PASS. Do not count nightly health as 4/3 of the old series.
- CR-B Option B **RTL has landed** at freeze `1ed4d350`. TB rename **has landed** (PR54). New series is **3/3 CLOSED** / **COMPLETE**. This file does **not** claim signoff.
- Do **not** treat PR51 merge `777865f0` as the RTL freeze pin.
