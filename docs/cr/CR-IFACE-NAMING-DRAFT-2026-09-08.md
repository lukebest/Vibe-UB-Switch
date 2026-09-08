# CR draft: interface naming `source_dest_meaning`

| Item | Value |
|------|--------|
| ID | CR-IFACE-NAMING-DRAFT-2026-09-08 |
| Status | **Inventory retained** — decision closed. Luke approved **Option B** 2026-09-08 Asia/Shanghai. Formal record: [`CR-IFACE-RENAME-B-2026-09-08.md`](CR-IFACE-RENAME-B-2026-09-08.md). Rename is **not** implemented in this docs PR. |
| Date | 2026-09-08 |
| Requested rule | Luke: interface signal names = `source_module_dest_module_meaning` |
| Luke example | `nw_dl_data` = network → datalink data |
| Repo token | This tree uses **`dll`**, not `dl`. This draft proposes **`dll`** as the datalink token. Equivalent of Luke’s example: `nw_dll_data`. |
| SPEC | SPEC-0.1 freeze (RTL `32a7f5e0`) broken **for naming only** by CR-B. Xia pin tables: SPEC-0.2 / AS. Functional widths still `32a7f5e0`. |
| This file | Inventory only (kept). Formal decision: [`CR-IFACE-RENAME-B-2026-09-08.md`](CR-IFACE-RENAME-B-2026-09-08.md). **Do not implement the RTL/TB rename here.** |

SPEC §1 / §18: after freeze, changing `cfg_wr_*`, `irq_logic`, per-port PMA `txdata`/`rxdata`/`txclk`/`rxclk`, or NW↔DLL `data[511:0]` `vld`/`ready` **semantics** needs a change request. A rename of those names is an interface change even if widths and fire rules stay the same.

`git diff 32a7f5e0 -- rtl/` stays empty on this docs record. Option B is approved; the freeze SHA breaks only when Design lands the rename.

---

## 1. Naming convention

Pattern:

```text
<source_token>_<dest_token>_<meaning>
```

- **Source** and **dest** are module tokens (table below), not a local TX/RX view.
- **Meaning** is the payload or qualifier (`data`, `lane0`, `cfg6`, `txdata`, …).
- One name on **both** ends of the same wire. Do not invert the pair per port (`dll_tx_*` on NW vs `nw_tx_*` on DLL).
- Direction is the **absolute** path of the beat (who drives → who sinks). Do **not** encode local `tx` / `rx` relative to “toward the PMA” or “toward the fabric”.

Luke’s spoken example used `dl`. The RTL tree is `rtl/dll/`, modules `vibe_dll*`, and TB `tc_dll*`. **Use `dll`.** Do not introduce a second `dl` token.

### 1.1 Abbreviations

| Token | Module / meaning | Notes |
|-------|------------------|--------|
| `nw` | `vibe_nw_adapt` (network adapt) | Overlay B 512b `vld`/`ready` @ `clk_fab` |
| `dll` | `vibe_dll` / `vibe_dll_tx` / `vibe_dll_rx` | **Not** `dl`. Luke example `nw_dl_data` → `nw_dll_data` |
| `pcs` | `vibe_pcs_tx` / `vibe_pcs_rx` | 640b window is DLL↔PCS only |
| `pma` | `vibe_pma_bnd` | Product 512b, no extra handshake |
| `fab` | `vibe_fabric` | SAF / VOQ egress and ingress |
| `mgmt` | `vibe_mgmt` / `vibe_mgmt_byp` / `vibe_cna_ep` | CFG6 terminate + reply inject |
| `cfg` | firmware static write (`cfg_wr_*`) | Product pin family; keep `cfg` token |
| `afifo` | `vibe_afifo` (per-lane CDC) | Internal; rename only if a later CR touches CDC ports |
| `lmsm` | `vibe_lmsm` | Sidebands (`link_up`, `link_ready`, `lmsm_go`); not a data handshake |

### 1.2 Handshake suffix

Ready/valid data interfaces keep the existing suffix spelling:

| Suffix | Role |
|--------|------|
| `_vld` | source asserts; beat is offered this cycle |
| `_ready` | dest asserts; fire when `_vld && _ready` |

Do not switch to `_valid`. Do not add a third enable name (SPEC §4.3 / AS §3).

PMA product data has **no** `_vld`/`_ready` (SPEC §4.4). Meaning tokens stay `txdata` / `rxdata` (or the proposed `pcs_pma_txdata` / `pma_pcs_rxdata` under Option B).

### 1.3 Clocks and resets — exempt or listed

