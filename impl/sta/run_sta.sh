#!/usr/bin/env bash
# OpenSTA wrapper. Requires a mapped netlist + liberty. No fake WNS/TNS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOP="${TOP:-vibe_ub_switch}"
NETLIST="${NETLIST:-$ROOT/impl/work/${TOP}.synth.v}"
SDC="${SDC:-$ROOT/impl/constraints/vibe_ub_switch.bringup.sdc}"
RPT_DIR="${RPT_DIR:-$ROOT/reports/signoff}"
STA="${STA:-}"
LIBERTY="${LIBERTY:-}"

find_sta() {
  if [ -n "${STA:-}" ] && command -v "$STA" >/dev/null 2>&1; then
    echo "$STA"
    return
  fi
  for c in sta opensta; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return
    fi
  done
  if [ -n "${ORFS:-}" ] && [ -x "$ORFS/tools/install/bin/sta" ]; then
    echo "$ORFS/tools/install/bin/sta"
    return
  fi
  return 1
}

if ! STA_BIN="$(find_sta)"; then
  cat >&2 <<'EOF'
OpenSTA not found.

Install via ORFS (recommended) or a standalone OpenSTA build:

  # ORFS prebuilts
  # https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithPrebuilt.html

  # ORFS Docker
  # https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithDocker.html

  git clone https://github.com/The-OpenROAD-Project/OpenSTA.git

Set STA=/path/to/sta and LIBERTY=/path/to/sky130_fd_sc_hd__tt_025C_1v80.lib
Do not commit liberty files to this repo.
EOF
  exit 2
fi

if [ -z "$LIBERTY" ]; then
  cat >&2 <<'EOF'
LIBERTY is unset. OpenSTA needs a Sky130 liberty file from ORFS or open_pdks.

Examples (do not copy these binaries into git):

  export LIBERTY=$ORFS/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
  export LIBERTY=$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

See docs/impl/README.md.
EOF
  exit 2
fi

if [ ! -f "$NETLIST" ]; then
  echo "Netlist not found: $NETLIST" >&2
  echo "Run: make -C impl synth-smoke   or   make -C impl synth" >&2
  exit 2
fi

mkdir -p "$RPT_DIR"

export TOP LIBERTY NETLIST SDC RPT_DIR
set +e
"$STA_BIN" -exit "$ROOT/impl/sta/sta.tcl" > "$RPT_DIR/sta.log" 2>&1
rc=$?
set -e

if [ ! -f "$RPT_DIR/drc.rpt" ]; then
  cat > "$RPT_DIR/drc.rpt" <<EOF
STATUS: not_run
NOTE: DRC is produced after detailed route / KLayout, not by this STA target.
      Do not invent a violation count. This flow does not default to P&R.
EOF
fi
if [ ! -f "$RPT_DIR/lvs.rpt" ]; then
  cat > "$RPT_DIR/lvs.rpt" <<EOF
STATUS: not_run
NOTE: LVS is produced after a GDS exists. Any future GDS under impl/work/
      is a local flow artifact and is NOT for foundry submit / tapeout.
EOF
fi

if [ -f "$RPT_DIR/sta.log" ]; then
  {
    echo ""
    echo "==== extracted from sta.log ===="
    grep -E -i 'wns|tns|worst|slack|error|warning' "$RPT_DIR/sta.log" || \
      echo "(no WNS/TNS keywords in log)"
  } >> "$RPT_DIR/sta_wns_tns.rpt"
fi

if [ "$rc" -ne 0 ]; then
  echo "OpenSTA failed (rc=$rc). See $RPT_DIR/sta.log" >&2
  exit "$rc"
fi

echo "sta ok  top=$TOP  reports=$RPT_DIR"
