# Vibe-UB-Switch verification (AS-0.1).
# Default gate is uvm-python + Verilator/Icarus (no xvlog).
# SV UVM + xsim is deprecated/secondary: `make sim-xsim`.
# Do not modify rtl/.

ROOT      := $(abspath ../..)
TB        := $(ROOT)/tb/vibe
RES       := $(TB)/results
PYUVM     := $(TB)/pyuvm
SIM       ?= verilator

.PHONY: all sim suite units port top cov clean help waves sim-icarus sim-xsim neg
all: sim

help:
	@echo "make sim            - uvm-python suite + units + top + neg (SIM=verilator|icarus)"
	@echo "make suite          - fabric+mgmt G1/TP suite (uvm-python)"
	@echo "make suite TC=name  - one suite test"
	@echo "make units          - leaf-unit + static/neg + port (uvm-python)"
	@echo "make port           - vibe_port PHY tests (uvm-python)"
	@echo "make top            - vibe_ub_switch smoke (uvm-python)"
	@echo "make neg            - static absent-feature scan"
	@echo "make sim-icarus     - legacy iverilog tree (historical 124-bucket)"
	@echo "make sim-xsim       - deprecated SV UVM + Vivado xsim"
	@echo "make cov            - verilator line/toggle coverage on vibe_* (if supported)"

$(RES):
	mkdir -p $(RES)

suite units port top neg sim: $(RES)
	$(MAKE) -C $(PYUVM) $@ SIM=$(SIM) TC="$(TC)"
	@$(TB)/scripts/summarize.sh $(RES) || true

sim-icarus: $(RES)
	$(MAKE) -f $(TB)/Makefile.icarus sim

sim-xsim: $(RES)
	@echo "DEPRECATED: SV UVM + xsim. Prefer make sim (uvm-python)."
	TC="$(TC)" $(TB)/uvm/scripts/run_xsim.sh suite
	TC="$(TC)" $(TB)/uvm/scripts/run_xsim.sh units
	$(TB)/uvm/scripts/run_xsim.sh top
	$(TB)/scripts/scan_absent.sh $(ROOT)/rtl | tee $(RES)/neg_absent.log
	@$(TB)/scripts/summarize.sh $(RES)

waves: $(RES)
	TC="$(TC)" $(TB)/scripts/run_waves.sh

cov: $(RES)
	$(TB)/scripts/run_verilator_cov.sh | tee $(RES)/cov.log

clean:
	rm -rf $(RES)/*
	rm -rf $(TB)/obj_dir $(PYUVM)/sim_build $(PYUVM)/results
	rm -rf xsim.dir xvlog.pb xelab.pb webtalk* *.wdb *.jou *.log
	rm -rf $(TB)/xsim.dir $(TB)/xvlog.pb $(TB)/xelab.pb $(TB)/*.wdb $(TB)/*.jou