These names are **exempt** from `source_dest_meaning`. They stay as listed product / domain names:

| Current name | Role |
|--------------|------|
| `clk_fab` | 1.25 GHz fabric / DLL / PCS digital / LMSM / mgmt |
| `clk` | leaf-module fabric-domain clock (tied to `clk_fab` at the parent) |
| `rst_n` | logical reset |
| `txclk` / `txclk_0`..`txclk_3` | per-port PMA TX 922 MHz |
| `rxclk` / `rxclk_0`..`rxclk_3` | per-port PMA RX 922 MHz |
| `port_rst` | per-port reset hold |
| `device_rst` | device reset |

Do not invent `fab_dll_clk` / `pma_pcs_rxclk` unless a later CR explicitly expands the rule to clocks.

### 1.4 Worked examples

| Intent | Luke / rule | Proposed |
|--------|-------------|----------|
| Network → datalink data | `nw_dl_data` | `nw_dll_data[511:0]` |
| same, handshake | — | `nw_dll_vld`, `nw_dll_ready` |
| Datalink → network data | dest/source swapped | `dll_nw_data[511:0]` |
| Datalink → PCS window | — | `dll_pcs_data[639:0]` |
| Fabric → network (VOQ egress) | not local `fab_tx_*` | `fab_nw_data[511:0]` |
| Network → fabric (ingress) | not local `fab_rx_*` | `nw_fab_data[511:0]` |
| Mgmt inject → network | not local `mgmt_tx_*` | `mgmt_nw_data[511:0]` |

---

## 2. Inventory — current vs proposed

Widths and fire rules below are **as implemented at freeze** (`32a7f5e0`). This draft does not change them.

### 2.1 NW ↔ DLL (512b Overlay B)

Same wires in `vibe_port`: `dll_tx_d` / `dll_rx_d`.

| Direction | Width | CURRENT (`vibe_nw_adapt`) | CURRENT (`vibe_dll`) | PROPOSED (both ends) |
|-----------|------:|---------------------------|----------------------|----------------------|
| NW → DLL | 512 | `dll_tx_data` / `dll_tx_vld` / `dll_tx_ready` | `nw_tx_data` / `nw_tx_vld` / `nw_tx_ready` | `nw_dll_data` / `nw_dll_vld` / `nw_dll_ready` |
| DLL → NW | 512 | `dll_rx_data` / `dll_rx_vld` / `dll_rx_ready` | `nw_rx_data` / `nw_rx_vld` / `nw_rx_ready` | `dll_nw_data` / `dll_nw_vld` / `dll_nw_ready` |

Child ports today: `vibe_dll_tx` `nw_*` / `pcs_*`; `vibe_dll_rx` `pcs_*` / `nw_*` (no dest token).

**Inconsistency (same wire, two names):** `vibe_port` ties `.dll_tx_data(dll_tx_d)` on NW to `.nw_tx_data(dll_tx_d)` on DLL. Hierarchical probes already disagree (`u_p.u_nw.dll_tx_data` vs `u_p.u_dll.nw_tx_data`). `tx`/`rx` is local (“toward PMA” / “from PMA”), not source→dest.

### 2.2 DLL ↔ PCS (640b window)

| Direction | Width | CURRENT (`vibe_dll`) | CURRENT (`vibe_pcs_tx` / `vibe_pcs_rx`) | PROPOSED (both ends) |
|-----------|------:|----------------------|------------------------------------------|----------------------|
| DLL → PCS | 640 | `pcs_tx_data` / `pcs_tx_vld` / `pcs_tx_ready` | `dll_data` / `dll_vld` / `dll_ready` | `dll_pcs_data` / `dll_pcs_vld` / `dll_pcs_ready` |
| PCS → DLL | 640 | `pcs_rx_data` / `pcs_rx_vld` / `pcs_rx_ready` | `dll_data` / `dll_vld` / `dll_ready` | `pcs_dll_data` / `pcs_dll_vld` / `pcs_dll_ready` |

**Inconsistency:** PCS TX and PCS RX both use `dll_*` with no dest token and no direction. DLL uses local `pcs_tx_*` / `pcs_rx_*`. The two `dll_data` ports are **different wires** (`pcs_tx_d` vs `pcs_rx_d` in `vibe_port`).

### 2.3 PCS ↔ PMA (lanes + product 512b)

Internal (not product pins):

