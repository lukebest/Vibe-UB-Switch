# pyCircuit sources (Decision I)

RTL freeze `302ac943` is **unfrozen** for a pyCircuit redesign. This tree is the
Python DSL source. **SPEC functional semantics and CR-B port names are
unchanged.** `{src}_{dst}_{meaning}` (`dll` not `dl`). Do not rewrite the chip
here — leaves land one module at a time. Stage-1: scaffold + `vibe_afifo`.
Stage-2: `vibe_pma_bnd`. Stage-3: `vibe_sync2`. Stage-4: `vibe_rst_sync`.
Stage-5: `vibe_gear_128_160`.
Stage-6: `vibe_gear_160_128`.
Stage-7: `vibe_pcs_scramble`.
Stage-8: `vibe_ebch16`.
Stage-9: `vibe_pcs_tx_cw2beat`.
Stage-10: `vibe_pcs_tx_amctl`.
Stage-11: `vibe_rs128_120_enc`.
Stage-12: `vibe_rs128_120_dec`.
Stage-13: `vibe_pcs_rx_deskew`.
Stage-14: `vibe_pcs_rx_amctl_lock`.
Stage-15: `vibe_pcs_rx_unpack`.
Stage-16: `vibe_pcs_tx_pack`.
Stage-17: `vibe_pcs_tx_fec`.
Stage-18: `vibe_pcs_rx_fec`.
Stage-19: `vibe_pcs_tx_g1`.
Stage-20: `vibe_bcrc`.
Stage-21: `vibe_dll_credit`.
Stage-22: `vibe_dll_sm`.
Stage-23: `vibe_dll_rx`.
Stage-24: `vibe_dll_retry_ack_sm`.
Stage-25: `vibe_dll_retry_buf`.
Stage-26: `vibe_dll_retry_req_sm`.
Stage-27: `vibe_fecn_mark`.
Stage-28: `vibe_vl_rr`.
Stage-29: `vibe_route_lu`.
Stage-30: `vibe_port_sel`.
Stage-31: `vibe_voq_egr`.
Stage-32: `vibe_saf_ing`.
Stage-33: `vibe_xbar`.
Stage-34: `vibe_dll_tx`.

## Toolchain pin

