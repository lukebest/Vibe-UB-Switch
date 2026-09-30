# CR: PMA idle fill = PRBS31 every cycle — APPROVED

**Human-approved interface semantic patch on 2026-09-30 (Asia/Shanghai).**

This file is the formal change-request record for that decision. It is **not** a signoff certificate, **not** an RTL/TB implementation, and **not** a freeze re-pin. Regime remains **UNFROZEN**.

| Item | Value |
|------|--------|
| ID | CR-PMA-IDLE-PRBS31-2026-09-30 |
| Status | **APPROVED** — interface semantics (human, 2026-09-30 Asia/Shanghai). Xia SPEC / CHANGELOG: **this docs PR**. Design / Verification **deferred until SPEC merge**. Do **not** claim idle-fill done in RTL/TB. |
| Decision | Idle / no valid traffic → **PRBS31 every cycle** on both PMA data buses. Valid traffic keeps existing per-beat data. No extra handshake. |
| Date | 2026-09-30 Asia/Shanghai |
| Kind | Interface-semantics CR (not naming-only; not a freeze re-pin) |
| RTL freeze today | **UNFROZEN** (Decision I). No new pin. Last historical pin `302ac943` stays **VOID as current**. |
| Impl gate | Path **B** remains **NOT PASS** (hold) |
| FPGA / proto | **Deferred** (hold) |
| `ovf_l` | **F1** still stands — no ECO |
| This file | Semantic record only. **No RTL / TB / include in this PR.** |

---

## 1. Motivation

Product PMA pins `pcs_pma_txdata_*` / `pma_pcs_rxdata_*` have **no** `_vld` / `_ready` (SPEC §4.4 already). Every `txclk` / `rxclk` cycle therefore **is** a data sample. A held-constant idle (all-zero, sticky last beat, or a static mark) does not satisfy “the bus must change every clock.”