| Direction | Width | CURRENT | PROPOSED |
|-----------|------:|---------|----------|
| PCS TX → AFIFO | 160×4 | `vibe_pcs_tx`: `lane0`..`lane3`, `lane_vld` | `pcs_afifo_lane0`..`lane3`, `pcs_afifo_lane_vld` |
| gear → PMA TX | 128×4 | `vibe_pma_bnd`: `tx_lane0`..`tx_lane3`, `tx_lane_vld` | `afifo_pma_lane0`..`lane3`, `afifo_pma_lane_vld` |
| PMA RX → AFIFO | 128×4 | `rx_lane0`..`rx_lane3`, `rx_lane_vld` | `pma_afifo_lane0`..`lane3`, `pma_afifo_lane_vld` |
| AFIFO → PCS RX | 160×4 | `vibe_pcs_rx`: `lane0`..`lane3`, `lane_vld` | `afifo_pcs_lane0`..`lane3`, `afifo_pcs_lane_vld` |

Product PMA (SPEC §4.1 / AS §18 — **frozen names**):

| Direction | Width | CURRENT (port / top) | PROPOSED (Option B only) |
|-----------|------:|----------------------|--------------------------|
| chip → PMA | 512 | `txdata` ; top `txdata_0`..`txdata_3` | `pcs_pma_txdata` ; `pcs_pma_txdata_0`..`_3` |
| PMA → chip | 512 | `rxdata` ; top `rxdata_0`..`rxdata_3` | `pma_pcs_rxdata` ; `pma_pcs_rxdata_0`..`_3` |

No PMA `_ready`. Slice stays `[127:0]`=lane0 … `[511:384]`=lane3.

**Inconsistency:** product pins use local `tx`/`rx` with no source token. Internal lane ports reuse `lane0` on both PCS TX and PCS RX.

### 2.4 NW ↔ FAB (512b)

| Direction | Width | CURRENT (`vibe_port` / `vibe_nw_adapt`) | CURRENT (`vibe_fabric`) | PROPOSED (both ends) |
|-----------|------:|-----------------------------------------|-------------------------|----------------------|
| FAB → NW (VOQ egress → TX) | 512 | `fab_tx_data` / `fab_tx_vld` / `fab_tx_ready` | `egr_data` / `egr_vld` / `egr_ready` | `fab_nw_data` / `fab_nw_vld` / `fab_nw_ready` |
| NW → FAB (RX → SAF ingress) | 512 | `fab_rx_data` / `fab_rx_vld` / `fab_rx_ready` | `ing_data` / `ing_vld` / `ing_ready` | `nw_fab_data` / `nw_fab_vld` / `nw_fab_ready` |

Top today: arrays `fab_tx[]` / `fab_rx[]` wired to fabric `.egr_*` / `.ing_*`.

**Inconsistency:** port `fab_tx_*` means “from fabric, toward PMA” (local TX). Fabric `egr_*` is the same wire with a third name. `fab_rx_*` vs `ing_*` is the same mismatch on the return path.

### 2.5 FAB ↔ mgmt

Two different paths. Neither uses `source_dest` today.

| Path | Width | CURRENT | PROPOSED |
|------|------:|---------|----------|
| FAB → mgmt (CFG6 terminate) | 512 + hit | fabric `cfg6_data[0:3]`, `cfg6_hit[3:0]` → `vibe_mgmt` same names | `fab_mgmt_cfg6_data`, `fab_mgmt_cfg6_hit` |
| mgmt → FAB consume | 4 | `cfg6_consume` | `mgmt_fab_cfg6_consume` |
| mgmt → NW inject (bypass; **not** xbar) | 512 | `vibe_cna_ep` `reply_data`/`reply_vld`/`reply_ready` → `vibe_mgmt_byp` `in_*`/`out_*` → port `mgmt_tx_*` | `mgmt_nw_data` / `mgmt_nw_vld` / `mgmt_nw_ready` |

**Inconsistency:** CFG6 uses a hit/data pair with no source token. Reply uses `reply_*` then generic `in_*`/`out_*` then local `mgmt_tx_*`. Bypass does not enter fabric (`vibe_mgmt_byp` comment / AS §8).

### 2.6 `vibe_port` `fab_*` / `mgmt_*` and PMA

| CURRENT port pin | Role today | PROPOSED |
|------------------|------------|----------|
| `fab_tx_data/vld/ready` | fabric egress into NW TX | `fab_nw_data/vld/ready` |
| `fab_rx_data/vld/ready` | NW RX into fabric ingress | `nw_fab_data/vld/ready` |
| `mgmt_tx_data/vld/ready` | mgmt inject into NW TX | `mgmt_nw_data/vld/ready` |
| `txdata` | PMA TX product | `pcs_pma_txdata` (Option B; SPEC-frozen today) |
| `rxdata` | PMA RX product | `pma_pcs_rxdata` (Option B; SPEC-frozen today) |

