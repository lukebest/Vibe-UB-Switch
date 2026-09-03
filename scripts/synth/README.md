# scripts/synth/

Yosys / ORFS (`sky130hd`) / OpenSTA **flow scaffold**, sibling of
`scripts/sim/`. Not a QoR drop and **not tapeout GDS**. Sky130 cannot
close the FS 1.25 GHz fabric clock. This flow must not edit `rtl/`.

## How to run (when RTL is frozen and tools are installed)

```bash
make -C scripts/synth help          # default — does not launch P&R
make -C scripts/synth check-sdc     # pin names vs rtl/top
make -C scripts/synth synth-smoke   # leaf vibe_sync2
make -C scripts/synth blocks        # per-module Yosys QoR (no full-chip slang)
make -C scripts/synth synth         # full top; not a QoR signoff
make -C scripts/synth sta           # needs mapped netlist + liberty
```

`SDC=bringup` (default) uses 100 MHz **FLOW BRING-UP** constraints.
`SDC=spec` uses 1.25 GHz / 922 MHz from FS/AS. Hop latency is
unconstrained. Area/power/utilization budgets are unspecified.

SDCs: `constraints/vibe_ub_switch.spec.sdc` and
`constraints/vibe_ub_switch.bringup.sdc`. Clock ports
(`clk_fab`, `txclk_*`, `rxclk_*`, `rst_n`) match
`rtl/top/vibe_ub_switch.sv`. CDC uses async clock groups, not a
chip-wide false path.

Block-level QoR lives under `reports/synth/` (dated write-up plus
generated `area.rpt` / `cells.rpt` / `blocks/`). `reports/signoff/`
stays keepers-only until OpenSTA is actually run. Do not hand-write
WNS/TNS/area. Do not raise slang `--unroll-limit` to 200000 (OOM).

## Tools / PDK (do not vendor binaries)

```bash
sudo apt-get update && sudo apt-get install -y yosys   # smoke only
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
export ORFS=$PWD/OpenROAD-flow-scripts
# prebuilts / Docker / local: https://openroad-flow-scripts.readthedocs.io/
export LIBERTY=$ORFS/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
make -C scripts/synth orfs-synth ORFS=$ORFS
```

Do not commit `.lib`, `.lef`, `.gds`, or PDK tarballs. Any work product
under `scripts/synth/work/` is local and **not for foundry submit**.
Full-chip P&R is opt-in only (`orfs-flow CONFIRM=1`) and is still not
signoff.

RTL ECO (function or drive strength) goes through design/verif, not this
directory.
