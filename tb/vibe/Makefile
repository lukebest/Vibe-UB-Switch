# Vibe-UB-Switch verification (AS-0.1).
# Default gate is uvm-python + Verilator/Icarus (no xvlog).
# SV UVM + xsim is deprecated/secondary: `make sim-xsim`.
# Do not modify rtl/.

ROOT      := $(abspath ../..)
TB        := $(ROOT)/tb/vibe
RES       := $(TB)/results
PYUVM     := $(TB)/pyuvm
SIM       ?= verilator

.PHONY: all sim suite units port top cov clean help waves sim-icarus sim-xsim neg afifo sync2 rst_sync gear_128_160 gear_160_128 dll pcs_scramble ebch16 cw2beat amctl
all: sim

help:
	@echo "make sim            - uvm-python suite + units + top + neg (SIM=verilator|icarus)"
	@echo "make suite          - fabric+mgmt G1/TP suite (uvm-python)"
	@echo "make suite TC=name  - one suite test"
	@echo "make units          - leaf-unit + static/neg + port (uvm-python)"
	@echo "make units TC=tc_vibe_afifo - Decision-I vibe_afifo (module-level)"
	@echo "make afifo          - same as units TC=tc_vibe_afifo (not full-chip gate)"
	@echo "make units TC=tc_vibe_sync2 - Decision-I vibe_sync2 (module-level)"
	@echo "make sync2          - same as units TC=tc_vibe_sync2 (not full-chip gate)"
	@echo "make units TC=tc_vibe_rst_sync - Decision-I vibe_rst_sync (module-level)"
	@echo "make rst_sync       - same as units TC=tc_vibe_rst_sync (not full-chip gate)"
	@echo "make units TC=tc_vibe_gear_128_160 - Decision-I vibe_gear_128_160 (module-level)"
	@echo "make gear_128_160   - same as units TC=tc_vibe_gear_128_160 (not full-chip gate)"
	@echo "make units TC=tc_vibe_gear_160_128 - Decision-I vibe_gear_160_128 (module-level)"
	@echo "make gear_160_128   - same as units TC=tc_vibe_gear_160_128 (not full-chip gate)"
	@echo "make units TC=tc_dll - TP-DLL-004 full vibe_dll >32-flit split"
	@echo "make dll            - same as units TC=tc_dll (≠1/3 ≠4/3 ≠signoff)"
	@echo "make units TC=tc_vibe_pcs_scramble - Decision-I vibe_pcs_scramble (module-level)"
	@echo "make pcs_scramble   - same as units TC=tc_vibe_pcs_scramble (not full-chip gate)"
	@echo "make units TC=tc_vibe_ebch16 - Decision-I vibe_ebch16 (module-level)"
	@echo "make ebch16         - same as units TC=tc_vibe_ebch16 (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_tx_cw2beat - Decision-I vibe_pcs_tx_cw2beat (module-level)"
	@echo "make cw2beat        - same as units TC=tc_vibe_pcs_tx_cw2beat (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_tx_amctl - Decision-I vibe_pcs_tx_amctl (module-level)"
	@echo "make amctl          - same as units TC=tc_vibe_pcs_tx_amctl (not full-chip gate)"
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

afifo: $(RES)
	$(MAKE) -C $(PYUVM) afifo SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

sync2: $(RES)
	$(MAKE) -C $(PYUVM) sync2 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

rst_sync: $(RES)
	$(MAKE) -C $(PYUVM) rst_sync SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

gear_128_160: $(RES)
	$(MAKE) -C $(PYUVM) gear_128_160 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

gear_160_128: $(RES)
	$(MAKE) -C $(PYUVM) gear_160_128 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

dll: $(RES)
	$(MAKE) -C $(PYUVM) dll SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

pcs_scramble: $(RES)
	$(MAKE) -C $(PYUVM) pcs_scramble SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

ebch16: $(RES)
	$(MAKE) -C $(PYUVM) ebch16 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

cw2beat: $(RES)
	$(MAKE) -C $(PYUVM) cw2beat SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

amctl: $(RES)
	$(MAKE) -C $(PYUVM) amctl SIM=$(SIM)
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
