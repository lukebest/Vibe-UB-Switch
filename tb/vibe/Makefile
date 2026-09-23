# Vibe-UB-Switch verification (AS-0.1).
# Default gate is uvm-python + Verilator/Icarus (no xvlog).
# SV UVM + xsim is deprecated/secondary: `make sim-xsim`.
# Do not modify rtl/.

ROOT      := $(abspath ../..)
TB        := $(ROOT)/tb/vibe
RES       := $(TB)/results
PYUVM     := $(TB)/pyuvm
SIM       ?= verilator

.PHONY: all sim suite units port top cov clean help waves sim-icarus sim-xsim neg afifo sync2 rst_sync gear_128_160 gear_160_128 dll pcs_scramble ebch16 cw2beat amctl rs128_120_enc rs128_120_dec deskew amctl_lock unpack pack tx_fec rx_fec g1 tx_g1 bcrc credit dll_sm sm dll_rx rx retry_ack_sm ack_sm retry_buf buf retry_req_sm req_sm fecn_mark fecn vl_rr vl route_lu route tc_vibe_route_lu port_sel psel tc_vibe_port_sel voq_egr voq tc_vibe_voq_egr saf_ing saf tc_vibe_saf_ing xbar tc_vibe_xbar dll_tx tx tc_vibe_dll_tx
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
	@echo "make units TC=tc_vibe_rs128_120_enc - Decision-I vibe_rs128_120_enc (module-level)"
	@echo "make rs128_120_enc  - same as units TC=tc_vibe_rs128_120_enc (not full-chip gate)"
	@echo "make units TC=tc_vibe_rs128_120_dec - Decision-I vibe_rs128_120_dec (module-level)"
	@echo "make rs128_120_dec  - same as units TC=tc_vibe_rs128_120_dec (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_rx_deskew - Decision-I vibe_pcs_rx_deskew (module-level)"
	@echo "make deskew         - same as units TC=tc_vibe_pcs_rx_deskew (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_rx_amctl_lock - Decision-I vibe_pcs_rx_amctl_lock (module-level)"
	@echo "make amctl_lock     - same as units TC=tc_vibe_pcs_rx_amctl_lock (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_rx_unpack - Decision-I vibe_pcs_rx_unpack (module-level)"
	@echo "make unpack         - same as units TC=tc_vibe_pcs_rx_unpack (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_tx_pack - Decision-I vibe_pcs_tx_pack (module-level)"
	@echo "make pack           - same as units TC=tc_vibe_pcs_tx_pack (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_tx_fec - Decision-I vibe_pcs_tx_fec (module-level)"
	@echo "make tx_fec         - same as units TC=tc_vibe_pcs_tx_fec (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_rx_fec - Decision-I vibe_pcs_rx_fec (module-level)"
	@echo "make rx_fec         - same as units TC=tc_vibe_pcs_rx_fec (not full-chip gate)"
	@echo "make units TC=tc_vibe_pcs_tx_g1 - Decision-I vibe_pcs_tx_g1 (module-level)"
	@echo "make g1             - same as units TC=tc_vibe_pcs_tx_g1 (not full-chip gate)"
	@echo "make tx_g1          - same as g1 / tc_vibe_pcs_tx_g1"
	@echo "make units TC=tc_vibe_bcrc - Decision-I vibe_bcrc (module-level)"
	@echo "make bcrc           - same as units TC=tc_vibe_bcrc (not full-chip gate)"
	@echo "make units TC=tc_vibe_dll_credit - Decision-I vibe_dll_credit (module-level)"
	@echo "make credit         - same as units TC=tc_vibe_dll_credit (not full-chip gate)"
	@echo "make units TC=tc_vibe_dll_sm - Decision-I vibe_dll_sm (module-level)"
	@echo "make dll_sm         - same as units TC=tc_vibe_dll_sm (not full-chip gate)"
	@echo "make sm             - same as dll_sm / tc_vibe_dll_sm"
	@echo "make units TC=tc_vibe_dll_rx - Decision-I vibe_dll_rx (module-level)"
	@echo "make dll_rx         - same as units TC=tc_vibe_dll_rx (not full-chip gate)"
	@echo "make rx             - same as dll_rx / tc_vibe_dll_rx"
	@echo "make units TC=tc_vibe_dll_retry_ack_sm - Decision-I vibe_dll_retry_ack_sm (module-level)"
	@echo "make retry_ack_sm   - same as units TC=tc_vibe_dll_retry_ack_sm (not full-chip gate)"
	@echo "make ack_sm         - same as retry_ack_sm / tc_vibe_dll_retry_ack_sm"
	@echo "make units TC=tc_vibe_dll_retry_buf - Decision-I vibe_dll_retry_buf (module-level)"
	@echo "make retry_buf      - same as units TC=tc_vibe_dll_retry_buf (not full-chip gate)"
	@echo "make buf            - same as retry_buf / tc_vibe_dll_retry_buf"
	@echo "make units TC=tc_vibe_dll_retry_req_sm - Decision-I vibe_dll_retry_req_sm (module-level)"
	@echo "make retry_req_sm   - same as units TC=tc_vibe_dll_retry_req_sm (not full-chip gate)"
	@echo "make req_sm         - same as retry_req_sm / tc_vibe_dll_retry_req_sm"
	@echo "make units TC=tc_vibe_fecn_mark - Decision-I vibe_fecn_mark (module-level)"
	@echo "make fecn_mark      - same as units TC=tc_vibe_fecn_mark (not full-chip gate)"
	@echo "make fecn           - same as fecn_mark / tc_vibe_fecn_mark"
	@echo "make units TC=tc_vibe_vl_rr - Decision-I vibe_vl_rr (module-level)"
	@echo "make vl_rr          - same as units TC=tc_vibe_vl_rr (not full-chip gate)"
	@echo "make vl             - same as vl_rr / tc_vibe_vl_rr"
	@echo "make units TC=tc_vibe_route_lu - Decision-I vibe_route_lu (module-level)"
	@echo "make route_lu       - same as units TC=tc_vibe_route_lu (not full-chip gate)"
	@echo "make route          - same as route_lu / tc_vibe_route_lu"
	@echo "make tc_vibe_route_lu - same as route_lu / route"
	@echo "make units TC=tc_vibe_port_sel - Decision-I vibe_port_sel (module-level)"
	@echo "make port_sel       - same as units TC=tc_vibe_port_sel (not full-chip gate)"
	@echo "make psel           - same as port_sel / tc_vibe_port_sel"
	@echo "make tc_vibe_port_sel - same as port_sel / psel"
	@echo "make units TC=tc_vibe_voq_egr - Decision-I vibe_voq_egr (module-level)"
	@echo "make voq_egr        - same as units TC=tc_vibe_voq_egr (not full-chip gate)"
	@echo "make voq            - same as voq_egr / tc_vibe_voq_egr"
	@echo "make tc_vibe_voq_egr - same as voq_egr / voq"
	@echo "make units TC=tc_vibe_saf_ing - Decision-I vibe_saf_ing (module-level)"
	@echo "make saf_ing        - same as units TC=tc_vibe_saf_ing (not full-chip gate)"
	@echo "make saf            - same as saf_ing / tc_vibe_saf_ing"
	@echo "make tc_vibe_saf_ing - same as saf_ing / saf"
	@echo "make units TC=tc_vibe_xbar - Decision-I vibe_xbar (module-level)"
	@echo "make xbar           - same as units TC=tc_vibe_xbar (not full-chip gate)"
	@echo "make tc_vibe_xbar   - same as xbar"
	@echo "make units TC=tc_vibe_dll_tx - Decision-I vibe_dll_tx (module-level)"
	@echo "make dll_tx         - same as units TC=tc_vibe_dll_tx (not full-chip gate)"
	@echo "make tx             - same as dll_tx / tc_vibe_dll_tx"
	@echo "make tc_vibe_dll_tx - same as dll_tx / tx"
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

