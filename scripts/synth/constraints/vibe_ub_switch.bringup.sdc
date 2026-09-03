# vibe_ub_switch.bringup.sdc
#
# FLOW BRING-UP constraints — NOT a signoff SDC and NOT the FS/AS spec.
#
# Sky130 (ORFS platform sky130hd) cannot close the spec 1.25 GHz fabric
# clock. This file slows the clocks so Yosys / OpenROAD / OpenSTA can be
# exercised as a methodology bring-up. Timing numbers collected against
# this file are flow-debug only.
#
# Bring-up periods (nanoseconds):
#   clk_fab          100 MHz   (10.000 ns)
#   txclk_[0-3]      100 MHz   (10.000 ns)  still modeled independent
#   rxclk_[0-3]      100 MHz   (10.000 ns)  still modeled independent
#
# Spec periods (for reference only; see vibe_ub_switch.spec.sdc):
#   clk_fab = 0.800 ns (1.25 GHz); PMA txclk/rxclk = 1.0846 ns (922 MHz).
#
# RTL timer constants (e.g. VIBE_US_CYC = 1250) still count clk_fab
# cycles. At 100 MHz a "1 µs" FS timeout is 12.5 µs wall-clock. This
# flow must not ECO those RTL constants.
#
# Hop latency remains unconstrained. Area/power/utilization budgets
# remain unspecified — do not invent them here.
#
# CDC policy matches the spec SDC: async clock groups, not a chip-wide
# false path. See vibe_ub_switch.spec.sdc for the CDC note.

current_design vibe_ub_switch

# ---------------------------------------------------------------------------
# FLOW BRING-UP periods (nanoseconds)
# ---------------------------------------------------------------------------
set CLK_FAB_PERIOD 10.000
set PMA_CLK_PERIOD 10.000

set IO_PCT 0.20
set FAB_IO_DELAY [expr {$CLK_FAB_PERIOD * $IO_PCT}]
set PMA_IO_DELAY [expr {$PMA_CLK_PERIOD * $IO_PCT}]

# ---------------------------------------------------------------------------
# Clocks — same port names as rtl/top/vibe_ub_switch.sv
# ---------------------------------------------------------------------------
create_clock -name clk_fab  -period $CLK_FAB_PERIOD [get_ports clk_fab]

create_clock -name txclk_0  -period $PMA_CLK_PERIOD [get_ports txclk_0]
create_clock -name txclk_1  -period $PMA_CLK_PERIOD [get_ports txclk_1]
create_clock -name txclk_2  -period $PMA_CLK_PERIOD [get_ports txclk_2]
create_clock -name txclk_3  -period $PMA_CLK_PERIOD [get_ports txclk_3]

create_clock -name rxclk_0  -period $PMA_CLK_PERIOD [get_ports rxclk_0]
create_clock -name rxclk_1  -period $PMA_CLK_PERIOD [get_ports rxclk_1]
create_clock -name rxclk_2  -period $PMA_CLK_PERIOD [get_ports rxclk_2]
create_clock -name rxclk_3  -period $PMA_CLK_PERIOD [get_ports rxclk_3]

# Clock uncertainty / latency / derate: unspecified. Do not invent.
# set_clock_uncertainty
# set_clock_latency
# set_timing_derate

# ---------------------------------------------------------------------------
# Async clock groups (CDC) — same grouping as the spec SDC.
# Independent PMA clocks + fabric. Crossings are gray AFIFO + rst_sync.
# Do NOT false-path all clocks / all I/O.
# ---------------------------------------------------------------------------
set_clock_groups -asynchronous \
  -group {clk_fab} \
  -group {txclk_0} \
  -group {txclk_1} \
  -group {txclk_2} \
  -group {txclk_3} \
  -group {rxclk_0} \
  -group {rxclk_1} \
  -group {rxclk_2} \
  -group {rxclk_3}

set_false_path -from [get_ports rst_n]

# ---------------------------------------------------------------------------
# I/O delay placeholders (20% of the bring-up period)
# ---------------------------------------------------------------------------
set_input_delay  $FAB_IO_DELAY -clock clk_fab [get_ports cfg_wr_vld]
set_input_delay  $FAB_IO_DELAY -clock clk_fab [get_ports cfg_wr_cmd]
set_input_delay  $FAB_IO_DELAY -clock clk_fab [get_ports cfg_wr_idx]
set_input_delay  $FAB_IO_DELAY -clock clk_fab [get_ports cfg_wr_data]
set_output_delay $FAB_IO_DELAY -clock clk_fab [get_ports cfg_wr_ready]
set_output_delay $FAB_IO_DELAY -clock clk_fab [get_ports irq_logic]

set_input_delay  $PMA_IO_DELAY -clock rxclk_0 [get_ports rxdata_0]
set_input_delay  $PMA_IO_DELAY -clock rxclk_1 [get_ports rxdata_1]
set_input_delay  $PMA_IO_DELAY -clock rxclk_2 [get_ports rxdata_2]
set_input_delay  $PMA_IO_DELAY -clock rxclk_3 [get_ports rxdata_3]

set_output_delay $PMA_IO_DELAY -clock txclk_0 [get_ports txdata_0]
set_output_delay $PMA_IO_DELAY -clock txclk_1 [get_ports txdata_1]
set_output_delay $PMA_IO_DELAY -clock txclk_2 [get_ports txdata_2]
set_output_delay $PMA_IO_DELAY -clock txclk_3 [get_ports txdata_3]
