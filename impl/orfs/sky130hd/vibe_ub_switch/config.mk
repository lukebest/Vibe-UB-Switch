# ORFS design config — platform sky130hd (the current ORFS Sky130 HD name).
#
# This is a FLOW BRING-UP vehicle. Sky130 cannot close the FS 1.25 GHz
# fabric clock. Do not treat ORFS results as tapeout-quality GDS or as a
# QoR signoff. RTL is not frozen.
#
# Invoke from the repo (preferred):
#   make -C impl orfs-synth ORFS=/path/to/OpenROAD-flow-scripts
#
# Or from an ORFS checkout:
#   make --file=$ORFS/flow/Makefile \
#     DESIGN_CONFIG=$VIBE_ROOT/impl/orfs/sky130hd/vibe_ub_switch/config.mk \
#     synth
#
# Do not vendor a commercial PDK. Do not copy liberty/LEF/GDS into git.
# sky130hd views come from the ORFS clone (flow/platforms/sky130hd) and/or
# open_pdks. See docs/impl/README.md.

export DESIGN_NICKNAME = vibe_ub_switch
export DESIGN_NAME     = vibe_ub_switch
export PLATFORM        = sky130hd

# This file: impl/orfs/sky130hd/vibe_ub_switch/config.mk
VIBE_ORFS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VIBE_ROOT     := $(abspath $(VIBE_ORFS_DIR)/../../../..)

include $(VIBE_ROOT)/impl/yosys/filelist.mk

export VERILOG_FILES        = $(VIBE_TOP_SV)
export VERILOG_INCLUDE_DIRS = $(VIBE_INC_DIR)
export SYNTH_HDL_FRONTEND   = slang

# Default to the bring-up SDC. Override to the spec file only when you
# intentionally want 1.25 GHz / 922 MHz numbers (they will not close).
export SDC_FILE ?= $(VIBE_ROOT)/impl/constraints/vibe_ub_switch.bringup.sdc

# Keep ORFS artifacts inside this repo's work tree (gitignored).
# Any GDS written here is a local flow artifact — NOT for foundry submit.
export WORK_HOME ?= $(VIBE_ROOT)/impl/work/orfs

# Hierarchical synth: the top is large (VOQ / retry / SAF memories).
export SYNTH_HIERARCHICAL ?= 1

# ---------------------------------------------------------------------------
# Product area / power / utilization budgets: UNSPECIFIED.
# Do not invent signoff numbers. ORFS floorplan (not synth) requires
# CORE_UTILIZATION or DIE_AREA — pass them on the make line if you ever
# run P&R, e.g.:
#   make -C impl orfs-synth CORE_UTILIZATION=40
# That value would be a flow knob, not a product budget.
# ---------------------------------------------------------------------------
# export CORE_UTILIZATION ?=
# export PLACE_DENSITY    ?=
# export DIE_AREA         ?=
# export CORE_AREA        ?=

# Full-chip P&R is not the default and is not a QoR signoff while RTL
# coverage is still open. Use `make synth` / `orfs-synth` only.