There is no `mgmt_rx_*`. CFG0 terminates in DLL and does not enter fabric.

### 2.7 Inconsistency summary

1. **Same wire, opposite local names:** NW `dll_tx_data` ↔ DLL `nw_tx_data`; NW `dll_rx_data` ↔ DLL `nw_rx_data`.
2. **Local `tx`/`rx` vs absolute source→dest:** `fab_tx_*` is fabric→NW; `fab_rx_*` is NW→fabric; `mgmt_tx_*` is mgmt→NW.
3. **Third name at fabric:** `ing_*` / `egr_*` vs port `fab_rx_*` / `fab_tx_*`.
4. **PCS `dll_*` is ambiguous:** TX input and RX output share the same port names.
5. **Product PMA `txdata`/`rxdata`** omit source/dest; SPEC/AS freeze those strings.
6. **Mgmt reply** is `reply_*` → `in_*`/`out_*` → `mgmt_tx_*` for one path.

---

## 3. Impact list (rough file-count via `gh`)

Counts from GitHub code search on `lukebest/Vibe-UB-Switch` (`origin/main` at draft time, HEAD `8540421`). Search `total_count` is a tree-scale estimate, not a line-level hit list.

| Area | `gh` query | Count | Option B touch |
|------|------------|------:|----------------|
| RTL SystemVerilog | `path:rtl extension:sv` | **49** | Boundary modules must rename ports; children that only have `clk`/`rst_n` may stay |
| RTL headers | `path:rtl/common` | **2** (`vibe_ub_params.vh`, `vibe_ub_fn.vh`) | Unlikely (no iface names) |
| Firmware header | `path:include` | **1** | Unlikely (`cfg_wr_*` / `irq_logic` stay unless product pins move) |
| TB vibe SV | `path:tb/vibe extension:sv` | **91** | Suite, units, harnesses, dumpvars |
| TB vibe unit TCs | `path:tb/vibe/tests extension:sv` | **86** | Any TC that binds `fab_*`, `dll_*`, `nw_*`, `txdata`/`rxdata` |
| TB vibe env | `path:tb/vibe/env` | **3** | `vibe_suite.sv` `$dumpvars`; `vibe_fabric_harness.sv` `ing_*`/`egr_*` |
| TB vibe scripts | `path:tb/vibe/scripts` | **11** | `vcd_to_png.py` hard-codes `fab_tx_*` / `txdata`; `run_waves.sh` / `run_units.sh` |
| TB vibe waves | `path:tb/vibe/waves` | **8** | README signal table; committed VCD names if regenerated |
| TB vibe results / checkers | `path:tb/vibe/results` | **9** | `CHECKER_AUDIT.md`, `TP_TC_MATRIX.md`, `REGRESSION.md` prose names |
| Docs Markdown | `path:docs extension:md` | **13** | `SPEC.md` §3–4/§6/§18; AS §3/§5/§18; testpoints; STATUS freeze watch |
| Repo `scripts/` | `path:scripts` | **13** | Synth filelists / SDC pin names if product PMA pins change |
| `reports/` tree | `path:reports` | **370** | Nightly lint/CDC/regress **scripts** + regenerated logs after Option B |

### 3.1 RTL modules (Option B)

Must change (boundary ports):

- `rtl/nw/vibe_nw_adapt.sv`
- `rtl/dll/vibe_dll.sv`, `vibe_dll_tx.sv`, `vibe_dll_rx.sv`
- `rtl/pcs/vibe_pcs_tx.sv`, `vibe_pcs_rx.sv`
- `rtl/pma/vibe_pma_bnd.sv`
- `rtl/port/vibe_port.sv`
- `rtl/top/vibe_ub_switch.sv`
- `rtl/fabric/vibe_fabric.sv` (`ing_*`/`egr_*`, `cfg6_*`)
- `rtl/mgmt/vibe_mgmt.sv`, `vibe_cna_ep.sv`, `vibe_mgmt_byp.sv`

Optional / later: `afifo` leaf ports (`wen`/`wdata`/`ren`/`rdata`), `lmsm` sidebands, PCS internals (`in_data`/`win_data`).

### 3.2 `tb/vibe` (suite / units / waves / dumpvars)

