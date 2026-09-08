# Vibe-UB-Switch — project status

| Item | Value |
|------|--------|
| Project | Vibe-UB-Switch |
| Snapshot date | **2026-09-08** (Asia/Shanghai) |
| `origin/main` HEAD | `63c41a17` — PR52 merge (`63c41a173df07ec8af60220f340543722ced7f6d`) |
| RTL freeze SHA | `1ed4d350` (`1ed4d35006848e6275e93d9bd2fc4e7f7af348f1`) — CR-B rename head; **same role as old `32a7f5e0`** |
| PR51 merge tip | `777865f0` (`777865f073faba87a564f876636db1ebe0e19790`) — **merge-trace only**, not the freeze pin |
| `git diff 1ed4d350 -- rtl/` | **empty** vs freeze (ports landed). Old `32a7f5e0` is **VOID**. |
| SPEC | **SPEC-0.2 naming frozen** (PR50 `6214b081`; Xia pin PR52). Functional body still SPEC-0.1 facts. CHANGELOG new RTL SHA is **`1ed4d350`** (done). |
| FPGA / proto | **Deferred** — no FPGA tree, no board bring-up in this repo |

This file is an in-repo snapshot for 芯片开发PM. Numbers below are copied from committed reports. **No WNS/TNS/slack is stated** because none exists in-repo. **No coverage numbers are invented** for the renamed DUT.

This snapshot follows PR52 (`63c41a17`, Xia freeze pin `1ed4d350`). Prior: PR51 merge tip `777865f0` (CR-B RTL landed; merge-trace only); PR50 SPEC/AS names at `6214b081`; PR49 CR-B approval. Decision **E** remains path **B**; decision **F** remains **F1**; decision **G** remains Option **B**.

**CR-B (iface rename) Design has landed.** Luke chose Option B on 2026-09-08 Asia/Shanghai: `{src}_{dst}_{meaning}` (`dll` not `dl`). Formal record [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md); inventory [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md). Ports at freeze `1ed4d350` (`rtl/` only on that commit). `ovf_l` stays **F1** (no ECO). Verification must rewrite `tb/vibe` against DUT `1ed4d350`. Old 3/3 greens are **VOID**. Chat PASS does not count. Xia CHANGELOG SHA fill is **done** (PR52).

---

## 1. Four gates

| Gate | Result | Evidence |
|------|--------|----------|
| SPEC freeze | **SPEC-0.2 naming frozen** | [`docs/SPEC.md`](SPEC.md) / AS product names landed PR50 (`6214b081`). Xia pinned port freeze `1ed4d350` in PR52. Naming only; functional widths / protocol still SPEC-0.1 facts. |
| Lint | **not re-run vs new DUT** | [`reports/lint/2026-09-08.md`](../reports/lint/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). No committed lint vs freeze `1ed4d350`. Nightly may fail until TB rename lands — expected; not an ECO. |
| Verification (consecutive green) | **VOID — 0/3 restart** | Old 3/3 ([`reports/regress/2026-09-03.md`](../reports/regress/2026-09-03.md) / [`-run2.md`](../reports/regress/2026-09-03-run2.md) / [`-run3.md`](../reports/regress/2026-09-03-run3.md)) is **VOID** with DUT `32a7f5e0`. New series starts at **1/3** only after `reports/regress/` lands against DUT `1ed4d350`. Chat PASS does **not** count. Nightly health may fail until TB rewrite lands — expected; **not** a consecutive green. |
| Impl signoff | **NOT PASS** | [`reports/signoff/`](../reports/signoff/) has [`PLAN-2026-09-04.md`](../reports/signoff/PLAN-2026-09-04.md) + [`DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md) + [`DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md) + [`README.md`](../reports/signoff/README.md) + `.gitkeep`. Luke chose **path B** (2026-09-05) and **F1** (2026-09-07). Path B **hold**: Sky130 scripts/docs only. PLAN stays historical. Methodology QoR still [`reports/synth/2026-09-03.md`](../reports/synth/2026-09-03.md) — **no top netlist**, **no WNS/TNS**. Do not claim signoff. FPGA **deferred**. |

FPGA is **not** a fifth gate. It is deferred.

---

## 2. Module × stage

Legend: **done** = locked / present at freeze SHA; **PASS** = committed gate or health check; **debt** = known, waived or frozen, not an ECO; **not started** / **NOT PASS** / **deferred** / **hold** as written.

Progress: **SPEC** = 0.2 naming frozen; **RTL** = CR-B landed at freeze `1ed4d350`; **DV** = TB rewrite in progress / greens **0/3** restart; **impl** = path B hold; **proto** = deferred.

