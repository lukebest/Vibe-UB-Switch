# Vibe-UB-Switch — risks

| Item | Value |
|------|--------|
| Snapshot date | **2026-09-08** (Asia/Shanghai) — after PR66 Lint ECO re-gate 2/3 |
| `origin/main` HEAD | `6cccdfff` (PR66 merge; Lint ECO re-gate 2/3, not nightly / not 4/3) |
| RTL freeze SHA | `982ddd0a` (`982ddd0a54cf19dbeb39cf8f8f523c4e26e593f6`) — Lint ECO head; **same role as old `1ed4d350` / earlier `32a7f5e0`**. PR62 `581d9d34` is merge-trace only. Old freeze `1ed4d350` is **VOID** as current freeze. |
| Companion | [`docs/STATUS.md`](STATUS.md) |

Facts only. After PR66 (`6cccdfff`, Lint ECO re-gate **2/3** — **not** a 4/3 / **not** nightly; `982ddd0a...main` rtl/ file list **empty**). **No WNS, TNS, or slack numbers** — OpenSTA was not run; [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep` (PLAN is historical proposal; E is path **B**; F is **F1**; not signoff); [`reports/synth/timing_summary.rpt`](../reports/synth/timing_summary.rpt) is `STATUS: not_run`. Coverage for the Lint ECO DUT is the committed 2/3 report: [`reports/regress/2026-09-08-lint-eco-2of3.md`](../reports/regress/2026-09-08-lint-eco-2of3.md) — **124/124**, LINE **715/745 = 96.0%**, functional **159/159**, **0 fail**. 1/3 remains [`reports/regress/2026-09-08-lint-eco-1of3.md`](../reports/regress/2026-09-08-lint-eco-1of3.md). Old CR-B series vs `1ed4d350` remains **VOID**.

---

## Top risks

| # | Risk | Owner | Status |
|---|------|--------|--------|
| 1 | **No mapped top / no STA / Sky130 × 1.25 GHz.** Top `vibe_ub_switch` was not mapped (full-chip slang elaborate OOM / unroll; Verilog frontend cannot parse unpacked-array ports on `vibe_fabric`). OpenSTA not installed / not run. Sky130 HD **cannot close** FS `clk_fab` 1.25 GHz. That is a **process / node risk**, not a missing signoff file. Path **B** (2026-09-05): do **not** chase top-level map / STA on Sky130. | Impl + 芯片开发PM | **OPEN** — accepted under path B **hold**. Methodology QoR only ([`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md)). Not tapeout. |
| 2 | **`ovf_l` CDC-WARN.** `rtl/port/vibe_port.sv`: 1-cycle `rxclk` sticky/pulse OR-reduction of `ovf_l`, then 2-FF into `clk_fab` as `afifo_ovf`. No pulse stretcher / req-ack. A single-cycle overflow can be missed (1.25 GHz ↔ 922 MHz). Data path is AFIFO-protected. Lint ECO did **not** ECO this path (**F1** untouched). **Not a fake signoff gap.** **Not blocking** the Lint ECO re-gate. | Design + 芯片开发PM | **OPEN** — **F1** unchanged, non-blocking. Permanent frozen WARN/waiver. Prior nightly [`reports/cdc/2026-09-08.md`](../reports/cdc/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). Record: [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md). |
| 3 | **xbar LATCH × 2 + fabric UNOPTFLAT × 2.** Structural Verilator `-Wall` debt (xbar combo `req`/`win`; fabric ready/valid combo loops; SAF BLKSEQ) was the Lint ECO. Cleared on freeze `982ddd0a` ([`reports/lint/2026-09-08-eco.md`](../reports/lint/2026-09-08-eco.md): **LATCH=0**, **UNOPTFLAT=0**, **BLKSEQ=0**). Remaining unused/width classes stay waived in [`reports/lint/WAIVERS.md`](../reports/lint/WAIVERS.md). Not an ECO chase. | Design | **CLOSED** — Lint ECO landed (PR62; freeze `982ddd0a`; merge `581d9d34` is trace only). |
| 4 | **Missing STATUS / RISKS** (PM cannot see gates / debts in-repo). | Docs / 芯片开发PM | **CLOSED** — files exist on main (PR31 `a3c8a331`). |
| 5 | **Lint ECO re-gate.** Lint ECO **landed** at freeze `982ddd0a` (PR62 merge `581d9d34` is merge-trace only; Xia pin PR63). CR-B consecutive-green **3/3** vs `1ed4d350` is **VOID**. New series is at **2/3**: [`reports/regress/2026-09-08-lint-eco-2of3.md`](../reports/regress/2026-09-08-lint-eco-2of3.md) — **124/124**, LINE **715/745 = 96.0%**, functional **159/159**, **0 fail**. 1/3 remains [`reports/regress/2026-09-08-lint-eco-1of3.md`](../reports/regress/2026-09-08-lint-eco-1of3.md). **F1** untouched. Old consecutive greens **3/3** (2026-09-03 run1/2/3 vs `32a7f5e0`) remain **VOID**. This is **not** 4/3 and **not** nightly health. Chat PASS does **not** count. Remaining work is consecutive green **3/3**. | Verification + 芯片开发PM | **OPEN** — 2/3 landed. Remaining **3/3**. SPEC-0.2 naming frozen (PR50). Xia CHANGELOG/SPEC pin **done** (PR63, freeze `982ddd0a`). Record: [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md). |

