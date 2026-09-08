# Vibe-UB-Switch — project status

| Item | Value |
|------|--------|
| Project | Vibe-UB-Switch |
| Snapshot date | **2026-09-08** (Asia/Shanghai) — evening refresh after PR60 |
| `origin/main` HEAD | `34712f3d` — PR60 merge (`34712f3d1ec63d3c94cd213bcc9ccc110aa06fa3`) |
| RTL freeze SHA | `982ddd0a` (`982ddd0a54cf19dbeb39cf8f8f523c4e26e593f6`) — Lint ECO head; **same role as old `1ed4d350` / earlier `32a7f5e0`** |
| PR62 merge tip | `581d9d34` (`581d9d34c6f7e27f80bdbd46e648343af5e40780`) — **merge-trace only**, not the freeze pin |
| `982ddd0a...main` rtl/ | freeze pin is Lint ECO head `982ddd0a`. Old `1ed4d350` is **VOID** as current freeze. |
| SPEC | **SPEC-0.2 naming frozen** (PR50 `6214b081`; Xia pin PR52 / this Lint ECO pin). Functional body still SPEC-0.1 facts. CHANGELOG new RTL SHA is **`982ddd0a`**. |
| FPGA / proto | **Deferred** — no FPGA tree, no board bring-up in this repo |

This file is an in-repo snapshot for 芯片开发PM. Numbers below are copied from committed reports. **No WNS/TNS/slack is stated** because none exists in-repo. **No coverage numbers are invented** beyond [`reports/regress/2026-09-08-crb-3of3.md`](../reports/regress/2026-09-08-crb-3of3.md) (1/3 remains [`reports/regress/2026-09-08-crb-1of3.md`](../reports/regress/2026-09-08-crb-1of3.md); 2/3 remains [`reports/regress/2026-09-08-crb-2of3.md`](../reports/regress/2026-09-08-crb-2of3.md)).

This snapshot is an evening refresh after PR60 (`34712f3d`, tb/waves Overlay-B NW/DLL/PMA dump on loopback VCD — **not** a gate event; no `rtl/` change). Prior STATUS at PR59 (`3e71c71`) still said HEAD `3fc359b8` (PR58). Prior: PR58 3/3 at `3fc359b8`; PR57 STATUS/RISKS at `6d1c3db7`; PR56 2/3 at `df348f10`; PR55 STATUS/RISKS at `7ed93868`; PR54 TB rename / 1/3 at `1bef293e`; PR53 STATUS/RISKS at `87999cba`; PR52 Xia freeze pin `1ed4d350`; PR51 merge tip `777865f0` (CR-B RTL landed; merge-trace only); PR50 SPEC/AS names at `6214b081`. Decision **E** remains path **B**; decision **F** remains **F1**; decision **G** remains Option **B**. Verification has landed. Only Path B **hold** / impl signoff **NOT PASS** remains.

**Xia pin (Lint ECO):** freeze `1ed4d350` **broken** by PR62. New freeze `982ddd0a` (merge `581d9d34` is trace only). Naming / functional interfaces unchanged. **F1** unchanged. CR-B 3/3 **voided**; verification restarts 1/3. PM snapshot body below is otherwise unchanged.

**CR-B (iface rename) Design has landed. TB rename has landed.** Luke chose Option B on 2026-09-08 Asia/Shanghai: `{src}_{dst}_{meaning}` (`dll` not `dl`). Formal record [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md); inventory [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md). Ports landed at then-freeze `1ed4d350` (`rtl/` only on that commit). `tb/vibe` rename landed in PR54. Re-gate **3/3** vs `1ed4d350` is now **VOID** (Lint ECO). `ovf_l` stays **F1** (no ECO). This is **not** 4/3 of the old series and **not** nightly health. Chat PASS does not count. Remaining work is Path B **hold** / impl signoff **NOT PASS**, plus verification 1/3 vs `982ddd0a`.

---

## 1. Four gates

| Gate | Result | Evidence |
|------|--------|----------|
| SPEC freeze | **SPEC-0.2 naming frozen** | [`docs/SPEC.md`](SPEC.md) / AS product names landed PR50 (`6214b081`). Xia pinned Lint ECO freeze `982ddd0a` (merge `581d9d34` is trace only). Naming only; functional widths / protocol still SPEC-0.1 facts. |
| Lint | **not re-run vs new DUT** | [`reports/lint/2026-09-08.md`](../reports/lint/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). No committed lint vs freeze `1ed4d350`. Do not invent lint numbers. |
| Verification (consecutive green) | **VOIDED** — restart 1/3 | CR-B series vs `1ed4d350` is **VOID** after Lint ECO. Historical: [`1of3`](../reports/regress/2026-09-08-crb-1of3.md) + [`2of3`](../reports/regress/2026-09-08-crb-2of3.md) + [`3of3`](../reports/regress/2026-09-08-crb-3of3.md). Restart 1/3 against `982ddd0a`. Chat PASS does **not** count. |
| Impl signoff | **NOT PASS** | [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep`. Luke chose **path B** (2026-09-05) and **F1** (2026-09-07). Path B **hold**: Sky130 scripts/docs only. PLAN stays historical. Methodology QoR still [`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md) — **no top netlist**, **no WNS/TNS**. Do not claim signoff. FPGA **deferred**. |

FPGA is **not** a fifth gate. It is deferred.

---

## 2. Module × stage

Legend: **done** = locked / present at freeze SHA; **PASS** = committed gate or health check; **debt** = known, waived or frozen, not an ECO; **not started** / **NOT PASS** / **deferred** / **hold** as written.

