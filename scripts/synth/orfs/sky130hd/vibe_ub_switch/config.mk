# ORFS design config — platform sky130hd (current ORFS Sky130 HD name).
#
# FLOW BRING-UP vehicle. Sky130 cannot close FS 1.25 GHz. Not tapeout GDS.
# Invoke: make -C scripts/synth orfs-synth ORFS=/path/to/OpenROAD-flow-scripts
#
# Do not vendor a commercial PDK. sky130hd views come from the ORFS clone
# (flow/platforms/sky130hd) and/or open_pdks. See scripts/synth/README.md.

export DESIGN_NICKNAME = vibe_ub_switch
export DESIGN_NAME     = vibe_ub_switch
export PLATFORM        = sky130hd

# This file: scripts/synth/orfs/sky130hd/vibe_ub_switch/config.mk
VIBE_ORFS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VIBE_ROOT     := $(abspath $(VIBE_ORFS_DIR)/../../../../..)

include $(VIBE_ROOT)/scripts/synth/yosys/filelist.mk

export VERILOG_FILES        = $(VIBE_TOP_SV)
export VERILOG_INCLUDE_DIRS = $(VIBE_INC_DIR)
export SYNTH_HDL_FRONTEND   = slang

# Default to the bring-up SDC. Override to spec only when you want
# 1.25 GHz / 922 MHz numbers (they will not close on Sky130).
export SDC_FILE ?= $(VIBE_ROOT)/scripts/synth/constraints/vibe_ub_switch.bringup.sdc

# Local work tree (gitignored). Any GDS here is NOT for foundry submit.
export WORK_HOME ?= $(VIBE_ROOT)/scripts/synth/work/orfs

export SYNTH_HIERARCHICAL ?= 1

# Product area / power / utilization budgets: UNSPECIFIED.
# ORFS floorplan (not synth) needs CORE_UTILIZATION or DIE_AREA — pass
# on the make line if you ever run P&R. That is a flow knob, not a budget.
# export CORE_UTILIZATION ?=
# export PLACE_DENSITY    ?=
# export DIE_AREA         ?=
# export CORE_AREA        ?=
