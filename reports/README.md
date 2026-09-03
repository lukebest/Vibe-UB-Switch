# reports/

Generated implementation reports. **Do not hand-write QoR numbers here.**

## `reports/lint/` (Verilator `--lint-only`)

Committed. Reproduce with `reports/lint/run_lint.sh`.  
Log: `vibe_ub_switch.lint.log`. Waivers: `WAIVERS.md` + `vibe_ub_switch.vlt`.  
Requirement: 0 `%Error-*`. Every `-Wall` warning class has a waiver note.

`reports/synth/` now holds a **methodology** block-level Yosys drop
(see `2026-09-03.md`). That is not tapeout and not a mapped top.

## `reports/synth/` (after Yosys / ORFS synth)

| File | Who writes it |
|------|----------------|
| `flow_info.txt` | `scripts/synth/yosys/run_synth.sh` — SHA, tool version, SDC, liberty path |
| `synth.log` | Yosys stdout/stderr |
| `stat.rpt` | Yosys `stat` / `stat -liberty` |
| `cells.rpt` | extracted cell/wire counts from `stat.rpt` |
| `area.rpt` | Sky130 area if liberty was used; otherwise `STATUS: generic_synth` |
| `hierarchy.rpt` | Yosys `hierarchy` |
| `timing_summary.rpt` | always `STATUS: not_run_by_yosys` (STA is a separate target) |

No liberty ⇒ no Sky130 area. That is not a license to invent one.

## `reports/signoff/` (after STA / later DRC-LVS)

| File | Who writes it |
|------|----------------|
| `sta.log` | OpenSTA stdout/stderr |
| `sta_wns_tns.rpt` | OpenSTA WNS/TNS header + pointers |
| `sta_checks.rpt` | `report_checks` (when OpenSTA ran) |
| `drc.rpt` | later KLayout/ORFS DRC; until then `STATUS: not_run` |
| `lvs.rpt` | later LVS; until then `STATUS: not_run` |

WNS/TNS on Sky130 against the spec SDC is **not** a closed timing
signoff. DRC/LVS counts must come from the tools. Any GDS under
`scripts/synth/work/` is a local artifact and is **not for foundry submit**.
