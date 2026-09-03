# vibe_sync2.bringup.sdc
#
# FLOW BRING-UP SDC for the synth-smoke leaf (rtl/cdc/vibe_sync2.sv).
# Not a signoff constraint. Period is 100 MHz so the leaf can be mapped
# and STA'd without a full-chip netlist.

current_design vibe_sync2

set CLK_PERIOD 10.000
set IO_PCT     0.20
set IO_DELAY   [expr {$CLK_PERIOD * $IO_PCT}]

create_clock -name clk -period $CLK_PERIOD [get_ports clk]

set_false_path -from [get_ports rst_n]

set_input_delay  $IO_DELAY -clock clk [get_ports d]
set_output_delay $IO_DELAY -clock clk [get_ports q]
