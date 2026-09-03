# Implementation flow (Sky130 bring-up)

Open-source backend path for **Vibe-UB-Switch**: Yosys +
[OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts)
(ORFS) + OpenSTA, targeting the ORFS platform **`sky130hd`**.

This is a **flow / methodology bring-up**, not a production-node
implementation and **not tapeout-quality GDS**.

## What this is / is not

| This flow does | This flow does not |
|----------------|--------------------|
| Check in SDC, Yosys/ORFS/STA scripts, report paths | Change RTL function (`rtl/` is read-only here) |
| Let another engineer re-run synth at a later freeze SHA | Claim Sky130 closes FS 1.25 GHz |
| Emit generated reports under `reports/` | Invent area / power / utilization / WNS / TNS |
| Stop at synth by default | Run full-chip P&R as a QoR signoff |
| | Submit GDS to a foundry |

RTL around SHA `25eb085e` is **not frozen** (coverage still open). Do not
treat a synth number from this revision as chip signoff. When RTL is
frozen, re-run from `impl/` at that SHA.

**RTL ECO:** functional or drive-strength changes belong with the
design / verification bots. This flow must not edit RTL function. A
tiny impl-only wrapper was not required for ORFS.

Function-spec true source is **outside this repo** (see the top-level
README). This document does not rewrite architecture specs.

## Spec clocks vs bring-up clocks

Pin names are taken from `rtl/top/vibe_ub_switch.sv`:

| Port | Role | Spec (FS/AS) | Bring-up SDC |
|------|------|--------------|--------------|
| `clk_fab` | fabric / DLL / PCS digital / LMSM / mgmt | 1.25 GHz (800 ps) | 100 MHz (10 ns) |
| `txclk_0..3` | per-port independent PMA TX | 922 MHz (~1084.6 ps) | 100 MHz, still async |
| `rxclk_0..3` | per-port independent PMA RX | 922 MHz (~1084.6 ps) | 100 MHz, still async |
| `rst_n` | logical reset (async assert) | false-path | false-path |

- Spec SDC: `impl/constraints/vibe_ub_switch.spec.sdc`
- Bring-up SDC: `impl/constraints/vibe_ub_switch.bringup.sdc` (**FLOW BRING-UP**, not signoff)

Hop latency is unconstrained. I/O delays are conservative 20%-of-period
placeholders, not a board spec.

**CDC:** gray-pointer AFIFO (`vibe_afifo` + `vibe_sync2`) and
`vibe_rst_sync` cross `clk_fab` ↔ per-port `txclk`/`rxclk`. Both SDCs
use `set_clock_groups -asynchronous` (one group per clock). That is
**not** `set_false_path` of the whole chip. CDC correctness stays with
`rtl/cdc` + `tb/vibe`.

**Sky130 cannot close 1.25 GHz.** Spec-SDC WNS/TNS on sky130hd is a
methodology artifact, not a node signoff. Bring-up SDC exists so the
tools can be exercised. RTL timer constants (e.g. `VIBE_US_CYC = 1250`)
are not changed by this flow; at 100 MHz a “1 µs” count is 12.5 µs
wall-clock.

Area / power / utilization **budgets are unspecified**. ORFS floorplan
knobs, if you ever pass them, are flow knobs — not product budgets.

## How to run

Entry point: `impl/Makefile` (or `scripts/impl/run_impl.sh`).

```bash
make -C impl help
make -C impl check-tools
make -C impl check-sdc
make -C impl synth-smoke          # leaf vibe_sync2; needs Yosys
make -C impl synth                # full top; not a QoR signoff
make -C impl sta TOP=vibe_sync2   # after smoke, if liberty + OpenSTA exist
make -C impl sta                  # after synth; SDC=bringup|spec
```

`make` / `make -C impl` prints help. It does **not** launch P&R.

### Tools missing on this machine

The scripts still land. Install, then re-run — do not paste fake QoR.

```bash
# Yosys (enough for synth-smoke)
sudo apt-get update && sudo apt-get install -y yosys

# Full stack: clone ORFS, then use official prebuilt / Docker / local build
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
export ORFS=$PWD/OpenROAD-flow-scripts
# https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithPrebuilt.html
# https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithDocker.html
```

Do **not** commit PDK, liberty, LEF, or GDS binaries. ORFS provides
`flow/platforms/sky130hd/`. Optional `open_pdks` / `$PDK_ROOT` is
documented in `impl/orfs/README.md`.

```bash
export LIBERTY=$ORFS/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
export ORFS=/path/to/OpenROAD-flow-scripts
make -C impl orfs-synth-smoke
make -C impl orfs-synth           # ORFS Yosys+slang, stop after synth
```

Full RTL-GDSII is opt-in only: `make -C impl orfs-flow CONFIRM=1 ORFS=...`
plus a `CORE_UTILIZATION` you choose as a **flow knob**. Any GDS under
`impl/work/` is a local artifact and is **not for foundry submit**.

## Reports (generated)

See `reports/README.md`. Directories are git-tracked with keepers;
filenames are produced by the flow, not hand-written metrics.

## Freeze SHA later

1. Check out the frozen RTL SHA (do not ECO function in this flow).
2. `make -C impl check-sdc synth-smoke`
3. If tools + liberty are present: `make -C impl synth SDC=bringup` and/or
   `make -C impl orfs-synth`
4. Optional comparison: `make -C impl sta SDC=spec` — expect Sky130 to
   miss 1.25 GHz; that is not a surprise.
5. Keep generated reports out of architecture docs; they are flow output.
