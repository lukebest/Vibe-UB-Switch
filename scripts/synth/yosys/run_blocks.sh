#!/usr/bin/env bash
# Block-level Yosys QoR. One module at a time. No full-chip slang elaborate.
# Caps: TIMEOUT_SEC (default 180), RSS_MB (default 12000). Do not invent numbers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RTL="$ROOT/rtl"
RUN="$ROOT/scripts/synth/yosys/run_synth.sh"
YOSYS="${YOSYS:-yosys}"
LIBERTY="${LIBERTY:-}"
RTL_SHA="${RTL_SHA:-32a7f5e0c3f04762aa27dae73b000e55773195da}"
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
RSS_MB="${RSS_MB:-12000}"
OUT_ROOT="${OUT_ROOT:-$ROOT/reports/synth/blocks}"
WORK_ROOT="${WORK_ROOT:-$ROOT/scripts/synth/work/blocks}"
INDEX="$ROOT/reports/synth/blocks_index.txt"

mkdir -p "$OUT_ROOT" "$WORK_ROOT"
: > "$INDEX"

# Sum VmRSS (kB) of pid and descendants (yosys is a child of run_synth.sh).
tree_rss_kb() {
  local p=$1 t=0 c
  t=$(awk '/VmRSS:/ {print $2}' "/proc/$p/status" 2>/dev/null || echo 0)
  for c in $(ps -o pid= --ppid "$p" 2>/dev/null); do
    t=$((t + $(tree_rss_kb "$c")))
  done
  echo "$t"
}

run_capped() {
  local timeout_sec=$1
  shift
  local log=$1
  # remaining args: command
  shift
  local pid rss_kb limit_kb
  limit_kb=$((RSS_MB * 1024))
  "$@" >"$log.stdout" 2>"$log.stderr" &
  pid=$!
  local start=$SECONDS
  while kill -0 "$pid" 2>/dev/null; do
    rss_kb=$(tree_rss_kb "$pid")
    if [ "${rss_kb:-0}" -gt "$limit_kb" ]; then
      echo "KILLED rss_kb=$rss_kb limit_kb=$limit_kb" >>"$log.stderr"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 1
      kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 137
    fi
    if [ $((SECONDS - start)) -ge "$timeout_sec" ]; then
      echo "KILLED timeout_sec=$timeout_sec" >>"$log.stderr"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 1
      kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 124
    fi
    sleep 1
  done
  wait "$pid"
  return $?
}

one_block() {
  local top=$1 frontend=$2 timeout_sec=$3
  shift 3
  local rpt="$OUT_ROOT/$top"
  local work="$WORK_ROOT/$top"
  mkdir -p "$rpt" "$work"
  echo "=== $top frontend=$frontend timeout=${timeout_sec}s ==="
  local rc=0
  TOP="$top" FRONTEND="$frontend" MEMORY_MAP=0 \
    RTL_SHA="$RTL_SHA" LIBERTY="$LIBERTY" YOSYS="$YOSYS" \
    RPT_DIR="$rpt" OUT_DIR="$work" \
    run_capped "$timeout_sec" "$rpt/watch" "$RUN" "$@"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "OK $top" | tee -a "$INDEX"
  elif [ "$rc" -eq 137 ]; then
    echo "FAIL $top OOM_OR_RSS_CAP (RSS_MB>$RSS_MB)" | tee -a "$INDEX"
    echo "STATUS: elaborate failed / OOM" >"$rpt/area.rpt"
    { echo "STATUS: killed RSS cap ${RSS_MB}MB"; cat "$rpt/watch.stderr" 2>/dev/null || true; } >"$rpt/fail.txt"
  elif [ "$rc" -eq 124 ]; then
    echo "FAIL $top TIMEOUT ${timeout_sec}s" | tee -a "$INDEX"
    echo "STATUS: timeout" >"$rpt/area.rpt"
    { echo "STATUS: killed timeout ${timeout_sec}s"; cat "$rpt/watch.stderr" 2>/dev/null || true; } >"$rpt/fail.txt"
  else
    echo "FAIL $top rc=$rc" | tee -a "$INDEX"
    echo "STATUS: synth_failed" >"$rpt/area.rpt"
    {
      echo "STATUS: yosys rc=$rc frontend=$frontend"
      echo "---- synth.log tail ----"
      tail -40 "$rpt/synth.log" 2>/dev/null || true
      echo "---- watch.stderr ----"
      cat "$rpt/watch.stderr" 2>/dev/null || true
    } >"$rpt/fail.txt"
  fi
  return 0
}

