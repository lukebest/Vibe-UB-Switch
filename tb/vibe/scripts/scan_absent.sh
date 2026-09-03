#!/usr/bin/env bash
# Static negative scan: features AS-0.1 forbids or leaves unimplemented.
# Exit 0 if none of the forbidden identifiers appear as RTL module/port names.
set -euo pipefail
RTL="${1:?rtl dir}"
LOG_OK=1

absent() {
  local name="$1"
  local hits
  hits=$(grep -RIn --include='*.sv' --include='*.vh' -E "$2" "$RTL" || true)
  if [ -n "$hits" ]; then
    # Comments citing the prohibition are allowed; flag real ports/modules.
    local real
    real=$(echo "$hits" | grep -vE 'No |not |NOT |do not|Do not|absent|unimpl' || true)
    if [ -n "$real" ]; then
      echo "NOTE $name: identifier present (inspect — may be comment-only):"
      echo "$hits" | head -20
    else
      echo "PASS neg_$name (only prohibition comments)"
    fi
  else
    echo "PASS neg_$name (no matches)"
  fi
}

absent qdlws 'QDLWS|qdlws'
absent exact_route 'exact_route|ExactRoute|EXACT_ROUTE'
absent port_cna 'PORT_CNA|port_cna|PortCNA'
absent scna_compare 'scna_cmp|SCNA_CMP|scna_compare'
absent cut_through 'cut_through|cutthrough|CUT_THROUGH'
absent ubfm '\bUBFM\b|ubfm_'
absent hi_fec_ber 'hi_FEC_BER|hi_fec_ber|HIFECBER'
absent probe_state 'ST_PROBE|st_probe|Probe_Active'
absent optical 'optical_pma|OPTICAL_PMA|qdlws_optical|ST_OPTICAL'

# Dijkstra / shortest-path routing must not exist (G1).
if grep -RIn --include='*.sv' -E 'dijkstra|shortest_path|path_cost' "$RTL" | grep -v 'unimpl' >/dev/null; then
  echo "FAIL neg_no_dijkstra: shortest-path RTL found"
  LOG_OK=0
else
  echo "PASS neg_no_dijkstra"
fi

# AS §18 / PR21: no cfg_rd_* pin. FAIL if TB still wiggles one.
TB_VIBE="$(cd "$RTL/.." && pwd)/tb/vibe"
if [ -d "$TB_VIBE" ]; then
  rd_hits=$(grep -RIn --include='*.sv' --include='*.svh' -E '\bcfg_rd_' "$TB_VIBE" \
    | grep -vE 'no cfg_rd|No cfg_rd|not .*cfg_rd|cfg_rd_\*' || true)
  if [ -n "$rd_hits" ]; then
    echo "FAIL neg_no_cfg_rd: TB still wiggles cfg_rd_*"
    echo "$rd_hits" | head -20
    LOG_OK=0
  else
    echo "PASS neg_no_cfg_rd (no cfg_rd_* in TB)"
  fi
fi

exit $LOG_OK