rs128_120_enc: $(RES)
	$(MAKE) -C $(PYUVM) rs128_120_enc SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

rs128_120_dec: $(RES)
	$(MAKE) -C $(PYUVM) rs128_120_dec SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

deskew: $(RES)
	$(MAKE) -C $(PYUVM) deskew SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

amctl_lock: $(RES)
	$(MAKE) -C $(PYUVM) amctl_lock SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

unpack: $(RES)
	$(MAKE) -C $(PYUVM) unpack SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

pack: $(RES)
	$(MAKE) -C $(PYUVM) pack SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tx_fec: $(RES)
	$(MAKE) -C $(PYUVM) tx_fec SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

rx_fec: $(RES)
	$(MAKE) -C $(PYUVM) rx_fec SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

g1: $(RES)
	$(MAKE) -C $(PYUVM) g1 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tx_g1: $(RES)
	$(MAKE) -C $(PYUVM) tx_g1 SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

bcrc: $(RES)
	$(MAKE) -C $(PYUVM) bcrc SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

credit: $(RES)
	$(MAKE) -C $(PYUVM) credit SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

dll_sm: $(RES)
	$(MAKE) -C $(PYUVM) dll_sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

sm: $(RES)
	$(MAKE) -C $(PYUVM) sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

dll_rx: $(RES)
	$(MAKE) -C $(PYUVM) dll_rx SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

