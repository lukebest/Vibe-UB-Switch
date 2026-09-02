# TP-0.3 regression (Icarus gate) — FS-0.2.7 / AS-0.1.2

Compiled **TB** on `cursor/vibe-tb-g1-6065` against **PR8 / `origin/cursor/as01-rtl-82c7` HEAD** (sim-only checkout; **not** committed).

Spec this pass: **FS-0.2.7 Overlay B** + **AS-0.1.2**. Official IDs stay **159**.
- NW↔DLL is ONLY `data[511:0]` @ 1.25 GHz + vld/ready. No 640-bit window on the NW pin.
- 640-bit / 4×160 AFIFO is **DLL↔PCS**.
- Credit threshold **1024 is cell** (Luke 2026-09-02). Not flit. Not 1024×n.
- RT=10/11 still drop+count+irq. 512-vs-LPH field packing not invented.

| Item | Value |
|------|--------|
| RTL compiled SHA | `d6549521f56d6517a3bf0a25cbd8a1d5f614046a` |
| RTL message | Count credit pending-to-return in cells, threshold 1024 cell |
| RTL ref | `origin/cursor/as01-rtl-82c7` (PR #8 lineage) |
| Overlay B (512b NW) in this SHA? | **No** — `vibe_nw_adapt` / `vibe_port` still `fab_tx_data[639:0]` |
| 1024-cell comparator in this SHA? | **Yes** |
| Gate | `make -C tb/vibe units` (+ suite `last_run.txt`) |
| Units | **80 pass_files / 5 fail_files / 0 compile_fail** (`run1` count now 85 incl. `tc_phy_nw_dll_512b`) |
| Suite | **27/27 PASS** (`SUITE_RESULT PASS`) |
| Official matrix | 159 IDs; MAPPED=106 ADDED=16 HOLE=9 NEG=28 |

Checkers were **not** weakened. Width FAILs are expected-vs-actual for 设计 (do not patch `rtl/`).

## Affected units this pass

| TC | Result vs `d6549521` | Notes |
|----|----------------------|--------|
| `tc_credit_1024_flit_bp` | **PASS** | 1023 cell no `bp_nw`; 1024 cell `bp_nw`+`force_crd_ack`. Filename historical. |
| `tc_credit_1024_hole` | **PASS** | same 1023→1024 **cell** score (G7 closed as cell) |
| `tc_credit_grain_n` | **PASS** | consume `ceil_div` flits→cells; sat `fc_ovf` |
| `tc_credit_timeout_1us` | **PASS** | 1 µs still independent of VOQ |
| `tc_tp_holes` | **PASS** | G7 note: 1024 is cell |
| `tc_phy_nw_dll_512b` | **FAIL** | expected NW 512; DUT 640 |
| `tc_nw_adapt_linkready` | **FAIL** | same width gate (link_ready path not reached) |
| `tc_nw_pkt_pma_loopback` | **FAIL** | same; LPH score not reached |
| `tc_nw_pkt_to_pma_tx` | **FAIL** | same |
| `tc_port_smoke` | **FAIL** | same |

## FAIL list (handoff to 设计)

Overlay B is **not** in `d6549521`. All five FAILs are NW width 512 vs DUT 640.
Do **not** “fix” RTL from this TB branch.

### `tc_phy_nw_dll_512b` (TP-PHY-008)

```
FAIL tc_phy_nw_dll_512b
  stimulus : FS-0.2.7 Overlay B — NW↔DLL data[511:0] @1.25GHz
  expected : $bits(fab_tx_data)=512 (and fab_rx_data=512)
  actual   : NW fab_tx_data=640 fab_rx_data=640
  hier     : u_n.fab_tx_data / vibe_nw_adapt / vibe_port
  reproduce: make -C tb/vibe units
```

### `tc_nw_adapt_linkready`

```
FAIL tc_nw_adapt_linkready
  stimulus : FS-0.2.7 Overlay B NW↔DLL data[511:0]
  expected : $bits(fab_tx_data)=512
  actual   : 640
  hier     : u_n.fab_tx_data
  reproduce: make -C tb/vibe units
```

### `tc_nw_pkt_pma_loopback` (TP-PHY-012)

```
FAIL tc_nw_pkt_pma_loopback
  stimulus : FS-0.2.7 Overlay B: NW pin is data[511:0]
  expected : NW width 512
  actual   : DUT NW pin is not 512 (see $bits)
  hier     : u_p.fab_tx_data
  reproduce: make -C tb/vibe units
  actual   : $bits(u_p.fab_tx_data)=640 $bits(u_p.fab_rx_data)=640
```

### `tc_nw_pkt_to_pma_tx`

```
FAIL tc_nw_pkt_to_pma_tx
  stimulus : FS-0.2.7 Overlay B: NW pin is data[511:0]
  expected : NW width 512
  actual   : DUT NW pin is not 512
  hier     : u_p.fab_tx_data
  reproduce: make -C tb/vibe units
  actual   : $bits=640
```

### `tc_port_smoke`

```
FAIL tc_port_smoke
  stimulus : FS-0.2.7 Overlay B: NW pin is data[511:0]
  expected : NW width 512
  actual   : DUT NW pin is not 512
  hier     : u_p.fab_tx_data
  reproduce: make -C tb/vibe units
  actual   : $bits=640
```

Credit 1024-cell TCs **PASS** on this SHA — no credit FAIL to hand off.

## Reproduce

```bash
git fetch origin cursor/as01-rtl-82c7
git checkout d6549521f56d6517a3bf0a25cbd8a1d5f614046a -- rtl
git restore --staged rtl
make -C tb/vibe units
# restore TB-branch rtl before any commit:
git checkout HEAD -- rtl
```

## Matrix

See [`TP_TC_MATRIX.md`](TP_TC_MATRIX.md) vs [`TP-0.3.md`](TP-0.3.md): **ID sets equal, 159/159**.
Also [`docs/Vibe-UB-Switch-testpoints.md`](../../../docs/Vibe-UB-Switch-testpoints.md) (same table).
Verdicts: MAPPED=106, ADDED=16, HOLE=9, NEG=28.
