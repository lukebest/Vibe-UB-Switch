#!/usr/bin/env bash
# Compile and run every standalone vibe TC with Icarus. Do not touch rtl/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TB="$ROOT/tb/vibe"
RTL="$ROOT/rtl"
RES="$TB/results"
INC="-I$RTL/common -I$TB/common -I$TB/env -I$TB/tests"
IVERILOG="${IVERILOG:-iverilog}"
VVP="${VVP:-vvp}"
mkdir -p "$RES"

fail_n=0
pass_n=0
compile_fail=0

run1() {
  local name="$1"
  shift
  local out="$RES/${name}.vvp"
  local log="$RES/${name}.log"
  echo "UNIT $name"
  if ! $IVERILOG -g2012 $INC -o "$out" "$@"; then
    echo "FAIL $name (compile)" | tee "$log"
    compile_fail=$((compile_fail + 1))
    fail_n=$((fail_n + 1))
    return 0
  fi
  set +e
  $VVP "$out" | tee "$log"
  local rc=${PIPESTATUS[0]}
  set -e
  if grep -q '^FAIL ' "$log"; then
    fail_n=$((fail_n + 1))
  elif grep -q '^PASS ' "$log"; then
    pass_n=$((pass_n + 1))
  elif [ "$rc" -ne 0 ]; then
    echo "FAIL $name (vvp rc=$rc)" | tee -a "$log"
    fail_n=$((fail_n + 1))
  else
    echo "NOTE $name: no PASS/FAIL line (treated as pass if rc=0)"
    pass_n=$((pass_n + 1))
  fi
}

T="$TB/tests"
run1 tc_cfg0_term_not_fabric "$T/tc_cfg0_term_not_fabric.sv" "$RTL/dll/vibe_dll_rx.sv"
run1 tc_icrc_txrx_vs_transit "$T/tc_icrc_txrx_vs_transit.sv" "$RTL/nw/vibe_icrc.sv"
run1 tc_vl_rr               "$T/tc_vl_rr.sv"               "$RTL/fabric/vibe_vl_rr.sv"
run1 tc_vl_rr_0_15          "$T/tc_vl_rr_0_15.sv"          "$RTL/fabric/vibe_vl_rr.sv"
run1 tc_credit_1024_hole    "$T/tc_credit_1024_hole.sv"
run1 tc_credit_1024_flit_bp "$T/tc_credit_1024_flit_bp.sv" "$RTL/dll/vibe_dll_credit.sv"
run1 tc_credit_timeout_1us  "$T/tc_credit_timeout_1us.sv"  "$RTL/dll/vibe_dll_credit.sv"
run1 tc_deadlock_timeout_1us "$T/tc_deadlock_timeout_1us.sv" "$RTL/fabric/vibe_voq_egr.sv"
run1 tc_cfg0_no_credit      "$T/tc_cfg0_no_credit.sv"      "$RTL/dll/vibe_dll_credit.sv"
run1 tc_neg_absent_features "$T/tc_neg_absent_features.sv" "$RTL/lmsm/vibe_lmsm.sv"
run1 tc_identity_cfg_space  "$T/tc_identity_cfg_space.sv"  "$RTL/mgmt/vibe_cfg_space.sv"
run1 tc_xbar_unit           "$T/tc_xbar_unit.sv"           "$RTL/fabric/vibe_xbar.sv"
run1 tc_dll_sm_states       "$T/tc_dll_sm_states.sv"       "$RTL/dll/vibe_dll_sm.sv"
run1 tc_bcrc_crc30          "$T/tc_bcrc_crc30.sv"          "$RTL/dll/vibe_bcrc.sv"
run1 tc_retry_buf_256       "$T/tc_retry_buf_256.sv"       "$RTL/dll/vibe_dll_retry_buf.sv"
run1 tc_retry_req_gbn       "$T/tc_retry_req_gbn.sv"       "$RTL/dll/vibe_dll_retry_req_sm.sv"
run1 tc_retry_ack_replay    "$T/tc_retry_ack_replay.sv"    "$RTL/dll/vibe_dll_retry_ack_sm.sv"
run1 tc_afifo_afull10       "$T/tc_afifo_afull10.sv"       "$RTL/cdc/vibe_afifo.sv" "$RTL/cdc/vibe_sync2.sv"
run1 tc_gear_160_128        "$T/tc_gear_160_128.sv"        "$RTL/cdc/vibe_gear_160_128.sv"
run1 tc_gear_128_160        "$T/tc_gear_128_160.sv"        "$RTL/cdc/vibe_gear_128_160.sv"
run1 tc_phy_u26_chain       "$T/tc_phy_u26_chain.sv" \
  "$RTL/cdc/vibe_gear_160_128.sv" "$RTL/cdc/vibe_gear_128_160.sv" "$RTL/pma/vibe_pma_bnd.sv"
