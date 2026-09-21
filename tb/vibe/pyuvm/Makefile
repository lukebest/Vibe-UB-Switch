# uvm-python + cocotb 1.9.x gate. SIM=verilator (baseline) or SIM=icarus.
SIM    ?= verilator
PYUVM  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV   := $(PYUVM)/.venv
PY     := $(VENV)/bin/python

.PHONY: venv gate suite units port top neg sim help clean
help:
	@echo "SIM=verilator|icarus (default verilator)"
	@echo "make -C tb/vibe/pyuvm venv"
	@echo "make -C tb/vibe/pyuvm suite   [TC=tc_rt10_must_drop]"
	@echo "make -C tb/vibe/pyuvm units   [TC=tc_vl_rr]"
	@echo "make -C tb/vibe/pyuvm port    [TC=tc_port_smoke]"
	@echo "make -C tb/vibe/pyuvm top"
	@echo "make -C tb/vibe/pyuvm sim     # suite + units + top + neg"

venv:
	test -x $(PY) || python3 -m venv $(VENV)
	$(PY) -m pip install -q -r $(PYUVM)/requirements.txt

gate suite units port top neg sim: venv
	$(PY) $(PYUVM)/run_gate.py $@ $(if $(TC),--tc $(TC),) --sim $(SIM)

clean:
	rm -rf $(PYUVM)/sim_build $(PYUVM)/results