rx: $(RES)
	$(MAKE) -C $(PYUVM) rx SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

retry_ack_sm: $(RES)
	$(MAKE) -C $(PYUVM) retry_ack_sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

ack_sm: $(RES)
	$(MAKE) -C $(PYUVM) ack_sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

retry_buf: $(RES)
	$(MAKE) -C $(PYUVM) retry_buf SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

buf: $(RES)
	$(MAKE) -C $(PYUVM) buf SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

retry_req_sm: $(RES)
	$(MAKE) -C $(PYUVM) retry_req_sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

req_sm: $(RES)
	$(MAKE) -C $(PYUVM) req_sm SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

fecn_mark: $(RES)
	$(MAKE) -C $(PYUVM) fecn_mark SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

fecn: $(RES)
	$(MAKE) -C $(PYUVM) fecn SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

vl_rr: $(RES)
	$(MAKE) -C $(PYUVM) vl_rr SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

vl: $(RES)
	$(MAKE) -C $(PYUVM) vl SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

route_lu: $(RES)
	$(MAKE) -C $(PYUVM) route_lu SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

route: $(RES)
	$(MAKE) -C $(PYUVM) route SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_route_lu: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_route_lu SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

port_sel: $(RES)
	$(MAKE) -C $(PYUVM) port_sel SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

psel: $(RES)
	$(MAKE) -C $(PYUVM) psel SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_port_sel: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_port_sel SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

voq_egr: $(RES)
	$(MAKE) -C $(PYUVM) voq_egr SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

voq: $(RES)
	$(MAKE) -C $(PYUVM) voq SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_voq_egr: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_voq_egr SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

saf_ing: $(RES)
	$(MAKE) -C $(PYUVM) saf_ing SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

saf: $(RES)
	$(MAKE) -C $(PYUVM) saf SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_saf_ing: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_saf_ing SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

xbar: $(RES)
	$(MAKE) -C $(PYUVM) xbar SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_xbar: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_xbar SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

dll_tx: $(RES)
	$(MAKE) -C $(PYUVM) dll_tx SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tx: $(RES)
	$(MAKE) -C $(PYUVM) tx SIM=$(SIM)
	@$(TB)/scripts/summarize.sh $(RES) || true

tc_vibe_dll_tx: $(RES)
	$(MAKE) -C $(PYUVM) tc_vibe_dll_tx SIM=$(SIM)
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