Progress: **SPEC** = 0.2 naming frozen; **RTL** = Lint ECO freeze `982ddd0a` (CR-B names unchanged); **DV** = CR-B 3/3 **VOIDED**, restart 1/3; **impl** = path B hold; **proto** = deferred.

| Module | Spec | RTL | DV | Impl | Proto |
|--------|------|-----|----|------|-------|
| top (`vibe_ub_switch`) | SPEC-0.2 naming frozen; AS names PR50 | CR-B landed `1ed4d350` (`{src}_{dst}_{meaning}`) | TB rename landed vs DUT freeze `1ed4d350`; greens **3/3 CLOSED** | **NOT PASS** — path B **hold**. Do **not** chase top-level map / STA | FPGA **deferred** |
| port / PMA / AFIFO | SPEC-0.2 naming frozen; §15 + AS §3–5 | CR-B landed (`vibe_port`, `vibe_pma_bnd`, `vibe_afifo`) | TB rename landed; old greens **VOID**; new series **3/3 CLOSED** | Path B **hold**. Leaf QoR historical only. Not a chip netlist | FPGA **deferred** |
| DLL / NW | SPEC-0.2 naming frozen; §2 + AS §4 | CR-B landed (`vibe_dll*`, `vibe_nw_adapt`) | TB rename landed; old greens **VOID**; new series **3/3 CLOSED** | Path B **hold**. Leaf QoR historical only | FPGA **deferred** |
| PCS / LMSM | SPEC-0.2 naming frozen; §15 + AS §4–5 | CR-B landed (`vibe_pcs_*`, `vibe_lmsm`) | TB rename landed; old greens **VOID**; new series **3/3 CLOSED** | Path B **hold**. Leaf QoR historical only | FPGA **deferred** |
| fabric / xbar / mgmt | SPEC-0.2 naming frozen; §2 + AS §4 | CR-B landed | TB rename landed; old greens **VOID**; new series **3/3 CLOSED** | Path B **hold**. **NOT mapped** (historical slang/unroll/timeout). Lint debt not re-measured on `1ed4d350` | FPGA **deferred** |
| CFG / headers | SPEC-0.2 naming frozen + register-map + RDL | CR-B landed (`vibe_cfg_space`; headers unchanged by the rename commit) | TB rename landed; old greens **VOID**; new series **3/3 CLOSED** | Path B **hold**. `vibe_cfg_space` Yosys `proc_dff` FAIL remains tool debt, not an ECO | FPGA **deferred** |
| CDC | SPEC-0.2 naming frozen; AS CDC + SPEC clocks | CR-B landed (`vibe_sync2`, `vibe_afifo`, `vibe_rst_sync`; `ovf_l` **F1**, no ECO) | No CDC report vs `1ed4d350`. Prior [`reports/cdc/2026-09-08.md`](../reports/cdc/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). **F1** unchanged, non-blocking | Path B **hold**. WARN stays permanent frozen waiver under **F1**; not ECO | FPGA **deferred** |
| Signoff package | SPEC §16: QoR is **not** a SPEC must | N/A (no RTL ECO for signoff; rename is CR-B naming only) | N/A | **NOT PASS** — path B **hold**; Sky130 scripts/docs only; OpenSTA **not run**; no `sta_wns_tns.rpt`; do not run tapeout flow | FPGA **deferred** |

---

## 3. Open issues / PRs

| Item | Count | As of |
|------|------:|--------|
| Open GitHub issues | **0** | 2026-09-08, `lukebest/Vibe-UB-Switch` |
| Closed GitHub issues | **0** | same |
| Open GitHub PRs | **1** | same (`origin/main` `34712f3d`; PR60 merged): #61 this STATUS/RISKS evening refresh. |

No issue was opened from lint, CDC, nightly health, the CR-B rename, or re-gate 1/3 / 2/3 / 3/3. Known debts stay in [`docs/RISKS.md`](RISKS.md), not as fake signoff gaps.

---

## 4. Next actions

1. **Path B hold** (Luke, 2026-09-05 Asia/Shanghai; human **decision E**). Keep Sky130 scripts/docs only. Do **not** chase top-level map / STA. [`reports/signoff/`](../reports/signoff/) stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. FPGA **deferred**. See [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). PLAN-2026-09-04 stays historical.
2. **Freeze watch** — new RTL freeze is `982ddd0a` (PR62 merge `581d9d34` is **merge-trace only**). Old `1ed4d350` is **VOID** as current freeze. Keep `git diff 982ddd0a -- rtl/` empty except via CR. F1 unchanged.
3. **`ovf_l` remains F1** (Luke, 2026-09-07 Asia/Shanghai; human **decision F**). Permanent frozen CDC-WARN/waiver on `ovf_l` in `rtl/port/vibe_port.sv`. Lint ECO did **not** touch F1. No issue. Not a signoff hole. See [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md).
4. **Verification — CR-B 3/3 VOIDED.** Lint ECO broke DUT `1ed4d350`. Series vs `1ed4d350` is historical only. Restart 1/3 against `982ddd0a`. Chat PASS does **not** count. Old 3/3 (2026-09-03) stays **VOID**. Do **not** count nightly health as 4/3. Remaining work is Path B **hold** / impl signoff **NOT PASS**.

Do not reopen the voided 3/3. Do not count chat PASS. Do not hand-write WNS/TNS. Do not invent coverage numbers. Do not use `581d9d34` as the freeze pin.
