# CR-B: interface rename to `source_dest_meaning` — APPROVED

**Luke approved Option B on 2026-09-08 (Asia/Shanghai).**

This file is the formal change-request record for that decision. It is **not** a signoff certificate, **not** an RTL/TB implementation, and **not** a SPEC functional rewrite.

Inventory and current-vs-proposed names stay in [`CR-IFACE-NAMING-DRAFT-2026-09-08.md`](CR-IFACE-NAMING-DRAFT-2026-09-08.md) (PR48 draft content, retained as the naming inventory).

| Item | Value |
|------|--------|
| ID | CR-IFACE-RENAME-B-2026-09-08 |
| Status | **APPROVED** — Option B (Luke, 2026-09-08). Xia SPEC/AS/CHANGELOG names: **landed** (docs follow-up). Design / Verification rename **in progress**. Do **not** claim rename done. |
| Decision | **Option B** — formal CR + full interface rename to `{src}_{dst}_{meaning}` |
| Chosen by | Luke |
| Date | 2026-09-08 Asia/Shanghai |
| RTL freeze today | `32a7f5e0` (`32a7f5e0c3f04762aa27dae73b000e55773195da`) — still the frozen SHA until Design lands ports |
| Impl gate | Path **B** remains **NOT PASS** |
| `ovf_l` | **F1** still stands — no ECO |

---

## 1. Decision

Luke chose **Option B** (full RTL / TB / SPEC / AS rename), not Option A (wave aliases only) and not “neither”.

Option A and the pre-decision default (“do nothing to RTL”) are closed.

---

## 2. Rule

Interface signal names use:

```text
{src}_{dst}_{meaning}
```

| Rule | Detail |
|------|--------|
| Tokens | Source module token, dest module token, meaning. Absolute direction (who drives → who sinks). Not a local `tx` / `rx` view. |
| Datalink token | **`dll`**, not `dl`. Luke’s spoken example `nw_dl_data` is `nw_dll_data` in this tree. |
| Handshake | Ready/valid data interfaces keep `_vld` / `_ready`. Fire when `_vld && _ready`. Do not switch to `_valid`. |
| Clocks / resets | **Exempt.** `clk_fab`, `clk`, `rst_n`, `txclk` / `rxclk` (and `_0`..`_3`), `port_rst`, `device_rst` stay as listed product / domain names. |
| Same wire | One name on **both** ends. Do not invert the pair per port. |

Abbreviation table, handshake suffix, clock/reset exemption list, and per-boundary proposed names are the inventory in the draft §1–§2. Do not invent a second `dl` token.

---

## 3. Scope

Rename to match the draft inventory. No functional width or protocol change.

| Owner | Work |
|-------|------|
| **Xia** | `docs/SPEC.md` and AS pin / datapath tables; SPEC / project CHANGELOG freeze-break note. Functional body semantics stay as frozen; names follow `{src}_{dst}_{meaning}`. **Done** in the SPEC-0.2 docs PR (names ahead of RTL). |
| **Design** | `rtl/` boundary ports on both ends of every draft §2 row (`vibe_nw_adapt`, `vibe_dll*`, `vibe_pcs_*`, `vibe_pma_bnd`, `vibe_port`, `vibe_ub_switch`, `vibe_fabric`, `vibe_mgmt` / `vibe_cna_ep` / `vibe_mgmt_byp`). |
| **Verification** | `tb/` suite, units, dumpvars, waves, checker hier strings; re-gate after the new SHA. |
| **芯片开发PM** | Acceptance of the CR and of the later rename landing. Not a signoff claim. |

This file is the **primary** Approved Option B record. It does **not** edit `rtl/` or `tb/`. SPEC/AS product interface names are updated in the Xia docs PR; functional semantics are not rewritten.

---

## 4. Effects

| Effect | What it means |
|--------|----------------|
| Breaks freeze SHA `32a7f5e0` | When Design lands the rename, `git diff 32a7f5e0 -- rtl/` will be non-empty. A new freeze SHA is required in the same implementation CR / SPEC status update (Xia). **Not broken on this docs record.** |
| Voids consecutive greens **3/3** | `reports/regress/2026-09-03.md` / `-run2` / `-run3` no longer count after the renamed DUT lands. |
| New series | Start a new consecutive-green series **only after** reports / regress land against the **new** SHA. Do not count nightly health as 4/3. |
| No ECO for `ovf_l` | Decision **F1** (2026-09-07) still stands. Permanent frozen CDC-WARN/waiver. Not in this rename. |
| Path B | Impl gate stays **NOT PASS**. Do not claim signoff. Do not run tapeout flow. |

---

## 5. Non-goals

1. **No functional width / protocol change.** Overlay B 512b, DLL↔PCS 640b window, PMA 512b without `_ready`, fire rules, and CFG6 / bypass paths stay as at `32a7f5e0`.
2. **No signoff claim.** This CR is naming + change control only.
3. **Path B still NOT PASS.** Sky130 scripts/docs only; no top map / STA chase.
4. **Do not claim the rename is done** until Design / Verification land `rtl/` / `tb/` and PM accepts.
5. **No `ovf_l` ECO.** F1 is unchanged.
6. **This file does not rewrite SPEC functional body.** Xia pin-table + CHANGELOG freeze-break are in SPEC-0.2 / AS; widths and protocol stay as at `32a7f5e0`.

---

## 6. Next actions (owners)

1. **Xia** — SPEC / AS pin tables + CHANGELOG freeze-break note. **Landed** (SPEC-0.2 CR-applied naming). Do not rewrite FS-0.2.7 behavior.
2. **Design** — rename `rtl/` ports to the draft inventory. New RTL freeze SHA left blank for Design to fill.
3. **Verification** — update `tb/` and re-gate against the new SHA; open a new consecutive-green series only after those reports land.
4. **芯片开发PM** — accept this docs landing and the later RTL/TB landing; do not treat this approval record as rename-complete or as signoff.
