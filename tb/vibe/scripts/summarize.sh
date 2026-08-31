#!/usr/bin/env bash
set -euo pipefail
RES="${1:?results dir}"
echo "======== Vibe TB summary ========"
p=0
f=0
for g in "$RES"/*.log; do
  [ -f "$g" ] || continue
  case "$(basename "$g")" in
    cov.log|cov_*.log) continue ;;
  esac
  echo "----- $(basename "$g") -----"
  grep -E '^(PASS|FAIL|NOTE|HOLE|SUITE|WARN)' "$g" || true
  p=$((p + $(grep -c '^PASS ' "$g" 2>/dev/null || true)))
  f=$((f + $(grep -c '^FAIL ' "$g" 2>/dev/null || true)))
done
echo "================================="
echo "TOTAL_PASS_LINES=$p TOTAL_FAIL_LINES=$f (excl. cov.log)"
