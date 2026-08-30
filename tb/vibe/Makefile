# Vibe-UB-Switch verification (AS-0.1 / FS-0.2.3).
# Compiles vibe_*.sv + tb/vibe only. Old tb/ is unused (void).
# Do not modify rtl/.

ROOT      := $(abspath ../..)
RTL       := $(ROOT)/rtl
TB        := $(ROOT)/tb/vibe
RES       := $(TB)/results
IVERILOG  ?= iverilog
VVP       ?= vvp
VERILATOR ?= verilator

INC := -I$(RTL)/common -I$(TB)/common -I$(TB)/env -I$(TB)/tests

FAB_RTL := \
  $(RTL)/fabric/vibe_saf_ing.sv \
  $(RTL)/fabric/vibe_route_lu.sv \
  $(RTL)/fabric/vibe_port_sel.sv \
  $(RTL)/fabric/vibe_xbar.sv \
  $(RTL)/fabric/vibe_voq_egr.sv \
  $(RTL)/fabric/vibe_vl_rr.sv \
  $(RTL)/fabric/vibe_fecn_mark.sv \
  $(RTL)/fabric/vibe_fabric.sv \
  $(RTL)/mgmt/vibe_cfg_space.sv \
  $(RTL)/mgmt/vibe_cna_ep.sv \
  $(RTL)/mgmt/vibe_irq_agg.sv \
  $(RTL)/mgmt/vibe_rst_ctl.sv \
  $(RTL)/mgmt/vibe_mgmt.sv

UNIT_RTL_DLLRX := $(RTL)/dll/vibe_dll_rx.sv
UNIT_RTL_ICRC  := $(RTL)/nw/vibe_icrc.sv
UNIT_RTL_VL    := $(RTL)/fabric/vibe_vl_rr.sv
UNIT_RTL_CRD   := $(RTL)/dll/vibe_dll_credit.sv
UNIT_RTL_LMSM  := $(RTL)/lmsm/vibe_lmsm.sv
UNIT_RTL_CFG   := $(RTL)/mgmt/vibe_cfg_space.sv

TOP_RTL := \
  $(RTL)/cdc/vibe_sync2.sv $(RTL)/cdc/vibe_afifo.sv \
  $(RTL)/cdc/vibe_rst_sync.sv $(RTL)/cdc/vibe_gear_160_128.sv \
  $(RTL)/cdc/vibe_gear_128_160.sv \
  $(RTL)/pma/vibe_pma_bnd.sv \
  $(wildcard $(RTL)/pcs/*.sv) \
  $(RTL)/lmsm/vibe_lmsm.sv \
  $(wildcard $(RTL)/dll/*.sv) \
  $(RTL)/nw/vibe_nw_adapt.sv $(RTL)/nw/vibe_icrc.sv \
  $(wildcard $(RTL)/fabric/*.sv) \
  $(wildcard $(RTL)/mgmt/*.sv) \
  $(RTL)/port/vibe_port.sv \
  $(RTL)/top/vibe_ub_switch.sv

.PHONY: all sim suite units top cov clean help
all: sim

help:
	@echo "make suite          - fabric+mgmt G1/TP suite (iverilog)"
	@echo "make suite TC=name  - one suite test"
	@echo "make units          - all standalone vibe TCs (PHY/DLL/PCS/CDC/neg)"
	@echo "make top            - vibe_ub_switch smoke + hier probe"
	@echo "make sim            - suite + units + top (gate)"
	@echo "make cov            - verilator line/toggle coverage on vibe_* (if supported)"
	@echo "make neg            - static absent-feature scan (no RTL change)"

$(RES):
	mkdir -p $(RES)

suite: $(RES)
	$(IVERILOG) -g2012 $(INC) -o $(RES)/vibe_suite.vvp \
	  $(TB)/env/vibe_fabric_harness.sv $(TB)/env/vibe_psel_harness.sv \
	  $(TB)/env/vibe_suite.sv $(FAB_RTL)
	$(VVP) $(RES)/vibe_suite.vvp $(if $(TC),+TC=$(TC),) | tee $(RES)/suite.log
	@cp -f $(RES)/suite.log $(RES)/last_run.txt

units: $(RES)
	$(TB)/scripts/run_units.sh

top: $(RES)
	$(IVERILOG) -g2012 $(INC) -o $(RES)/tc_top.vvp \
	  $(TB)/tests/tc_top_smoke.sv $(TOP_RTL)
	$(VVP) $(RES)/tc_top.vvp | tee $(RES)/tc_top.log

neg: $(RES)
	$(TB)/scripts/scan_absent.sh $(RTL) | tee $(RES)/neg_absent.log

sim: suite units top neg
	@$(TB)/scripts/summarize.sh $(RES)

cov: $(RES)
	$(TB)/scripts/run_verilator_cov.sh | tee $(RES)/cov.log

clean:
	rm -rf $(RES)/*
	rm -rf $(TB)/obj_dir