- **Suite:** `tb/vibe/env/vibe_suite.sv` `$dumpvars` (`wav_ing0`, `h.ing_vld`, `h.egr_vld`, `cfg6_hit`).
- **Units (known name users):** `tc_dll`, `tc_nw_adapt_linkready`, `tc_phy_nw_dll_512b`, `tc_nw_pkt_to_pma_tx`, `tc_nw_pkt_pma_loopback`, `tc_port_smoke`, `tc_top_smoke`, `tc_phy_u26_chain`, plus PMA/PCS units that bind `txdata`/`dll_data`.
- **Waves:** `tb/vibe/waves/README.md`; `tc_nw_pkt_pma_loopback.sv` selected `$dumpvars`; `tb/vibe/scripts/vcd_to_png.py` labels `fab_tx_vld` / `fab_tx_data` / `txdata`.
- **Checkers:** `tb/vibe/results/CHECKER_AUDIT.md`, `tb/vibe/common/vibe_tb_nw512.svh`, `vibe_tb_nw_pma.svh` (hier strings such as `u_n.dll_tx_data`).

Old `tb/{pcs,dll,nw,cdc,switch}/ub_*` (~26 files) is already **void** (`tb/vibe/Makefile`). Do not treat it as a rename source.

### 3.3 docs / SPEC / AS

- `docs/SPEC.md` — mermaid, §4.1 pin table, §4.3–4.4, §6 T8, §18. **Functional body stays frozen** until an approved CR.
- `docs/Vibe-UB-Switch-architecture-spec.md` — §3 clocks/PMA, §5 T0–T8, §18 product pins.
- `docs/Vibe-UB-Switch-testpoints.md`, `tb/vibe/results/TP-0.3.md` — `txdata`/`rxdata` TP text.

### 3.4 reports scripts

- `reports/lint/run_lint.sh` — pin-name-agnostic; logs will churn if RTL ports change.
- `scripts/synth/constraints/*.sdc` — product `txdata_*` / `rxdata_*` / `txclk_*` if Option B renames PMA pins.
- `scripts/synth/yosys/filelist.mk` — file list only (no port names).

---

## 4. Implementation options

### Option A — wave aliases only (no freeze break)

- Keep every RTL / SPEC / AS / product pin name exactly as at `32a7f5e0`.
- In TB only, add **alias wires** for dumps and PNG labels, e.g. `assign nw_dll_data = u_p.u_nw.dll_tx_data;` and `$dumpvars` the alias.
- Update `tb/vibe/waves/README.md` / `vcd_to_png.py` to **display** proposed names while VCD still records current DUT names (or both).
- No `rtl/` diff. No SPEC §18 CR. **3/3 greens stay valid.**
- Does **not** fix the hierarchical mismatch (`dll_tx_data` vs `nw_tx_data`); it only makes waves readable.

### Option B — full RTL / TB / SPEC rename

- Rename ports on both ends of every row in §2 to the proposed `source_dest_meaning` names.
- Update `tb/vibe` suite, units, dumpvars, waves, checker hier strings, `vcd_to_png.py`.
- Update `docs/SPEC.md` and AS product-pin / datapath tables **only after** a human-approved change request (SPEC §18).
- Re-run the verification gate (`make -C tb/vibe sim`, waves, coverage as required).
- **Void the existing 3/3 consecutive greens** (`reports/regress/2026-09-03.md` / `-run2` / `-run3`). Start a new consecutive-green series on the renamed DUT. Do not count nightly health as 4/3.
- `git diff 32a7f5e0 -- rtl/` will be non-empty; freeze SHA / SPEC version must be updated in the same CR.

---

## 5. Explicit non-goals of this draft PR

1. **No functional rewrite.** Overlay B widths / fire / protocol stay as at `32a7f5e0`. SPEC-0.2 / AS pin tables use proposed names; this file keeps the current-vs-proposed inventory.
2. **Do not implement the RTL/TB rename in the docs PRs.** No edits under `rtl/`, `tb/`, or `include/`.
3. No waiver of lint/CDC/QoR. No new consecutive-green claim.
4. Approval of Option A vs B was a human decision. **Luke chose Option B on 2026-09-08.** See [`CR-IFACE-RENAME-B-2026-09-08.md`](CR-IFACE-RENAME-B-2026-09-08.md). This file keeps the inventory; it does not implement the rename.

---

## 6. Decision (closed)

| Choice | Effect | Outcome |
|--------|--------|---------|
| **A** | Waves use `nw_dll_*` labels; DUT names stay; freeze intact | Not chosen |
| **B** | Formal CR + RTL/TB/SPEC rename + re-verification + void 3/3 | **Approved** 2026-09-08 — [`CR-IFACE-RENAME-B-2026-09-08.md`](CR-IFACE-RENAME-B-2026-09-08.md) |
| **Neither** | Draft remains on file; current inconsistent names stay | Not chosen |
