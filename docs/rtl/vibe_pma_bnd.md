# vibe_pma_bnd

Product PMA boundary (AS-0.1 §3). Decision I stage-2 pyCircuit leaf.
Re-homes pre-Decision I stock RTL (PRBS23 + dest-domain resets +
`PMA_IDLE_MARK`, issue #115 / PR116) under the pycircuit → rtl flow.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/pma/vibe_pma_bnd.py` |
| Helpers | `pycircuit/pma/prbs23.py` |
| Product SV | `rtl/pma/vibe_pma_bnd.sv` |
| Instantiator | `vibe_port` (`u_pma`) |
| SPEC / CR-B | Unchanged. `{src}_{dst}_{meaning}`; clocks/resets exempt |

## Ports (product)

Same as tip `ef3f121` / freeze `302ac943`. No PMA ready. No input defaults
on `txrst_n` / `rxrst_n` (Verilator UNSUPPORTED; parent ties dest-domain
resets).

| Port | Dir | Notes |
|------|-----|--------|
| `txclk` | in | TX SerDes / PMA clock |
| `rxclk` | in | RX SerDes / PMA clock |
| `txrst_n` | in | TX-domain async active-low (no default) |
| `rxrst_n` | in | RX-domain async active-low (no default) |
| `afifo_pma_lane0..3[127:0]` | in | gear → PMA, 128b × 4 |
| `afifo_pma_lane_vld` | in | no `_ready`; fire is this valid |
| `pcs_pma_txdata[511:0]` | out | packed `[511:384]=lane3` … `[127:0]=lane0` |
| `pma_pcs_rxdata[511:0]` | in | pin / loopback 512b |
| `pma_afifo_lane0..3[127:0]` | out | PMA → AFIFO slice |
| `pma_afifo_lane_vld` | out | 0 when decorated pin-idle |

## Idle-PRBS (issue #115)

Every `txclk` without a DLL/PCS beat emits PRBS23 XOR `PMA_IDLE_MARK`
(`128'h8000…0000`) so the pin is never held at 0 and pin-idle is **not**
the same stream as PCS scramble(0) (same poly + seed). RX un-XORs the
mark, then tests the PRBS23 recurrence on each 128b slice. Raw PRBS /
scramble(0) keeps `pma_afifo_lane_vld`. Fan-in is `pma_pcs_rxdata` /
`rxclk` only — do **not** sample `txclk` `pcs_pma_txdata` (closed
txclk→rxclk CDC).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pma_bnd
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low reset, product PRBS functions,
and idle-mark stay.
