# Decision I: emit leaves into rtl/. Hand-finished SV is the product leaf.
# pycc Verilog is optional prototype (needs LLVM 19).

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PYTHONPATH := $(ROOT)/pycircuit$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: help setup mlir vibe_afifo vibe_pma_bnd vibe_sync2 vibe_rst_sync \
        vibe_gear_128_160 vibe_gear_160_128 vibe_pcs_scramble \
        vibe_ebch16 vibe_pcs_tx_cw2beat vibe_pcs_tx_amctl \
        vibe_rs128_120_enc vibe_rs128_120_dec vibe_pcs_rx_deskew \
        vibe_pcs_rx_amctl_lock vibe_pcs_rx_unpack vibe_pcs_tx_pack \
        vibe_pcs_tx_fec vibe_pcs_rx_fec vibe_pcs_tx_g1 \
        vibe_bcrc vibe_dll_credit vibe_dll_sm vibe_dll_rx \
        vibe_dll_retry_ack_sm vibe_dll_retry_buf vibe_dll_retry_req_sm \
        vibe_dll_tx vibe_dll \
        vibe_fecn_mark vibe_vl_rr vibe_route_lu vibe_port_sel \
        vibe_voq_egr vibe_saf_ing vibe_xbar \
        handfinish handfinish-pma handfinish-sync2 handfinish-rst-sync \
        handfinish-gear-128-160 handfinish-gear-160-128 \
        handfinish-pcs-scramble handfinish-ebch16 \
        handfinish-pcs-tx-cw2beat handfinish-pcs-tx-amctl \
        handfinish-rs128-120-enc handfinish-rs128-120-dec \
        handfinish-pcs-rx-deskew handfinish-pcs-rx-amctl-lock \
        handfinish-pcs-rx-unpack handfinish-pcs-tx-pack \
        handfinish-pcs-tx-fec handfinish-pcs-rx-fec \
        handfinish-pcs-tx-g1 handfinish-bcrc handfinish-dll-credit \
        handfinish-dll-sm handfinish-dll-rx \
        handfinish-dll-retry-ack-sm handfinish-dll-retry-buf \
        handfinish-dll-retry-req-sm handfinish-dll-tx \
        handfinish-dll \
        handfinish-fecn-mark \
        handfinish-vl-rr handfinish-route-lu handfinish-port-sel \
        handfinish-voq-egr handfinish-saf-ing handfinish-xbar \
        lint-leaf lint-leaf-pma lint-leaf-sync2 lint-leaf-rst-sync \
        lint-leaf-gear-128-160 lint-leaf-gear-160-128 \
        lint-leaf-pcs-scramble lint-leaf-ebch16 \
        lint-leaf-pcs-tx-cw2beat lint-leaf-pcs-tx-amctl \
        lint-leaf-rs128-120-enc lint-leaf-rs128-120-dec \
        lint-leaf-pcs-rx-deskew lint-leaf-pcs-rx-amctl-lock \
        lint-leaf-pcs-rx-unpack lint-leaf-pcs-tx-pack \
        lint-leaf-pcs-tx-fec lint-leaf-pcs-rx-fec \
        lint-leaf-pcs-tx-g1 lint-leaf-bcrc lint-leaf-dll-credit \
        lint-leaf-dll-sm lint-leaf-dll-rx \
        lint-leaf-dll-retry-ack-sm lint-leaf-dll-retry-buf \
        lint-leaf-dll-retry-req-sm lint-leaf-dll-tx \
        lint-leaf-dll \
        lint-leaf-fecn-mark \
        lint-leaf-vl-rr lint-leaf-route-lu lint-leaf-port-sel \
        lint-leaf-voq-egr lint-leaf-saf-ing lint-leaf-xbar

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
	@echo "vibe_rs128_120_enc land hand-finished rtl/pcs/vibe_rs128_120_enc.sv (try pycc first)"
	@echo "vibe_rs128_120_dec land hand-finished rtl/pcs/vibe_rs128_120_dec.sv (try pycc first)"
	@echo "vibe_pcs_rx_deskew land hand-finished rtl/pcs/vibe_pcs_rx_deskew.sv (try pycc first)"
	@echo "vibe_pcs_rx_amctl_lock land hand-finished rtl/pcs/vibe_pcs_rx_amctl_lock.sv (try pycc first)"
	@echo "vibe_pcs_rx_unpack land hand-finished rtl/pcs/vibe_pcs_rx_unpack.sv (try pycc first)"
	@echo "vibe_pcs_tx_pack   land hand-finished rtl/pcs/vibe_pcs_tx_pack.sv (try pycc first)"
	@echo "vibe_pcs_tx_fec    land hand-finished rtl/pcs/vibe_pcs_tx_fec.sv (try pycc first)"
	@echo "vibe_pcs_rx_fec    land hand-finished rtl/pcs/vibe_pcs_rx_fec.sv (try pycc first)"
	@echo "vibe_pcs_tx_g1     land hand-finished rtl/pcs/vibe_pcs_tx_g1.sv (try pycc first)"
	@echo "vibe_bcrc          land hand-finished rtl/dll/vibe_bcrc.sv (try pycc first)"
	@echo "vibe_dll_credit    land hand-finished rtl/dll/vibe_dll_credit.sv (try pycc first)"
	@echo "vibe_dll_sm        land hand-finished rtl/dll/vibe_dll_sm.sv (try pycc first)"
	@echo "vibe_dll_rx        land hand-finished rtl/dll/vibe_dll_rx.sv (try pycc first)"
	@echo "vibe_dll_retry_ack_sm land hand-finished rtl/dll/vibe_dll_retry_ack_sm.sv (try pycc first)"
	@echo "vibe_dll_retry_buf  land hand-finished rtl/dll/vibe_dll_retry_buf.sv (try pycc first)"
	@echo "vibe_dll_retry_req_sm land hand-finished rtl/dll/vibe_dll_retry_req_sm.sv (try pycc first)"
	@echo "vibe_dll_tx        land hand-finished rtl/dll/vibe_dll_tx.sv (try pycc first)"
	@echo "vibe_dll           land hand-finished rtl/dll/vibe_dll.sv (try pycc first)"
	@echo "vibe_fecn_mark     land hand-finished rtl/fabric/vibe_fecn_mark.sv (try pycc first)"
	@echo "vibe_vl_rr         land hand-finished rtl/fabric/vibe_vl_rr.sv (try pycc first)"
	@echo "vibe_route_lu      land hand-finished rtl/fabric/vibe_route_lu.sv (try pycc first)"
	@echo "vibe_port_sel      land hand-finished rtl/fabric/vibe_port_sel.sv (try pycc first)"
	@echo "vibe_voq_egr       land hand-finished rtl/fabric/vibe_voq_egr.sv (try pycc first)"
	@echo "vibe_saf_ing       land hand-finished rtl/fabric/vibe_saf_ing.sv (try pycc first)"
	@echo "vibe_xbar          land hand-finished rtl/fabric/vibe_xbar.sv (try pycc first)"
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
	@echo "handfinish-rs128-120-enc write product vibe_rs128_120_enc SV only"
	@echo "handfinish-rs128-120-dec write product vibe_rs128_120_dec SV only"
	@echo "handfinish-pcs-rx-deskew write product vibe_pcs_rx_deskew SV only"
	@echo "handfinish-pcs-rx-amctl-lock write product vibe_pcs_rx_amctl_lock SV only"
	@echo "handfinish-pcs-rx-unpack write product vibe_pcs_rx_unpack SV only"
	@echo "handfinish-pcs-tx-pack write product vibe_pcs_tx_pack SV only"
	@echo "handfinish-pcs-tx-fec write product vibe_pcs_tx_fec SV only"
	@echo "handfinish-pcs-rx-fec write product vibe_pcs_rx_fec SV only"
	@echo "handfinish-pcs-tx-g1 write product vibe_pcs_tx_g1 SV only"
	@echo "handfinish-bcrc    write product vibe_bcrc SV only"
	@echo "handfinish-dll-credit write product vibe_dll_credit SV only"
	@echo "handfinish-dll-sm  write product vibe_dll_sm SV only"
	@echo "handfinish-dll-rx  write product vibe_dll_rx SV only"
	@echo "handfinish-dll-retry-ack-sm write product vibe_dll_retry_ack_sm SV only"
	@echo "handfinish-dll-retry-buf write product vibe_dll_retry_buf SV only"
	@echo "handfinish-dll-retry-req-sm write product vibe_dll_retry_req_sm SV only"
	@echo "handfinish-dll-tx  write product vibe_dll_tx SV only"
	@echo "handfinish-dll     write product vibe_dll SV only"
	@echo "handfinish-fecn-mark write product vibe_fecn_mark SV only"
	@echo "handfinish-vl-rr   write product vibe_vl_rr SV only"
	@echo "handfinish-route-lu write product vibe_route_lu SV only"
	@echo "handfinish-port-sel write product vibe_port_sel SV only"
	@echo "handfinish-voq-egr write product vibe_voq_egr SV only"
	@echo "handfinish-saf-ing write product vibe_saf_ing SV only"
	@echo "handfinish-xbar    write product vibe_xbar SV only"
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
	@echo "lint-leaf-rs128-120-enc Verilator --lint-only on vibe_rs128_120_enc"
	@echo "lint-leaf-rs128-120-dec Verilator --lint-only on vibe_rs128_120_dec"
	@echo "lint-leaf-pcs-rx-deskew Verilator --lint-only on vibe_pcs_rx_deskew"
	@echo "lint-leaf-pcs-rx-amctl-lock Verilator --lint-only on vibe_pcs_rx_amctl_lock"
	@echo "lint-leaf-pcs-rx-unpack Verilator --lint-only on vibe_pcs_rx_unpack"
	@echo "lint-leaf-pcs-tx-pack Verilator --lint-only on vibe_pcs_tx_pack"
	@echo "lint-leaf-pcs-tx-fec Verilator --lint-only on vibe_pcs_tx_fec"
	@echo "lint-leaf-pcs-rx-fec Verilator --lint-only on vibe_pcs_rx_fec"
	@echo "lint-leaf-pcs-tx-g1 Verilator --lint-only on vibe_pcs_tx_g1"
	@echo "lint-leaf-bcrc     Verilator --lint-only on vibe_bcrc"
	@echo "lint-leaf-dll-credit Verilator --lint-only on vibe_dll_credit"
	@echo "lint-leaf-dll-sm   Verilator --lint-only on vibe_dll_sm"
	@echo "lint-leaf-dll-rx   Verilator --lint-only on vibe_dll_rx"
	@echo "lint-leaf-dll-retry-ack-sm Verilator --lint-only on vibe_dll_retry_ack_sm"
	@echo "lint-leaf-dll-retry-buf Verilator --lint-only on vibe_dll_retry_buf"
	@echo "lint-leaf-dll-retry-req-sm Verilator --lint-only on vibe_dll_retry_req_sm"
	@echo "lint-leaf-dll-tx   Verilator --lint-only on vibe_dll_tx"
	@echo "lint-leaf-dll      Verilator --lint-only on vibe_dll (children on filelist)"
	@echo "lint-leaf-fecn-mark Verilator --lint-only on vibe_fecn_mark"
	@echo "lint-leaf-vl-rr    Verilator --lint-only on vibe_vl_rr"
	@echo "lint-leaf-route-lu Verilator --lint-only on vibe_route_lu"
	@echo "lint-leaf-port-sel Verilator --lint-only on vibe_port_sel"
	@echo "lint-leaf-voq-egr  Verilator --lint-only on vibe_voq_egr"
	@echo "lint-leaf-saf-ing  Verilator --lint-only on vibe_saf_ing"
	@echo "lint-leaf-xbar     Verilator --lint-only on vibe_xbar"

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