# --- Verilog frontend: blocks without unpacked-array ports -----------------
one_block vibe_sync2            verilog 60  "$RTL/cdc/vibe_sync2.sv"
one_block vibe_rst_sync         verilog 60  "$RTL/cdc/vibe_rst_sync.sv"
one_block vibe_gear_160_128     verilog 90  "$RTL/cdc/vibe_gear_160_128.sv"
one_block vibe_gear_128_160     verilog 90  "$RTL/cdc/vibe_gear_128_160.sv"
one_block vibe_afifo            verilog 120 "$RTL/cdc/vibe_sync2.sv" "$RTL/cdc/vibe_afifo.sv"
one_block vibe_pma_bnd          verilog 60  "$RTL/pma/vibe_pma_bnd.sv"
one_block vibe_ebch16           verilog 60  "$RTL/pcs/vibe_ebch16.sv"
one_block vibe_pcs_scramble     verilog 90  "$RTL/pcs/vibe_pcs_scramble.sv"
one_block vibe_pcs_tx_amctl     verilog 90  "$RTL/pcs/vibe_pcs_tx_amctl.sv"
one_block vibe_pcs_tx_g1        verilog 120 "$RTL/pcs/vibe_pcs_tx_g1.sv"
one_block vibe_pcs_tx_cw2beat   verilog 90  "$RTL/pcs/vibe_pcs_tx_cw2beat.sv"
one_block vibe_pcs_rx_amctl_lock verilog 90 "$RTL/pcs/vibe_pcs_rx_amctl_lock.sv"
one_block vibe_pcs_rx_deskew    verilog 90  "$RTL/pcs/vibe_pcs_rx_deskew.sv"
one_block vibe_pcs_rx_unpack    verilog 90  "$RTL/pcs/vibe_pcs_rx_unpack.sv"
one_block vibe_lmsm             verilog 90  "$RTL/lmsm/vibe_lmsm.sv"
one_block vibe_bcrc             verilog 120 "$RTL/dll/vibe_bcrc.sv"
one_block vibe_dll_sm           verilog 90  "$RTL/dll/vibe_dll_sm.sv"
one_block vibe_dll_credit       verilog 90  "$RTL/dll/vibe_dll_credit.sv"
one_block vibe_dll_retry_req_sm verilog 90  "$RTL/dll/vibe_dll_retry_req_sm.sv"
one_block vibe_dll_retry_ack_sm verilog 90  "$RTL/dll/vibe_dll_retry_ack_sm.sv"
one_block vibe_dll_retry_buf    verilog 180 "$RTL/dll/vibe_dll_retry_buf.sv"
one_block vibe_dll_rx           verilog 180 "$RTL/dll/vibe_dll_rx.sv"
one_block vibe_dll_tx           verilog 180 "$RTL/dll/vibe_dll_tx.sv"
one_block vibe_icrc             verilog 120 "$RTL/nw/vibe_icrc.sv"
one_block vibe_nw_adapt         verilog 90  "$RTL/nw/vibe_nw_adapt.sv"
one_block vibe_irq_agg          verilog 60  "$RTL/mgmt/vibe_irq_agg.sv"
one_block vibe_mgmt_byp         verilog 90  "$RTL/mgmt/vibe_mgmt_byp.sv"
one_block vibe_rst_ctl          verilog 60  "$RTL/mgmt/vibe_rst_ctl.sv"
one_block vibe_cfg_space        verilog 90  "$RTL/mgmt/vibe_cfg_space.sv"
one_block vibe_route_lu         verilog 90  "$RTL/fabric/vibe_route_lu.sv"
one_block vibe_port_sel         verilog 90  "$RTL/fabric/vibe_port_sel.sv"
one_block vibe_saf_ing          verilog 180 "$RTL/fabric/vibe_saf_ing.sv"
one_block vibe_voq_egr          verilog 180 "$RTL/fabric/vibe_voq_egr.sv"
one_block vibe_vl_rr            verilog 90  "$RTL/fabric/vibe_vl_rr.sv"
one_block vibe_fecn_mark        verilog 90  "$RTL/fabric/vibe_fecn_mark.sv"
one_block vibe_rs128_120_enc    verilog 180 "$RTL/pcs/vibe_rs128_120_enc.sv"
one_block vibe_rs128_120_dec    verilog 180 "$RTL/pcs/vibe_rs128_120_dec.sv"

# --- Slang: unpacked-array ports. Default unroll-limit only. No 200000. --
# Do not invoke full-chip vibe_ub_switch here.
one_block vibe_xbar     slang 180 "$RTL/fabric/vibe_xbar.sv"
one_block vibe_cna_ep   slang 180 "$RTL/mgmt/vibe_cna_ep.sv"
one_block vibe_mgmt     slang 180 \
  "$RTL/mgmt/vibe_cfg_space.sv" "$RTL/mgmt/vibe_cna_ep.sv" \
  "$RTL/mgmt/vibe_irq_agg.sv" "$RTL/mgmt/vibe_rst_ctl.sv" \
  "$RTL/mgmt/vibe_mgmt.sv"
one_block vibe_fabric   slang 180 \
  "$RTL/fabric/vibe_saf_ing.sv" "$RTL/fabric/vibe_route_lu.sv" \
  "$RTL/fabric/vibe_port_sel.sv" "$RTL/fabric/vibe_xbar.sv" \
  "$RTL/fabric/vibe_voq_egr.sv" "$RTL/fabric/vibe_vl_rr.sv" \
  "$RTL/fabric/vibe_fecn_mark.sv" "$RTL/fabric/vibe_fabric.sv"

echo "DONE blocks. Index: $INDEX"
cat "$INDEX"
