# uvm-python + cocotb 1.9.x gate. SIM=verilator (baseline) or SIM=icarus.
SIM    ?= verilator
PYUVM  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV   := $(PYUVM)/.venv
PY     := $(VENV)/bin/python

.PHONY: venv gate suite units port top neg sim afifo sync2 rst_sync gear_128_160 gear_160_128 dll pcs_scramble ebch16 cw2beat amctl rs128_120_enc rs128_120_dec deskew amctl_lock unpack pack tx_fec rx_fec g1 tx_g1 bcrc credit dll_sm sm dll_rx rx retry_ack_sm ack_sm help clean
help:
	@echo "SIM=verilator|icarus (default verilator)"
	@echo "make -C tb/vibe/pyuvm venv"
	@echo "make -C tb/vibe/pyuvm suite   [TC=tc_rt10_must_drop]"
	@echo "make -C tb/vibe/pyuvm units   [TC=tc_vl_rr]"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_afifo"
	@echo "make -C tb/vibe/pyuvm afifo   # Decision-I leaf vibe_afifo (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_sync2"
	@echo "make -C tb/vibe/pyuvm sync2   # Decision-I leaf vibe_sync2 (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_rst_sync"
	@echo "make -C tb/vibe/pyuvm rst_sync # Decision-I leaf vibe_rst_sync (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_gear_128_160"
	@echo "make -C tb/vibe/pyuvm gear_128_160 # Decision-I leaf vibe_gear_128_160 (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_gear_160_128"
	@echo "make -C tb/vibe/pyuvm gear_160_128 # Decision-I leaf vibe_gear_160_128 (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_dll"
	@echo "make -C tb/vibe/pyuvm dll     # TP-DLL-004 full vibe_dll split (not a leaf)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_scramble"
	@echo "make -C tb/vibe/pyuvm pcs_scramble # Decision-I leaf vibe_pcs_scramble (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_ebch16"
	@echo "make -C tb/vibe/pyuvm ebch16  # Decision-I leaf vibe_ebch16 (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_tx_cw2beat"
	@echo "make -C tb/vibe/pyuvm cw2beat # Decision-I leaf vibe_pcs_tx_cw2beat (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_tx_amctl"
	@echo "make -C tb/vibe/pyuvm amctl   # Decision-I leaf vibe_pcs_tx_amctl (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_rs128_120_enc"
	@echo "make -C tb/vibe/pyuvm rs128_120_enc # Decision-I leaf vibe_rs128_120_enc (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_rs128_120_dec"
	@echo "make -C tb/vibe/pyuvm rs128_120_dec # Decision-I leaf vibe_rs128_120_dec (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_rx_deskew"
	@echo "make -C tb/vibe/pyuvm deskew  # Decision-I leaf vibe_pcs_rx_deskew (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_rx_amctl_lock"
	@echo "make -C tb/vibe/pyuvm amctl_lock # Decision-I leaf vibe_pcs_rx_amctl_lock (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_rx_unpack"
	@echo "make -C tb/vibe/pyuvm unpack  # Decision-I leaf vibe_pcs_rx_unpack (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_tx_pack"
	@echo "make -C tb/vibe/pyuvm pack    # Decision-I leaf vibe_pcs_tx_pack (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_tx_fec"
	@echo "make -C tb/vibe/pyuvm tx_fec  # Decision-I leaf vibe_pcs_tx_fec (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_rx_fec"
	@echo "make -C tb/vibe/pyuvm rx_fec  # Decision-I leaf vibe_pcs_rx_fec (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_pcs_tx_g1"
	@echo "make -C tb/vibe/pyuvm g1      # Decision-I leaf vibe_pcs_tx_g1 (module-level)"
	@echo "make -C tb/vibe/pyuvm tx_g1   # same as g1 / tc_vibe_pcs_tx_g1"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_bcrc"
	@echo "make -C tb/vibe/pyuvm bcrc    # Decision-I leaf vibe_bcrc (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_dll_credit"
	@echo "make -C tb/vibe/pyuvm credit  # Decision-I leaf vibe_dll_credit (module-level)"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_dll_sm"
	@echo "make -C tb/vibe/pyuvm dll_sm  # Decision-I leaf vibe_dll_sm (module-level)"
	@echo "make -C tb/vibe/pyuvm sm      # same as dll_sm / tc_vibe_dll_sm"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_dll_rx"
	@echo "make -C tb/vibe/pyuvm dll_rx  # Decision-I leaf vibe_dll_rx (module-level)"
	@echo "make -C tb/vibe/pyuvm rx      # same as dll_rx / tc_vibe_dll_rx"
	@echo "make -C tb/vibe/pyuvm units   TC=tc_vibe_dll_retry_ack_sm"
	@echo "make -C tb/vibe/pyuvm retry_ack_sm # Decision-I leaf vibe_dll_retry_ack_sm (module-level)"
	@echo "make -C tb/vibe/pyuvm ack_sm  # same as retry_ack_sm / tc_vibe_dll_retry_ack_sm"
	@echo "make -C tb/vibe/pyuvm port    [TC=tc_port_smoke]"
	@echo "make -C tb/vibe/pyuvm top"
	@echo "make -C tb/vibe/pyuvm sim     # suite + units + top + neg"

venv:
	test -x $(PY) || python3 -m venv $(VENV)
	$(PY) -m pip install -q -r $(PYUVM)/requirements.txt

gate suite units port top neg sim: venv
	$(PY) $(PYUVM)/run_gate.py $@ $(if $(TC),--tc $(TC),) --sim $(SIM)

# Module-level Decision-I leaves. Not the full-chip consecutive-green gate.
afifo: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_afifo --sim $(SIM)

sync2: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_sync2 --sim $(SIM)

rst_sync: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_rst_sync --sim $(SIM)

gear_128_160: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_gear_128_160 --sim $(SIM)

gear_160_128: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_gear_160_128 --sim $(SIM)

# Full-wrapper TP-DLL-004. Not a Decision-I leaf. ≠1/3 ≠4/3 ≠signoff.
dll: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_dll --sim $(SIM)

pcs_scramble: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_scramble --sim $(SIM)

ebch16: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_ebch16 --sim $(SIM)

cw2beat: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_tx_cw2beat --sim $(SIM)

amctl: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_tx_amctl --sim $(SIM)

rs128_120_enc: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_rs128_120_enc --sim $(SIM)

rs128_120_dec: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_rs128_120_dec --sim $(SIM)

deskew: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_rx_deskew --sim $(SIM)

amctl_lock: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_rx_amctl_lock --sim $(SIM)

unpack: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_rx_unpack --sim $(SIM)

pack: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_tx_pack --sim $(SIM)

tx_fec: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_tx_fec --sim $(SIM)

rx_fec: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_rx_fec --sim $(SIM)

g1: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_pcs_tx_g1 --sim $(SIM)

tx_g1: g1

bcrc: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_bcrc --sim $(SIM)

credit: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_dll_credit --sim $(SIM)

dll_sm: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_dll_sm --sim $(SIM)

sm: dll_sm

dll_rx: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_dll_rx --sim $(SIM)

rx: dll_rx

retry_ack_sm: venv
	$(PY) $(PYUVM)/run_gate.py units --tc tc_vibe_dll_retry_ack_sm --sim $(SIM)

ack_sm: retry_ack_sm

clean:
	rm -rf $(PYUVM)/sim_build $(PYUVM)/results
