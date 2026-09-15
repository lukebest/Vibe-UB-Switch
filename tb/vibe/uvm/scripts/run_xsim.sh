#!/usr/bin/env bash
# Compile and run the UVM env on AMD Vivado xsim (UVM 1.2).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
TB="$ROOT/tb/vibe"
RTL="$ROOT/rtl"
UVM="$TB/uvm"
RES="$TB/results"
mkdir -p "$RES"
cd "$TB"

XVLOG="${XVLOG:-xvlog}"
XELAB="${XELAB:-xelab}"
XSIM="${XSIM:-xsim}"

INC="-i $RTL/common -i $TB/common -i $UVM/pkg -i $UVM/if"

python3 "$TB/scripts/scan_official_neg.py" "$RTL" --inc "$TB/common/neg_official_scan.inc"

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

UNIT_RTL=(
  "$RTL/dll/"*.sv
  "$RTL/lmsm/vibe_lmsm.sv"
  "$RTL/mgmt/vibe_cfg_space.sv"
  "$RTL/mgmt/vibe_irq_agg.sv"
  "$RTL/mgmt/vibe_cna_ep.sv"
  "$RTL/mgmt/vibe_mgmt_byp.sv"
  "$RTL/fabric/vibe_vl_rr.sv"
  "$RTL/fabric/vibe_route_lu.sv"
  "$RTL/fabric/vibe_port_sel.sv"
  "$RTL/fabric/vibe_voq_egr.sv"
  "$RTL/fabric/vibe_xbar.sv"
  "$RTL/fabric/vibe_fecn_mark.sv"
  "$RTL/cdc/"*.sv
  "$RTL/pma/vibe_pma_bnd.sv"
  "$RTL/pcs/"*.sv
  "$RTL/nw/vibe_nw_adapt.sv"
  "$RTL/nw/vibe_icrc.sv"
)

PORT_RTL=(
  "$RTL/cdc/"*.sv
  "$RTL/pma/vibe_pma_bnd.sv"
  "$RTL/pcs/"*.sv
  "$RTL/lmsm/vibe_lmsm.sv"
  "$RTL/dll/"*.sv
  "$RTL/nw/vibe_nw_adapt.sv"
  "$RTL/nw/vibe_icrc.sv"
  "$RTL/port/vibe_port.sv"
)

TOP_RTL=(
  "$RTL/cdc/vibe_sync2.sv" "$RTL/cdc/vibe_afifo.sv"
  "$RTL/cdc/vibe_rst_sync.sv" "$RTL/cdc/vibe_gear_160_128.sv"
  "$RTL/cdc/vibe_gear_128_160.sv"
  "$RTL/pma/vibe_pma_bnd.sv"
  "$RTL/pcs/"*.sv
  "$RTL/lmsm/vibe_lmsm.sv"
  "$RTL/dll/"*.sv
  "$RTL/nw/vibe_nw_adapt.sv" "$RTL/nw/vibe_icrc.sv"
  "$RTL/fabric/"*.sv
  "$RTL/mgmt/"*.sv
  "$RTL/port/vibe_port.sv"
  "$RTL/top/vibe_ub_switch.sv"
)

compile_common() {
  $XVLOG -sv --incr --relax -L uvm --uvm_version 1.2 $INC \
    "$UVM/if/vibe_if.sv" "$UVM/pkg/vibe_uvm_pkg.sv" "$@" \
    2>&1 | tee "$RES/xvlog.log"
}

run_one() {
  local snap="$1"
  local test="$2"
  local log="$RES/${test}.log"
  echo "UVM $test"
  set +e
  $XSIM "$snap" --tclbatch "$UVM/scripts/runall.tcl" \
    -testplusarg "UVM_TESTNAME=$test" \
    -testplusarg "UVM_VERBOSITY=UVM_LOW" \
    -testplusarg "UVM_NO_RELNOTES" \
    2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  set -e
  if grep -qiE 'Could not obtain the necessary license|Unable to get Licensing' "$log"; then
    echo "FAIL $test (xsim license)" | tee -a "$log"
    return 1
  fi
  if grep -q '^FAIL ' "$log"; then
    return 1
  fi
  if grep -qE 'UVM_ERROR :[ ]*[1-9]' "$log" || grep -qE 'UVM_FATAL :[ ]*[1-9]' "$log"; then
    echo "FAIL $test (UVM_ERROR/FATAL)" | tee -a "$log"
    return 1
  fi
  if ! grep -q '^PASS ' "$log"; then
    echo "FAIL $test (no PASS line, rc=$rc)" | tee -a "$log"
    return 1
  fi
  if [ "$rc" -ne 0 ]; then
    echo "FAIL $test (xsim rc=$rc)" | tee -a "$log"
    return 1
  fi
  return 0
}

elab() {
  local top="$1"
  local snap="$2"
  $XELAB -L uvm --timescale 1ns/1ps --debug typical --relax \
    --snapshot "$snap" "work.$top" \
    2>&1 | tee "$RES/xelab_${snap}.log"
}

