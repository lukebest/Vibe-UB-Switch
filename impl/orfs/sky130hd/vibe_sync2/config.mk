# ORFS smoke design: rtl/cdc/vibe_sync2.sv (2-FF gray-pointer sync).
# FLOW BRING-UP only. Same sky130hd rules as the top config.

export DESIGN_NICKNAME = vibe_sync2
export DESIGN_NAME     = vibe_sync2
export PLATFORM        = sky130hd

VIBE_ORFS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VIBE_ROOT     := $(abspath $(VIBE_ORFS_DIR)/../../../..)

include $(VIBE_ROOT)/impl/yosys/filelist.mk

export VERILOG_FILES        = $(VIBE_SMOKE_SV)
export VERILOG_INCLUDE_DIRS = $(VIBE_INC_DIR)
export SDC_FILE             = $(VIBE_ROOT)/impl/constraints/vibe_sync2.bringup.sdc
export WORK_HOME           ?= $(VIBE_ROOT)/impl/work/orfs

# Floorplan knobs are unspecified product budgets. Smoke synth does not
# need them. Supply CORE_UTILIZATION only if you run ORFS past synth.
# export CORE_UTILIZATION ?=
