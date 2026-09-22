# Decision I stage-1: emit vibe_afifo into rtl/cdc/.
# Hand-finished SV is the product leaf. pycc Verilog is optional prototype.

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PYTHONPATH := $(ROOT)/pycircuit$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: help setup mlir vibe_afifo handfinish lint-leaf

help:
	@echo "setup       install pycircuit-hisi or clone lukebest/pyCircuit (pinned)"
	@echo "mlir        frontend emit vibe_afifo.pyc (needs pycircuit import)"
	@echo "vibe_afifo  land hand-finished rtl/cdc/vibe_afifo.sv (try pycc first)"
	@echo "handfinish  write product SV only"
	@echo "lint-leaf   Verilator --lint-only on vibe_afifo + vibe_sync2"

setup:
	sh $(ROOT)/scripts/pycircuit/setup_toolchain.sh

mlir:
	mkdir -p $(ROOT)/.pycircuit_out/vibe_afifo
	python3 -m pycircuit.cli emit $(ROOT)/pycircuit/cdc/vibe_afifo.py \
	  -o $(ROOT)/.pycircuit_out/vibe_afifo/vibe_afifo.pyc

vibe_afifo:
	sh $(ROOT)/scripts/pycircuit/emit.sh

handfinish:
	python3 $(ROOT)/pycircuit/cdc/handfinish_vibe_afifo.py

lint-leaf:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_afifo \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/cdc/vibe_sync2.sv \
	  $(ROOT)/rtl/cdc/vibe_afifo.sv
