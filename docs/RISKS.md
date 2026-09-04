# Vibe-UB-Switch — risks

| Item | Value |
|------|--------|
| Snapshot date | **2026-09-04 evening** (Asia/Shanghai) |
| `origin/main` HEAD | `b6904159` (PR32) |
| RTL freeze SHA | `32a7f5e0` — `rtl/` unchanged vs this SHA |
| Companion | [`docs/STATUS.md`](STATUS.md) |

Facts only. **No WNS, TNS, or slack numbers** — OpenSTA was not run; [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep` (PLAN is proposal only, not signoff); [`reports/synth/timing_summary.rpt`](../reports/synth/timing_summary.rpt) is `STATUS: not_run`.

---

## Top risks

| # | Risk | Owner | Status |
|---|------|--------|--------|
| 1 | **No mapped top / no STA / Sky130 × 1.25 GHz.** Top `vibe_ub_switch` was not mapped (full-chip slang elaborate OOM / unroll; Verilog frontend cannot parse unpacked-array ports on `vibe_fabric`). OpenSTA not installed / not run. Sky130 HD **cannot close** FS `clk_fab` 1.25 GHz. That is a **process / node risk**, not a missing signoff file. | Impl + 芯片开发PM | **OPEN** — methodology QoR only ([`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md)). Not tapeout. |
| 2 | **`ovf_l` CDC-WARN.** `rtl/port/vibe_port.sv:244`: 1-cycle `rxclk` sticky/pulse OR-reduction of `ovf_l`, then 2-FF into `clk_fab` as `afifo_ovf`. No pulse stretcher / req-ack. A single-cycle overflow can be missed (1.25 GHz ↔ 922 MHz). Data path is AFIFO-protected. Pre-existing at freeze; **not an ECO**; **not a fake signoff gap**. | Design + 芯片开发PM | **OPEN** — frozen. First baseline [`reports/cdc/2026-09-04.md`](../reports/cdc/2026-09-04.md). Pending human **decision F**. |
| 3 | **xbar LATCH × 2 + fabric UNOPTFLAT × 2.** Verilator `-Wall`: `vibe_xbar.sv` combo `req`/`win` not assigned on every path; `vibe_fabric` ready/valid combo loops (`x_in_v`, `xb_r`). Counts unchanged on 2026-09-04 (0 new keys). Waived in [`reports/lint/WAIVERS.md`](../reports/lint/WAIVERS.md). Pre-existing; RTL frozen. | Design | **OPEN** — known lint debt. Not an ECO under freeze. |
| 4 | **Missing STATUS / RISKS** (PM cannot see gates / debts in-repo). | Docs / 芯片开发PM | **CLOSED** — files exist on main (PR31 `a3c8a331`). |

---

## Pending human decisions

| ID | Decision | Why it is blocked | Default until decided |
|----|----------|-------------------|------------------------|
| **E** | **Signoff next-gate definition.** Path A / B / C from PLAN. What must exist for impl gate → PASS (mapped top? which PDK? STA tool? DRC/LVS?) | PLAN landed ([`reports/signoff/PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md)); path A/B/C still need Luke/PM **explicit** choice. Methodology QoR is explicitly **not** tapeout; SPEC §16 says QoR is **not** a SPEC must | Until chosen: do not run tapeout flow, do not claim signoff. Default suggestion remains path A (Sky130 100 MHz bring-up). Impl gate stays **NOT PASS**. Do not invent WNS/TNS. Do not treat Sky130 1.25 GHz fail as a missing file. |
| **F** | **`ovf_l` disposition.** Permanent waiver vs later ECO (pulse stretch / req-ack). | CDC-WARN recorded; RTL freeze SHA `32a7f5e0`; no issue opened | **OPEN** / frozen. Leave RTL as-is. Do not ECO. Do not call it a signoff hole. |

No other human decisions are listed here. CFG6 payload packing remains **未知** (SPEC / register-map); that is a documented unknown, not a new risk row.

---

## What this file does not claim

- No chip area, utilization, or die size (block µm² in the synth report are stdcell-only / flattened artifacts).
- No Sky130 or any-node WNS/TNS/slack.
- No FPGA schedule (proto is deferred; see STATUS).
- Nightly [`reports/regress/2026-09-04.md`](../reports/regress/2026-09-04.md) is post-gate health, **not** consecutive-green 4/3.
