# Vibe-UB-Switch Python UVM 1.2 (uvm-python)

Primary verification gate. Accellera UVM 1.2 **Python functional equivalence**
via [lukebest/uvm-python](https://github.com/lukebest/uvm-python) + cocotb 1.9.x.

Does **not** modify `rtl/` or `include/`. Does not require Vivado xsim.

## Install pins

```
cocotb>=1.9.2,<2          # 2.x cannot import this library
cocotb-bus
cocotb-coverage
regex
uvm-python @ git+https://github.com/lukebest/uvm-python.git
```

```bash
make -C tb/vibe/pyuvm venv
# or: python3 -m venv tb/vibe/pyuvm/.venv && \
#      tb/vibe/pyuvm/.venv/bin/pip install -r tb/vibe/pyuvm/requirements.txt
```

## Run (no xvlog)

```bash
make -C tb/vibe sim              # default: this tree
make -C tb/vibe suite            # fabric+mgmt G1/CFG/SAF/length
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units            # leaf units + static/neg + port
make -C tb/vibe units TC=tc_vl_rr
make -C tb/vibe/pyuvm units TC=tc_vibe_afifo   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm afifo                    # same as units TC=tc_vibe_afifo
make -C tb/vibe/pyuvm tc_vibe_afifo            # same as afifo
make -C tb/vibe/pyuvm units TC=tc_vibe_sync2   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm sync2                    # same as units TC=tc_vibe_sync2
make -C tb/vibe/pyuvm tc_vibe_sync2            # same as sync2
make -C tb/vibe/pyuvm units TC=tc_vibe_rst_sync  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rst_sync                 # same as units TC=tc_vibe_rst_sync
make -C tb/vibe/pyuvm tc_vibe_rst_sync         # same as rst_sync
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_128_160  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_128_160             # same as units TC=tc_vibe_gear_128_160
make -C tb/vibe/pyuvm tc_vibe_gear_128_160     # same as gear_128_160
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_160_128  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_160_128             # same as units TC=tc_vibe_gear_160_128
make -C tb/vibe/pyuvm tc_vibe_gear_160_128     # same as gear_160_128
make -C tb/vibe/pyuvm units TC=tc_dll          # TP-DLL-004 full vibe_dll split
make -C tb/vibe/pyuvm dll                      # same as units TC=tc_dll (≠1/3 ≠4/3)
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_scramble  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm pcs_scramble             # same as units TC=tc_vibe_pcs_scramble
make -C tb/vibe/pyuvm tc_vibe_pcs_scramble     # same as pcs_scramble
make -C tb/vibe/pyuvm units TC=tc_vibe_ebch16  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm ebch16                   # same as units TC=tc_vibe_ebch16
make -C tb/vibe/pyuvm tc_vibe_ebch16           # same as ebch16
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_cw2beat  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm cw2beat                  # same as units TC=tc_vibe_pcs_tx_cw2beat
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_cw2beat   # same as cw2beat
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_amctl  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm amctl                    # same as units TC=tc_vibe_pcs_tx_amctl
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_amctl     # same as amctl
make -C tb/vibe/pyuvm units TC=tc_vibe_rs128_120_enc  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rs128_120_enc             # same as units TC=tc_vibe_rs128_120_enc
make -C tb/vibe/pyuvm tc_vibe_rs128_120_enc     # same as rs128_120_enc
make -C tb/vibe/pyuvm units TC=tc_vibe_rs128_120_dec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rs128_120_dec             # same as units TC=tc_vibe_rs128_120_dec
make -C tb/vibe/pyuvm tc_vibe_rs128_120_dec     # same as rs128_120_dec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_deskew  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm deskew                   # same as units TC=tc_vibe_pcs_rx_deskew
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_deskew    # same as deskew
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_amctl_lock  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm amctl_lock               # same as units TC=tc_vibe_pcs_rx_amctl_lock
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_amctl_lock  # same as amctl_lock
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_unpack  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm unpack                   # same as units TC=tc_vibe_pcs_rx_unpack
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_unpack    # same as unpack
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_pack  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm pack                     # same as units TC=tc_vibe_pcs_tx_pack
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_pack      # same as pack
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_fec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm tx_fec                   # same as units TC=tc_vibe_pcs_tx_fec
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_fec       # same as tx_fec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_fec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rx_fec                   # same as units TC=tc_vibe_pcs_rx_fec
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_fec       # same as rx_fec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_g1  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm g1                       # same as units TC=tc_vibe_pcs_tx_g1
make -C tb/vibe/pyuvm tx_g1                    # same as g1 / tc_vibe_pcs_tx_g1
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_g1        # same as g1
make -C tb/vibe/pyuvm units TC=tc_vibe_bcrc    # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm bcrc                     # same as units TC=tc_vibe_bcrc
make -C tb/vibe/pyuvm tc_vibe_bcrc             # same as bcrc
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_credit  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm credit                   # same as units TC=tc_vibe_dll_credit
make -C tb/vibe/pyuvm tc_vibe_dll_credit       # same as credit
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm dll_sm                   # same as units TC=tc_vibe_dll_sm
make -C tb/vibe/pyuvm sm                       # same as dll_sm / tc_vibe_dll_sm
make -C tb/vibe/pyuvm tc_vibe_dll_sm           # same as dll_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_rx  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm dll_rx                   # same as units TC=tc_vibe_dll_rx
make -C tb/vibe/pyuvm rx                       # same as dll_rx / tc_vibe_dll_rx
make -C tb/vibe/pyuvm tc_vibe_dll_rx           # same as dll_rx
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_ack_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_ack_sm             # same as units TC=tc_vibe_dll_retry_ack_sm
make -C tb/vibe/pyuvm ack_sm                   # same as retry_ack_sm / tc_vibe_dll_retry_ack_sm
make -C tb/vibe/pyuvm tc_vibe_dll_retry_ack_sm # same as retry_ack_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_buf  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_buf                # same as units TC=tc_vibe_dll_retry_buf
make -C tb/vibe/pyuvm buf                      # same as retry_buf / tc_vibe_dll_retry_buf
make -C tb/vibe/pyuvm tc_vibe_dll_retry_buf    # same as retry_buf
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_req_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_req_sm             # same as units TC=tc_vibe_dll_retry_req_sm
make -C tb/vibe/pyuvm req_sm                   # same as retry_req_sm / tc_vibe_dll_retry_req_sm
make -C tb/vibe/pyuvm tc_vibe_dll_retry_req_sm # same as retry_req_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_fecn_mark  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm fecn_mark                # same as units TC=tc_vibe_fecn_mark
make -C tb/vibe/pyuvm fecn                     # same as fecn_mark / tc_vibe_fecn_mark
make -C tb/vibe/pyuvm tc_vibe_fecn_mark        # same as fecn_mark
make -C tb/vibe/pyuvm units TC=tc_vibe_vl_rr   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm vl_rr                    # same as units TC=tc_vibe_vl_rr
make -C tb/vibe/pyuvm vl                       # same as vl_rr / tc_vibe_vl_rr
make -C tb/vibe/pyuvm tc_vibe_vl_rr            # same as vl_rr
make -C tb/vibe/pyuvm units TC=tc_vibe_route_lu  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm route_lu                 # same as units TC=tc_vibe_route_lu
make -C tb/vibe/pyuvm route                    # same as route_lu / tc_vibe_route_lu
make -C tb/vibe/pyuvm tc_vibe_route_lu         # same as route_lu / route
make -C tb/vibe/pyuvm units TC=tc_vibe_port_sel  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm port_sel                 # same as units TC=tc_vibe_port_sel
make -C tb/vibe/pyuvm psel                     # same as port_sel / tc_vibe_port_sel
make -C tb/vibe/pyuvm tc_vibe_port_sel         # same as port_sel / psel
make -C tb/vibe/pyuvm units TC=tc_vibe_voq_egr  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm voq_egr                  # same as units TC=tc_vibe_voq_egr
make -C tb/vibe/pyuvm voq                      # same as voq_egr / tc_vibe_voq_egr
make -C tb/vibe/pyuvm tc_vibe_voq_egr          # same as voq_egr / voq
make -C tb/vibe/pyuvm units TC=tc_vibe_saf_ing  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm saf_ing                  # same as units TC=tc_vibe_saf_ing
make -C tb/vibe/pyuvm saf                      # same as saf_ing / tc_vibe_saf_ing
make -C tb/vibe/pyuvm tc_vibe_saf_ing          # same as saf_ing / saf
make -C tb/vibe/pyuvm units TC=tc_vibe_xbar  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm xbar                     # same as units TC=tc_vibe_xbar
make -C tb/vibe/pyuvm tc_vibe_xbar             # same as xbar
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_tx  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm dll_tx                   # same as units TC=tc_vibe_dll_tx
make -C tb/vibe/pyuvm tx                       # same as dll_tx / tc_vibe_dll_tx
make -C tb/vibe/pyuvm tc_vibe_dll_tx           # same as dll_tx / tx
make -C tb/vibe/pyuvm units TC=tc_vibe_dll  # Decision-I wrap leaf (not TP-DLL-004)
make -C tb/vibe/pyuvm dll_wrap                 # same as units TC=tc_vibe_dll
make -C tb/vibe/pyuvm wrap                     # same as dll_wrap / tc_vibe_dll
make -C tb/vibe/pyuvm tc_vibe_dll              # same as dll_wrap / wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_icrc  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm icrc                     # same as units TC=tc_vibe_icrc
make -C tb/vibe/pyuvm tc_vibe_icrc             # same as icrc
make -C tb/vibe/pyuvm units TC=tc_vibe_nw_adapt  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm nw_adapt                 # same as units TC=tc_vibe_nw_adapt
make -C tb/vibe/pyuvm tc_vibe_nw_adapt         # same as nw_adapt
make -C tb/vibe/pyuvm units TC=tc_vibe_irq_agg  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm irq_agg                  # same as units TC=tc_vibe_irq_agg
make -C tb/vibe/pyuvm tc_vibe_irq_agg          # same as irq_agg
make -C tb/vibe/pyuvm units TC=tc_vibe_cna_ep  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm cna_ep                   # same as units TC=tc_vibe_cna_ep
make -C tb/vibe/pyuvm tc_vibe_cna_ep           # same as cna_ep
make -C tb/vibe/pyuvm units TC=tc_vibe_cfg_space  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm cfg_space                # same as units TC=tc_vibe_cfg_space
make -C tb/vibe/pyuvm tc_vibe_cfg_space        # same as cfg_space
make -C tb/vibe/pyuvm units TC=tc_vibe_port  # Decision-I wrap leaf (not tc_port_smoke)
make -C tb/vibe/pyuvm port_wrap                # same as units TC=tc_vibe_port
make -C tb/vibe/pyuvm tc_vibe_port             # same as port_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_ub_switch  # Decision-I wrap leaf (not tc_top_smoke)
make -C tb/vibe/pyuvm top_wrap                 # same as units TC=tc_vibe_ub_switch
make -C tb/vibe/pyuvm tc_vibe_ub_switch        # same as top_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_mgmt  # Decision-I wrap leaf (not tc_mgmt)
make -C tb/vibe/pyuvm mgmt_wrap                # same as units TC=tc_vibe_mgmt
make -C tb/vibe/pyuvm tc_vibe_mgmt             # same as mgmt_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_fabric  # Decision-I wrap leaf (not suite)
make -C tb/vibe/pyuvm fabric_wrap              # same as units TC=tc_vibe_fabric
make -C tb/vibe/pyuvm tc_vibe_fabric           # same as fabric_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx  # Decision-I wrap leaf (not tc_pcs_tx)
make -C tb/vibe/pyuvm pcs_tx_wrap              # same as units TC=tc_vibe_pcs_tx
make -C tb/vibe/pyuvm tc_vibe_pcs_tx           # same as pcs_tx_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx  # Decision-I wrap leaf (not tc_pcs_rx)
make -C tb/vibe/pyuvm pcs_rx_wrap              # same as units TC=tc_vibe_pcs_rx
make -C tb/vibe/pyuvm tc_vibe_pcs_rx           # same as pcs_rx_wrap
make -C tb/vibe/pyuvm units TC=tc_vibe_lmsm  # Decision-I wrap leaf (not tc_lmsm_walk)
make -C tb/vibe/pyuvm lmsm_wrap                # same as units TC=tc_vibe_lmsm
make -C tb/vibe/pyuvm tc_vibe_lmsm             # same as lmsm_wrap
make -C tb/vibe/pyuvm vibe_port_wrap           # Decision-I wrap leaf (not make port / port_wrap)
make -C tb/vibe port TC=tc_port_smoke
make -C tb/vibe top              # vibe_ub_switch + peer PMA
make -C tb/vibe neg              # absent-feature scan
```

Simulator: `SIM=verilator` (baseline) or `SIM=icarus`.

```bash
make -C tb/vibe/pyuvm sim SIM=icarus
make -C tb/vibe/pyuvm units TC=tc_vl_rr SIM=icarus
make -C tb/vibe/pyuvm afifo SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_afifo SIM=verilator  # same as afifo
make -C tb/vibe/pyuvm sync2 SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_sync2 SIM=verilator  # same as sync2
make -C tb/vibe/pyuvm rst_sync SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_rst_sync SIM=verilator  # same as rst_sync
make -C tb/vibe/pyuvm gear_128_160 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_gear_128_160 SIM=verilator  # same as gear_128_160
make -C tb/vibe/pyuvm gear_160_128 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_gear_160_128 SIM=verilator  # same as gear_160_128
make -C tb/vibe/pyuvm pcs_scramble SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_scramble SIM=verilator  # same as pcs_scramble
make -C tb/vibe/pyuvm ebch16 SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_ebch16 SIM=verilator  # same as ebch16
make -C tb/vibe/pyuvm cw2beat SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_cw2beat SIM=verilator  # same as cw2beat
make -C tb/vibe/pyuvm amctl SIM=verilator         # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_amctl SIM=verilator  # same as amctl
make -C tb/vibe/pyuvm rs128_120_enc SIM=verilator # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_rs128_120_enc SIM=verilator  # same as rs128_120_enc
make -C tb/vibe/pyuvm rs128_120_dec SIM=verilator # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_rs128_120_dec SIM=verilator  # same as rs128_120_dec
make -C tb/vibe/pyuvm deskew SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_deskew SIM=verilator  # same as deskew
make -C tb/vibe/pyuvm amctl_lock SIM=verilator    # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_amctl_lock SIM=verilator  # same as amctl_lock
make -C tb/vibe/pyuvm unpack SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_unpack SIM=verilator  # same as unpack
make -C tb/vibe/pyuvm pack SIM=verilator          # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_pack SIM=verilator  # same as pack
make -C tb/vibe/pyuvm tx_fec SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_fec SIM=verilator  # same as tx_fec
make -C tb/vibe/pyuvm rx_fec SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_rx_fec SIM=verilator  # same as rx_fec
make -C tb/vibe/pyuvm g1 SIM=verilator            # or SIM=icarus
make -C tb/vibe/pyuvm tx_g1 SIM=verilator         # same as g1
make -C tb/vibe/pyuvm tc_vibe_pcs_tx_g1 SIM=verilator  # same as g1
make -C tb/vibe/pyuvm bcrc SIM=verilator          # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_bcrc SIM=verilator  # same as bcrc
make -C tb/vibe/pyuvm credit SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_dll_credit SIM=verilator # same as credit
make -C tb/vibe/pyuvm dll_sm SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm sm SIM=verilator            # same as dll_sm
make -C tb/vibe/pyuvm tc_vibe_dll_sm SIM=verilator # same as dll_sm
make -C tb/vibe/pyuvm dll_rx SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm rx SIM=verilator            # same as dll_rx
make -C tb/vibe/pyuvm tc_vibe_dll_rx SIM=verilator # same as dll_rx
make -C tb/vibe/pyuvm retry_ack_sm SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm ack_sm SIM=verilator        # same as retry_ack_sm
make -C tb/vibe/pyuvm tc_vibe_dll_retry_ack_sm SIM=verilator # same as retry_ack_sm
make -C tb/vibe/pyuvm retry_buf SIM=verilator     # or SIM=icarus
make -C tb/vibe/pyuvm buf SIM=verilator           # same as retry_buf
make -C tb/vibe/pyuvm tc_vibe_dll_retry_buf SIM=verilator # same as retry_buf
make -C tb/vibe/pyuvm retry_req_sm SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm req_sm SIM=verilator        # same as retry_req_sm
make -C tb/vibe/pyuvm tc_vibe_dll_retry_req_sm SIM=verilator # same as retry_req_sm
make -C tb/vibe/pyuvm fecn_mark SIM=verilator     # or SIM=icarus
make -C tb/vibe/pyuvm fecn SIM=verilator          # same as fecn_mark
make -C tb/vibe/pyuvm tc_vibe_fecn_mark SIM=verilator # same as fecn_mark
make -C tb/vibe/pyuvm vl_rr SIM=verilator         # or SIM=icarus
make -C tb/vibe/pyuvm vl SIM=verilator            # same as vl_rr
make -C tb/vibe/pyuvm tc_vibe_vl_rr SIM=verilator # same as vl_rr
make -C tb/vibe/pyuvm route_lu SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm route SIM=verilator         # same as route_lu
make -C tb/vibe/pyuvm tc_vibe_route_lu SIM=verilator  # same as route_lu
make -C tb/vibe/pyuvm port_sel SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm psel SIM=verilator          # same as port_sel
make -C tb/vibe/pyuvm tc_vibe_port_sel SIM=verilator  # same as port_sel
make -C tb/vibe/pyuvm voq_egr SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm voq SIM=verilator           # same as voq_egr
make -C tb/vibe/pyuvm tc_vibe_voq_egr SIM=verilator  # same as voq_egr
make -C tb/vibe/pyuvm saf_ing SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm saf SIM=verilator           # same as saf_ing
make -C tb/vibe/pyuvm tc_vibe_saf_ing SIM=verilator  # same as saf_ing
make -C tb/vibe/pyuvm xbar SIM=verilator           # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_xbar SIM=verilator   # same as xbar
make -C tb/vibe/pyuvm dll_tx SIM=verilator         # or SIM=icarus
make -C tb/vibe/pyuvm tx SIM=verilator             # same as dll_tx
make -C tb/vibe/pyuvm tc_vibe_dll_tx SIM=verilator # same as dll_tx
make -C tb/vibe/pyuvm dll_wrap SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm wrap SIM=verilator           # same as dll_wrap
make -C tb/vibe/pyuvm tc_vibe_dll SIM=verilator    # same as dll_wrap
make -C tb/vibe/pyuvm icrc SIM=verilator           # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_icrc SIM=verilator   # same as icrc
make -C tb/vibe/pyuvm nw_adapt SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_nw_adapt SIM=verilator # same as nw_adapt
make -C tb/vibe/pyuvm irq_agg SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_irq_agg SIM=verilator  # same as irq_agg
make -C tb/vibe/pyuvm cna_ep SIM=verilator         # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_cna_ep SIM=verilator # same as cna_ep
make -C tb/vibe/pyuvm cfg_space SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_cfg_space SIM=verilator # same as cfg_space
make -C tb/vibe/pyuvm port_wrap SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_port SIM=verilator   # same as port_wrap
make -C tb/vibe/pyuvm top_wrap SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_ub_switch SIM=verilator # same as top_wrap
make -C tb/vibe/pyuvm mgmt_wrap SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_mgmt SIM=verilator   # same as mgmt_wrap
make -C tb/vibe/pyuvm fabric_wrap SIM=verilator    # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_fabric SIM=verilator # same as fabric_wrap
make -C tb/vibe/pyuvm pcs_tx_wrap SIM=verilator    # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_tx SIM=verilator # same as pcs_tx_wrap
make -C tb/vibe/pyuvm pcs_rx_wrap SIM=verilator    # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_pcs_rx SIM=verilator # same as pcs_rx_wrap
make -C tb/vibe/pyuvm lmsm_wrap SIM=verilator      # or SIM=icarus
make -C tb/vibe/pyuvm tc_vibe_lmsm SIM=verilator   # same as lmsm_wrap
make -C tb/vibe/pyuvm vibe_port_wrap SIM=verilator # or SIM=icarus
```

`tc_vibe_afifo` / `make afifo` / `make tc_vibe_afifo` is **module-level
only** (dual-clock `wrst_n`/`rrst_n`, CDC integrity across wclk/rclk
including 0/all-1s/walk-1, fill/`almost_full` at occ≥10, `wfull` at
16, write-while-full, drain/`rempty`, read-while-empty, async mid-run
reset, pin scan). It is **not** the full-chip consecutive-green gate
and **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_afifo_afull10.sv` remains optional control. This is
**not** `vibe_sync2` / `vibe_rst_sync` / gear. Instantiated by
`vibe_port` TX×4 (`W=160`) and RX×4 (`W=128`). `ovf_l` (F1) is not in
this module. CFG6 packing is 未知. CHILDREN from product SV: `u_r2w` /
`u_w2r` (`vibe_sync2`).

`tc_vibe_sync2` / `make sync2` / `make tc_vibe_sync2` is **module-level
only** (reset `q==0`, stable `d` reaches `q` after 2 posedges not 1,
walk-1 on W=5, all-1s, streaming 2-cycle delay vs golden, async
`rst_n` clears the pipe, hold-through posedge, no ready/valid pins).
It is **not** 1/3, 4/3, freeze, or signoff. There is no stock Icarus
`tc_sync2`; this is the leaf scorer. This is **not** `vibe_rst_sync`
and **not** gear. Instantiated by `vibe_afifo` `u_r2w` / `u_w2r`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_rst_sync` / `make rst_sync` / `make tc_vibe_rst_sync` is
**module-level only** (async `rst_n_in` asserts `rst_n_out` without a dest
posedge, sync deassert after 2 dest clocks not 1, hold-through dest posedge,
mid-run re-assert clears both flops, released `rst_n_out` stays 1, no
ready/valid pins). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_rst_sync.sv` / `tc_rst_sync` remains optional control. This
is **not** `vibe_sync2` / `vibe_afifo` / gear. Instantiated by `vibe_port`
`u_txrst` / `u_rxrst`. `ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_gear_128_160` / `make gear_128_160` / `make tc_vibe_gear_128_160`
is **module-level only** (reset idle / no spurious `out_vld`, combo
`in_ready = !hold_vld || out_ready` including hold-empty + `out_ready=0`,
5×128 → exactly 4×160 LSB-first residue packing vs golden, hold-full
backpressure without drop/dup, same-cycle take+accept when hold is full
and `out_ready=1`, phase wrap on a second group, mid-run async `rst_n`
clears `hold_vld`/`phase`, pin scan). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_gear_128_160.sv` / `tc_gear_128_160`
remains optional count-only control. This is **not** `vibe_gear_160_128` /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` and **not** TP-DLL-004 /
full-chip `tc_dll` (`make -C tb/vibe/pyuvm dll` / `units TC=tc_dll` scores
that ID). Instantiated by `vibe_port` `u_rg0`..`u_rg3`. `ovf_l` (F1) is
not in this module. CHILDREN: none.

`tc_vibe_gear_160_128` / `make gear_160_128` / `make tc_vibe_gear_160_128`
is **module-level only** (reset idle / no spurious `out_vld`, combo
`in_ready = can_load && (rbits != 4)` including hold-empty + `out_ready=0`
and `rbits==4` blocking even when `can_load`, 4×160 → exactly 5×128
LSB-first residue packing vs golden, hold-full / `rbits==4` backpressure
without drop/dup, same-cycle take+accept when hold is full and
`out_ready=1` and `rbits!=4`, residue flush when `rbits==4 && can_load`,
phase wrap on a second group, mid-run async `rst_n` clears
`hold_vld`/`rbits`, pin scan). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_gear_160_128.sv` / `tc_gear_160_128`
remains optional count-only control. This is **not** `vibe_gear_128_160` /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` and **not** TP-DLL-004 /
full-chip `tc_dll` (`make -C tb/vibe/pyuvm dll` / `units TC=tc_dll` scores
that ID). Instantiated by `vibe_port` `u_g0`..`u_g3`. `ovf_l` (F1) is
not in this module. CHILDREN: none.

`tc_vibe_pcs_scramble` / `make pcs_scramble` / `make tc_vibe_pcs_scramble`
is **module-level only** (reset idle / no spurious `out_vld`, async
`rst_n` clear of registered outs, known LID seed `{19'd1, lane_id, 2'b01}`
vs golden 160b xmask, distinct LIDs, AMCTL/EEIB `en=0` pass-through
without LFSR advance, XOR round-trip, `seed_load`+`in_vld`+`en` NBA
last-wins is the 160-step advance, mid-run async `rst_n` returns the
LFSR to reset seed `{21'd0, 2'b01}`, pin scan with instance `u_u`).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_pcs_scramble.sv` / `tc_pcs_scramble` remains optional
control. Official TP-PHY-017 stays scored by `tc_pcs_scramble`. This is
**not** `vibe_pcs_tx` / `vibe_pcs_rx` / `vibe_ebch16` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` and **not** TP-DLL-004 /
`gear_160_128`. Instantiated by `vibe_pcs_tx` `u_s0`..`u_s3` and
`vibe_pcs_rx` `u_d0`..`u_d3`. `ovf_l` (F1) is not in this module.
CHILDREN: none.

`tc_vibe_ebch16` / `make ebch16` / `make tc_vibe_ebch16`
is **module-level only** (combo idle / no sequential hold — the DUT
has no `clk` / `rst_n`, so there is no async clear to pulse, Table 3-5
encode LUT + default sel 31 vs product SV golden, unique invert decode,
complementary pairs at Hamming 16, min Hamming distance 8, mid-run
`cw_sel` walk without hold, pin scan with instance `u_u`). It is **not**
1/3, 4/3, freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_ebch16_lut.sv`
/ `tc_ebch16_lut` remains optional control. This is **not** TP-PHY-017 /
`pcs_scramble` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` /
`vibe_sync2` / `vibe_rst_sync`. Instantiated by `vibe_pcs_tx_amctl`
`u3`/`u8`/`u9`/`u10`/`u21`/`u22`/`u28` and `vibe_pcs_rx_amctl_lock`
the same named LUT cells. `ovf_l` (F1) is not in this module.
CHILDREN: none.

`tc_vibe_pcs_tx_cw2beat` / `make cw2beat` / `make tc_vibe_pcs_tx_cw2beat`
is **module-level only** (reset idle / no spurious `beat_vld`, async
`rst_n` clear of registered halves, 1024→exactly 2×512 high-then-low
vs golden split, hold-full backpressure without drop/dup, `cw_vld`
while not ready does not overwrite parked halves, consume-last+`cw_vld`
does not accept — `cw_ready` and `beat_vld` are exclusive, second
codeword after drain, mid-run async `rst_n` through dest posedge,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_cw2beat.sv` /
`tc_pcs_cw2beat` remains optional count-only control. Official
TP-PHY-009 stays scored by `tc_pcs_cw2beat`. This is **not**
TP-PHY-017 / `pcs_scramble` / `ebch16` / `vibe_pcs_tx` / `vibe_pcs_rx`
/ gear / `vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Instantiated
by `vibe_pcs_tx` `u_cw`. `ovf_l` (F1) is not in this module.
CHILDREN: none.

`tc_vibe_pcs_tx_amctl` / `make amctl` / `make tc_vibe_pcs_tx_amctl`
is **module-level only** (reset / idle `ack=0`, async `rst_n` combo
hold of the unused pin, 40-symbol eBCH-16 insert/align vs Table 3-5
BODY/END/LID/CTRL_TYPE/CTRL_DETAIL, all four `lane_id` LID mux arms,
`ack=req&&link_up`, combo hold, mid-run async `rst_n` through dest
posedge still holds, CHILD eBCH-16 `u3`/`u8`/`u9`/`u10`/`u21`/`u22`/`u28`
vs Table 3-5, pin scan with instance `u_u`). `clk` / `rst_n` /
`sdf_period` are unused in the assemble body. It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_pcs_amctl.sv` /
`tc_pcs_amctl` remains optional control. Official TP-PHY-016 stays
scored by `tc_pcs_amctl`. This is **not** TP-PHY-009 / `cw2beat` /
`ebch16` / `pcs_scramble` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Instantiated by
`vibe_pcs_tx_pack` `u_am0`..`u_am3`. `ovf_l` (F1) is not in this
module. CHILDREN: `u3`/`u8`/`u9`/`u10`/`u21`/`u22`/`u28`
(`vibe_ebch16`).

`tc_vibe_rs128_120_enc` / `make rs128_120_enc` /
`make tc_vibe_rs128_120_enc` is **module-level only** (reset / idle
`in_ready=0` `done=0` `parity=0`, systematic RS(128,120) encode /
8-symbol parity vs golden GF(256) LFSR, `start` restart, `in_vld`
stall without a step, second message after `done`, mid-run async
`rst_n` through dest posedge, pin scan with instance `u_u`). It is
**not** 1/3, 4/3, freeze, or signoff. There is no stock Icarus leaf
`tc_rs128_120_enc`; FEC wrap TCs (`tc_pcs_fec_*`) remain the official
scorers for the instantiator. The Decision-I wrap leaf is
`tc_vibe_pcs_tx_fec` / `make tx_fec` / `make tc_vibe_pcs_tx_fec`.
This is **not** TP-PHY-016 /
`amctl` / `cw2beat` / `ebch16` / `pcs_scramble` / `vibe_pcs_tx` /
`vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`
/ `rs128_120_dec`. Instantiated by `vibe_pcs_tx_fec` `u_enc_a` /
`u_enc_b`. `ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_rs128_120_dec` / `make rs128_120_dec` /
`make tc_vibe_rs128_120_dec` is **module-level only** (reset / idle
`in_ready=0` `done=0` `fec_fail=0` `data_out=0`, RS(128,120)
syndrome-check decode / `data_out` pack vs golden Horner, valid CW
`fec_fail=0` vs corrupted CW `fec_fail=1` (no correction), `start`
restart, `in_vld` stall without a step, second CW after `done`,
mid-run async `rst_n` through dest posedge, pin scan with instance
`u_u`). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_rs_dec_syndrome.sv` / `tc_rs_dec_syndrome` remains
the official done-pulse scorer. The Decision-I wrap leaf is
`tc_vibe_pcs_rx_fec` / `make rx_fec` /
`make tc_vibe_pcs_rx_fec`. This is **not** the encoder leaf /
`rs128_120_enc` / `amctl` / `cw2beat` / `ebch16` / `pcs_scramble` /
`vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` /
`vibe_rst_sync`. Same Horner recurrence is inlined in
`vibe_pcs_rx_fec` (not an instance). `ovf_l` (F1) is not in this
module. CHILDREN: none.

`tc_vibe_pcs_rx_deskew` / `make deskew` /
`make tc_vibe_pcs_rx_deskew` is **module-level only**
(reset / idle `aligned=0` no spurious `out_vld`, staggered AMCTL
lane-skew absorb / first-AMCTL lock / `aligned`, factory
physical=logical pass-through with no lane swap, AM drop
`out_vld=0`, `in_vld` stall without a saw step, second data group
after lock, mid-run async `rst_n` through dest posedge, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_pcs_rx_deskew.sv` / `tc_pcs_rx_deskew`
remains the official staggered-AM / `out_vld` scorer. This is
**not** the decoder leaf / `rs128_120_dec` / `amctl_lock` /
`unpack` / `amctl` / `cw2beat` / `ebch16` / `pcs_scramble` /
`vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` /
`vibe_sync2` / `vibe_rst_sync` / `g1` / `tx_fec` / `pack`.
Instantiated by `vibe_pcs_rx` `u_dsk`. `ovf_l` (F1) is not in
this module. CHILDREN: none.

`tc_vibe_pcs_rx_amctl_lock` / `make amctl_lock` /
`make tc_vibe_pcs_rx_amctl_lock` is **module-level
only** (reset / idle `locked=0` no spurious `is_amctl`/`sdf`/`edf`,
AMCTL detect on `match_w0`/`match_w1`/`match_pair`, `CONFIRM_N=3`
lock, `UNLOCK_N=3` legacy unlock, TX-layout sticky lock, all four
LID mux arms, `lid_bad` (U24, no swap), `in_vld` stall without a
confirm/unlock step, mid-run async `rst_n` through dest posedge,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_rx_amctl.sv` /
`tc_pcs_rx_amctl` remains the official 4-pair / LID / unlock /
`lid_bad` scorer. This is **not** the deskew leaf / `deskew` /
`unpack` / `amctl` / `cw2beat` / `ebch16` / `pcs_scramble` /
`vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` /
`vibe_sync2` / `vibe_rst_sync` / `g1` / `tx_fec` / `pack`.
Instantiated by `vibe_pcs_rx` `u_l0`..`u_l3`. `ovf_l` (F1) is
not in this module. CHILDREN: `u3` / `u8` / `u9` / `u10` /
`u21` / `u22` / `u28` (`vibe_ebch16`).

`tc_vibe_pcs_rx_unpack` / `make unpack` /
`make tc_vibe_pcs_rx_unpack` is **module-level
only** (reset / idle `beat_vld=0` no spurious beat, AMCTL
`am0..am3` skip, 4×640 → exactly 5×512 unpack vs golden
LSB-first pack, `beat_ready` hold without drop/dup, `am_gap`
n-reset that keeps an in-flight emit, dual-buffer `nxt_full`
/ acc swap, `lane_vld` stall without a take, second group
after drain, mid-run async `rst_n` through dest posedge,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_rx_unpack.sv` /
`tc_pcs_rx_unpack` remains the official `beat_vld` / `am_gap`
/ `nxt_full` scorer. This is **not** the AMCTL-lock leaf /
`amctl_lock` / `deskew` / `amctl` / `cw2beat` / `ebch16` /
`pcs_scramble` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` / `g1` /
`tx_fec` / `pack`. Instantiated by `vibe_pcs_rx` `u_un`.
`ovf_l` (F1) is not in this module. CHILDREN: none. Pairs
with TX pack (`make pack` / `tc_vibe_pcs_tx_pack`).

`tc_vibe_pcs_tx_pack` / `make pack` /
`make tc_vibe_pcs_tx_pack` is **module-level only** (reset /
idle `lane_vld=0` `beat_ready` no spurious emit, 5×512 →
exactly 4×640 pack vs golden LSB-first inverse of unpack,
`lane_ready` / `afifo_afull` hold without drop/dup,
`beat_vld` stall without a take, AMCTL insert on the 512 /
640-symbol timer with per-lane 40B halves, AM wait until a
finishing 4×640 emits, second group after drain, mid-run
async `rst_n` through dest posedge, pin scan with instance
`u_u`). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_pcs_tx_pack.sv` / `tc_pcs_tx_pack`
remains the official `lane_vld` scorer. This is **not** the
RX unpack leaf / `unpack` / `amctl` / `cw2beat` / `ebch16` /
`pcs_scramble` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` / `g1` /
`tx_fec`. Instantiated by `vibe_pcs_tx` `u_pack`. `ovf_l`
(F1) is not in this module. CHILDREN: `u_am0` / `u_am1` /
`u_am2` / `u_am3` (`vibe_pcs_tx_amctl`). Pairs with RX
unpack (`make unpack` / `tc_vibe_pcs_rx_unpack`).

`tc_vibe_pcs_tx_fec` / `make tx_fec` /
`make tc_vibe_pcs_tx_fec` is **module-level only** (reset /
idle `win_ready=1` `cw_vld=0` no spurious CW, two-window
bypass `{w0,64'd0}` then `{w1,64'd0}`, T=4 / T=2 encode wrap
vs golden RS(128,120) parity, `cw_ready` hold without
drop/dup, `win_vld` stall after the first window,
`win_ready=!have1` until both CWs drain, second pair after
drain, mid-run async `rst_n` through dest posedge, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_fec_*.sv` /
`tc_pcs_fec_*` remain the official wrap scorers. This is
**not** the encoder leaf / `rs128_120_enc` / `amctl` /
`cw2beat` / `ebch16` / `pcs_scramble` / `vibe_pcs_tx` /
`vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` /
`vibe_rst_sync` / `g1` / `rs128_120_dec`. Instantiated by
`vibe_pcs_tx` `u_fec`. `ovf_l` (F1) is not in this module.
CHILDREN: `u_enc_a` / `u_enc_b` (`vibe_rs128_120_enc`).
Sits on stage-11 enc + stage-16 pack.

`tc_vibe_pcs_rx_fec` / `make rx_fec` /
`make tc_vibe_pcs_rx_fec` is **module-level
only** (reset / idle `beat_ready=1` `win_vld=0` no spurious
window, two-beat bypass `{hi, lo[511:64]}`, T=4 / T=2
syndrome-check unwrap vs golden RS(128,120) Horner, garbage
CW `fec_fail=1` without forwarding a 960, `win_ready` hold
(`beat_ready=!win_vld`), `beat_vld` stall after the first
half-CW, `am_gap` drop of leftover `have_hi`, second CW
after drain, mid-run async `rst_n` through dest posedge,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_rx_fec.sv` /
`tc_pcs_rx_fec` remains the official `win_vld` scorer.
This is **not** the decoder leaf / `rs128_120_dec` /
`amctl_lock` / `deskew` / `unpack` / `amctl` / `cw2beat` /
`ebch16` / `pcs_scramble` / `vibe_pcs_tx` / `vibe_pcs_rx` /
gear / `vibe_afifo` / `vibe_sync2` / `vibe_rst_sync` / `g1` /
`tx_fec` / `pack`. Instantiated by `vibe_pcs_rx` `u_fec`.
`ovf_l` (F1) is not in this module. CHILDREN: none (Horner
inlined). Pairs with TX FEC (`make tx_fec` /
`tc_vibe_pcs_tx_fec`).

`tc_vibe_pcs_tx_g1` / `make g1` / `make tx_g1` /
`make tc_vibe_pcs_tx_g1` is **module-level only** (reset / idle
`win_vld=0` no spurious 960, 6-Null idle fill, isolated 4-flit +
2-Null complete, 1.5-beat rem-complete plus rem leftover + 4-Null
fill, `win_ready` hold without drop/dup, `in_vld` stall at
`nflit==4`, `link_up=0` no take / no idle fill, same-cycle
ack+take, second window after drain, mid-run async `rst_n`
through dest posedge, pin scan with instance `u_u`). It is
**not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_pcs_tx_g1_window.sv` / `tc_pcs_tx_g1_window`
remains the official `win_vld` scorer. This is **not** the TX FEC
wrap / `tx_fec` / `cw2beat` / `amctl` / `ebch16` / `pcs_scramble`
/ `vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` /
`vibe_sync2` / `vibe_rst_sync`. Instantiated by `vibe_pcs_tx`
`u_g1`. `ovf_l` (F1) is not in this module. CHILDREN: none.
Feeds stage-17 `vibe_pcs_tx_fec`.

`tc_vibe_bcrc` / `make bcrc` /
`make tc_vibe_bcrc` is **module-level only** (reset / idle
`crc_word=0` `done=0` no spurious pulse, AS §12 CRC30 encode vs
golden init-all-1 / no invert / LSB-first 160b eat, `ERROR_FLAG` /
reserved packing, check DUT word vs golden residue, `start` restart
that wins over `in_vld`, `in_vld` stall without a step, `last`
without `in_vld`, second block after `done`, mid-run async `rst_n`
through dest posedge, pin scan with instance `u_u`). It is **not** 1/3,
4/3, freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_bcrc_crc30.sv` /
`tc_bcrc_crc30` remains the official bit31 / bit30 scorer. This is
**not** TP-DLL-004 / `dll` / `credit` / `dll_sm` / `dll_rx` / `icrc` /
`vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` /
`vibe_rst_sync`. First DLL leaf after PCS stage-1..19. Instantiated
as TB helper `u_bcrc`; `vibe_dll_tx` inlines the same CRC30.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll_credit` / `make credit` /
`make tc_vibe_dll_credit` is **module-level only** (reset /
idle `pending=0` `credit_low=1` no `bp_nw` / `proto_err` / `fc_ovf`,
`credit_ret` grant already cells, consume `ceil(flits/n)` vs golden,
CFG0 skip, `grain_n=0` → 0, `consume_vld` stall without a step,
same-cycle `credit_ret` && `consume_vld`, 1023 vs 1024 cell thresh,
second consume after the first, `port_rst` / `!link_up` clear, 1µs
timeout → `proto_err`, mid-run async `rst_n` through dest posedge,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_credit_*.sv` /
`tc_cfg0_no_credit` remain the official cell-thresh / grain / CFG0 /
timeout scorers. This is **not** TP-DLL-004 / `dll` / `bcrc` /
`dll_sm` / `dll_rx` / `icrc` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Second DLL leaf after
`vibe_bcrc`. Instantiated by `vibe_dll` `u_crd`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll_sm` / `make dll_sm` / `make sm` /
`make tc_vibe_dll_sm` is **module-level
only** (reset → Disabled, `!link_up` / `port_rst` / `dll_error`
→ Disabled, walk Disabled → Param → Credit → Normal on
`param_ok` / `credit_ok`, `status_up` only in Normal, `disabled`
only in Disabled, hold in Normal, mid-run async `rst_n`
through dest posedge, pin scan with instance `u_u`). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_dll_sm_states.sv`
/ `tc_dll_sm_states` remains the official TP-DLL-001 / 002 / 003
scorer. This is **not** TP-DLL-004 / `dll` / `bcrc` / `credit` /
`dll_rx` / `icrc` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Third DLL leaf after
`vibe_bcrc` / `vibe_dll_credit`. Instantiated by `vibe_dll` `u_sm`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll_rx` / `make dll_rx` / `make rx` /
`make tc_vibe_dll_rx` is **module-level
only** (reset / `port_rst` / `!link_up` clears, CFG0 terminate
does not enter fabric, PCS→NW packing / LPH / EOP leftover drop,
FEC fail → `start_retry`, `rx_ovf` on buffer full, ready/valid
handshake, mid-run async `rst_n` through dest posedge, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_cfg0_term_not_fabric.sv` /
`tc_dll_rx_errflag.sv` / `tc_fec_fail_gbn.sv` remain the official
TP scorers. This is **not** TP-DLL-004 / `dll` / `bcrc` / `credit` /
`dll_sm` / `icrc` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Fourth DLL leaf
after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm`. Instantiated
by `vibe_dll` `u_rx`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll_retry_ack_sm` / `make retry_ack_sm` / `make ack_sm` /
`make tc_vibe_dll_retry_ack_sm` is **module-level only** (reset /
`port_rst` clears to NORMAL, `start_ack` → 1 Idle then 32 Ack,
replay `RdPtr` from `RcvPtr` until `WrPtr`, return to NORMAL,
`start_ack` ignored in ACK / PLAY, mid-run async `rst_n` through
dest posedge, pin scan with instance `u_u`). It is **not** 1/3,
4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_retry_ack_replay.sv` / `tc_retry_ack_replay`
remains the official TP scorer. This is **not** TP-DLL-004 /
`dll` / `bcrc` / `credit` / `dll_sm` / `dll_rx` / `icrc` /
`vibe_pcs_tx` / `vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` /
`vibe_rst_sync`. Fifth DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx`. Instantiated by `vibe_dll` `u_ack`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll_retry_buf` / `make retry_buf` / `make buf` /
`make tc_vibe_dll_retry_buf` is **module-level only** (reset /
`port_rst` / `!link_up` pointers and free to reset values,
`proto_err` cleared on hard `rst_n` only, normal write advances
`wr_ptr` and decrements free, `can_send` tracks free vs
`send_size`, Null and Retry writes do not enter, ack release
advances `tail`/`rcv` and restores free, overflow
`free+rel_size>256` asserts `proto_err`, `rd_ptr_i` returns the
stored flit, mid-run async `rst_n` through dest posedge, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_retry_buf_256.sv` /
`tc_retry_buf_256` remains the official TP scorer. This is **not**
TP-DLL-004 / `dll` / `bcrc` / `credit` / `dll_sm` / `dll_rx` /
`retry_ack_sm` / `icrc` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Sixth DLL leaf
after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm`. Instantiated by
`vibe_dll` `u_rbuf`. `ovf_l` (F1) is not in this module.
CHILDREN: none.

`tc_vibe_dll_retry_req_sm` / `make retry_req_sm` / `make req_sm` /
`make tc_vibe_dll_retry_req_sm` is **module-level only** (reset /
`port_rst` / `device_rst` clears to NORMAL, `start_retry` → 1 Idle
then 32 Req, REQ → WAIT or RETRAIN at `NUM_RETRY` /
`phy_retrain`, `wait_done_ack` → NORMAL, WAIT timeout → REQ,
RETRAIN 1-cycle then NORMAL or ERROR at `NUM_PHY_REINIT`, ERROR
waits Port/device reset, mid-run async `rst_n` through dest
posedge, pin scan with instance `u_u`). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_retry_req_gbn.sv` / `tc_retry_wait_retrain.sv`
remain the official TP scorers. This is **not** TP-DLL-004 /
`dll` / `bcrc` / `credit` / `dll_sm` / `dll_rx` / `retry_ack_sm` /
`retry_buf` / `icrc` / `vibe_pcs_tx` / `vibe_pcs_rx` / gear /
`vibe_afifo` / `vibe_sync2` / `vibe_rst_sync`. Seventh DLL leaf
after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf`.
Instantiated by `vibe_dll` `u_req`. `ovf_l` (F1) is not in this
module. CHILDREN: none.

`tc_vibe_fecn_mark` / `make fecn_mark` / `make fecn` /
`make tc_vibe_fecn_mark` is **module-level only** (combo idle /
no clk / no `rst_n` / no ready / no sequential hold, stock Mode
`3'b100`/`3'b010` + VOQ watermark `FECN_WM=24`, FECN `2'b00`
unmarkable / `2'b11` already-severe / non-markable modes,
congestion vs packet FECN worse, golden rewrite of FECN and LoC
vs pass-through, wrap-vs-DUT instance score on `u_u`, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_fecn_mark.sv` /
`tc_fecn_mark` remains the official TP scorer (direct
`vibe_fecn_mark` top, instance `u_f`). This is **not** CAQM.
First fabric leaf after NW tip-align wave complete (stage-79
`vibe_nw_adapt` wrap). Instance `u_u` matches Decision-I leaf
wrappers; product instantiator is `vibe_fabric` `u_fecn`; stock
Icarus uses `u_f`. `ovf_l` (F1) is not in this module. CHILDREN:
none. This is **not** `dll_wrap` / `wrap` / `top` / `port` /
`icrc` / `nw_adapt` / `vibe_icrc` / `vibe_nw_adapt` /
`vibe_bcrc` / `vibe_dll`. Do not invent `vibe_vl_rr` here.

`tc_vibe_vl_rr` / `make vl_rr` / `make vl` /
`make tc_vibe_vl_rr` is **module-level only** (reset `rr=0` /
first pick from 0, `valid=|nonempty`, single-bit nonempty incl.
VL15, `grant&&valid` walks the pointer, hold without grant,
grant while `!valid` does not advance, stock nonempty=`FFFF`
16-grant `seen=FFFF`, wrap and sparse masks, async `rst_n`
mid-stream clears `rr`, wrap-vs-DUT instance score on `u_u`,
pin scan with instance `u_u`). It is **not** 1/3, 4/3, freeze,
or signoff. Stock Icarus `tb/vibe/tests/tc_vl_rr.sv` /
`tc_vl_rr_0_15.sv` / `tc_vl_rr` / `tc_vl_rr_0_15` remain the
official TP scorers (direct `vibe_vl_rr` top, instance `u_rr`).
Second fabric leaf after stage-80 `vibe_fecn_mark` wrap.
Instance `u_u` matches Decision-I leaf wrappers; product
instantiator is `vibe_fabric` `u_rr` in `g_egr`; stock Icarus
uses `u_rr`. `ovf_l` (F1) is not in this module. CHILDREN:
none. This is **not** `dll_wrap` / `wrap` / `top` / `port` /
`icrc` / `nw_adapt` / `fecn_mark` / `vibe_fecn_mark` /
`vibe_icrc` / `vibe_nw_adapt` / `vibe_bcrc` / `vibe_dll`.
Do not invent `vibe_route_lu` here.

`tc_vibe_route_lu` / `make route_lu` / `make route` /
`make tc_vibe_route_lu` is **module-level only** (async `rst_n`
/ sync `device_rst` clear `tbl[*]` + `bitmap` + `drop_g1`,
`wr_en` stores `wr_data` at `wr_idx[7:0]`, `lu_vld` + RT=00/01
returns `tbl[dest[7:0]][3:0]`, RT=10/11 pulse `drop_g1` one
cycle and force `bitmap=0`, without `lu_vld` no drop / no
bitmap update, wrap-vs-DUT instance score on `u_u`, pin scan
with instance `u_u`). It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_route_lu.sv` /
`tc_route_lu` remains the official TP scorer (direct
`vibe_route_lu` top, instance `u_rt`). Third fabric leaf after
stage-80 `vibe_fecn_mark` wrap and stage-81 `vibe_vl_rr` wrap.
Instance `u_u` matches Decision-I leaf wrappers; product
instantiator is `vibe_fabric` `u_rt` / `g_rt.u_rti`; stock
Icarus uses `u_rt`. `ovf_l` (F1) is not in this module.
CHILDREN: none. This is **not** `dll_wrap` / `wrap` / `top` /
`port` / `icrc` / `nw_adapt` / `fecn_mark` / `vl_rr` /
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_icrc` / `vibe_nw_adapt` /
`vibe_bcrc` / `vibe_dll`. No Dijkstra / RT rewrite. Count/irq
are fabric-side. Do not invent `vibe_port_sel` here.

`tc_vibe_port_sel` / `make port_sel` / `make psel` /
`make tc_vibe_port_sel` is **module-level only** (async `rst_n`
clears `egr` / `drop` / `drop_down_cnt` / `rr` / `sticky[0:15]`,
normal select when `bitmap & status_up` is nonempty, `drop_g1`
pulses `drop` without bumping `drop_down_cnt`, empty avail +
Default all-0 + port0 up picks port 0 / port0 down drops and
increments `drop_down_cnt` with no flood, RT=00 sticky on
`sticky[vl]`, RT=01 per-packet RR via `rr`, wrap-vs-DUT instance
score on `u_u`, pin scan with instance `u_u`). It is **not** 1/3,
4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_p0_down_drop.sv` / `tc_p0_down_drop` remains
the official TP scorer (direct `vibe_port_sel` top, instance
`u_ps`). Fourth fabric leaf after stage-80 `vibe_fecn_mark` wrap,
stage-81 `vibe_vl_rr` wrap, and stage-82 `vibe_route_lu` wrap.
Instance `u_u` matches Decision-I leaf wrappers; product
instantiator is `vibe_fabric` `u_ps` / `g_rt.u_psi`; stock
Icarus uses `u_ps`. `ovf_l` (F1) is not in this module.
CHILDREN: none. This is **not** `dll_wrap` / `wrap` / `top` /
`port` / `icrc` / `nw_adapt` / `fecn_mark` / `vl_rr` /
`route_lu` / `vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_icrc` / `vibe_nw_adapt` / `vibe_bcrc` / `vibe_dll`. Compact
sticky slot is `vl` (cfg/src/dest are product ports). Do not
invent `vibe_voq_egr` here.

`tc_vibe_voq_egr` / `make voq_egr` / `make voq` /
`make tc_vibe_voq_egr` is **module-level only** (async `rst_n`
clears `deadlock_*` / `wptr` / `rptr`, combo `wr_ready` /
`nonempty` / `occ_vl0` / `rd_*`, wr then rd same VL
data/sop/eop, `wr_ready=0` at `occ==DEPTH`, per-VL
`nonempty`, short `deadlock_drop` after `VIBE_US_CYC=1250`
aging). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_voq_rd.sv` / `tc_deadlock_timeout_1us.sv`
/ `tc_voq_rd` / `tc_deadlock_timeout_1us` remain the official
TP scorers. Fifth fabric leaf after `vibe_fecn_mark` /
`vibe_vl_rr` / `vibe_route_lu` / `vibe_port_sel`. `ovf_l`
(F1) is not in this module.

`tc_vibe_saf_ing` / `make saf_ing` / `make saf` /
`make tc_vibe_saf_ing` is **module-level only** (async `rst_n`
clears pointers / assemble state / `len_err`, combo `in_ready` /
`pkt_*`, SAF hold until declared beats assembled, wr then drain
data/sop/eop + `pkt_bytes`, 1-beat `sop&&eop`, oversize PLEN
pulses `len_err` and rewinds `wptr`). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_saf_ing.sv` /
`tc_saf_ing` remains the official TP scorer. Sixth fabric leaf
after `vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel` / `vibe_voq_egr`. `ovf_l` (F1) is not in this
module.

`tc_vibe_xbar` / `make xbar` / `make tc_vibe_xbar` is
**module-level only** (async `rst_n` clears `lock` / `locked` /
`rr`, combo `in_ready` / `out_*`, 1-beat `sop&&eop` route,
2-beat locked grant, candidate `out_data` independent of
`out_ready`, ingress RR on conflict + `rr<=lock+1` after EOP,
down port `status_up=0` emits no data, parallel distinct dests).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_xbar_unit.sv` / `tc_xbar_unit` remains the
official TP scorer. Seventh fabric leaf after `vibe_fecn_mark` /
`vibe_vl_rr` / `vibe_route_lu` / `vibe_port_sel` /
`vibe_voq_egr` / `vibe_saf_ing`. `ovf_l` (F1) is not in this
module. Mgmt bypass is fabric-level and does not enter this DUT.

`tc_vibe_dll_tx` / `make dll_tx` / `make tx` /
`make tc_vibe_dll_tx` is **module-level only** (async `rst_n`
clears rem / pkt / `fq` / `dll_pcs_*`, combo `nw_dll_ready`
backpressure, CFG0 `consume_cfg0`, 1-flit EOP Null-pad + BCRC
emit, 80-byte rem pack across two 64B beats, AMCTL zero-beat,
replay `{replay_flit, 480'0}`, mid-run async `rst_n` through dest
posedge, pin scan with instance `u_u`). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_dll_tx_cfg0.sv` / `tc_dll_tx_cfg0` remains the
official TP scorer (tx + credit cells). This is **not** TP-DLL-004 /
`dll` / `bcrc` / `credit` / `dll_sm` / `dll_rx` / `retry_ack_sm` /
`retry_buf` / `retry_req_sm` / `icrc` / `vibe_pcs_tx` /
`vibe_pcs_rx` / gear / `vibe_afifo` / `vibe_sync2` /
`vibe_rst_sync`. Eighth DLL leaf after `vibe_bcrc` /
`vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm`. Instantiated by `vibe_dll` `u_tx`.
`ovf_l` (F1) is not in this module. CHILDREN: none.

`tc_vibe_dll` / `make dll_wrap` / `make wrap` /
`make tc_vibe_dll` is **wrap-level only** (seven children present,
wrap-local `proto_err` / `fc_ovf`, async `rst_n` / LinkUp=0 →
Disabled, hardcoded `param_ok`/`credit_ok` walk to Normal, `credit_low`
blocks NW, 1-flit CFG3 TX smoke, CFG0 RX terminate, CFG3 1-flit RX
smoke, `fec_fail` → `start_retry` → `drop_data`, `port_rst` /
`!link_up` force Disabled, wrap-vs-DUT instance score on `u_dll`,
mid-run async `rst_n` through dest posedge then a fresh stimulus
walk with no leftover mid-protocol residue, pin scan with instance
`u_dll`). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_dll.sv` / pyuvm `tc_dll` / `make dll` remain the
official TP-DLL-004 scorers (>32-flit split). First DLL structural
wrap after the eight DLL child leaves (`vibe_bcrc` /
`vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm` / `vibe_dll_tx`). CHILDREN as instantiated:
`u_sm` / `u_crd` / `u_rbuf` / `u_req` / `u_ack` / `u_tx` / `u_rx`.
`ovf_l` (F1) is not in this module; do not ECO F1.

`tc_vibe_icrc` / `make icrc` / `make tc_vibe_icrc` is
**module-level only** (async `rst_n` clears `crc` / `crc_out` /
`done`, idle `last` without `in_vld` does not eat, AS §13 CRC32
encode vs golden — init all-1, per-byte bit reverse then
reverse+invert — `start` reloads and wins over `in_vld`, `in_vld=0`
stall, second block after `done`, wrap-vs-DUT instance score on
`u_u`, mid-run async `rst_n` through dest posedge then a fresh
encode with no leftover residue, pin scan with instance `u_u`).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_icrc_txrx_vs_transit.sv` /
`tc_icrc_txrx_vs_transit` remains the official unit-responds
scorer (direct `vibe_icrc` top, wrap-style). First NW leaf after
stage-77 DLL wrap (PCS/CDC/DLL/fabric leaves stage-1..77).
Instance `u_u` matches Decision-I leaf wrappers; product
instantiator is Unit TB / `cna_ep` `u_icrc`. `ovf_l` (F1) is
not in this module. CHILDREN: none. Transit has no ICRC unit.
This is **not** `dll_wrap` / `wrap` / `top` / `port` /
`vibe_bcrc` / `vibe_dll` / `vibe_nw_adapt`.

`tc_vibe_nw_adapt` / `make nw_adapt` / `make tc_vibe_nw_adapt` is
**module-level only** (combo idle; `clk` / `rst_n` unused in the
combo body; `link_ready` gates both TX readies and `nw_dll_vld`;
mgmt inject priority over VOQ; TX/RX 512b GOLDEN plus SOP LPH
`[511:352]`; ready trees `mgmt_nw_ready` / `fab_nw_ready` /
`dll_nw_ready`; wrap-vs-DUT instance score on `u_u`; `rst_n`
toggle does not change combo outs; pin scan with instance `u_u`).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_nw_adapt_linkready.sv` /
`tc_nw_adapt_linkready` remains the official LinkReady / mgmt-pri
scorer (direct `vibe_nw_adapt` top, instance `u_n`). Last NW leaf
after stage-78 `vibe_icrc` wrap (PCS/CDC/DLL/fabric/NW leaves
stage-1..79; NW tip-align wave complete). Instance `u_u` matches
Decision-I leaf wrappers; product instantiator is `vibe_port`
`u_nw`; stock Icarus uses `u_n`. `ovf_l` (F1) is not in this
module. CHILDREN: none. This is **not** `dll_wrap` / `wrap` /
`top` / `port` / `icrc` / `vibe_icrc` / `vibe_bcrc` / `vibe_dll`.

`tc_vibe_irq_agg` / `make irq_agg` / `make tc_vibe_irq_agg` is
**module-level only** (async `rst_n` clears `sticky` / `irq_logic`,
idle sources stay 0, SPEC §14 / AS §15 must-observe sources —
`rx_ovf` / `fc_ovf` / `proto_err` / `retry_error` / `icrc_fail` /
`len_err` / `deadlock_drop` / `drop_g1` / `afifo_ovf` — including
walk-1 on every 4-bit port vector, sticky hold after deassert,
`irq_clr` wins same-cycle over `any_err`, multi-source OR still
one bit). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_irq_agg.sv` / `tc_irq_agg` remains the official
TP scorer (direct `vibe_irq_agg` top). First mgmt leaf after
PCS/CDC/DLL/fabric/NW leaves (stage-1..36). `ovf_l` (F1) is not
in this module. Port Reset is not a leaf clear. `device_rst` is
OR'd into `irq_clr` by `vibe_mgmt` (held).

`tc_vibe_cna_ep` / `make cna_ep` / `make tc_vibe_cna_ep` is
**module-level only** (idle / no-hit stay 0, stock Icarus
`tc_cna_ep` terminate vs forward — DCNA==written CNA, NLP=1,
miss, CNA unwritten — per-port walk-1, combo drop after hit
deassert, `mgmt_nw_ready` unused, NLP=1 with CNA unwritten
still terms, request echo, `icrc_fail=0`). Opcode `0x10` is
scored only as RTL `flit[103:96]`: without `us` it does **not**
terminate; with `us` the request is echoed (no CFG6 CSR
assemble, no Appendix D offsets). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_cna_ep.sv` /
`tc_cna_ep` remains the official TP scorer
(`vibe_cna_ep_cocotb_top`, wrap-style). Second mgmt leaf after
stage-40 `vibe_irq_agg`. Icarus 12 VPI leaves 512-bit packed
`mgmt_nw_data_*` X — X is not treated as 0; packed `consume` /
`mgmt_nw_vld` / `icrc_fail` still score. Verilator resolves
echo data. `ovf_l` (F1) is not in this module.
CFG6 R/W / Appendix D packing is 未知 — do not invent.

`tc_vibe_cfg_space` / `make cfg_space` / `make tc_vibe_cfg_space` is
**module-level only** (reset/idle seq 0 + `cfg_wr_ready=1`, RTL
identity constants GUID Type 0x3 / Class 0x0300 / PORT_BASIC/CAP,
stock Icarus `tc_identity_cfg_space` / `tc_cna_16bit` static writes
— cmd 0 CNA, 1 route pulse, 2 Default bitmap, 3 Port Reset
`data[0]==0` must-not / `data[0]==1` W1C, 4 `device_rst_pulse`,
5 `lmsm_go`, 7 ignored still `irq_clr`, `device_rst` pin clears
CNA — walk-1 Port Reset / `lmsm_go`, 1-cycle pulses, held CNA /
bitmap / `rt_wr_*`, cmd 6–15 ignore, `hold_fall` HW clear,
same-cycle W1C retrigger, RSVD data bits ignored). No `cfg_rd_*`
(AS §18). CFG6 R/W / Appendix D packing is 未知 — do not invent;
CFG6 elsewhere is echo-only. It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_identity_cfg_space.sv` /
`tc_identity_cfg_space` remains the official TP scorer (direct
`vibe_cfg_space` top, wrap-style). Third mgmt leaf after stage-40
`vibe_irq_agg` and stage-41 `vibe_cna_ep`. `ovf_l` (F1) is not in
this module.

`tc_vibe_port` / `make port_wrap` / `make tc_vibe_port` is
**wrap-level only** (AS-0.1 §4 children present, wrap-local
`fec_mode=T4` / F1 `afifo_ovf` CDC idle, async `rst_n` / LMSM Idle
→ DLL Disabled, TB-only Force `am_locked` walk to LinkUp/LinkReady,
`credit_low` blocks fabric NW, 1-flit CFG3 TX smoke through `u_nw`,
wrap `cfg0_hit` / `fec_fail` follow `u_dll` / `u_prx` (no Force
over PCS), `port_rst` / async `rst_n` force Disabled). It is
**not** 1/3, 4/3, freeze, or signoff. Stock Icarus /
pyuvm `tc_port_smoke` / `tc_nw_pkt_to_pma_tx` /
`tc_nw_pkt_pma_loopback` / `make port` remain the official TP-PHY
scorers (PMA loopback). First port structural wrap after stage-35
`vibe_dll`. Do not rewrite F1 `ovf_l`. `vibe_top` stays HOLD.
No invented Appendix D / CFG opcode. Icarus LMSM Force
bring-up may not reach ACTIVE (same class as stock `tc_port_smoke`);
children / reset / combo / async rst still score.

`tc_vibe_port` / `make vibe_port_wrap` is the Decision-I **stage-50**
wrap leaf (tip `4b2eefe4` / product body still `cd71b1d0`). It is
**wrap-level only** (AS-0.1 §4 CHILDREN from SV — `u_txrst` /
`u_rxrst` / `u_lmsm` / `u_nw` / `u_dll` / `u_ptx` / `u_prx` /
4× `u_at*` + `u_g*` / `u_pma` / 4× `u_ar*` + `u_rg*` — wrap-local
nets on Verilator 5.020 VPI, async `rst_n` / `port_rst`, wrap-local
`fec_mode=T4` / F1 `afifo_ovf` idle, LMSM Idle → DLL Disabled,
`lmsm_go` observe Idle → Disc.A without AM invent). It is
**not** 1/3, 4/3, freeze, or signoff. Stock Icarus / pyuvm
`tc_port_smoke` / `make port` remain the official TP-PHY scorers.
Do **not** steal `make top` / `make wrap` / `make port` /
`make top_wrap` / `make mgmt_wrap` / `make fabric_wrap` /
`make pcs_tx_wrap` / `make pcs_rx_wrap` / `make lmsm_wrap`.
No invented Appendix D / CFG opcode. CFG6 R/W packing is 未知 —
do not invent (this DUT has no CFG pin). Prefer observing wrap /
child-driven nets over Force. Do not rewrite F1 `ovf_l`.

`tc_vibe_ub_switch` / `make top_wrap` / `make tc_vibe_ub_switch` is
**wrap-level only** (AS-0.1 §4/§17 children present — 4× `vibe_port`,
`vibe_fabric`, `vibe_mgmt`, 4× `vibe_mgmt_byp` — async `rst_n` /
LMSM Idle → DLL Disabled on every port, observe `credit_low` /
`!link_ready` blocking fabric NW, light CFG write smoke for RTL-known
cmds 0–5 / 7 ignore). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus / pyuvm `tc_top_smoke` / `make top` remain the official
product-pin PMA+peer scorers. Do **not** steal `make top` / `make wrap`.
Decision-I `vibe_fabric` wrap TC is `tc_vibe_fabric` / `make fabric_wrap`.
No invented
Appendix D / CFG opcode. CFG6 R/W packing is 未知 — do not invent.
Prefer observing child-driven nets over Force. Do not rewrite F1
`ovf_l`. Consecutive-green stays STOPPED.

`tc_vibe_mgmt` / `make mgmt_wrap` / `make tc_vibe_mgmt` is
**wrap-level only** (AS-0.1 §4/§10 children present — `u_cfg` /
`u_rst` / `u_cna` / `u_irq` — async `rst_n`, wrap `port_rst` =
`rst_ctl` hold | cfg RW1C, light CFG write smoke for RTL-known
cmds 0–5 / 7 ignore, rst_ctl Port Reset / device-reset stretch
then HW clear, CFG6 terminate + request echo through `u_cna`,
`irq_agg` sticky from `drop_g1` cleared on any accepted write).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus /
pyuvm `tc_mgmt` remains the official direct-top scorer. Do
**not** steal `make top` / `make wrap` / `make port` /
`make top_wrap`. No invented
Appendix D / CFG opcode. CFG6 R/W packing is 未知 — do not invent.
Do not rewrite F1 `ovf_l` (lives in `vibe_port`). Flattened
`fab_mgmt_cfg6_data_*` / `mgmt_nw_data_*` for cocotb; Icarus 12
VPI may leave 512-bit echo X (packed consume / `mgmt_nw_vld`
still score).

`tc_vibe_fabric` / `make fabric_wrap` / `make tc_vibe_fabric` is
**wrap-level only** (AS-0.1 §8/§9 children present — 4× `vibe_saf_ing`,
`u_rt` / `u_ps`, 3× `g_rt` `u_rti` / `u_psi`, `u_xbar`, 4× `g_egr`
`u_voq` / `u_rr` / `u_fecn` — async `rst_n`, RTL-known `rt_wr_*`,
G1 RT=10 drop, CFG6 terminate vs forward via stock
`vibe_cfg6_should_term`, one CFG3 beat through xbar). It is
**not** 1/3, 4/3, freeze, or signoff. Stock Icarus / pyuvm
`make suite` / `entry_fab` remain the official fabric+mgmt scorers.
Do **not** steal `make top` / `make wrap` / `make port` /
`make top_wrap` / `make mgmt_wrap`. No invented Appendix D /
CFG opcode. CFG6 R/W packing is 未知 — do not invent. Prefer
observing child-driven nets over Force. Do not rewrite F1
`ovf_l` (lives in `vibe_port`). Flattened `nw_fab_data_*` /
`fab_nw_data_*` / `fab_mgmt_cfg6_data_*` for cocotb.

`tc_vibe_pcs_tx` / `make pcs_tx_wrap` / `make tc_vibe_pcs_tx` is
**wrap-level only** (AS-0.1 §5 children present — `u_g1` / `u_fec` /
`u_cw` / `u_pack` / 4× `vibe_pcs_scramble` `u_s0`..`u_s3` — async
`rst_n`, `link_up` ready, RTL-known `fec_mode` bypass pipeline
observe, `afifo_afull` backpressure). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tc_pcs_tx` remains the official
full-stack scorer. Do **not** steal `make top` / `make wrap` /
`make port` / `make top_wrap` / `make mgmt_wrap` /
`make fabric_wrap`. No invented Appendix D / CFG opcode. CFG6 R/W
packing is 未知 — do not invent (this DUT has no CFG pin). Prefer
observing child-driven nets over Force. Do not rewrite F1
`ovf_l` (lives in `vibe_port`). `vibe_lmsm` stays HOLD.

`tc_vibe_pcs_rx` / `make pcs_rx_wrap` / `make tc_vibe_pcs_rx` is
**wrap-level only** (AS-0.1 §6 children present — 4×
`vibe_pcs_rx_amctl_lock` `u_l0`..`u_l3`, 4× `vibe_pcs_scramble`
`u_d0`..`u_d3`, `u_dsk` / `u_un` / `u_fec` — async `rst_n`,
`link_up` seed hold, RTL-known `fec_mode` pin, non-AM lanes
observe no lock, `pcs_dll_ready` to FEC `win_ready`). It is
**not** 1/3, 4/3, freeze, or signoff. Stock Icarus `tc_pcs_rx`
remains the official full-stack scorer. Do **not** steal
`make top` / `make wrap` / `make port` / `make top_wrap` /
`make mgmt_wrap` / `make fabric_wrap` / `make pcs_tx_wrap`.
No invented Appendix D / CFG opcode. CFG6 R/W packing is 未知 —
do not invent (this DUT has no CFG pin). Prefer observing
child-driven nets over Force. Do not rewrite F1 `ovf_l` (lives
in `vibe_port`). `vibe_lmsm` stays HOLD.

`tc_vibe_lmsm` / `make lmsm_wrap` / `make tc_vibe_lmsm` is
**wrap-level only** (AS-0.1 §11 FSM leaf — CHILDREN empty, no
child-instance asserts — DUT `u_lmsm` present or wrap-local nets on
Verilator 5.020 VPI, async `rst_n` / `port_rst`, light Idle →
Disc.A/C → CFG → NULL → ACTIVE observe, `lid_bad` / `retrain_req`
on RTL-known pins). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus / pyuvm `tc_lmsm_walk` / `tc_lmsm_vlock` /
`tc_lmsm_cc` / `tc_lmsm_idle_discovery` remain the official FSM
scorers. Do **not** steal `make top` / `make wrap` / `make port` /
`make top_wrap` / `make mgmt_wrap` / `make fabric_wrap` /
`make pcs_tx_wrap` / `make pcs_rx_wrap`. No invented Appendix D /
CFG opcode. CFG6 R/W packing is 未知 — do not invent (this DUT has
no CFG pin). Prefer observing wrap / FSM nets over Force. Do not
rewrite F1 `ovf_l` (lives in `vibe_port`). Do not invent Probe /
RXEQ_Optimize / Change_Speed / QDLWS.

## Topology

```
UVMTest
 └─ UVMEnv
     ├─ Agent (Sequencer / Driver / Monitor)   # pull-mode
     └─ VibeAsScoreboard                       # G1, length, CFG6, SAF, ICRC
```

Phases / sequences / drivers are `async def` + `await`. Objections in `run_phase`.
ConfigDb outs are fresh empty lists. Types registered with `uvm_component_utils`
/ `uvm_object_utils`.

## Name mapping (old → new)

| Old gate | New |
|----------|-----|
| Icarus `vibe_suite.sv` tasks | `tc_suite_all` or `UVM_TESTNAME=tc_*` on `entry_fab` |
| SV UVM `+UVM_TESTNAME=` | same class name, Python UVM 1.2 |
| Icarus `tb/vibe/tests/tc_*.sv` | same `tc_*` class in `unit_leaf.py` / `unit_more.py` / `unit_pcs.py` / `unit_afifo.py` / `unit_sync2.py` / `unit_rst_sync.py` / `unit_gear_128_160.py` / `unit_gear_160_128.py` / `unit_dll.py` / `unit_pcs_scramble.py` / `unit_ebch16.py` / `unit_pcs_tx_cw2beat.py` / `unit_pcs_tx_amctl.py` / `unit_rs128_120_enc.py` / `unit_rs128_120_dec.py` / `unit_pcs_rx_deskew.py` / `unit_pcs_rx_amctl_lock.py` / `unit_pcs_rx_unpack.py` / `unit_pcs_tx_pack.py` / `unit_pcs_tx_fec.py` / `unit_pcs_rx_fec.py` / `unit_pcs_tx_g1.py` / `unit_bcrc.py` / `unit_dll_credit.py` / `unit_dll_sm.py` / `unit_dll_rx.py` / `unit_dll_retry_ack_sm.py` / `unit_dll_retry_buf.py` / `unit_dll_retry_req_sm.py` / `unit_fecn_mark.py` / `unit_vl_rr.py` / `unit_route_lu.py` / `unit_port_sel.py` / `unit_voq_egr.py` / `unit_saf_ing.py` / `unit_xbar.py` / `unit_dll_tx.py` / `unit_dll_wrap.py` / `unit_icrc.py` / `unit_irq_agg.py` / `unit_cna_ep.py` / `unit_cfg_space.py` / `unit_port_wrap.py` / `unit_ub_switch_wrap.py` / `unit_mgmt_wrap.py` / `unit_fabric_wrap.py` / `unit_pcs_tx_wrap.py` / `unit_pcs_rx_wrap.py` / `unit_lmsm_wrap.py` / `port_tests.py` / `static_tests.py` |
| Icarus `tc_afifo_afull10` | still `tc_afifo_afull10`; Decision-I module TC is `tc_vibe_afifo` |
| Icarus `tc_rst_sync` | still `tc_rst_sync`; Decision-I module TC is `tc_vibe_rst_sync` |
| Icarus `tc_gear_128_160` | still `tc_gear_128_160`; Decision-I module TC is `tc_vibe_gear_128_160` |
| Icarus `tc_gear_160_128` | still `tc_gear_160_128`; Decision-I module TC is `tc_vibe_gear_160_128` |
| Icarus `tc_pcs_scramble` | still `tc_pcs_scramble`; Decision-I module TC is `tc_vibe_pcs_scramble` |
| Icarus `tc_ebch16_lut` | still `tc_ebch16_lut`; Decision-I module TC is `tc_vibe_ebch16` |
| Icarus `tc_pcs_cw2beat` | still `tc_pcs_cw2beat`; Decision-I module TC is `tc_vibe_pcs_tx_cw2beat` |
| Icarus `tc_pcs_amctl` | still `tc_pcs_amctl`; Decision-I module TC is `tc_vibe_pcs_tx_amctl` |
| Icarus `tc_pcs_fec_*` (wrap) | still the FEC wrap scorers; Decision-I module TC is `tc_vibe_pcs_tx_fec` |
| Icarus `tc_rs_dec_syndrome` | still `tc_rs_dec_syndrome`; Decision-I module TC is `tc_vibe_rs128_120_dec` |
| Icarus `tc_pcs_rx_deskew` | still `tc_pcs_rx_deskew`; Decision-I module TC is `tc_vibe_pcs_rx_deskew` |
| Icarus `tc_pcs_rx_amctl` | still `tc_pcs_rx_amctl`; Decision-I module TC is `tc_vibe_pcs_rx_amctl_lock` |
| Icarus `tc_pcs_rx_unpack` | still `tc_pcs_rx_unpack`; Decision-I module TC is `tc_vibe_pcs_rx_unpack` |
| Icarus `tc_pcs_tx_pack` | still `tc_pcs_tx_pack`; Decision-I module TC is `tc_vibe_pcs_tx_pack` |
| Icarus `tc_pcs_rx_fec` | still `tc_pcs_rx_fec`; Decision-I module TC is `tc_vibe_pcs_rx_fec` |
| Icarus `tc_pcs_tx_g1_window` | still `tc_pcs_tx_g1_window`; Decision-I module TC is `tc_vibe_pcs_tx_g1` |
| Icarus `tc_bcrc_crc30` | still `tc_bcrc_crc30`; Decision-I module TC is `tc_vibe_bcrc` |
| Icarus `tc_credit_*` / `tc_cfg0_no_credit` | still those IDs; Decision-I module TC is `tc_vibe_dll_credit` |
| Icarus `tc_dll_sm_states` | still `tc_dll_sm_states`; Decision-I module TC is `tc_vibe_dll_sm` |
| Icarus `tc_cfg0_term_not_fabric` / `tc_dll_rx_errflag` / `tc_fec_fail_gbn` | still those IDs; Decision-I module TC is `tc_vibe_dll_rx` |
| Icarus `tc_retry_ack_replay` | still `tc_retry_ack_replay`; Decision-I module TC is `tc_vibe_dll_retry_ack_sm` |
| Icarus `tc_retry_buf_256` | still `tc_retry_buf_256`; Decision-I module TC is `tc_vibe_dll_retry_buf` |
| Icarus `tc_retry_req_gbn` / `tc_retry_wait_retrain` | still those IDs; Decision-I module TC is `tc_vibe_dll_retry_req_sm` |
| Icarus `tc_fecn_mark` | still `tc_fecn_mark`; Decision-I module TC is `tc_vibe_fecn_mark` |
| Icarus `tc_vl_rr` / `tc_vl_rr_0_15` | still those IDs; Decision-I module TC is `tc_vibe_vl_rr` |
| Icarus `tc_route_lu` | still `tc_route_lu`; Decision-I module TC is `tc_vibe_route_lu` |
| Icarus `tc_p0_down_drop` | still `tc_p0_down_drop`; Decision-I module TC is `tc_vibe_port_sel` |
| Icarus `tc_voq_rd` / `tc_deadlock_timeout_1us` | still those IDs; Decision-I module TC is `tc_vibe_voq_egr` |
| Icarus `tc_saf_ing` | still `tc_saf_ing`; Decision-I module TC is `tc_vibe_saf_ing` |
| Icarus `tc_xbar_unit` | still `tc_xbar_unit`; Decision-I module TC is `tc_vibe_xbar` |
| Icarus `tc_dll_tx_cfg0` | still `tc_dll_tx_cfg0`; Decision-I module TC is `tc_vibe_dll_tx` |
| Icarus `tc_icrc_txrx_vs_transit` | still `tc_icrc_txrx_vs_transit`; Decision-I module TC is `tc_vibe_icrc` |
| Icarus `tc_nw_adapt_linkready` | still `tc_nw_adapt_linkready`; Decision-I module TC is `tc_vibe_nw_adapt` |
| Icarus `tc_irq_agg` | still `tc_irq_agg`; Decision-I module TC is `tc_vibe_irq_agg` |
| Icarus `tc_cna_ep` | still `tc_cna_ep`; Decision-I module TC is `tc_vibe_cna_ep` |
| Icarus `tc_identity_cfg_space` / `tc_cna_16bit` | still those IDs; Decision-I module TC is `tc_vibe_cfg_space` |
| Icarus `tc_port_smoke` / `tc_nw_pkt_*` | still those IDs; Decision-I wrap TC is `tc_vibe_port` |
| Icarus `tc_top_smoke` / `make top` | still `tc_top_smoke`; Decision-I wrap TC is `tc_vibe_ub_switch` |
| Icarus `tc_mgmt` | still `tc_mgmt`; Decision-I wrap TC is `tc_vibe_mgmt` |
| Icarus fabric suite / `make suite` | still `entry_fab`; Decision-I wrap TC is `tc_vibe_fabric` |
| Icarus `tc_pcs_tx` (full stack) | still Icarus-only; Decision-I wrap TC is `tc_vibe_pcs_tx` |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` / `tc_cfg9_no_icrc` | fabric suite (`entry_fab` / `tc_suite_all`) |
| Icarus `tc_pcs_rx` (full stack) | still Icarus-only; Decision-I wrap TC is `tc_vibe_pcs_rx` |
| Icarus `tc_lmsm_walk` / `tc_lmsm_vlock` / `tc_lmsm_cc` / `tc_lmsm_idle_discovery` | still those IDs; Decision-I wrap TC is `tc_vibe_lmsm` |
| Icarus `tc_dll` (full stack) | still `tc_dll` (**TP-DLL-004**); Decision-I wrap TC is `tc_vibe_dll` |
| Icarus `tc_timers_indep` | `tc_timers_indep` (`vibe_timers_indep_cocotb_top`) |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` | fabric suite (`tc_suite_all`) |
| Icarus `tc_id_nports_entity0` / `tc_tp_holes` / `tc_neg_*` | `static_tests.py` (no simulator) |
| `make top` / `tc_top_smoke` | `entry_switch` / `tc_top_smoke` |
| `make neg` / `scan_absent.sh` | `static_tests.run_absent_scan` |
| `make sim-xsim` | deprecated secondary (needs xvlog) |

Identifiers (`tc_rt10_must_drop`, `tc_credit_1024_flit_bp`, …) are unchanged.
**Python correspondence** (HAS / GAP) lives in
[`tb/vibe/results/TP_PYUVM_MATRIX.md`](../results/TP_PYUVM_MATRIX.md).
`TP_TC_MATRIX.md` is the SV/UVM-biased scorer map — stock `tc_*.sv` alone
does not mean a Python TC exists. That matrix is **not** 1/3, 4/3, freeze, or signoff.

## Gate status (this tree)

Icarus (`SIM=icarus`) is the complete no-xvlog gate. Verilator is the
fabric/unit baseline (`--timing`); port/top hierarchical `Force` of LMSM
lock does not take effect under Verilator 5.020 + cocotb 1.9.2 VPI, so
those two stay Icarus.

| Bucket | Icarus | Verilator |
|--------|--------|-----------|
| `suite` (`tc_suite_all`, 28) | PASS | PASS |
| leaf units + static/neg + PCS | PASS (incl. `tc_phy_u26_chain`, `tc_timers_indep`) | `tc_vl_rr` PASS; fabric suite PASS |
| `tc_vibe_afifo` (module-level; ≠ full-chip gate) | PASS | PASS |
| `tc_vibe_sync2` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rst_sync` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_128_160` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_160_128` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_dll` (full `vibe_dll`; **TP-DLL-004**; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_scramble` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_ebch16` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_cw2beat` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_amctl` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rs128_120_enc` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rs128_120_dec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_deskew` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_amctl_lock` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_unpack` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_pack` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_fec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_fec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_g1` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_bcrc` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_credit` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_rx` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_ack_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_buf` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_req_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_fecn_mark` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_vl_rr` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_route_lu` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_port_sel` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_voq_egr` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_saf_ing` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_xbar` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_tx` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_icrc` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_nw_adapt` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_irq_agg` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_cna_ep` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_cfg_space` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_port` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_ub_switch` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_mgmt` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_fabric` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_lmsm` (wrap-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `port` (smoke / TX / 100-pkt loopback) | PASS 100/100 | compile OK; LMSM Force bring-up does not reach ACTIVE |
| `top` (`tc_top_smoke`) | PASS | not scored (same Force path) |
| `neg` | PASS | n/a (no sim) |

#115 (`tc_port_smoke` / `tc_nw_pkt_pma_loopback` / `tc_top_smoke`) is **not**
failing on `main` with PR116. Checkers were **not** relaxed.

Not Python-sim in this PR (still `make sim-icarus`): full-stack `tc_pcs_rx`,
`tc_pcs_tx`. Full-stack `tc_dll` is now uvm-python and scores **TP-DLL-004**.
Leaf PCS units remain the scorers for those TPs.

## #115

PMA idle-PRBS ECO (`a658d141`) made Icarus `tc_port_smoke` /
`tc_nw_pkt_pma_loopback` / `tc_top_smoke` fail. PR116 landed a DUT fix on
`main`. This TB **does not** weaken those checkers. If they fail on a freeze
without that ECO, report them as DUT fails.

## Layout

```
tb/vibe/pyuvm/
  vibe_uvm/          items, vifs, agents, env, scoreboard, tests
                     tests/unit_afifo.py  Decision-I vibe_afifo (module-level)
                     tests/unit_sync2.py  Decision-I vibe_sync2 (module-level)
                     tests/unit_rst_sync.py  Decision-I vibe_rst_sync (module-level)
                     tests/unit_gear_128_160.py  Decision-I vibe_gear_128_160 (module-level)
                     tests/unit_gear_160_128.py  Decision-I vibe_gear_160_128 (module-level)
                     tests/unit_dll.py    full vibe_dll; TP-DLL-004 split
                     tests/unit_pcs_scramble.py  Decision-I vibe_pcs_scramble (module-level)
                     tests/unit_ebch16.py  Decision-I vibe_ebch16 (module-level)
                     tests/unit_pcs_tx_cw2beat.py  Decision-I vibe_pcs_tx_cw2beat (module-level)
                     tests/unit_pcs_tx_amctl.py  Decision-I vibe_pcs_tx_amctl (module-level)
                     tests/unit_rs128_120_enc.py  Decision-I vibe_rs128_120_enc (module-level)
                     tests/unit_rs128_120_dec.py  Decision-I vibe_rs128_120_dec (module-level)
                     tests/unit_pcs_rx_deskew.py  Decision-I vibe_pcs_rx_deskew (module-level)
                     tests/unit_pcs_rx_amctl_lock.py  Decision-I vibe_pcs_rx_amctl_lock (module-level)
                     tests/unit_pcs_rx_unpack.py  Decision-I vibe_pcs_rx_unpack (module-level)
                     tests/unit_pcs_tx_pack.py  Decision-I vibe_pcs_tx_pack (module-level)
                     tests/unit_pcs_tx_fec.py  Decision-I vibe_pcs_tx_fec (module-level)
                     tests/unit_pcs_rx_fec.py  Decision-I vibe_pcs_rx_fec (module-level)
                     tests/unit_pcs_tx_g1.py  Decision-I vibe_pcs_tx_g1 (module-level)
                     tests/unit_bcrc.py  Decision-I vibe_bcrc (module-level)
                     tests/unit_dll_credit.py  Decision-I vibe_dll_credit (module-level)
                     tests/unit_dll_sm.py  Decision-I vibe_dll_sm (module-level)
                     tests/unit_dll_rx.py  Decision-I vibe_dll_rx (module-level)
                     tests/unit_dll_retry_ack_sm.py  Decision-I vibe_dll_retry_ack_sm (module-level)
                     tests/unit_dll_retry_buf.py  Decision-I vibe_dll_retry_buf (module-level)
                     tests/unit_dll_retry_req_sm.py  Decision-I vibe_dll_retry_req_sm (module-level)
                     tests/unit_fecn_mark.py  Decision-I vibe_fecn_mark (module-level)
                     tests/unit_vl_rr.py  Decision-I vibe_vl_rr (module-level)
                     tests/unit_route_lu.py  Decision-I vibe_route_lu (module-level)
                     tests/unit_port_sel.py  Decision-I vibe_port_sel (module-level)
                     tests/unit_voq_egr.py  Decision-I vibe_voq_egr (module-level)
                     tests/unit_saf_ing.py  Decision-I vibe_saf_ing (module-level)
                     tests/unit_xbar.py  Decision-I vibe_xbar (module-level)
                     tests/unit_dll_tx.py  Decision-I vibe_dll_tx (module-level)
                     tests/unit_dll_wrap.py  Decision-I vibe_dll wrap (not TP-DLL-004)
                     tests/unit_icrc.py  Decision-I vibe_icrc (module-level)
                     tests/unit_irq_agg.py  Decision-I vibe_irq_agg (module-level)
                     tests/unit_cna_ep.py  Decision-I vibe_cna_ep (module-level)
                     tests/unit_cfg_space.py  Decision-I vibe_cfg_space (module-level)
                     tests/unit_port_wrap.py  Decision-I stage-50 vibe_port wrap (not tc_port_smoke)
                     tests/unit_ub_switch_wrap.py  Decision-I vibe_ub_switch wrap (not tc_top_smoke)
                     tests/unit_mgmt_wrap.py  Decision-I vibe_mgmt wrap (not tc_mgmt)
                     tests/unit_fabric_wrap.py  Decision-I vibe_fabric wrap (not suite)
                     tests/unit_pcs_tx_wrap.py  Decision-I vibe_pcs_tx wrap (not tc_pcs_tx)
                     tests/unit_pcs_rx_wrap.py  Decision-I vibe_pcs_rx wrap (not tc_pcs_rx)
                     tests/unit_lmsm_wrap.py  Decision-I vibe_lmsm wrap (not tc_lmsm_walk)
  tb/                cocotb Verilog wrappers (no SV UVM)
  entry_*.py         @cocotb.test() → await run_test(...)
  catalog.py         RTL lists + TC map
  run_gate.py        suite / units / top / neg
  requirements.txt
```
