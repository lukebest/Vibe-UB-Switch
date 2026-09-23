# pyCircuit sources (Decision I)

RTL freeze `302ac943` is **unfrozen** for a pyCircuit redesign. This tree is the
Python DSL source. **SPEC functional semantics and CR-B port names are
unchanged.** `{src}_{dst}_{meaning}` (`dll` not `dl`). Do not rewrite the chip
here — leaves land one module at a time. Stage-1: scaffold + `vibe_afifo`.
Stage-2: `vibe_pma_bnd`. Stage-3: `vibe_sync2`. Stage-4: `vibe_rst_sync`.
Stage-5: `vibe_gear_128_160`.

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
  pma/        vibe_pma_bnd   ← stage-2 leaf (rtl/pma/vibe_pma_bnd.sv)
  pcs/ dll/ nw/ fabric/ mgmt/ port/ top/   stubs
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