| Item | Value |
|------|--------|
| Repo | [lukebest/pyCircuit](https://github.com/lukebest/pyCircuit) |
| Commit | `43cc5918e3d09ecc0c814cabef6c1384cb9980ae` |
| Release | pyc4.0 / pyc0.40 |
| PyPI name | `pycircuit-hisi` 0.1.0 (import remains `pycircuit`; CLI is `pycc`) |

File: [`TOOLCHAIN.lock`](TOOLCHAIN.lock).

Install (prefer wheel, else clone the pin):

```bash
sh scripts/pycircuit/setup_toolchain.sh
```

`python3 -m pip install pycircuit-hisi` was **not published** on 2026-09-22.
The setup script clones `lukebest/pyCircuit` at the commit above and
`pip install -e` the frontend. That does **not** install `pycc`. Building
`pycc` needs LLVM 19:

```bash
bash /path/to/pyCircuit/flows/scripts/pyc build
export PYC_TOOLCHAIN_ROOT=/path/to/pyCircuit/.pycircuit_out/toolchain/install
```

Do **not** put this repo's root on `PYTHONPATH`. The toolchain package is also
named `pycircuit`; a shadow import breaks emit.

## Layering

Mirrors `rtl/` (plus `cdc`, where the first leaf already lives):

```
pycircuit/
  common/     params + gray helpers (rtl/common)
  cdc/        vibe_afifo     ← stage-1 leaf (rtl/cdc/vibe_afifo.sv)
              vibe_sync2     ← stage-3 leaf (rtl/cdc/vibe_sync2.sv)
              vibe_rst_sync  ← stage-4 leaf (rtl/cdc/vibe_rst_sync.sv)
              vibe_gear_128_160 ← stage-5 leaf (rtl/cdc/vibe_gear_128_160.sv)
              vibe_gear_160_128 ← stage-6 leaf (rtl/cdc/vibe_gear_160_128.sv)
  pma/        vibe_pma_bnd   ← stage-2 leaf (rtl/pma/vibe_pma_bnd.sv)
  pcs/        vibe_pcs_scramble ← stage-7 leaf (rtl/pcs/vibe_pcs_scramble.sv)
              vibe_ebch16    ← stage-8 leaf (rtl/pcs/vibe_ebch16.sv)
              vibe_pcs_tx_cw2beat ← stage-9 leaf (rtl/pcs/vibe_pcs_tx_cw2beat.sv)
              vibe_pcs_tx_amctl ← stage-10 leaf (rtl/pcs/vibe_pcs_tx_amctl.sv)
              vibe_rs128_120_enc ← stage-11 leaf (rtl/pcs/vibe_rs128_120_enc.sv)
              vibe_rs128_120_dec ← stage-12 leaf (rtl/pcs/vibe_rs128_120_dec.sv)
              vibe_pcs_rx_deskew ← stage-13 leaf (rtl/pcs/vibe_pcs_rx_deskew.sv)
              vibe_pcs_rx_amctl_lock ← stage-14 leaf (rtl/pcs/vibe_pcs_rx_amctl_lock.sv)
              vibe_pcs_rx_unpack ← stage-15 leaf (rtl/pcs/vibe_pcs_rx_unpack.sv)
              vibe_pcs_tx_pack ← stage-16 leaf (rtl/pcs/vibe_pcs_tx_pack.sv)
              vibe_pcs_tx_fec  ← stage-17 leaf (rtl/pcs/vibe_pcs_tx_fec.sv)
              vibe_pcs_rx_fec  ← stage-18 leaf (rtl/pcs/vibe_pcs_rx_fec.sv)
              vibe_pcs_tx_g1   ← stage-19 leaf (rtl/pcs/vibe_pcs_tx_g1.sv)
  dll/        vibe_bcrc      ← stage-20 leaf (rtl/dll/vibe_bcrc.sv)
              vibe_dll_credit ← stage-21 leaf (rtl/dll/vibe_dll_credit.sv)
              vibe_dll_sm    ← stage-22 leaf (rtl/dll/vibe_dll_sm.sv)
              vibe_dll_rx    ← stage-23 leaf (rtl/dll/vibe_dll_rx.sv)
              vibe_dll_retry_ack_sm ← stage-24 leaf (rtl/dll/vibe_dll_retry_ack_sm.sv)
              vibe_dll_retry_buf ← stage-25 leaf (rtl/dll/vibe_dll_retry_buf.sv)
              vibe_dll_retry_req_sm ← stage-26 leaf (rtl/dll/vibe_dll_retry_req_sm.sv)
              vibe_dll_tx    ← stage-34 leaf (rtl/dll/vibe_dll_tx.sv)
  fabric/     vibe_fecn_mark ← stage-27 leaf (rtl/fabric/vibe_fecn_mark.sv)
              vibe_vl_rr     ← stage-28 leaf (rtl/fabric/vibe_vl_rr.sv)
              vibe_route_lu  ← stage-29 leaf (rtl/fabric/vibe_route_lu.sv)
              vibe_port_sel  ← stage-30 leaf (rtl/fabric/vibe_port_sel.sv)
              vibe_voq_egr   ← stage-31 leaf (rtl/fabric/vibe_voq_egr.sv)
              vibe_saf_ing   ← stage-32 leaf (rtl/fabric/vibe_saf_ing.sv)
              vibe_xbar      ← stage-33 leaf (rtl/fabric/vibe_xbar.sv)
  nw/ mgmt/ port/ top/   stubs
```

`dll` stays `dll`, not `dl`. Later leaves land one module at a time.

## Regenerate `vibe_afifo`

```bash
make -C pycircuit vibe_afifo
# or
sh scripts/pycircuit/emit.sh
```

What that does:

1. Frontend emit `vibe_afifo.pyc` when `import pycircuit` works.
2. `pycc --emit=verilog` when `pycc` is on `PATH` (optional prototype).
3. **Always** land the hand-finished product SV via
   `pycircuit/cdc/handfinish_vibe_afifo.py` → `rtl/cdc/vibe_afifo.sv`.

`pycc` lowers registers to **sync active-high** reset and CDC to
`pyc_cdc_sync`. Product RTL must keep **async active-low** `wrst_n` /
`rrst_n`, combo RAM (contents not reset), `vibe_sync2`, and
`vibe_bin2gray5` / `vibe_gray2bin5`. That is why the landed file is
hand-finished. Do not drop those when a later emit looks “cleaner.”

Do **not** instantiate `pyc.async_fifo`. That primitive is ready/valid, has
no `wocc` / `almost_full`, and would change the product interface.

## First leaf

See [`docs/rtl/vibe_afifo.md`](../docs/rtl/vibe_afifo.md) and
[`cdc/vibe_afifo.py`](cdc/vibe_afifo.py).

## Stage-2 leaf `vibe_pma_bnd`

Same emit pattern. Product SV keeps async-low `txrst_n` / `rxrst_n`,
PRBS23 pin-idle, and `PMA_IDLE_MARK` decorate/undecorate (issue #115).
Do not sample `txclk` into the RX idle check.

```bash
make -C pycircuit vibe_pma_bnd
# or
sh scripts/pycircuit/emit.sh vibe_pma_bnd
```

See [`docs/rtl/vibe_pma_bnd.md`](../docs/rtl/vibe_pma_bnd.md) and
[`pma/vibe_pma_bnd.py`](pma/vibe_pma_bnd.py).

## Stage-3 leaf `vibe_sync2`

Same emit pattern. Product SV keeps async-low `rst_n` (`or negedge rst_n`)
and the 2-FF body (`q1` then `q`). This is the same-layer CDC cell
`vibe_afifo` already instantiates. Leave `vibe_rst_sync` / gear for later.

```bash
make -C pycircuit vibe_sync2
# or
sh scripts/pycircuit/emit.sh vibe_sync2
```

See [`docs/rtl/vibe_sync2.md`](../docs/rtl/vibe_sync2.md) and
[`cdc/vibe_sync2.py`](cdc/vibe_sync2.py).

## Stage-4 leaf `vibe_rst_sync`

Same emit pattern. Product SV keeps async assert on `rst_n_in`
(`or negedge rst_n_in`) and sync release into `clk` (`r1` then
`rst_n_out`). This is the same-layer CDC reset cell `vibe_port`
already instantiates (`u_txrst` / `u_rxrst`). Leave gear for later.

```bash
make -C pycircuit vibe_rst_sync
# or
sh scripts/pycircuit/emit.sh vibe_rst_sync
```

See [`docs/rtl/vibe_rst_sync.md`](../docs/rtl/vibe_rst_sync.md) and
[`cdc/vibe_rst_sync.py`](cdc/vibe_rst_sync.py).

## Stage-5 leaf `vibe_gear_128_160`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo `in_ready = !hold_vld || out_ready`,
and the 5-beat dual-residue `case (phase)` (5×128 = 4×160). This is
the same-layer RX gear `vibe_port` already instantiates
(`u_rg0`..`u_rg3`). Leave `vibe_gear_160_128` (TX 160→128) for later.

```bash
make -C pycircuit vibe_gear_128_160
# or
sh scripts/pycircuit/emit.sh vibe_gear_128_160
```

See [`docs/rtl/vibe_gear_128_160.md`](../docs/rtl/vibe_gear_128_160.md) and
[`cdc/vibe_gear_128_160.py`](cdc/vibe_gear_128_160.py).

## Stage-6 leaf `vibe_gear_160_128`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo `in_ready = can_load && (rbits != 4)`,
and the 4-beat residue `case (rbits)` (4×160 = 5×128). This is
the same-layer TX gear `vibe_port` already instantiates
(`u_g0`..`u_g3`). Same-layer pair of stage-5 `vibe_gear_128_160`.

```bash
make -C pycircuit vibe_gear_160_128
# or
sh scripts/pycircuit/emit.sh vibe_gear_160_128
```

See [`docs/rtl/vibe_gear_160_128.md`](../docs/rtl/vibe_gear_160_128.md) and
[`cdc/vibe_gear_160_128.py`](cdc/vibe_gear_160_128.py).

## Stage-7 leaf `vibe_pcs_scramble`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo 160b `xmask` from the current LFSR,
pass-through when `en=0` (AMCTL/EEIB; LFSR does not advance),
and seed `{19'd1, lane_id, 2'b01}`. This is the first PCS cell
(`vibe_pcs_tx` `u_s0`..`u_s3`, `vibe_pcs_rx` `u_d0`..`u_d3`).
Leave `vibe_pcs_tx` / rx / FEC / RS for later.

```bash
make -C pycircuit vibe_pcs_scramble
# or
sh scripts/pycircuit/emit.sh vibe_pcs_scramble
```

See [`docs/rtl/vibe_pcs_scramble.md`](../docs/rtl/vibe_pcs_scramble.md) and
[`pcs/vibe_pcs_scramble.py`](pcs/vibe_pcs_scramble.py).

## Stage-8 leaf `vibe_ebch16`

Same emit pattern. Product SV keeps the combo `case (cw_sel)` Table 3-5
LUT (`cw_sel[4:0]` → `cw[15:0]`; default `16'hFFFF`). This is the
same-layer PCS helper `vibe_pcs_tx_amctl` and `vibe_pcs_rx_amctl_lock`
already instantiate. Leave `vibe_pcs_tx` / rx / FEC / RS / amctl for
later.

```bash
make -C pycircuit vibe_ebch16
# or
sh scripts/pycircuit/emit.sh vibe_ebch16
```

See [`docs/rtl/vibe_ebch16.md`](../docs/rtl/vibe_ebch16.md) and
[`pcs/vibe_ebch16.py`](pcs/vibe_ebch16.py).

## Stage-9 leaf `vibe_pcs_tx_cw2beat`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo `cw_ready` / `beat_vld` / `beat_data`,
and the ready/valid 1024→2×512 split (high beat first). This is the
same-layer PCS cell `vibe_pcs_tx` already instantiates (`u_cw`).
Leave `vibe_pcs_tx` / amctl / pack / FEC / RS / rx for later.

```bash
make -C pycircuit vibe_pcs_tx_cw2beat
# or
sh scripts/pycircuit/emit.sh vibe_pcs_tx_cw2beat
```

See [`docs/rtl/vibe_pcs_tx_cw2beat.md`](../docs/rtl/vibe_pcs_tx_cw2beat.md) and
[`pcs/vibe_pcs_tx_cw2beat.py`](pcs/vibe_pcs_tx_cw2beat.py).

## Stage-10 leaf `vibe_pcs_tx_amctl`

Same emit pattern. Product SV keeps the stock `vibe_ebch16` instances,
combo LID `case (lane_id)`, and 40-symbol assemble (BODY / END / LID /
CTRL_TYPE Link Width / CTRL_DETAIL x4 SDF). `clk` / `rst_n` /
`sdf_period` stay on the pin list (pack wires them); the combo body
does not sample them. This is the same-layer PCS cell
`vibe_pcs_tx_pack` already instantiates (`u_am0`..`u_am3`).
Leave `vibe_pcs_tx` / pack / FEC / RS / rx for later.

```bash
make -C pycircuit vibe_pcs_tx_amctl
# or
sh scripts/pycircuit/emit.sh vibe_pcs_tx_amctl
```

See [`docs/rtl/vibe_pcs_tx_amctl.md`](../docs/rtl/vibe_pcs_tx_amctl.md) and
[`pcs/vibe_pcs_tx_amctl.py`](pcs/vibe_pcs_tx_amctl.py).

## Stage-11 leaf `vibe_rs128_120_enc`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_fn.vh"`, `vibe_gf256_mul`
LFSR step, combo `in_ready = busy && (cnt < 120)`, and
`parity = {r7..r0}`. This is the same-layer PCS FEC building
block `vibe_pcs_tx_fec` already instantiates (`u_enc_a` /
`u_enc_b`). Leave `vibe_pcs_tx_fec` / pack / g1 / tx wrap / rx /
decoder for later.

```bash
make -C pycircuit vibe_rs128_120_enc
# or
sh scripts/pycircuit/emit.sh vibe_rs128_120_enc
```

See [`docs/rtl/vibe_rs128_120_enc.md`](../docs/rtl/vibe_rs128_120_enc.md) and
[`pcs/vibe_rs128_120_enc.py`](pcs/vibe_rs128_120_enc.py).

## Stage-12 leaf `vibe_rs128_120_dec`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_fn.vh"`, combo
next-syndromes (last symbol included before `fec_fail`),
`msg[0:119]` pack into 960b `data_out`, and
`in_ready = busy && (cnt < 128)`. This is the same-layer
PCS FEC building block paired with stage-11
`vibe_rs128_120_enc`. `vibe_pcs_rx_fec` uses the same
Horner recurrence in one shot (not an instance). Leave
FEC wrap / pack / g1 / tx / rx / amctl_lock / deskew /
unpack for later.

```bash
make -C pycircuit vibe_rs128_120_dec
# or
sh scripts/pycircuit/emit.sh vibe_rs128_120_dec
```

See [`docs/rtl/vibe_rs128_120_dec.md`](../docs/rtl/vibe_rs128_120_dec.md) and
[`pcs/vibe_rs128_120_dec.py`](pcs/vibe_rs128_120_dec.py).

## Stage-13 leaf `vibe_pcs_rx_deskew`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo `aligned` / `out_vld`,
pass-through `out0`..`out3`, first-AMCTL lock pointers, and
hunt FIFOs whose contents are not reset. Factory
physical=logical (U24): no lane swap and no delay once
aligned. This is the same-layer PCS cell `vibe_pcs_rx`
already instantiates (`u_dsk`). Leave FEC wrap / pack / g1 /
tx / rx tops / amctl_lock / unpack for later.

```bash
make -C pycircuit vibe_pcs_rx_deskew
# or
sh scripts/pycircuit/emit.sh vibe_pcs_rx_deskew
```

See [`docs/rtl/vibe_pcs_rx_deskew.md`](../docs/rtl/vibe_pcs_rx_deskew.md) and
[`pcs/vibe_pcs_rx_deskew.py`](pcs/vibe_pcs_rx_deskew.py).

## Stage-14 leaf `vibe_pcs_rx_amctl_lock`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"`, seven
`vibe_ebch16` instances, combo `is_amctl`, and the hunt /
confirm / unlock always-block (`CONFIRM_N` = `UNLOCK_N` = 3).
Factory physical=logical (U24): LID not {0,1,2,3} sets
`lid_bad`; no lane swap. This is the same-layer PCS cell
`vibe_pcs_rx` already instantiates (`u_l0`..`u_l3`). Continues
the RX path after stage-13 deskew; pairs with stage-10
`vibe_pcs_tx_amctl`. Leave FEC wrap / pack / g1 / tx / rx
tops / unpack for later.

```bash
make -C pycircuit vibe_pcs_rx_amctl_lock
# or
sh scripts/pycircuit/emit.sh vibe_pcs_rx_amctl_lock
```

See [`docs/rtl/vibe_pcs_rx_amctl_lock.md`](../docs/rtl/vibe_pcs_rx_amctl_lock.md) and
[`pcs/vibe_pcs_rx_amctl_lock.py`](pcs/vibe_pcs_rx_amctl_lock.py).

## Stage-15 leaf `vibe_pcs_rx_unpack`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), stock `am_gap = 1'b0` default, combo
`beat_vld` / `beat_data`, and the dual-buffer 4×640 → 5×512
always-block (inverse G2). This is the same-layer PCS cell
`vibe_pcs_rx` already instantiates (`u_un`). Continues the
RX path after stage-13 deskew and stage-14 amctl_lock.
Leave FEC wrap / pack / g1 / tx / rx tops for later.

```bash
make -C pycircuit vibe_pcs_rx_unpack
# or
sh scripts/pycircuit/emit.sh vibe_pcs_rx_unpack
```

See [`docs/rtl/vibe_pcs_rx_unpack.md`](../docs/rtl/vibe_pcs_rx_unpack.md) and
[`pcs/vibe_pcs_rx_unpack.py`](pcs/vibe_pcs_rx_unpack.py).

## Stage-16 leaf `vibe_pcs_tx_pack`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"`, four
`vibe_pcs_tx_amctl` instances, combo `beat_ready` / `lane_vld` /
`am_word` / lane mux, and the timer / pack / emit always-block
(5×512 → 4×640, inverse G2). This is the same-layer PCS cell
`vibe_pcs_tx` already instantiates (`u_pack`). Inverse of
stage-15 `vibe_pcs_rx_unpack`. Instantiates stage-10
`vibe_pcs_tx_amctl` (`u_am0`..`u_am3`). Leave FEC wrap / g1 /
tx / rx tops for later.

```bash
make -C pycircuit vibe_pcs_tx_pack
# or
sh scripts/pycircuit/emit.sh vibe_pcs_tx_pack
```

See [`docs/rtl/vibe_pcs_tx_pack.md`](../docs/rtl/vibe_pcs_tx_pack.md) and
[`pcs/vibe_pcs_tx_pack.py`](pcs/vibe_pcs_tx_pack.py).

## Stage-17 leaf `vibe_pcs_tx_fec`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"`, two
`vibe_rs128_120_enc` instances, combo `win_ready` / symbol
slices / `enc_*_vld`, and the collect / encode / bypass /
emit always-block (two interleaved RS(128,120); T=4 / T=2 /
bypass). This is the same-layer PCS cell `vibe_pcs_tx`
already instantiates (`u_fec`). Instantiates stage-11
`vibe_rs128_120_enc` (`u_enc_a` / `u_enc_b`). Leave RX FEC
wrap / g1 / tx / rx tops for later.

```bash
make -C pycircuit vibe_pcs_tx_fec
# or
sh scripts/pycircuit/emit.sh vibe_pcs_tx_fec
```

See [`docs/rtl/vibe_pcs_tx_fec.md`](../docs/rtl/vibe_pcs_tx_fec.md) and
[`pcs/vibe_pcs_tx_fec.py`](pcs/vibe_pcs_tx_fec.py).

## Stage-18 leaf `vibe_pcs_rx_fec`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"` /
`vibe_ub_fn.vh`, combo `beat_ready = !win_vld`, stock
`am_gap = 1'b0` default on waived line 14, inline
`gf_mul2` / `rs_syndromes` (no `vibe_rs128_120_dec`
instance), and the collect / check / emit always-block
(2×512 → syndrome or bypass → 960b / `fec_fail`). This is
the same-layer PCS cell `vibe_pcs_rx` already instantiates
(`u_fec`). Pairs with stage-17 `vibe_pcs_tx_fec`. Leave
g1 / tx / rx tops for later.

```bash
make -C pycircuit vibe_pcs_rx_fec
# or
sh scripts/pycircuit/emit.sh vibe_pcs_rx_fec
```

See [`docs/rtl/vibe_pcs_rx_fec.md`](../docs/rtl/vibe_pcs_rx_fec.md) and
[`pcs/vibe_pcs_rx_fec.py`](pcs/vibe_pcs_rx_fec.py).

## Stage-19 leaf `vibe_pcs_tx_g1`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), combo `in_ready` / `win_data` /
`win_vld`, `NULL_FLIT = 160'd0`, rem / rem_vld / nflit /
acc / have, and the collect / rem leftover / idle-Null
always-block (6 flits / 960b FEC window; AS-0.1 §5 T2).
This is the same-layer PCS cell `vibe_pcs_tx` already
instantiates (`u_g1`). After stage-17 `vibe_pcs_tx_fec` /
stage-18 `vibe_pcs_rx_fec`. Self-contained (no child
instances). Leave tx / rx tops for later.

```bash
make -C pycircuit vibe_pcs_tx_g1
# or
sh scripts/pycircuit/emit.sh vibe_pcs_tx_g1
```

See [`docs/rtl/vibe_pcs_tx_g1.md`](../docs/rtl/vibe_pcs_tx_g1.md) and
[`pcs/vibe_pcs_tx_g1.py`](pcs/vibe_pcs_tx_g1.py).

## Stage-20 leaf `vibe_bcrc`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"` for
`VIBE_BCRC_POLY`, `crc30_step`, the 160-bit eat loop,
CRC30 init all-1s / no invert, and
`{1'b0, error_flag, crc[29:0]}` on `last` (bit31 reserved,
bit30 `ERROR_FLAG`; AS-0.1 §12). First DLL leaf after PCS
leaf cells (stage-1..19). Self-contained (no child
instances). Unit helper (TB `u_bcrc`); `vibe_dll_tx`
inlines the same CRC30. Leave PCS tx / rx tops and the
rest of DLL for later.

```bash
make -C pycircuit vibe_bcrc
# or
sh scripts/pycircuit/emit.sh vibe_bcrc
```

See [`docs/rtl/vibe_bcrc.md`](../docs/rtl/vibe_bcrc.md) and
[`dll/vibe_bcrc.py`](dll/vibe_bcrc.py).

## Stage-21 leaf `vibe_dll_credit`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"` for
`VIBE_CREDIT_THRESH` / `VIBE_US_CYC`, `ceil_div`, consume
`ceil(DLLDP_flits/n)` (CFG0 skip), credit return in cells,
thresh 1024 → `bp_nw` + force Crd_Ack, 1µs timeout →
`proto_err`, and 17-bit cells-sum `fc_ovf` (AS-0.1 §12 /
FS-0.2.6). No credit underflow code. Second DLL leaf after
`vibe_bcrc`. Self-contained (no child instances).
`vibe_dll` instantiates it (`u_crd`). Leave PCS tx / rx
tops and the rest of DLL for later.

```bash
make -C pycircuit vibe_dll_credit
# or
sh scripts/pycircuit/emit.sh vibe_dll_credit
```

See [`docs/rtl/vibe_dll_credit.md`](../docs/rtl/vibe_dll_credit.md) and
[`dll/vibe_dll_credit.py`](dll/vibe_dll_credit.py).

## Stage-22 leaf `vibe_dll_sm`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), Disabled when `LinkUp==0`, no
entity-reset pin (must not force Disabled via `rst`
alone beyond async `rst_n` / `port_rst`), states
Disabled → Param → Credit → Normal, `dll_error` →
Disabled, and `status_up` when Normal (AS-0.1 §12).
Third DLL leaf after `vibe_bcrc` / `vibe_dll_credit`.
Self-contained (no child instances). `vibe_dll`
instantiates it (`u_sm`). Leave PCS tx / rx tops and
remaining DLL wraps (retry_*, tx/rx, dll top) for later.

```bash
make -C pycircuit vibe_dll_sm
# or
sh scripts/pycircuit/emit.sh vibe_dll_sm
```

See [`docs/rtl/vibe_dll_sm.md`](../docs/rtl/vibe_dll_sm.md) and
[`dll/vibe_dll_sm.py`](dll/vibe_dll_sm.py).

## Stage-23 leaf `vibe_dll_rx`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_fn.vh"` for
`vibe_lph_cfg` / `vibe_lph_vl` / `vibe_pkt_bytes`,
parameter `RXBUF` default 1024, 640b PCS → 4 flits /
unBCRC / 512b NW remainder, LPH first 160b, EOP leftover
drop, CFG0 terminate, FEC/BCRC fail → Go-Back-N, and
`start_ack` tied 0 (AS-0.1.2 / FS-0.2.7 overlay B).
Fourth DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm`. Self-contained (no child instances).
`vibe_dll` instantiates it (`u_rx`). Leave PCS tx / rx
tops, `vibe_dll_retry_*`, `vibe_dll_tx`, and `vibe_dll`
top for later.

```bash
make -C pycircuit vibe_dll_rx
# or
sh scripts/pycircuit/emit.sh vibe_dll_rx
```

See [`docs/rtl/vibe_dll_rx.md`](../docs/rtl/vibe_dll_rx.md) and
[`dll/vibe_dll_rx.py`](dll/vibe_dll_rx.py).

## Stage-24 leaf `vibe_dll_retry_ack_sm`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), NORMAL / ACK (1 Idle + 32 Ack then
replay `RdPtr=RcvPtr` until `WrPtr`) (AS-0.1 §12). Fifth
DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx`. Self-contained (no child
instances). `vibe_dll` instantiates it (`u_ack`). Leave
PCS tx / rx tops, `vibe_dll_tx`, other `retry_*`
(`retry_buf`, `retry_req_sm`), and `vibe_dll` top for
later.

```bash
make -C pycircuit vibe_dll_retry_ack_sm
# or
sh scripts/pycircuit/emit.sh vibe_dll_retry_ack_sm
```

See [`docs/rtl/vibe_dll_retry_ack_sm.md`](../docs/rtl/vibe_dll_retry_ack_sm.md) and
[`dll/vibe_dll_retry_ack_sm.py`](dll/vibe_dll_retry_ack_sm.py).

## Stage-25 leaf `vibe_dll_retry_buf`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), depth-256 RETRY buffer (Null and
Retry blocks do not enter; `NumFreeBuf+ReleaseSize>256`
→ DL Protocol Error) (AS-0.1 §12). Sixth DLL leaf after
`vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm`. Self-contained
(no child instances). `vibe_dll` instantiates it
(`u_rbuf`). Leave PCS tx / rx tops, `vibe_dll_tx`,
`vibe_dll_retry_req_sm`, and `vibe_dll` top for later.

```bash
make -C pycircuit vibe_dll_retry_buf
# or
sh scripts/pycircuit/emit.sh vibe_dll_retry_buf
```

See [`docs/rtl/vibe_dll_retry_buf.md`](../docs/rtl/vibe_dll_retry_buf.md) and
[`dll/vibe_dll_retry_buf.py`](dll/vibe_dll_retry_buf.py).

## Stage-26 leaf `vibe_dll_retry_req_sm`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), NORMAL / REQ (1 Idle + burst Req) /
WAIT (`RETRY_WAIT_CYC`, default 12500) / RETRAIN / ERROR
(AS-0.1 §12). Seventh DLL leaf after `vibe_bcrc` /
`vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf`.
Self-contained (no child instances). `vibe_dll`
instantiates it (`u_req`). Leave PCS tx / rx tops,
`vibe_dll_tx`, and `vibe_dll` top for later.

```bash
make -C pycircuit vibe_dll_retry_req_sm
# or
sh scripts/pycircuit/emit.sh vibe_dll_retry_req_sm
```

See [`docs/rtl/vibe_dll_retry_req_sm.md`](../docs/rtl/vibe_dll_retry_req_sm.md) and
[`dll/vibe_dll_retry_req_sm.py`](dll/vibe_dll_retry_req_sm.py).

## Stage-27 leaf `vibe_fecn_mark`

Same emit pattern. Product SV keeps the combo FECN / LoC
rewrite (CCI.Mode `3'b100` or `3'b010` and local congestion
`voq_occ >= FECN_WM` worse than packet FECN; else
pass-through). Not CAQM (AS-0.1 §8). First fabric leaf after
DLL helpers (stage-20..26). Self-contained (no child
instances). `vibe_fabric` instantiates it (`u_fecn`). Leave
PCS tx / rx tops, `vibe_dll_tx`, and `vibe_dll` top for
later.

```bash
make -C pycircuit vibe_fecn_mark
# or
sh scripts/pycircuit/emit.sh vibe_fecn_mark
```

See [`docs/rtl/vibe_fecn_mark.md`](../docs/rtl/vibe_fecn_mark.md) and
[`fabric/vibe_fecn_mark.py`](fabric/vibe_fecn_mark.py).

## Stage-28 leaf `vibe_vl_rr`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), RR among non-empty VOQs of an egress
(first nonempty from `rr`, wrap 16; on `grant && valid`
advance `rr` to `vl_sel+1`; reset clears `rr`). FCFS within
VL; no SL (AS-0.1 §8). Second fabric leaf after
`vibe_fecn_mark`. Self-contained (no child instances).
`vibe_fabric` instantiates it (`u_rr`). Leave PCS tx / rx
tops, `vibe_dll_tx`, and `vibe_dll` top for later.

```bash
make -C pycircuit vibe_vl_rr
# or
sh scripts/pycircuit/emit.sh vibe_vl_rr
```

See [`docs/rtl/vibe_vl_rr.md`](../docs/rtl/vibe_vl_rr.md) and
[`fabric/vibe_vl_rr.py`](fabric/vibe_vl_rr.py).

## Stage-29 leaf `vibe_route_lu`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `!rst_n || device_rst` table
clear, CFG0_ROUTE_TABLE dest → 4-bit egress bitmap
(`DEPTH=256`), and RT=10/11 DROP (pulse `drop_g1`).
No Dijkstra, no treat-as-RT=00, no RT rewrite
(AS-0.1 §2/§8 + FS-0.2.3 G1). Third fabric leaf after
`vibe_fecn_mark` / `vibe_vl_rr`. Self-contained (no
child instances). `vibe_fabric` instantiates it
(`u_rt`, `g_rt.u_rti`). Leave PCS tx / rx tops,
`vibe_dll_tx`, `vibe_dll` top, and `vibe_fabric` top
for later.

```bash
make -C pycircuit vibe_route_lu
# or
sh scripts/pycircuit/emit.sh vibe_route_lu
```

See [`docs/rtl/vibe_route_lu.md`](../docs/rtl/vibe_route_lu.md) and
[`fabric/vibe_route_lu.py`](fabric/vibe_route_lu.py).

## Stage-30 leaf `vibe_port_sel`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `available = bitmap & status_up`
(forced 0 if `drop_g1`), Default / port-0 fallback
(`4'b0001`) AND `status_up`, drop + `drop_down_cnt` when
still empty (no flood), RT=00 per-flow sticky RR
(`fidx=vl`, sticky `[0:15]`), and RT=01 per-packet RR via
`rr` (`pick_rr` walks 4 ports from start; AS-0.1 §2/§8).
Fourth fabric leaf after `vibe_fecn_mark` / `vibe_vl_rr` /
`vibe_route_lu`. Self-contained (no child instances).
`vibe_fabric` instantiates it (`u_ps`, `g_rt.u_psi`).
Leave PCS tx / rx tops, `vibe_dll_tx`, `vibe_dll` top,
and `vibe_fabric` top for later. Do not migrate
`vibe_voq_egr` / `vibe_saf_ing` / `vibe_xbar` here.

```bash
make -C pycircuit vibe_port_sel
# or
sh scripts/pycircuit/emit.sh vibe_port_sel
```

See [`docs/rtl/vibe_port_sel.md`](../docs/rtl/vibe_port_sel.md) and
[`fabric/vibe_port_sel.py`](fabric/vibe_port_sel.py).

## Stage-31 leaf `vibe_voq_egr`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), 16 VL × DEPTH mem + sop/eop/age,
combo `wr_ready` / `rd_*` / `nonempty` / `occ_vl0`,
enqueue `age = VIBE_US_CYC`, and 1 µs deadlock timeout
from enqueue (AS-0.1 §8/§14). Fifth fabric leaf after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel`. Self-contained (no child instances).
`vibe_fabric` instantiates it (`g_egr.u_voq`).
Leave PCS tx / rx tops, `vibe_dll_tx`, `vibe_dll` top,
and `vibe_fabric` top for later. Do not migrate
`vibe_saf_ing` / `vibe_xbar` here.

```bash
make -C pycircuit vibe_voq_egr
# or
sh scripts/pycircuit/emit.sh vibe_voq_egr
```

See [`docs/rtl/vibe_voq_egr.md`](../docs/rtl/vibe_voq_egr.md) and
[`fabric/vibe_voq_egr.py`](fabric/vibe_voq_egr.py).

## Stage-32 leaf `vibe_saf_ing`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), DEPTH mem, combo `in_ready` /
`pkt_*`, header temps `plen` / `dflits` (combo, not
BLKSEQ), store-and-forward until declared beats, and
16–4300 B Packet Length Error drop (AS-0.1 §8). Sixth
fabric leaf after `vibe_fecn_mark` / `vibe_vl_rr` /
`vibe_route_lu` / `vibe_port_sel` / `vibe_voq_egr`.
Self-contained (no child instances). `vibe_fabric`
instantiates it (`g_saf.u_saf`). Leave PCS tx / rx
tops, `vibe_dll_tx`, `vibe_dll` top, and `vibe_fabric`
top for later. Do not migrate `vibe_xbar` here.

```bash
make -C pycircuit vibe_saf_ing
# or
sh scripts/pycircuit/emit.sh vibe_saf_ing
```

See [`docs/rtl/vibe_saf_ing.md`](../docs/rtl/vibe_saf_ing.md) and
[`fabric/vibe_saf_ing.py`](fabric/vibe_saf_ing.py).

## Stage-33 leaf `vibe_xbar`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), unpacked 4-port arrays, candidate
grant independent of `out_ready` (UNOPTFLAT `xb_r`),
ingress RR on conflict, one full packet per grant, and
down-port no-DLLDP (AS-0.1 §8). Seventh fabric leaf after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel` / `vibe_voq_egr` / `vibe_saf_ing`.
Self-contained (no child instances). `vibe_fabric`
instantiates it (`u_xbar`). Leave PCS tx / rx tops,
`vibe_dll_tx`, `vibe_dll` top, and `vibe_fabric` top
for later.

```bash
make -C pycircuit vibe_xbar
# or
sh scripts/pycircuit/emit.sh vibe_xbar
```

See [`docs/rtl/vibe_xbar.md`](../docs/rtl/vibe_xbar.md) and
[`fabric/vibe_xbar.py`](fabric/vibe_xbar.py).

## Stage-34 leaf `vibe_dll_tx`

Same emit pattern. Product SV keeps async-low `rst_n`
(`or negedge rst_n`), `include "vibe_ub_params.vh"` /
`vibe_ub_fn.vh`, 512b NW → 20B flits with cross-beat
remainder, 640b emit when a 4-flit group is ready
(BCRC in last 32b), Null-pad short EOP, and credit
consume on data flits only (CFG0 skip). Eighth DLL
leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm`. Self-contained (no child
instances). `vibe_dll` instantiates it (`u_tx`).
Leave PCS tx / rx tops, `vibe_dll` top, and
`vibe_fabric` top for later.

```bash
make -C pycircuit vibe_dll_tx
# or
sh scripts/pycircuit/emit.sh vibe_dll_tx
```

See [`docs/rtl/vibe_dll_tx.md`](../docs/rtl/vibe_dll_tx.md) and
[`dll/vibe_dll_tx.py`](dll/vibe_dll_tx.py).
