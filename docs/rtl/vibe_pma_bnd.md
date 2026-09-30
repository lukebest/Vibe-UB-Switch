# vibe_pma_bnd

Product PMA boundary (AS-0.1 §3 / SPEC §4.4). Decision I stage-2
pyCircuit leaf. Ports match tip `afcc2162`. Decision I **UNFROZEN**.
Path B hold. **No SPEC / CR-B name change.** Pin-idle follows
[CR-PMA-IDLE-PRBS31-2026-09-30](../cr/CR-PMA-IDLE-PRBS31-2026-09-30.md):
idle / no valid traffic = **PRBS31 every cycle**. Historical #115
PRBS23 + `PMA_IDLE_MARK` is **no longer** the SPEC idle rule.

| | |
|---|---|
| Python | `pycircuit/pma/vibe_pma_bnd.py` |
| Helpers | `pycircuit/pma/prbs31.py` (`prbs23.py` kept for history / PCS scramble) |
| Product SV | `rtl/pma/vibe_pma_bnd.sv` |
| Instantiator | `vibe_port` (`u_pma`) |
| SPEC / CR-B | Unchanged names. `{src}_{dst}_{meaning}`; clocks/resets exempt |

## Ports (product)

Same as tip `afcc2162`. No PMA ready. No input defaults on `txrst_n` /
`rxrst_n` (Verilator UNSUPPORTED; parent ties dest-domain resets).

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
| `pma_afifo_lane_vld` | out | 0 when PRBS31 pin-idle |

## Idle-PRBS31 (SPEC §4.4 / CR-PMA-IDLE-PRBS31)

Every `txclk` without a DLL/PCS beat emits ITU-T O.150 **PRBS31** so
the pin changes every clock. Valid traffic keeps the packed-lane beat
(`[127:0]`=lane0 … `[511:384]`=lane3). No new PMA `_vld` / `_ready`.

Design choice (documented here and in RTL / Python):

- **Poly:** x^31 + x^28 + 1. LFSR step: `{s[30:0], s[30] ^ s[27]}` (31-bit state).
- **Per-lane seed:** `{27'd1, lid[1:0], 2'b01}` for lid=0..3. Non-zero only.
- **Word:** 128b window, bit *i* = LFSR[0] after *i* steps (LSB first), then advance 128 steps per idle beat per lane.
- **No `PMA_IDLE_MARK` XOR.** PRBS31 is a different poly than PCS scramble(0) (PRBS23), so the decorated mark is unnecessary.

RX idle detect = PRBS31 recurrence `w[i] == w[i-31] ^ w[i-28]` on each
128b slice (no un-XOR). Non-PRBS31 (including scramble(0)) keeps
`pma_afifo_lane_vld`. Fan-in is `pma_pcs_rxdata` / `rxclk` only — do
**not** sample `txclk` `pcs_pma_txdata` (closed txclk→rxclk CDC).

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_pma_bnd
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low reset and product PRBS31
functions stay.
