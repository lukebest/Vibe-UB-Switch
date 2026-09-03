#!/bin/sh
# Verilator --lint-only for vibe_ub_switch (AS-0.1.2 static-write change).
# 0 errors required. Warnings stay in the log; see WAIVERS.md.
set -e
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="$ROOT/reports/lint/vibe_ub_switch.lint.log"
{
  echo "tool: $(verilator --version 2>&1 | head -n 1)"
  echo "top: vibe_ub_switch"
  echo "flags: --lint-only -Wall -Wno-fatal"
  echo "waiver: reports/lint/vibe_ub_switch.vlt (UNSUPPORTED input defaults, BLKLOOPINIT route_lu)"
  echo "----"
  verilator --lint-only -Wall -Wno-fatal --top-module vibe_ub_switch \
    -I"$ROOT/rtl/common" \
    "$ROOT/reports/lint/vibe_ub_switch.vlt" \
    "$ROOT"/rtl/cdc/*.sv \
    "$ROOT"/rtl/pma/*.sv \
    "$ROOT"/rtl/pcs/*.sv \
    "$ROOT"/rtl/lmsm/*.sv \
    "$ROOT"/rtl/dll/*.sv \
    "$ROOT"/rtl/nw/*.sv \
    "$ROOT"/rtl/fabric/*.sv \
    "$ROOT"/rtl/mgmt/*.sv \
    "$ROOT"/rtl/port/*.sv \
    "$ROOT"/rtl/top/vibe_ub_switch.sv
} > "$OUT" 2>&1
ERR=$(grep -cE '%Error-[A-Z]' "$OUT" || true)
WARN=$(grep -c '%Warning' "$OUT" || true)
echo "wrote $OUT  Error- codes=$ERR  Warning lines=$WARN"
test "$ERR" = "0"