vibe_rs128_120_enc:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_rs128_120_enc

vibe_rs128_120_dec:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_rs128_120_dec

vibe_pcs_rx_deskew:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_rx_deskew

vibe_pcs_rx_amctl_lock:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_rx_amctl_lock

vibe_pcs_rx_unpack:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_rx_unpack

vibe_pcs_tx_pack:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_tx_pack

vibe_pcs_tx_fec:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_tx_fec

vibe_pcs_rx_fec:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_rx_fec

vibe_pcs_tx_g1:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_pcs_tx_g1

vibe_bcrc:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_bcrc

vibe_dll_credit:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_credit

vibe_dll_sm:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_sm

vibe_dll_rx:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_rx

vibe_dll_retry_ack_sm:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_retry_ack_sm

vibe_dll_retry_buf:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_retry_buf

vibe_dll_retry_req_sm:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_retry_req_sm

vibe_dll_tx:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll_tx

vibe_dll:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_dll

vibe_fecn_mark:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_fecn_mark

vibe_vl_rr:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_vl_rr

vibe_route_lu:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_route_lu

vibe_port_sel:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_port_sel

vibe_voq_egr:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_voq_egr

vibe_saf_ing:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_saf_ing

vibe_xbar:
	sh $(ROOT)/scripts/pycircuit/emit.sh vibe_xbar

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

