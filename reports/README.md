# reports/

Generated implementation reports. **Do not hand-write QoR numbers here.**

Directories are tracked with `.gitkeep`. Files below are produced by
`make -C impl synth-smoke`, `synth`, `sta`, or a later ORFS run.

## `reports/synth/` (after Yosys / ORFS synth)

| File | Who writes it |
|------|----------------|
| `flow_info.txt` | `impl/yosys/run_synth.sh` — SHA, tool version, SDC, liberty path |
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
`impl/work/` is a local artifact and is **not for foundry submit**.
