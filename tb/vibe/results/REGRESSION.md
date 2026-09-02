# TP-0.3 regression — FS-0.2.7 Overlay B **content** compare

Compiled **TB** on `cursor/vibe-tb-g1-6065` against **PR8 HEAD** (sim-only; **not** committed).

Spec: **FS-0.2.7 / AS-0.1.2**. Official 159 IDs unchanged.
- NW↔DLL `data[511:0]` must match a unique 512-bit GOLDEN (TX and RX), not width-only.
- GOLDEN is not all-zero and not `old640[511:0]`. No LPH/NTH extract on the 512 bus.
- 640-bit DUT pin cannot PASS by matching `[511:0]`.

| Item | Value |
|------|--------|
| RTL compiled SHA | `a3ecec9f` + parents `f7192ea` (overlay B 512b NW) |
| Full SHA | `a3ecec9` — Fix overlay-B remainder shift width and CNA first-flit opcode |
| Overlay B in this SHA? | **Yes** — `vibe_nw_adapt` / `vibe_port` `fab_*` / `dll_*` are `[511:0]`; DLL↔PCS stays 640 |
| Gate | `make -C tb/vibe units` (five Overlay-B TCs named below) |

Checkers not weakened. Loopback/port_smoke RX FAILs go to 设计. Do not patch `rtl/`.

## Five Overlay-B content TCs vs `a3ecec9`

| TC | Result | What was compared |
|----|--------|-------------------|
| `tc_phy_nw_dll_512b` | **PASS** | TX `dll_tx_data===GOLDEN_TX`; RX `fab_rx_data===GOLDEN_RX`; handshake |
| `tc_nw_adapt_linkready` | **PASS** | same GOLDEN TX+RX; LinkReady=0 blocks; mgmt pri uses GOLDEN_RX |
| `tc_nw_pkt_to_pma_tx` | **PASS** | accepted-beat `u_p.dll_tx_d===GOLDEN_TX`; PMA pack / lane / gear still scored |
| `tc_port_smoke` | **FAIL** | TX GOLDEN matched; RX `fab_rx_vld=0`, data=0 (not GOLDEN) |
| `tc_nw_pkt_pma_loopback` | **FAIL** | TX GOLDEN matched; recover `fab_rx===GOLDEN_TX` never happened |

## FAIL list (handoff to 设计)

TX NW→DLL content is good on this SHA. PMA loopback does **not** deliver the same 512-bit GOLDEN on NW RX (`fab_rx_vld` stayed 0). Supporting: `fec_fail=0`, `am_locked=1111`, `deskew=1`, `saw_txnz=1`, `saw_pcs_rx=0`.

### `tc_nw_pkt_pma_loopback` (TP-PHY-012)

```
  detail   : vld=0 last_rx=0...0 pcs_rx_v=0 am_lock=1111 fec_fail=0 deskew=1 afrv=0000
  peak     : saw_txnz=1 saw_afrv=1 saw_am=1 saw_pcs_rx=0 saw_fab_rx=0 saw_fec_fail=0 saw_deskew=1
FAIL tc_nw_pkt_pma_loopback
  stimulus : PMA loopback; recover NW RX data[511:0] === GOLDEN_TX
  expected : width=512 data=4e57353154582121a5a5a5a55a5a5a5a0123456789abcdeffedcba98765432101111111122222222333333334444444455555555666666667777777788888888
  actual   : width=512 data=00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
  hier     : u_p.fab_rx_data
  reproduce: make -C tb/vibe units
```

### `tc_port_smoke`

```
FAIL tc_port_smoke
  stimulus : PMA loopback; recover NW RX data[511:0] === GOLDEN_TX
  expected : width=512 data=4e57353154582121a5a5a5a55a5a5a5a0123456789abcdeffedcba98765432101111111122222222333333334444444455555555666666667777777788888888
  actual   : width=512 data=0000...0000
  hier     : u_p.fab_rx_data
  reproduce: make -C tb/vibe units
  actual   : fab_rx_vld=0 fec_fail=0 am_locked=1111
```

GOLDEN_TX lives in `tb/vibe/common/vibe_tb_nw512.svh`. TB does not invent LPH packing to force a PASS.

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
