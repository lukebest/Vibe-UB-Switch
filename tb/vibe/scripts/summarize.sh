#!/usr/bin/env bash
set -euo pipefail
RES="${1:?results dir}"
echo "======== Vibe TB summary ========"
for f in "$RES"/*.log; do
  [ -f "$f" ] || continue
  echo "----- $(basename "$f") -----"
  grep -E '^(PASS|FAIL|NOTE|HOLE|SUITE|WARN)' "$f" || true
done
echo "================================="
p=$(grep -h '^PASS ' "$RES"/*.log 2>/dev/null | wc -l | tr -d ' ')
f=$(grep -h '^FAIL ' "$RES"/*.log 2>/dev/null | wc -l | tr -d ' ')
echo "TOTAL_PASS_LINES=$p TOTAL_FAIL_LINES=$f"
