# Overlay-B 100-pkt PMA loopback waves for Vivado xsim GUI.
# Snapshot: vibe_port_tb  Test: tc_nw_pkt_pma_loopback

log_wave /vibe_port_tb_top/clk_fab
log_wave /vibe_port_tb_top/txclk
log_wave /vibe_port_tb_top/rxclk
log_wave -recursive /vibe_port_tb_top/u_p
log_wave -recursive /vibe_port_tb_top/pif

catch {add_wave_divider {clocks / reset / link}}
catch {add_wave /vibe_port_tb_top/clk_fab}
catch {add_wave /vibe_port_tb_top/txclk}
catch {add_wave /vibe_port_tb_top/rxclk}
catch {add_wave /vibe_port_tb_top/u_p/rst_n}
catch {add_wave /vibe_port_tb_top/u_p/link_ready}
catch {add_wave /vibe_port_tb_top/u_p/status_up}
catch {add_wave /vibe_port_tb_top/u_p/am_locked}

catch {add_wave_divider {TX Fabric->NW 512b}}
catch {add_wave /vibe_port_tb_top/pif/fab_nw_vld}
catch {add_wave /vibe_port_tb_top/pif/fab_nw_ready}
catch {add_wave /vibe_port_tb_top/pif/fab_nw_data}

catch {add_wave_divider {NW<->DLL 512b}}
catch {add_wave /vibe_port_tb_top/u_p/nw_dll_vld}
catch {add_wave /vibe_port_tb_top/u_p/nw_dll_ready}
catch {add_wave /vibe_port_tb_top/u_p/nw_dll_data}
catch {add_wave /vibe_port_tb_top/u_p/dll_nw_vld}
catch {add_wave /vibe_port_tb_top/u_p/dll_nw_ready}
catch {add_wave /vibe_port_tb_top/u_p/dll_nw_data}

catch {add_wave_divider {DLL<->PCS 640b}}
catch {add_wave /vibe_port_tb_top/u_p/dll_pcs_vld}
catch {add_wave /vibe_port_tb_top/u_p/dll_pcs_ready}
catch {add_wave /vibe_port_tb_top/u_p/dll_pcs_data}
catch {add_wave /vibe_port_tb_top/u_p/pcs_dll_vld}
catch {add_wave /vibe_port_tb_top/u_p/pcs_dll_ready}
catch {add_wave /vibe_port_tb_top/u_p/pcs_dll_data}

catch {add_wave_divider {PMA loopback 512b}}
catch {add_wave /vibe_port_tb_top/u_p/pcs_pma_txdata}
catch {add_wave /vibe_port_tb_top/u_p/pma_pcs_rxdata}
catch {add_wave /vibe_port_tb_top/u_p/afifo_pma_lane_vld}
catch {add_wave /vibe_port_tb_top/u_p/afifo_pma_lane0}
catch {add_wave /vibe_port_tb_top/u_p/afifo_pma_lane1}
catch {add_wave /vibe_port_tb_top/u_p/afifo_pma_lane2}
catch {add_wave /vibe_port_tb_top/u_p/afifo_pma_lane3}

catch {add_wave_divider {RX NW Fabric 512b}}
catch {add_wave /vibe_port_tb_top/u_p/nw_fab_vld}
catch {add_wave /vibe_port_tb_top/u_p/nw_fab_ready}
catch {add_wave /vibe_port_tb_top/u_p/nw_fab_data}

run all
catch {save_wave_config waves/nw_pkt_pma_loopback.wcfg}
exit
