# Vibe-UB-Switch synth flow scaffold (Sky130 + Yosys / ORFS / OpenSTA).
# Sibling of scripts/sim/. Default target is help — do not launch P&R.
# This flow must not edit RTL function. ECOs go through design/verif.

VIBE_ROOT := $(abspath ../..)
include $(VIBE_ROOT)/scripts/synth/yosys/filelist.mk

SYNTH     := $(VIBE_ROOT)/scripts/synth
RPT_SYNTH := $(VIBE_ROOT)/reports/synth
RPT_SO    := $(VIBE_ROOT)/reports/signoff
WORK      := $(SYNTH)/work

YOSYS     ?= yosys
STA       ?=
ORFS      ?= $(OPENROAD_FLOW_ROOT)
LIBERTY   ?= $(SKY130HD_LIB)
PDK_ROOT  ?=

# SDC=bringup (default) or SDC=spec. After synth-smoke: make sta TOP=vibe_sync2
SDC_SEL   ?= bringup
STA_TOP   ?= $(if $(TOP),$(TOP),vibe_ub_switch)
SDC_SPEC      := $(SYNTH)/constraints/vibe_ub_switch.spec.sdc
SDC_BRINGUP   := $(SYNTH)/constraints/vibe_ub_switch.bringup.sdc
SDC_SMOKE     := $(SYNTH)/constraints/vibe_sync2.bringup.sdc

ifeq ($(SDC_SEL),spec)
  SDC_TOP := $(SDC_SPEC)
else
  SDC_TOP := $(SDC_BRINGUP)
endif

ORFS_CFG_TOP   := $(SYNTH)/orfs/sky130hd/vibe_ub_switch/config.mk
ORFS_CFG_SMOKE := $(SYNTH)/orfs/sky130hd/vibe_sync2/config.mk

.DEFAULT_GOAL := help

.PHONY: help check-tools check-sdc synth-smoke synth sta blocks \
        orfs-synth orfs-synth-smoke _orfs-synth orfs-flow clean

help:
	@echo "Vibe-UB-Switch synth flow (Sky130hd bring-up, not tapeout)"
	@echo
	@echo "  make check-tools       - print Yosys / OpenSTA / ORFS / liberty"
	@echo "  make check-sdc         - confirm SDC pin names vs rtl/top"
	@echo "  make synth-smoke       - Yosys on leaf $(VIBE_SMOKE_TOP) (no P&R)"
	@echo "  make blocks            - per-module Yosys QoR (no full-chip slang)"
	@echo "  make synth             - Yosys on vibe_ub_switch (no P&R, not QoR signoff)"
	@echo "  make sta               - OpenSTA WNS/TNS if netlist+liberty exist"
	@echo "  make orfs-synth        - ORFS 'make synth' for the top (needs ORFS=)"
	@echo "  make orfs-synth-smoke  - ORFS 'make synth' for $(VIBE_SMOKE_TOP)"
	@echo "  make clean             - remove scripts/synth/work and generated reports"
	@echo
	@echo "SDC=bringup (default) or SDC=spec. LIBERTY= / ORFS= / STA= as needed."
	@echo "Full-chip P&R is not a target. See scripts/synth/README.md."

check-tools:
	@echo "yosys:   $$(command -v $(YOSYS) 2>/dev/null || echo MISSING)"
	@if command -v $(YOSYS) >/dev/null 2>&1; then $(YOSYS) -V 2>/dev/null | head -n 1; fi
	@echo "sta:     $$(command -v $${STA:-sta} 2>/dev/null || command -v opensta 2>/dev/null || echo MISSING)"
	@echo "openroad:$$(command -v openroad 2>/dev/null || echo MISSING)"
	@echo "ORFS:    $${ORFS:-$(ORFS)}"
	@echo "LIBERTY: $${LIBERTY:-$(LIBERTY)}"
	@echo "PDK_ROOT:$${PDK_ROOT:-unset}"
	@echo "SDC_SEL: $(SDC_SEL) -> $(SDC_TOP)"

# Fail if a clock/reset/IO name in the spec SDC is missing from the top.
check-sdc:
	@top=$(VIBE_ROOT)/rtl/top/vibe_ub_switch.sv; \
	for n in clk_fab rst_n \
	         txclk_0 txclk_1 txclk_2 txclk_3 \
	         rxclk_0 rxclk_1 rxclk_2 rxclk_3 \
	         txdata_0 txdata_1 txdata_2 txdata_3 \
	         rxdata_0 rxdata_1 rxdata_2 rxdata_3 \
	         cfg_wr_vld cfg_wr_ready cfg_wr_cmd cfg_wr_idx cfg_wr_data \
	         irq_logic; do \
	  if ! grep -q "$$n" "$$top"; then \
	    echo "SDC pin '$$n' not found in $$top" >&2; exit 1; \
	  fi; \
	done
	@grep -q 'FLOW BRING-UP' $(SDC_BRINGUP)
	@grep -q '1.25 GHz' $(SDC_SPEC)
	@echo "check-sdc ok (pins match rtl/top/vibe_ub_switch.sv)"

