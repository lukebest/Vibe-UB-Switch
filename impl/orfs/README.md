# ORFS (OpenROAD-flow-scripts) hookup

This directory is a **design config** for ORFS. It is not a vendored copy
of ORFS or of the Sky130 PDK.

## Platform name

Current ORFS public platform name: **`sky130hd`**
(`flow/platforms/sky130hd`). There is also `sky130hs`. This repo targets
`sky130hd`.

## Obtain ORFS and Sky130 views (do not commit them)

```bash
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
# record the SHA you actually ran (print it into reports/synth/flow_info.txt)
```

Install tools using one of the official methods (do not vendor binaries here):

- Prebuilts: https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithPrebuilt.html
- Docker: https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithDocker.html
- Local build: https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildLocally.html

`sky130hd` liberty / LEF / tracks ship **inside the ORFS clone** at
`flow/platforms/sky130hd/`. Those files come from
[google/skywater-pdk](https://github.com/google/skywater-pdk) via
[open_pdks](https://github.com/RTimothyEdwards/open_pdks). Optional extra
views:

```bash
# example — paths vary by installer (volare / conda / open_pdks)
export PDK_ROOT=/path/to/pdks
# typical liberty:
# $ORFS/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
```

**Do not** add `.lib`, `.lef`, `.gds`, or PDK tarballs to this git repo.

## Run

From this repo, after `export ORFS=/path/to/OpenROAD-flow-scripts`:

```bash
make -C impl orfs-synth          # Yosys via ORFS, stop after synth
make -C impl orfs-synth-smoke    # same, leaf vibe_sync2
```

ORFS `make` with no target is a full RTL-GDSII flow. This repo does **not**
default to that. Full-chip P&R is not a QoR signoff while RTL coverage is
open, and Sky130 cannot close 1.25 GHz.

Any GDS written under `impl/work/` stays a local artifact and is **not**
for foundry submit / tapeout.
