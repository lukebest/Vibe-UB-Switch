# ORFS smoke design: rtl/cdc/vibe_sync2.sv. FLOW BRING-UP only.

export DESIGN_NICKNAME = vibe_sync2
export DESIGN_NAME     = vibe_sync2
export PLATFORM        = sky130hd

VIBE_ORFS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VIBE_ROOT     := $(abspath $(VIBE_ORFS_DIR)/../../../../..)

include $(VIBE_ROOT)/scripts/synth/yosys/filelist.mk

export VERILOG_FILES        = $(VIBE_SMOKE_SV)
export VERILOG_INCLUDE_DIRS = $(VIBE_INC_DIR)
export SDC_FILE             = $(VIBE_ROOT)/scripts/synth/constraints/vibe_sync2.bringup.sdc
export WORK_HOME           ?= $(VIBE_ROOT)/scripts/synth/work/orfs

# export CORE_UTILIZATION ?=
