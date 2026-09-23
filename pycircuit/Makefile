# Decision I: emit leaves into rtl/. Hand-finished SV is the product leaf.
# pycc Verilog is optional prototype (needs LLVM 19).

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PYTHONPATH := $(ROOT)/pycircuit$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: help setup mlir vibe_afifo vibe_pma_bnd vibe_sync2 vibe_rst_sync \
        vibe_gear_128_160 vibe_gear_160_128 vibe_pcs_scramble \
        vibe_ebch16 vibe_pcs_tx_cw2beat vibe_pcs_tx_amctl \
        handfinish handfinish-pma handfinish-sync2 handfinish-rst-sync \
        handfinish-gear-128-160 handfinish-gear-160-128 \
        handfinish-pcs-scramble handfinish-ebch16 \
        handfinish-pcs-tx-cw2beat handfinish-pcs-tx-amctl \
        lint-leaf lint-leaf-pma lint-leaf-sync2 lint-leaf-rst-sync \
        lint-leaf-gear-128-160 lint-leaf-gear-160-128 \
        lint-leaf-pcs-scramble lint-leaf-ebch16 \
        lint-leaf-pcs-tx-cw2beat lint-leaf-pcs-tx-amctl

help:
	@echo "setup              install pycircuit-hisi or clone lukebest/pyCircuit (pinned)"
	@echo "mlir               frontend emit vibe_afifo.pyc (needs pycircuit import)"
	@echo "vibe_afifo         land hand-finished rtl/cdc/vibe_afifo.sv (try pycc first)"
	@echo "vibe_pma_bnd       land hand-finished rtl/pma/vibe_pma_bnd.sv (try pycc first)"
	@echo "vibe_sync2         land hand-finished rtl/cdc/vibe_sync2.sv (try pycc first)"
	@echo "vibe_rst_sync      land hand-finished rtl/cdc/vibe_rst_sync.sv (try pycc first)"
	@echo "vibe_gear_128_160  land hand-finished rtl/cdc/vibe_gear_128_160.sv (try pycc first)"
	@echo "vibe_gear_160_128  land hand-finished rtl/cdc/vibe_gear_160_128.sv (try pycc first)"
	@echo "vibe_pcs_scramble  land hand-finished rtl/pcs/vibe_pcs_scramble.sv (try pycc first)"
	@echo "vibe_ebch16        land hand-finished rtl/pcs/vibe_ebch16.sv (try pycc first)"
	@echo "vibe_pcs_tx_cw2beat land hand-finished rtl/pcs/vibe_pcs_tx_cw2beat.sv (try pycc first)"
	@echo "vibe_pcs_tx_amctl   land hand-finished rtl/pcs/vibe_pcs_tx_amctl.sv (try pycc first)"
	@echo "handfinish         write product vibe_afifo SV only"
	@echo "handfinish-pma     write product vibe_pma_bnd SV only"
	@echo "handfinish-sync2   write product vibe_sync2 SV only"
	@echo "handfinish-rst-sync write product vibe_rst_sync SV only"
	@echo "handfinish-gear-128-160 write product vibe_gear_128_160 SV only"
	@echo "handfinish-gear-160-128 write product vibe_gear_160_128 SV only"
	@echo "handfinish-pcs-scramble write product vibe_pcs_scramble SV only"
	@echo "handfinish-ebch16  write product vibe_ebch16 SV only"
	@echo "handfinish-pcs-tx-cw2beat write product vibe_pcs_tx_cw2beat SV only"
	@echo "handfinish-pcs-tx-amctl write product vibe_pcs_tx_amctl SV only"
	@echo "lint-leaf          Verilator --lint-only on vibe_afifo + vibe_sync2"
	@echo "lint-leaf-pma      Verilator --lint-only on vibe_pma_bnd"
	@echo "lint-leaf-sync2    Verilator --lint-only on vibe_sync2"
	@echo "lint-leaf-rst-sync Verilator --lint-only on vibe_rst_sync"
	@echo "lint-leaf-gear-128-160 Verilator --lint-only on vibe_gear_128_160"
	@echo "lint-leaf-gear-160-128 Verilator --lint-only on vibe_gear_160_128"
	@echo "lint-leaf-pcs-scramble Verilator --lint-only on vibe_pcs_scramble"
	@echo "lint-leaf-ebch16   Verilator --lint-only on vibe_ebch16"
	@echo "lint-leaf-pcs-tx-cw2beat Verilator --lint-only on vibe_pcs_tx_cw2beat"
	@echo "lint-leaf-pcs-tx-amctl Verilator --lint-only on vibe_pcs_tx_amctl"

setup:
	sh $(ROOT)/scripts/pycircuit/setup_toolchain.sh

mlir:
	mkdir -p $(ROOT)/.pycircuit_out/vibe_afifo
	python3 -m pycircuit.cli emit $(ROOT)/pycircuit/cdc/vibe_afifo.py \
	  -o $(ROOT)/.pycircuit_out/vibe_afifo/vibe_afifo.pyc

vibe_afifo:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_afifo

vibe_pma_bnd:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pma_bnd

vibe_sync2:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_sync2

vibe_rst_sync:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_rst_sync

vibe_gear_128_160:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_gear_128_160

vibe_gear_160_128:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_gear_160_128

vibe_pcs_scramble:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_scramble

vibe_ebch16:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_ebch16

vibe_pcs_tx_cw2beat:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_tx_cw2beat

vibe_pcs_tx_amctl:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_tx_amctl

handfinish:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_afifo.py

handfinish-pma:
	python3 $(ROOT)/pycircuit/pma/handfinish_vibe_pma_bnd.py

handfinish-sync2:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_sync2.py

handfinish-rst-sync:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_rst_sync.py

handfinish-gear-128-160:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_gear_128_160.py

handfinish-gear-160-128:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_gear_160_128.py

handfinish-pcs-scramble:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_scramble.py

handfinish-ebch16:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_ebch16.py

handfinish-pcs-tx-cw2beat:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_tx_cw2beat.py

handfinish-pcs-tx-amctl:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_tx_amctl.py

lint-leaf:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_afifo \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/cdc/vibe_sync2.sv \
	  $(ROOT)/rtl/cdc/vibe_afifo.sv

lint-leaf-pma:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pma_bnd \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pma/vibe_pma_bnd.sv

lint-leaf-sync2:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_sync2 \
	  $(ROOT)/rtl/cdc/vibe_sync2.sv

lint-leaf-rst-sync:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_rst_sync \
	  $(ROOT)/rtl/cdc/vibe_rst_sync.sv

lint-leaf-gear-128-160:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_gear_128_160 \
	  $(ROOT)/rtl/cdc/vibe_gear_128_160.sv

lint-leaf-gear-160-128:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_gear_160_128 \
	  $(ROOT)/rtl/cdc/vibe_gear_160_128.sv

lint-leaf-pcs-scramble:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_scramble \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_pcs_scramble.sv

lint-leaf-ebch16:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_ebch16 \
	  $(ROOT)/rtl/pcs/vibe_ebch16.sv

lint-leaf-pcs-tx-cw2beat:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_tx_cw2beat \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_cw2beat.sv

lint-leaf-pcs-tx-amctl:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_tx_amctl \
	  $(ROOT)/rtl/pcs/vibe_ebch16.sv \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_amctl.sv
