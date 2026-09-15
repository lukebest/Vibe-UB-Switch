#!/usr/bin/env bash
# Open a saved xsim WDB in the Vivado Simulator GUI (static view).
#
# Do not use `xsim <snapshot> -wdb <file>`: that starts a live sim at t=0.
# Do not use `xsim -gui`: it injects `current_fileset` (no FPGA parts here).
# Use `xsim <file.wdb>` so xsim opens the captured run, then start_gui.
set -euo pipefail
TB="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TB"
WDB="${WDB:-waves/nw_pkt_pma_loopback.wdb}"
WCFG="${WCFG:-waves/nw_pkt_pma_loopback.wcfg}"
TCL="$TB/uvm/scripts/open_loopback_wdb.tcl"

if [ ! -f "$WDB" ]; then
  echo "missing WDB: $TB/$WDB" >&2
  echo "dump it with: $TB/uvm/scripts/dump_loopback_waves.sh" >&2
  exit 1
fi
# A live `xsim <snapshot> -wdb` session overwrites this file (~1.4MB, all X).
# A real 100-pkt capture with log_wave is ~12MB.
sz=$(stat -c%s "$WDB")
if [ "$sz" -lt 5000000 ]; then
  echo "WDB is only $sz bytes (empty/overwritten, waves will be X)." >&2
  echo "Re-dump: $TB/uvm/scripts/dump_loopback_waves.sh" >&2
  exit 1
fi

export VIBE_XSIM_WCFG="$WCFG"
exec xsim "$WDB" --tclbatch "$TCL"
