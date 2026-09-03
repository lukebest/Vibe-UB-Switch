# vibe_ub_switch.spec.sdc
#
# SPEC timing constraints from FS/AS clock names and periods.
# Source of pin names: rtl/top/vibe_ub_switch.sv (not assumed).
#
#   clk_fab          1.25 GHz  (800.0 ps)
#   txclk_[0-3]      922 MHz   (~1084.6 ps)  per-port independent
#   rxclk_[0-3]      922 MHz   (~1084.6 ps)  per-port independent
#
# This file is the spec constraint set. It is NOT a Sky130 signoff SDC.
# Sky130 (sky130hd) cannot close 1.25 GHz; do not treat WNS/TNS collected
# against this file on Sky130 as a production-node result.
#
# Hop latency is explicitly unconstrained (FS/AS). No set_max_delay
# between ports / hops.
#
# Area / power / utilization budgets: unspecified. Do not invent numbers
# in this file.
#
# CDC: the design has real async crossings (see notes below). This SDC
# uses set_clock_groups -asynchronous. That models independent domains.
# It is NOT a blanket set_false_path of the chip.

current_design vibe_ub_switch

# ---------------------------------------------------------------------------
# Periods (nanoseconds; OpenSTA / ORFS convention)
# 1/1.25e9 = 800 ps; 1/922e6 ≈ 1084.5987 ps
# ---------------------------------------------------------------------------
set CLK_FAB_PERIOD 0.800
set PMA_CLK_PERIOD 1.0846

# Conservative I/O delay placeholders (fraction of the related period).
# Not a board/package spec — replace when a real I/O budget exists.
set IO_PCT 0.20

set FAB_IO_DELAY [expr {$CLK_FAB_PERIOD * $IO_PCT}]
set PMA_IO_DELAY [expr {$PMA_CLK_PERIOD * $IO_PCT}]

# ---------------------------------------------------------------------------
# Clocks — names match top ports in rtl/top/vibe_ub_switch.sv
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
# Async clock groups (CDC)
#
# AS-0.1 §3 / §7:
#   - clk_fab is the fabric / DLL / PCS-digital / LMSM / mgmt clock
#   - each port's txclk / rxclk is an independent 922 MHz PMA clock
#   - do not assume txclk_* or rxclk_* are common across ports
#
# Intended crossings (do not "false-path the world"):
#   - per-lane gray-pointer AFIFO (vibe_afifo + vibe_sync2) between
#     clk_fab and txclk_* (TX) / rxclk_* (RX)
#   - async-assert / sync-deassert reset (vibe_rst_sync) into txclk/rxclk
#
# set_clock_groups -asynchronous stops inter-domain setup/hold. It does
# not verify gray-code, sync depth, or reset ordering — that is owned by
# rtl/cdc + tb/vibe, not by a chip-wide false path.
#
# Do NOT add:
#   set_false_path -from [all_clocks] -to [all_clocks]
#   set_false_path -from [all_inputs] -to [all_outputs]
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

# Logical reset: async assert (top rst_n). Not a timed data pin.
set_false_path -from [get_ports rst_n]

# ---------------------------------------------------------------------------
# I/O delays — conservative placeholders, related to the real clock
#
#   cfg_wr_* / irq_logic  : mgmt on clk_fab
#   rxdata_*              : PMA RX, sampled on the matching rxclk_*
#   txdata_*              : PMA TX, launched on the matching txclk_*
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

# Driving cell / external load: unspecified. Do not invent.
# set_driving_cell
# set_load