handfinish-rs128-120-enc:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_rs128_120_enc.py

handfinish-rs128-120-dec:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_rs128_120_dec.py

handfinish-pcs-rx-deskew:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_rx_deskew.py

handfinish-pcs-rx-amctl-lock:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_rx_amctl_lock.py

handfinish-pcs-rx-unpack:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_rx_unpack.py

handfinish-pcs-tx-pack:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_tx_pack.py

handfinish-pcs-tx-fec:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_tx_fec.py

handfinish-pcs-rx-fec:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_rx_fec.py

handfinish-pcs-tx-g1:
	python3 $(ROOT)/pycircuit/pcs/handfinish_vibe_pcs_tx_g1.py

handfinish-bcrc:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_bcrc.py

handfinish-dll-credit:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_credit.py

handfinish-dll-sm:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_sm.py

handfinish-dll-rx:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_rx.py

handfinish-dll-retry-ack-sm:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_retry_ack_sm.py

handfinish-dll-retry-buf:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_retry_buf.py

handfinish-dll-retry-req-sm:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_retry_req_sm.py

handfinish-dll-tx:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll_tx.py

handfinish-dll:
	python3 $(ROOT)/pycircuit/dll/handfinish_vibe_dll.py

handfinish-fecn-mark:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_fecn_mark.py

