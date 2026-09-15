# Vibe-UB-Switch verification (AS-0.1). Default simulator is AMD Vivado xsim + UVM 1.2.
# Compiles vibe_*.sv + tb/vibe/uvm. Old tb/ is unused (void). Do not modify rtl/.

ROOT      := $(abspath ../..)
TB        := $(ROOT)/tb/vibe
RES       := $(TB)/results

.PHONY: all sim suite units port top cov clean help waves sim-icarus
all: sim

help:
	@echo "make suite          - UVM fabric+mgmt G1/TP suite (xsim)"
	@echo "make suite TC=name  - one UVM suite test"
	@echo "make units          - UVM leaf-unit + port PHY tests (xsim)"
	@echo "make port           - UVM vibe_port PHY tests (xsim)"
	@echo "make top            - UVM vibe_ub_switch smoke (xsim)"
	@echo "make sim            - suite + units + top + absent-feature scan"
	@echo "make sim-icarus     - previous iverilog gate (legacy)"
	@echo "make cov            - verilator line/toggle coverage on vibe_* (if supported)"
	@echo "make neg            - static absent-feature scan"
	@echo "make waves          - +DUMP VCD + PNG"

$(RES):
	mkdir -p $(RES)

suite: $(RES)
	TC="$(TC)" $(TB)/uvm/scripts/run_xsim.sh suite

units: $(RES)
	TC="$(TC)" $(TB)/uvm/scripts/run_xsim.sh units

port: $(RES)
	TC="$(TC)" $(TB)/uvm/scripts/run_xsim.sh port

top: $(RES)
	$(TB)/uvm/scripts/run_xsim.sh top

neg: $(RES)
	$(TB)/scripts/scan_absent.sh $(ROOT)/rtl | tee $(RES)/neg_absent.log

sim: suite units top neg
	@$(TB)/scripts/summarize.sh $(RES)

sim-icarus: $(RES)
	$(MAKE) -f $(TB)/Makefile.icarus sim

waves: $(RES)
	TC="$(TC)" $(TB)/scripts/run_waves.sh

cov: $(RES)
	$(TB)/scripts/run_verilator_cov.sh | tee $(RES)/cov.log

clean:
	rm -rf $(RES)/*
	rm -rf $(TB)/obj_dir
	rm -rf xsim.dir xvlog.pb xelab.pb webtalk* *.wdb *.jou *.log
	rm -rf $(TB)/xsim.dir $(TB)/xvlog.pb $(TB)/xelab.pb $(TB)/*.wdb $(TB)/*.jou