run1 tc_pma_512b_slice      "$T/tc_pma_512b_slice.sv"      "$RTL/pma/vibe_pma_bnd.sv"
run1 tc_pma_922mhz          "$T/tc_pma_922mhz.sv"          "$RTL/pma/vibe_pma_bnd.sv"
run1 tc_pcs_tx_g1_window    "$T/tc_pcs_tx_g1_window.sv"    "$RTL/pcs/vibe_pcs_tx_g1.sv"
run1 tc_pcs_fec_bypass      "$T/tc_pcs_fec_bypass.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run1 tc_pcs_fec_dual_enc    "$T/tc_pcs_fec_dual_enc.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run1 tc_pcs_fec_t2          "$T/tc_pcs_fec_t2.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run1 tc_pcs_cw2beat         "$T/tc_pcs_cw2beat.sv"         "$RTL/pcs/vibe_pcs_tx_cw2beat.sv"
run1 tc_pcs_amctl           "$T/tc_pcs_amctl.sv" \
  "$RTL/pcs/vibe_pcs_tx_amctl.sv" "$RTL/pcs/vibe_ebch16.sv"
run1 tc_pcs_scramble        "$T/tc_pcs_scramble.sv"        "$RTL/pcs/vibe_pcs_scramble.sv"
run1 tc_ebch16_lut          "$T/tc_ebch16_lut.sv"          "$RTL/pcs/vibe_ebch16.sv"
run1 tc_lmsm_idle_discovery "$T/tc_lmsm_idle_discovery.sv" "$RTL/lmsm/vibe_lmsm.sv"
run1 tc_rst_port_device     "$T/tc_rst_port_device.sv"     "$RTL/mgmt/vibe_rst_ctl.sv"
run1 tc_fecn_mark           "$T/tc_fecn_mark.sv"           "$RTL/fabric/vibe_fecn_mark.sv"
run1 tc_nw_adapt_linkready  "$T/tc_nw_adapt_linkready.sv"  "$RTL/nw/vibe_nw_adapt.sv"
run1 tc_dll_tx_cfg0         "$T/tc_dll_tx_cfg0.sv" \
  "$RTL/dll/vibe_dll_tx.sv" "$RTL/dll/vibe_bcrc.sv" "$RTL/dll/vibe_dll_credit.sv"
run1 tc_mgmt_byp            "$T/tc_mgmt_byp.sv"            "$RTL/mgmt/vibe_mgmt_byp.sv"
run1 tc_rst_sync            "$T/tc_rst_sync.sv"            "$RTL/cdc/vibe_rst_sync.sv"
run1 tc_rs_dec_syndrome     "$T/tc_rs_dec_syndrome.sv"     "$RTL/pcs/vibe_rs128_120_dec.sv"
run1 tc_neg_qdlws           "$T/tc_neg_qdlws.sv"
run1 tc_neg_exact_route     "$T/tc_neg_exact_route.sv"
run1 tc_neg_port_cna        "$T/tc_neg_port_cna.sv"
run1 tc_neg_cut_through     "$T/tc_neg_cut_through.sv"
run1 tc_neg_ubfm            "$T/tc_neg_ubfm.sv"
run1 tc_neg_hi_fec_ber      "$T/tc_neg_hi_fec_ber.sv"
run1 tc_neg_probe           "$T/tc_neg_probe.sv"
run1 tc_neg_dijkstra        "$T/tc_neg_dijkstra.sv"

echo "UNITS pass_files=$pass_n fail_files=$fail_n compile_fail=$compile_fail"
if [ "$fail_n" -ne 0 ]; then
  exit 1
fi
exit 0