| Module | Spec | RTL | DV | Impl | Proto |
|--------|------|-----|----|------|-------|
| top (`vibe_ub_switch`) | SPEC-0.2 naming frozen; AS names PR50 | CR-B landed `1ed4d350` (`{src}_{dst}_{meaning}`) | TB rewrite vs DUT `1ed4d350` in progress; greens **0/3** restart | **NOT PASS** — path B **hold**. Do **not** chase top-level map / STA | FPGA **deferred** |
| port / PMA / AFIFO | SPEC-0.2 naming frozen; §15 + AS §3–5 | CR-B landed (`vibe_port`, `vibe_pma_bnd`, `vibe_afifo`) | TB rewrite in progress; old greens **VOID** | Path B **hold**. Leaf QoR historical only. Not a chip netlist | FPGA **deferred** |
| DLL / NW | SPEC-0.2 naming frozen; §2 + AS §4 | CR-B landed (`vibe_dll*`, `vibe_nw_adapt`) | TB rewrite in progress; old greens **VOID** | Path B **hold**. Leaf QoR historical only | FPGA **deferred** |
| PCS / LMSM | SPEC-0.2 naming frozen; §15 + AS §4–5 | CR-B landed (`vibe_pcs_*`, `vibe_lmsm`) | TB rewrite in progress; old greens **VOID** | Path B **hold**. Leaf QoR historical only | FPGA **deferred** |
| fabric / xbar / mgmt | SPEC-0.2 naming frozen; §2 + AS §4 | CR-B landed | TB rewrite in progress; old greens **VOID** | Path B **hold**. **NOT mapped** (historical slang/unroll/timeout). Lint debt not re-measured on `1ed4d350` | FPGA **deferred** |
| CFG / headers | SPEC-0.2 naming frozen + register-map + RDL | CR-B landed (`vibe_cfg_space`; headers unchanged by the rename commit) | TB rewrite in progress; old greens **VOID** | Path B **hold**. `vibe_cfg_space` Yosys `proc_dff` FAIL remains tool debt, not an ECO | FPGA **deferred** |
| CDC | SPEC-0.2 naming frozen; AS CDC + SPEC clocks | CR-B landed (`vibe_sync2`, `vibe_afifo`, `vibe_rst_sync`; `ovf_l` **F1**, no ECO) | No CDC report vs `1ed4d350`. Prior [`reports/cdc/2026-09-08.md`](../reports/cdc/2026-09-08.md) was DUT `32a7f5e0` (**VOID**). **F1** non-blocking | Path B **hold**. WARN stays permanent frozen waiver under **F1**; not ECO | FPGA **deferred** |
| Signoff package | SPEC §16: QoR is **not** a SPEC must | N/A (no RTL ECO for signoff; rename is CR-B naming only) | N/A | **NOT PASS** — path B **hold**; Sky130 scripts/docs only; OpenSTA **not run**; no `sta_wns_tns.rpt`; do not run tapeout flow | FPGA **deferred** |

---

## 3. Open issues / PRs

| Item | Count | As of |
|------|------:|--------|
| Open GitHub issues | **0** | 2026-09-08, `lukebest/Vibe-UB-Switch` |
| Closed GitHub issues | **0** | same |
| Open GitHub PRs | **2** | same (`origin/main` `63c41a17`): #53 this STATUS/RISKS refresh; #54 TB rewrite (not landed) |

No issue was opened from lint, CDC, nightly health, or the CR-B rename. Known debts stay in [`docs/RISKS.md`](RISKS.md), not as fake signoff gaps. Nightly fail until TB lands is expected — do not open an ECO issue. #54 is the TB rewrite; do not count it as 1/3 until `reports/regress/` lands.

---

## 4. Next actions

1. **Path B hold** (Luke, 2026-09-05 Asia/Shanghai; human **decision E**). Keep Sky130 scripts/docs only. Do **not** chase top-level map / STA. [`reports/signoff/`](../reports/signoff/) stays PLAN + keepers. Impl gate remains **NOT PASS**. Do not claim signoff. Do not run tapeout flow. FPGA **deferred**. See [`reports/signoff/DECISION-2026-09-05.md`](../reports/signoff/DECISION-2026-09-05.md). PLAN-2026-09-04 stays historical.
2. **Freeze watch** — keep `git diff 1ed4d350 -- rtl/` empty. Freeze pin is rename head `1ed4d350` (same role as old `32a7f5e0`). PR51 `777865f0` is **merge-trace only**. Old freeze `32a7f5e0` is **VOID**.
3. **`ovf_l` remains F1** (Luke, 2026-09-07 Asia/Shanghai; human **decision F**). Permanent frozen CDC-WARN/waiver on `ovf_l` in `rtl/port/vibe_port.sv`. No ECO. No issue. Not a signoff hole. Not blocking CR-B. See [`reports/signoff/DECISION-F-2026-09-07.md`](../reports/signoff/DECISION-F-2026-09-07.md).
4. **Verification — TB rewrite** against DUT `1ed4d350`. Restart consecutive greens at **1/3** only after `reports/regress/` lands. Chat PASS does **not** count. Current gate is **0/3**. Old 3/3 is **VOID**.
5. **Nightly health** may fail until TB rename lands — **expected**. Do not treat as a consecutive green or an ECO chase.

Do not reopen the voided 3/3. Do not count chat PASS. Do not hand-write WNS/TNS. Do not invent coverage numbers. Do not use `777865f0` as the freeze pin.