---

## Pending human decisions

| ID | Decision | Why it is blocked | Default until decided |
|----|----------|-------------------|------------------------|
| **E** | **Signoff next-gate definition.** **DECIDED 2026-09-05 (Asia/Shanghai): path B.** Keep Sky130 scripts/docs only. Do not chase top-level map / STA. `reports/signoff/` stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. Path B **hold** after Lint ECO. RTL freeze pin `982ddd0a`. | Not blocked — Luke chose **B**. PLAN ([`reports/signoff/PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md)) stays historical. Record: [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). Methodology QoR is explicitly **not** tapeout; SPEC §16 says QoR is **not** a SPEC must | **Decided: B.** Do not run tapeout flow. Do not claim signoff. Do not invent WNS/TNS. Do not treat Sky130 1.25 GHz fail as a missing file. Do not chase mapped top / STA on this node. |
| **F** | **`ovf_l` disposition.** **DECIDED 2026-09-07 (Asia/Shanghai): F1.** Permanently record `ovf_l` CDC-WARN as frozen WARN/waiver. No ECO. No issue. Not a signoff hole. **Unchanged / non-blocking** for Lint ECO (ECO commit did not touch `ovf_l`). | Not blocked — Luke chose **F1**. Record: [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md). | **Decided: F1.** Permanent frozen WARN/waiver. Leave `ovf_l` as-is. Do not ECO. Do not open an issue. Do not call it a signoff hole. |
| **G** | **Interface naming.** **DECIDED 2026-09-08 (Asia/Shanghai): Option B.** Formal CR + full rename to `{src}_{dst}_{meaning}` (`dll` not `dl`). SPEC-0.2 naming **frozen** (PR50). Design **landed** (then-freeze `1ed4d350`; PR51 merge `777865f0` is trace only). Xia CHANGELOG/SPEC pin **done** (PR52 then; Lint ECO pin PR63). TB rename **landed** (PR54). Lint ECO **landed** (freeze `982ddd0a`; PR62 merge `581d9d34` is trace only). CR-B 3/3 vs `1ed4d350` is **VOID**. Verification restart in progress at **2/3**; remaining **3/3**. No functional width/protocol change. F1 (`ovf_l`) still stands — no ECO. | Not blocked on the decision. **Blocked on Verification 3/3 only.** Inventory: [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md). Record: [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md). | **Decided: B.** Design + Xia pin + TB rename + Lint ECO + 2/3 done. Remaining: consecutive green **3/3** vs DUT freeze `982ddd0a`; chat PASS does not count; not nightly / not 4/3. Path B still **NOT PASS**. |

No other human decisions are listed here. CFG6 payload packing remains **未知** (SPEC / register-map); that is a documented unknown, not a new risk row.

---

## What this file does not claim

- No chip area, utilization, or die size (block µm² in the synth report are stdcell-only / flattened artifacts).
- No Sky130 or any-node WNS/TNS/slack.
- No FPGA schedule (proto is deferred; see STATUS).
- No coverage / LINE / TP numbers beyond the committed Lint ECO 1/3 and 2/3 reports ([`reports/regress/2026-09-08-lint-eco-2of3.md`](../reports/regress/2026-09-08-lint-eco-2of3.md): **124/124**, LINE **715/745 = 96.0%**, functional **159/159**, **0 fail**; 1/3 remains [`reports/regress/2026-09-08-lint-eco-1of3.md`](../reports/regress/2026-09-08-lint-eco-1of3.md)).
- Old consecutive greens **3/3** (2026-09-03 vs `32a7f5e0`) are **VOID**. Old CR-B 3/3 vs `1ed4d350` is **VOID**. Do not count them. Do not count chat PASS. Do not count nightly health as 4/3 or as 3/3.
- Lint ECO **RTL has landed** at freeze `982ddd0a`. New series is **2/3**, remaining **3/3**, not a new 3/3. This file does **not** claim signoff.
- Do **not** treat PR62 merge `581d9d34` as the RTL freeze pin.