Historical RTL (#115 / PR116) filled pin-idle with **PRBS23** XOR `PMA_IDLE_MARK` inside `vibe_pma_bnd`. That was an ECO against a then-frozen pin, not a SPEC idle-fill rule. This CR writes the **approved product semantic**: idle / no valid traffic = **PRBS31** every cycle, both TX egress and RX ingress, still with no extra handshake.

---

## 2. Semantic rule

`pcs_pma_txdata` / `pma_pcs_rxdata` (per-port `_0`..`_3`) **MUST change every clock cycle**.

| Condition | Bus content | Handshake |
|-----------|-------------|-----------|
| **Idle** = no valid traffic this cycle | **PRBS31** fill, every cycle, on **both** sides: TX egress (`pcs_pma_txdata` @ `txclk`) and RX ingress (`pma_pcs_rxdata` @ `rxclk`). Semantics are consistent in both directions. | None. No PMA `_vld` / `_ready` / extra name. |
| **Valid traffic** | Keep existing per-beat packed-lane data (`[127:0]`=lane0 … `[511:384]`=lane3). | None. Same as SPEC §4.4 today. |

Idle is “no valid traffic on that PMA data bus this cycle,” not a new sideband and not electrical idle (EEI / EEIB). LMSM / DLL Null Block / PCS scramble(0) stay as already locked in FS-0.2.7 / AS-0.1. This CR only names the **product 512b pin-idle** fill.

TX and RX use the same PRBS31 meaning so a near-end or peer loopback can tell idle from a packed beat without adding a handshake. Exact LFSR polynomial, seed, and lane-slice mapping are **Design follow-up** after SPEC merge (do not invent them in this docs PR).

---

## 3. Scope

| Owner | Work |
|-------|------|
| **Xia** | `docs/SPEC.md` §4.4 plus related product-interface rows that name these buses; SPEC / project CHANGELOG entry. **This PR.** Functional widths, fire rules, and “no extra handshake” stay. AS / FS alignment note below — **do not rewrite AS body here**. |
| **Design** | After SPEC merge: `pcs_tx`, `pcs_rx`, `pma_bnd` / AFIFO boundary so pin-idle is PRBS31 every cycle and valid beats keep today’s pack/unpack. **Not in this PR.** |
| **Verification** | After SPEC merge: TB / scoreboard / loopback / idle checkers that today assume PRBS23 + `PMA_IDLE_MARK` or a held pin. **Not in this PR.** |
| **芯片开发PM** | Accept this docs CR. Do not treat Accept as RTL/TB done, freeze re-pin, 1/3, 4/3, or signoff. |

This file is the **primary** Approved idle-fill record. It does **not** edit `rtl/`, `tb/`, `include/`, or `pycircuit/`.

---

## 4. Impacted modules (later RTL / TB)

| Module / surface | Why |
|------------------|-----|
| `vibe_pcs_tx` (pack / egress toward PMA) | Valid-beat source; must not leave a static pin when there is no beat. |
| `vibe_pcs_rx` (unpack / ingress from PMA) | Must accept PRBS31 as idle / no valid traffic, not as a packed beat. |
| `vibe_pma_bnd` | Product 512b concat / slice; historical PRBS23 + `PMA_IDLE_MARK` idle-fill lives here today. |
| AFIFO boundary (`afifo_pma_lane_vld` / `pma_afifo_lane_vld`) | Idle vs packed-beat valid at the PMA↔AFIFO edge. No new PMA handshake. |
| Related TB | `tc_pma_*`, PMA loopback, `tc_nw_pkt_to_pma_tx` / `tc_phy_pma_pcs_boundary` / `tc_if_pma_no_handshake`, pyuvm PHY units that score `pcs_pma_txdata` / `pma_pcs_rxdata`. |

Clock / reset names stay exempt (`txclk` / `rxclk` / `_0`..`_3`). CR-B `{src}_{dst}_{meaning}` names stay.

---

## 5. Alignment with FS / AS

| Doc | Alignment |
|-----|-----------|
| **FS-0.2.7** | Overlay B PMA remains 512b @ 922 MHz, no extra handshake, no analog PMA. This CR does **not** rewrite FS locked datapath, FEC, AMCTL, or LMSM. Idle fill is a product-pin semantic on top of “every cycle is a sample.” FS true source is outside this repo. |
| **AS-0.1 / AS-0.1.2** | AS §3 / §5 T8 / §6 already: product PMA = `pcs_pma_txdata` / `pma_pcs_rxdata` + clocks; **NO PMA ready**; RX AFIFO overflow drop/count/irq. This CR keeps that. AS body is **not** rewritten in this PR. After SPEC merge, a later docs pass may echo the PRBS31 idle sentence into AS §3 if PM wants the two books identical. |
| **SPEC-0.2** | §4.4 (and the PMA rows in §1.1 / §2 / §4.1 / §6 / §15 / §18) take the idle = PRBS31 rule. Status stays **UNFROZEN**. Not a new SPEC version, not a freeze SHA. |

Do **not** treat historical #115 PRBS23 + `PMA_IDLE_MARK` as the SPEC idle rule after this CR.

---

## 6. Effects

| Effect | What it means |
|--------|----------------|
| Interface semantics | PMA 512b idle content is now specified (PRBS31 every cycle, both directions). Names, widths, and “no extra handshake” stay. |
| Not a freeze re-pin | Decision I **UNFROZEN** unchanged. No new CHANGELOG pin. Do **not** treat this CR as replacing `302ac943` or starting a new pin. |
| ≠ 1/3 ≠ 4/3 ≠ signoff | Does not open, continue, or close a consecutive-green series. Does not claim impl signoff. |
| Path B / FPGA | **Hold** / **deferred**, unchanged. Do not run tapeout or board bring-up from this CR. |
| No ECO for `ovf_l` | Decision **F1** still stands. |
| Historical idle-mark | #115 / PR116 PRBS23 + `PMA_IDLE_MARK` remains history on the last void pin. Design replaces pin-idle with PRBS31 **after** SPEC merge. |

---

## 7. Non-goals

1. **No RTL / TB / include / pycircuit in this PR.** Design and Verification follow after SPEC merge.
2. **No freeze re-pin.** Regime stays UNFROZEN.
3. **No extra handshake.** Do not add PMA `_vld` / `_ready` / enable.
4. **No analog PMA / SerDes / Gray / 预编码.** Still §非目标.
5. **No LMSM electrical-idle rewrite** (EEI / EEIB / AMCTL-with-EEI). Different from pin-idle PRBS31.
6. **No signoff claim.** Path B hold. FPGA deferred.
7. **Do not count this PR as 1/3 or 4/3.**
8. **This file does not rewrite FS-0.2.7 locked datapath** beyond the PMA pin-idle sentence.

---

## 8. Acceptance criteria (later RTL / TB — not this PR)

After SPEC merge, a later Design/Verification landing is Accept-ready when:

1. Every `txclk` cycle, each port `pcs_pma_txdata_*[511:0]` changes. Idle cycles are PRBS31; valid-traffic cycles keep today’s packed-lane beat.
2. Every `rxclk` cycle, each port `pma_pcs_rxdata_*[511:0]` is treated the same way: idle / no valid traffic = PRBS31 fill; valid traffic = existing per-beat data.
3. No PMA `_vld` / `_ready` / extra handshake name is added on the product pins.
4. `pcs_tx`, `pcs_rx`, `pma_bnd`, and the AFIFO valid boundary agree on idle vs packed beat (RX AFIFO overflow rule unchanged: drop, count, `irq_logic`).
5. TB / scoreboard / loopback no longer require PRBS23 + `PMA_IDLE_MARK` as the SPEC idle pattern.
6. Official lint stays Error=0 on the later RTL PR; no `txclk`→`rxclk` sample of `pcs_pma_txdata` is reopened (CDC hold from #115 / PR109 remains).
7. F1 `ovf_l` untouched. Path B / FPGA still hold. Not a freeze pin unless a later Xia pin CR says so.

---

## 9. Next actions (owners)

1. **Xia** — SPEC §4.4 + related interface rows + CHANGELOG. **This PR.**
2. **芯片开发PM** — Accept this docs CR. Then Design/Verification may land RTL/TB.
3. **Design** — PRBS31 idle fill in `pcs_tx` / `pcs_rx` / `pma_bnd` / AFIFO boundary after SPEC merge. Document polynomial / seed in that PR.
4. **Verification** — update TB and re-gate after the Design SHA. Do not start 1/3 from this docs PR.
