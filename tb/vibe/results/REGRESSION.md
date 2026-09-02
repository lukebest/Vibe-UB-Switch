# TP-0.3 regression — FS-0.2.7 Overlay B **content** compare

Compiled **TB** on `cursor/vibe-tb-g1-6065` against **PR8 HEAD** (sim-only; **not** committed).

Spec: **FS-0.2.7 / AS-0.1.2**. Official 159 IDs unchanged.
- NW↔DLL `data[511:0]` must match a unique 512-bit GOLDEN (TX and RX), not width-only.
- GOLDEN is not all-zero and not `old640[511:0]`. No LPH/NTH extract on the 512 bus.
- 640-bit DUT pin cannot PASS by matching `[511:0]`.

| Item | Value |
|------|--------|
| RTL compiled SHA | `a3ecec9f40e987e2dc49f586c34092c3ede5baa5` |
| RTL message | Fix overlay-B remainder shift width and CNA first-flit opcode |
| Overlay B in this SHA? | **Yes** — NW `fab_tx`/`fab_rx`/`dll_*` are `[511:0]`; DLL↔PCS stays 640 |
| SOP LPH (设计) | `[511:352]` (160b); `[351:0]` packet data. Not README `[511:496]`. |
| Gate | five Overlay-B TCs via `iverilog`/`vvp` (`make -C tb/vibe units` path) |

Checkers compare full 512-bit GOLDEN **and** SOP LPH fields from GOLDEN[511:352] vs DUT[511:352]. Do not patch `rtl/`.

## Five Overlay-B content TCs vs `a3ecec9f`

| TC | Result | What was compared |
|----|--------|-------------------|
| `tc_phy_nw_dll_512b` | **PASS** | TX `dll_tx===GOLDEN_TX` + SOP LPH; RX `fab_rx===GOLDEN_RX` + SOP LPH |
| `tc_nw_adapt_linkready` | **PASS** | same GOLDEN TX+RX + SOP LPH; LinkReady / mgmt pri |
| `tc_nw_pkt_to_pma_tx` | **PASS** | accepted-beat `dll_tx===GOLDEN_TX` + SOP LPH; PMA pack |
| `tc_port_smoke` | **PASS** | TX GOLDEN + SOP LPH; recovered `fab_rx===GOLDEN_TX`; PMA pack |
| `tc_nw_pkt_pma_loopback` | **PASS** | recovered RX 512b === TX GOLDEN; `fec_fail=0`; `am_locked=1111` |

## FAIL list (handoff to 设计)

**None** vs `a3ecec9f` on these five TCs.

## Reproduce

```bash
git fetch origin cursor/as01-rtl-82c7
git checkout a3ecec9 -- rtl
git restore --staged rtl
make -C tb/vibe units
git checkout HEAD -- rtl
```

## Matrix

[`TP_TC_MATRIX.md`](TP_TC_MATRIX.md) / [`TP-0.3.md`](TP-0.3.md) / [`docs/Vibe-UB-Switch-testpoints.md`](../../../docs/Vibe-UB-Switch-testpoints.md): **159/159**.
