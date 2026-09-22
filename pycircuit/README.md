# pyCircuit sources (Decision I)

RTL freeze `302ac943` is **unfrozen** for a pyCircuit redesign. This tree is the
Python DSL source. **SPEC functional semantics and CR-B port names are
unchanged.** `{src}_{dst}_{meaning}` (`dll` not `dl`). Do not rewrite the chip
here — leaves land one module at a time. Stage-1: scaffold + `vibe_afifo`.
Stage-2: `vibe_pma_bnd`.

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