SUITE_TESTS=(
  tc_rt00_per_flow_rr_fwd
  tc_rt01_per_packet_rr_fwd
  tc_rt10_must_drop
  tc_rt11_must_drop
  tc_rt_shortest_unimpl_count
  tc_rt_shortest_irq_logic
  tc_rt_irq_logic_sticky
  tc_rt_no_rewrite
  tc_rt10_not_as_rt00
  tc_rt_counter_32b_sat
  tc_cfg_identity_guid_class
  tc_default_rt_all0_port0
  tc_pkt_len_err_drop
  tc_cfg6_term_vs_fwd
  tc_saf_full_pkt
  tc_icrc_transit_no_recompute
  tc_cfg3_fwd
  tc_cfg4_fwd
  tc_cfg5_fwd
  tc_cfg7_fwd
  tc_cfg9_fwd
  tc_cfg_reserved_fwd
  tc_cfg_fwd_class
  tc_cfg0_fabric_no_special
  tc_port_rst_via_cfg
  tc_device_rst_via_cfg
  tc_pkt_len_legal_16_4300
  tc_cfg9_no_icrc
)

UNIT_TESTS=(
  tc_id_nports_entity0
  tc_neg_ubfm
  tc_neg_qdlws
  tc_neg_exact_route
  tc_neg_port_cna
  tc_neg_cut_through
  tc_neg_hi_fec_ber
  tc_neg_probe
  tc_neg_dijkstra
  tc_neg_no_optical
  tc_tp_holes
  tc_credit_1024_flit_bp
  tc_credit_1024_hole
  tc_credit_timeout_1us
  tc_cfg0_no_credit
  tc_credit_no_underflow
  tc_credit_grain_n
  tc_lmsm_idle_discovery
  tc_identity_cfg_space
  tc_cna_16bit
  tc_irq_agg
  tc_vl_rr
  tc_vl_rr_0_15
  tc_bcrc_crc30
  tc_afifo_afull10
  tc_p0_down_drop
  tc_rt_g1_official
  tc_neg_official
  tc_neg_absent_features
  tc_dll_sm_states
  tc_route_lu
  tc_rst_sync
  tc_mgmt_byp
  tc_fecn_mark
  tc_retry_buf_256
  tc_retry_req_gbn
  tc_retry_ack_replay
  tc_retry_wait_retrain
  tc_deadlock_timeout_1us
  tc_timers_indep
  tc_dll_rx_errflag
  tc_fec_fail_gbn
  tc_cfg0_term_not_fabric
  tc_dll
  tc_lmsm_walk
  tc_lmsm_vlock
  tc_pcs_cw2beat
  tc_pcs_fec_dual_enc
  tc_pcs_fec_t2
  tc_pcs_fec_bypass
  tc_pcs_scramble
  tc_pcs_amctl
  tc_pma_512b_slice
  tc_pma_922mhz
  tc_phy_u26_chain
  tc_phy_nw_dll_512b
  tc_nw_adapt_linkready
  tc_xbar_unit
  tc_icrc_txrx_vs_transit
  tc_cna_ep
)

PORT_TESTS=(
  tc_port_smoke
  tc_nw_pkt_to_pma_tx
  tc_nw_pkt_pma_loopback
)

target="${1:-sim}"
shift || true

fail_n=0
pass_n=0

run_list() {
  local snap="$1"
  shift
  local t
  for t in "$@"; do
    if run_one "$snap" "$t"; then
      pass_n=$((pass_n + 1))
    else
      fail_n=$((fail_n + 1))
    fi
  done
}

case "$target" in
  suite)
    compile_common "${FAB_RTL[@]}" "$UVM/tb/vibe_fab_tb_top.sv"
    elab vibe_fab_tb_top vibe_fab_tb
    if [ "${TC:-}" != "" ]; then
      run_list vibe_fab_tb "$TC" || true
    else
      run_list vibe_fab_tb "${SUITE_TESTS[@]}" || true
    fi
    ;;
  units)
    compile_common "${UNIT_RTL[@]}" "$UVM/tb/vibe_unit_tb_top.sv"
    elab vibe_unit_tb_top vibe_unit_tb
    if [ "${TC:-}" != "" ]; then
      if printf '%s\n' "${PORT_TESTS[@]}" | grep -qx "$TC"; then
        compile_common "${PORT_RTL[@]}" "$UVM/tb/vibe_port_tb_top.sv"
        elab vibe_port_tb_top vibe_port_tb
        run_list vibe_port_tb "$TC" || true
      else
        run_list vibe_unit_tb "$TC" || true
      fi
    else
      run_list vibe_unit_tb "${UNIT_TESTS[@]}" || true
      compile_common "${PORT_RTL[@]}" "$UVM/tb/vibe_port_tb_top.sv"
      elab vibe_port_tb_top vibe_port_tb
      run_list vibe_port_tb "${PORT_TESTS[@]}" || true
    fi
    ;;
  port)
    compile_common "${PORT_RTL[@]}" "$UVM/tb/vibe_port_tb_top.sv"
    elab vibe_port_tb_top vibe_port_tb
    if [ "${TC:-}" != "" ]; then
      run_list vibe_port_tb "$TC" || true
    else
      run_list vibe_port_tb "${PORT_TESTS[@]}" || true
    fi
    ;;
  top)
    compile_common "${TOP_RTL[@]}" "$UVM/tb/vibe_switch_tb_top.sv"
    elab vibe_switch_tb_top vibe_switch_tb
    run_list vibe_switch_tb tc_top_smoke || true
    ;;
  sim)
    "$0" suite
    "$0" units
    "$0" top
    "$TB/scripts/scan_absent.sh" "$RTL" | tee "$RES/neg_absent.log"
    ;;
  *)
    echo "usage: $0 {suite|units|port|top|sim} [TC=name]"
    exit 2
    ;;
esac

echo "UVM xsim pass_files=$pass_n fail_files=$fail_n"
if [ "$fail_n" -ne 0 ]; then
  exit 1
fi
exit 0
