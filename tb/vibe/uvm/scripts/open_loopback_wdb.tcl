# Static WDB view. Do not pass a live snapshot + `-wdb` (that is t=0, no
# history). Do not pass `xsim -gui` (injects current_fileset / Project 1-848).
# `xsim <file.wdb>` opens the saved run; start_gui then shows the Wave window.
set _vibe_init [file join [file dirname [info script]] xsim_gui_init.tcl]
if {[file exists $_vibe_init]} {
  source $_vibe_init
}
set wcfg waves/nw_pkt_pma_loopback.wcfg
if {[info exists ::env(VIBE_XSIM_WCFG)] && $::env(VIBE_XSIM_WCFG) ne ""} {
  set wcfg $::env(VIBE_XSIM_WCFG)
}
puts "vibe_xsim_gui: start_gui (static WDB)"
start_gui
puts "vibe_xsim_gui: GUI up"
if {[file exists $wcfg]} {
  if {[catch {open_wave_config $wcfg} err]} {
    puts "vibe_xsim_gui: open_wave_config failed: $err"
  } else {
    puts "vibe_xsim_gui: opened $wcfg ($err)"
  }
} else {
  puts "vibe_xsim_gui: missing wcfg $wcfg"
}
if {[catch {current_wave_config} cw] || [string length $cw] == 0} {
  puts "vibe_xsim_gui: no wave config; create + add_wave"
  catch {create_wave_config vibe_loopback}
  catch {add_wave /vibe_port_tb_top/clk_fab}
  catch {add_wave /vibe_port_tb_top/txclk}
  catch {add_wave /vibe_port_tb_top/rxclk}
  catch {add_wave /vibe_port_tb_top/u_p/rst_n}
  catch {add_wave /vibe_port_tb_top/u_p/link_ready}
  catch {add_wave /vibe_port_tb_top/u_p/status_up}
  catch {add_wave /vibe_port_tb_top/pif/fab_nw_vld}
  catch {add_wave /vibe_port_tb_top/u_p/nw_dll_vld}
  catch {add_wave /vibe_port_tb_top/u_p/dll_pcs_vld}
  catch {add_wave /vibe_port_tb_top/u_p/pcs_pma_txdata}
  catch {add_wave /vibe_port_tb_top/u_p/pma_pcs_rxdata}
  catch {add_wave /vibe_port_tb_top/u_p/nw_fab_vld}
}