handfinish-vl-rr:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_vl_rr.py

handfinish-route-lu:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_route_lu.py

handfinish-port-sel:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_port_sel.py

handfinish-voq-egr:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_voq_egr.py

handfinish-saf-ing:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_saf_ing.py

handfinish-xbar:
	python3 $(ROOT)/pycircuit/fabric/handfinish_vibe_xbar.py

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

lint-leaf-rs128-120-enc:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_rs128_120_enc \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_rs128_120_enc.sv

lint-leaf-rs128-120-dec:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_rs128_120_dec \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_rs128_120_dec.sv

lint-leaf-pcs-rx-deskew:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_rx_deskew \
	  $(ROOT)/rtl/pcs/vibe_pcs_rx_deskew.sv

lint-leaf-pcs-rx-amctl-lock:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_rx_amctl_lock \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_ebch16.sv \
	  $(ROOT)/rtl/pcs/vibe_pcs_rx_amctl_lock.sv

lint-leaf-pcs-rx-unpack:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_rx_unpack \
	  $(ROOT)/reports/lint/vibe_ub_switch.vlt \
	  $(ROOT)/rtl/pcs/vibe_pcs_rx_unpack.sv

lint-leaf-pcs-tx-pack:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_tx_pack \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_ebch16.sv \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_amctl.sv \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_pack.sv

lint-leaf-pcs-tx-fec:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_tx_fec \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/pcs/vibe_rs128_120_enc.sv \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_fec.sv

lint-leaf-pcs-rx-fec:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_rx_fec \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/reports/lint/vibe_ub_switch.vlt \
	  $(ROOT)/rtl/pcs/vibe_pcs_rx_fec.sv

lint-leaf-pcs-tx-g1:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_pcs_tx_g1 \
	  $(ROOT)/rtl/pcs/vibe_pcs_tx_g1.sv

lint-leaf-bcrc:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_bcrc \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_bcrc.sv

lint-leaf-dll-credit:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_credit \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_credit.sv

lint-leaf-dll-sm:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_sm \
	  $(ROOT)/rtl/dll/vibe_dll_sm.sv

lint-leaf-dll-rx:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_rx \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_rx.sv

lint-leaf-dll-retry-ack-sm:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_retry_ack_sm \
	  $(ROOT)/rtl/dll/vibe_dll_retry_ack_sm.sv

lint-leaf-dll-retry-buf:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_retry_buf \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_retry_buf.sv

lint-leaf-dll-retry-req-sm:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_retry_req_sm \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_retry_req_sm.sv

lint-leaf-dll-tx:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll_tx \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_tx.sv

lint-leaf-dll:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_dll \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/dll/vibe_dll_sm.sv \
	  $(ROOT)/rtl/dll/vibe_dll_credit.sv \
	  $(ROOT)/rtl/dll/vibe_dll_retry_buf.sv \
	  $(ROOT)/rtl/dll/vibe_dll_retry_req_sm.sv \
	  $(ROOT)/rtl/dll/vibe_dll_retry_ack_sm.sv \
	  $(ROOT)/rtl/dll/vibe_dll_tx.sv \
	  $(ROOT)/rtl/dll/vibe_dll_rx.sv \
	  $(ROOT)/rtl/dll/vibe_dll.sv

lint-leaf-fecn-mark:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_fecn_mark \
	  $(ROOT)/rtl/fabric/vibe_fecn_mark.sv

lint-leaf-vl-rr:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_vl_rr \
	  $(ROOT)/rtl/fabric/vibe_vl_rr.sv

lint-leaf-route-lu:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_route_lu \
	  $(ROOT)/reports/lint/vibe_ub_switch.vlt \
	  $(ROOT)/rtl/fabric/vibe_route_lu.sv

lint-leaf-port-sel:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_port_sel \
	  $(ROOT)/rtl/fabric/vibe_port_sel.sv

lint-leaf-voq-egr:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_voq_egr \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/fabric/vibe_voq_egr.sv

lint-leaf-saf-ing:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_saf_ing \
	  -I$(ROOT)/rtl/common \
	  $(ROOT)/rtl/fabric/vibe_saf_ing.sv

lint-leaf-xbar:
	verilator --lint-only -Wall -Wno-fatal --top-module vibe_xbar \
	  $(ROOT)/rtl/fabric/vibe_xbar.sv