synth-smoke: check-sdc
	@mkdir -p $(RPT_SYNTH) $(WORK)
	TOP=$(VIBE_SMOKE_TOP) \
	INC_DIR=$(VIBE_INC_DIR) \
	RPT_DIR=$(RPT_SYNTH) \
	OUT_DIR=$(WORK) \
	SDC=$(SDC_SMOKE) \
	LIBERTY="$(LIBERTY)" \
	YOSYS=$(YOSYS) \
	$(SYNTH)/yosys/run_synth.sh $(VIBE_SMOKE_SV)

blocks:
	RTL_SHA=32a7f5e0c3f04762aa27dae73b000e55773195da \
	YOSYS=$(YOSYS) LIBERTY="$(LIBERTY)" \
	$(SYNTH)/yosys/run_blocks.sh

# Full-chip Yosys. Do not treat as QoR signoff. Prefer 'make blocks'.
# Standalone Yosys -sv is best-effort; ORFS slang (orfs-synth) is preferred.
synth: check-sdc
	@echo "NOTE: full-chip synth is not a QoR signoff (RTL not frozen; Sky130 != 1.25 GHz)."
	@mkdir -p $(RPT_SYNTH) $(WORK)
	TOP=vibe_ub_switch \
	INC_DIR=$(VIBE_INC_DIR) \
	RPT_DIR=$(RPT_SYNTH) \
	OUT_DIR=$(WORK) \
	SDC=$(SDC_TOP) \
	LIBERTY="$(LIBERTY)" \
	YOSYS=$(YOSYS) \
	$(SYNTH)/yosys/run_synth.sh $(VIBE_TOP_SV)

ifeq ($(STA_TOP),vibe_sync2)
  STA_SDC := $(SDC_SMOKE)
else
  STA_SDC := $(SDC_TOP)
endif

sta:
	@mkdir -p $(RPT_SO)
	TOP=$(STA_TOP) \
	NETLIST="$(WORK)/$(STA_TOP).synth.v" \
	SDC=$(STA_SDC) \
	RPT_DIR=$(RPT_SO) \
	LIBERTY="$(LIBERTY)" \
	STA="$(STA)" \
	ORFS="$(ORFS)" \
	$(SYNTH)/sta/run_sta.sh

orfs-synth: check-sdc
	@$(MAKE) -f $(lastword $(MAKEFILE_LIST)) _orfs-synth \
	  ORFS_DESIGN_CONFIG=$(ORFS_CFG_TOP)

orfs-synth-smoke: check-sdc
	@$(MAKE) -f $(lastword $(MAKEFILE_LIST)) _orfs-synth \
	  ORFS_DESIGN_CONFIG=$(ORFS_CFG_SMOKE)

_orfs-synth:
	@if [ -z "$(ORFS)" ]; then \
	  echo "Set ORFS=/path/to/OpenROAD-flow-scripts" >&2; \
	  echo "See scripts/synth/README.md" >&2; \
	  exit 2; \
	fi
	@test -f "$(ORFS)/flow/Makefile" || { \
	  echo "ORFS flow Makefile not found: $(ORFS)/flow/Makefile" >&2; exit 2; }
	$(MAKE) --file=$(ORFS)/flow/Makefile \
	  DESIGN_CONFIG=$(ORFS_DESIGN_CONFIG) \
	  WORK_HOME=$(WORK)/orfs \
	  synth
	@echo "ORFS synth finished. Copy reports from $(WORK)/orfs if present."
	@echo "This is not a QoR signoff and not tapeout GDS."

# Explicit, opt-in, not the default. Still not a signoff / tapeout path.
orfs-flow:
	@echo "Full ORFS RTL-GDSII is opt-in and NOT a tapeout or QoR signoff." >&2
	@echo "Re-run: make -C scripts/synth orfs-flow CONFIRM=1 ORFS=... CORE_UTILIZATION=<n>" >&2
	@echo "CORE_UTILIZATION is a flow knob, not a product budget." >&2
	@test "$(CONFIRM)" = "1" || exit 2
	@test -n "$(ORFS)" || { echo "Set ORFS=..." >&2; exit 2; }
	$(MAKE) --file=$(ORFS)/flow/Makefile \
	  DESIGN_CONFIG=$(ORFS_CFG_TOP) \
	  WORK_HOME=$(WORK)/orfs

clean:
	rm -rf $(WORK)
	rm -f $(RPT_SYNTH)/* $(RPT_SO)/*
	@# keep directory keepers
	touch $(RPT_SYNTH)/.gitkeep $(RPT_SO)/.gitkeep
