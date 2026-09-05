# Vibe-UB-Switch — risks

| Item | Value |
|------|--------|
| Snapshot date | **2026-09-05** (Asia/Shanghai) |
| `origin/main` HEAD | `da76d8da` (PR35) |
| RTL freeze SHA | `32a7f5e0` — `rtl/` unchanged vs this SHA |
| Companion | [`docs/STATUS.md`](STATUS.md) |

Facts only. **No WNS, TNS, or slack numbers** — OpenSTA was not run; [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep` (PLAN is historical proposal; decision is path **B**; not signoff); [`reports/synth/timing_summary.rpt`](../reports/synth/timing_summary.rpt) is `STATUS: not_run`.

---

## Top risks

| # | Risk | Owner | Status |
|---|------|--------|--------|
| 1 | **No mapped top / no STA / Sky130 × 1.25 GHz.** Top `vibe_ub_switch` was not mapped (full-chip slang elaborate OOM / unroll; Verilog frontend cannot parse unpacked-array ports on `vibe_fabric`). OpenSTA not installed / not run. Sky130 HD **cannot close** FS `clk_fab` 1.25 GHz. That is a **process / node risk**, not a missing signoff file. Path **B** (2026-09-05): do **not** chase top-level map / STA on Sky130. | Impl + 芯片开发PM | **OPEN** — accepted under path B. Methodology QoR only ([`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md)). Not tapeout. |
| 2 | **`ovf_l` CDC-WARN.** `rtl/port/vibe_port.sv:244`: 1-cycle `rxclk` sticky/pulse OR-reduction of `ovf_l`, then 2-FF into `clk_fab` as `afifo_ovf`. No pulse stretcher / req-ack. A single-cycle overflow can be missed (1.25 GHz ↔ 922 MHz). Data path is AFIFO-protected. Pre-existing at freeze; **not an ECO**; **not a fake signoff gap**. | Design + 芯片开发PM | **OPEN** — frozen. Nightly [`reports/cdc/2026-09-05.md`](../reports/cdc/2026-09-05.md) (unchanged vs 2026-09-04 baseline). Pending human **decision F**. |
| 3 | **xbar LATCH × 2 + fabric UNOPTFLAT × 2.** Verilator `-Wall`: `vibe_xbar.sv` combo `req`/`win` not assigned on every path; `vibe_fabric` ready/valid combo loops (`x_in_v`, `xb_r`). Counts unchanged on 2026-09-05 (0 new keys). Waived in [`reports/lint/WAIVERS.md`](../reports/lint/WAIVERS.md). Pre-existing; RTL frozen. | Design | **OPEN** — known lint debt. Not an ECO under freeze. |
| 4 | **Missing STATUS / RISKS** (PM cannot see gates / debts in-repo). | Docs / 芯片开发PM | **CLOSED** — files exist on main (PR31 `a3c8a331`). |

---

## Pending human decisions

| ID | Decision | Why it is blocked | Default until decided |
|----|----------|-------------------|------------------------|
| **E** | **Signoff next-gate definition.** **DECIDED 2026-09-05 (Asia/Shanghai): path B.** Keep Sky130 scripts/docs only. Do not chase top-level map / STA. `reports/signoff/` stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. RTL freeze still `32a7f5e0`. | Not blocked — Luke chose **B**. PLAN ([`reports/signoff/PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md)) stays historical. Record: [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). Methodology QoR is explicitly **not** tapeout; SPEC §16 says QoR is **not** a SPEC must | **Decided: B.** Do not run tapeout flow. Do not claim signoff. Do not invent WNS/TNS. Do not treat Sky130 1.25 GHz fail as a missing file. Do not chase mapped top / STA on this node. |
| **F** | **`ovf_l` disposition.** Permanent waiver vs later ECO (pulse stretch / req-ack). | CDC-WARN recorded; RTL freeze SHA `32a7f5e0`; no issue opened | **OPEN** / frozen. Leave RTL as-is. Do not ECO. Do not call it a signoff hole. |

No other human decisions are listed here. CFG6 payload packing remains **未知** (SPEC / register-map); that is a documented unknown, not a new risk row.

---

## What this file does not claim

- No chip area, utilization, or die size (block µm² in the synth report are stdcell-only / flattened artifacts).
- No Sky130 or any-node WNS/TNS/slack.
- No FPGA schedule (proto is deferred; see STATUS).
- Nightly [`reports/regress/2026-09-05.md`](../reports/regress/2026-09-05.md) is post-gate health, **not** consecutive-green 4/3.
