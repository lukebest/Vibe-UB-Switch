#!/usr/bin/env bash
# Verilator line/toggle coverage on vibe_* exercised by vibe_suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TB="$ROOT/tb/vibe"
RTL="$ROOT/rtl"
RES="$TB/results"
mkdir -p "$RES"

FAB_RTL=(
  "$RTL/fabric/vibe_saf_ing.sv"
  "$RTL/fabric/vibe_route_lu.sv"
  "$RTL/fabric/vibe_port_sel.sv"
  "$RTL/fabric/vibe_xbar.sv"
  "$RTL/fabric/vibe_voq_egr.sv"
  "$RTL/fabric/vibe_vl_rr.sv"
  "$RTL/fabric/vibe_fecn_mark.sv"
  "$RTL/fabric/vibe_fabric.sv"
  "$RTL/mgmt/vibe_cfg_space.sv"
  "$RTL/mgmt/vibe_cna_ep.sv"
  "$RTL/mgmt/vibe_irq_agg.sv"
  "$RTL/mgmt/vibe_rst_ctl.sv"
  "$RTL/mgmt/vibe_mgmt.sv"
)

if ! command -v verilator >/dev/null; then
  echo "NOTE cov: verilator not installed; Icarus has no coverage engine"
  exit 0
fi

cd "$TB"
rm -rf obj_dir
echo "COV: port_sel-only (full suite hits BLKLOOPINIT / long VOQ compile)"
set +e
verilator --binary --timing --coverage --coverage-line --coverage-toggle \
  --top-module tc_psel_cov \
  -I"$RTL/common" -Wno-fatal \
  cov/tc_psel_cov.sv "$RTL/fabric/vibe_port_sel.sv" \
  -o psel_cov
vc=$?
set -e
if [ "$vc" -ne 0 ]; then
  echo "NOTE cov: verilator port_sel compile exit $vc"
  exit 0
fi
./obj_dir/psel_cov || true
if [ -f coverage.dat ]; then
  verilator_coverage coverage.dat | tee "$RES/cov_report.txt"
else
  echo "NOTE cov: Verilator 5 --binary ran but wrote no coverage.dat (no invented %)"
fi
echo "COV_TOOL=verilator $(verilator --version | head -1)"
echo "COV: full vibe_* line/toggle/fsm = not collected"
