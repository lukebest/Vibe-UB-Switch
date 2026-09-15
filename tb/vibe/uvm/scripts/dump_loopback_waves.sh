#!/usr/bin/env bash
# Capture tc_nw_pkt_pma_loopback into a static WDB (log_wave then run all).
# Do not open this file with `xsim <snapshot> -wdb <this>` — that overwrites
# the capture with a live t=0 session (all X).
set -euo pipefail
TB="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TB"
mkdir -p waves
SNAP="${SNAP:-vibe_port_tb}"
WDB="${WDB:-waves/nw_pkt_pma_loopback.wdb}"
TCL="$TB/uvm/scripts/run_loopback_waves.tcl"

if [ ! -d "$TB/xsim.dir/$SNAP" ]; then
  echo "missing snapshot $SNAP; compiling port TB..." >&2
  TC=tc_nw_pkt_pma_loopback "$TB/uvm/scripts/run_xsim.sh" port
fi

echo "dump $SNAP -> $WDB (UVM_TESTNAME=tc_nw_pkt_pma_loopback)"
xsim "$SNAP" --tclbatch "$TCL" \
  -testplusarg UVM_TESTNAME=tc_nw_pkt_pma_loopback \
  -testplusarg UVM_VERBOSITY=UVM_LOW \
  -testplusarg UVM_NO_RELNOTES \
  -wdb "$WDB"

ls -lh "$WDB" waves/nw_pkt_pma_loopback.wcfg
sz=$(stat -c%s "$WDB")
if [ "$sz" -lt 5000000 ]; then
  echo "WDB only $sz bytes — log_wave likely missing; not a usable capture" >&2
  exit 1
fi
