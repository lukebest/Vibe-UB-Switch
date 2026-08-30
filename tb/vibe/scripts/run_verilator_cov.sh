#!/usr/bin/env bash
# Real Verilator line/toggle coverage on vibe_*.sv.
# Fixes prior --binary gap: generated main never wrote coverage.dat ($finish).
# Uses a custom C++ main that calls VerilatedCov::write() after the sim loop.
# BLKLOOPINIT in vibe_route_lu is waived (RTL freeze), not patched.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TB="$ROOT/tb/vibe"
RTL="$ROOT/rtl"
RES="$TB/results"
COV="$TB/cov/out"
mkdir -p "$RES" "$COV"
rm -rf "$COV"/*
mkdir -p "$COV"

if ! command -v verilator >/dev/null; then
  echo "NOTE cov: verilator not installed"
  exit 0
fi

VERILATOR="${VERILATOR:-verilator}"
INC="-I$RTL/common -I$TB/common -I$TB/env -I$TB/tests"
WARN="-Wno-fatal -Wno-BLKLOOPINIT -Wno-UNOPTFLAT -Wno-WIDTH -Wno-UNUSED -Wno-DECLFILENAME -Wno-PINCONNECTEMPTY -Wno-UNUSEDSIGNAL -Wno-VARHIDDEN -Wno-IMPORTSTAR -Wno-EOFNEWLINE"
COMMON="$VERILATOR --cc --timing --coverage --coverage-line --coverage-toggle --build -j 0 $INC $WARN"

write_main() {
  local top="$1"
  local dest="$2"
  cat > "$dest" <<EOF
#include "V${top}.h"
#include "verilated.h"
#include "verilated_cov.h"
#include <memory>
int main(int argc, char** argv) {
  const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
  contextp->debug(0);
  contextp->commandArgs(argc, argv);
  const std::unique_ptr<V${top}> topp{new V${top}{contextp.get()}};
  while (!contextp->gotFinish()) {
    topp->eval();
    if (!topp->eventsPending()) break;
    contextp->time(topp->nextTimeSlot());
  }
  VerilatedCov::write("coverage.dat");
  topp->final();
  return 0;
}
EOF
}

# Each cluster: name, top, extra sources...
run_cluster() {
  local name="$1"
  local top="$2"
  shift 2
  local work="$COV/$name"
  mkdir -p "$work"
  write_main "$top" "$work/cov_main.cpp"
  echo "COV cluster $name top=$top"
  set +e
  (
    cd "$work"
    $COMMON --top-module "$top" --exe cov_main.cpp --Mdir obj_dir \
      -CFLAGS "-I$work/obj_dir" "$@"
  )
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "NOTE cov: cluster $name compile rc=$rc"
    return 0
  fi
  set +e
  (
    cd "$work"
    ./obj_dir/V${top}
  )
  set -e
  if [ -f "$work/coverage.dat" ]; then
    cp -f "$work/coverage.dat" "$COV/${name}.dat"
    echo "COV cluster $name wrote coverage.dat"
  else
    echo "NOTE cov: cluster $name ran but no coverage.dat"
  fi
}

T="$TB/tests"
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

# Small / medium clusters (must produce numbers)
run_cluster dll_sm tc_dll_sm_states "$T/tc_dll_sm_states.sv" "$RTL/dll/vibe_dll_sm.sv"
run_cluster credit tc_credit_1024_flit_bp "$T/tc_credit_1024_flit_bp.sv" "$RTL/dll/vibe_dll_credit.sv"
run_cluster credit_to tc_credit_timeout_1us "$T/tc_credit_timeout_1us.sv" "$RTL/dll/vibe_dll_credit.sv"
run_cluster cfg0_crd tc_cfg0_no_credit "$T/tc_cfg0_no_credit.sv" "$RTL/dll/vibe_dll_credit.sv"
run_cluster bcrc tc_bcrc_crc30 "$T/tc_bcrc_crc30.sv" "$RTL/dll/vibe_bcrc.sv"
run_cluster retry_buf tc_retry_buf_256 "$T/tc_retry_buf_256.sv" "$RTL/dll/vibe_dll_retry_buf.sv"
run_cluster retry_req tc_retry_req_gbn "$T/tc_retry_req_gbn.sv" "$RTL/dll/vibe_dll_retry_req_sm.sv"
run_cluster retry_ack tc_retry_ack_replay "$T/tc_retry_ack_replay.sv" "$RTL/dll/vibe_dll_retry_ack_sm.sv"
run_cluster dll_rx tc_cfg0_term_not_fabric "$T/tc_cfg0_term_not_fabric.sv" "$RTL/dll/vibe_dll_rx.sv"
run_cluster dll_tx tc_dll_tx_cfg0 "$T/tc_dll_tx_cfg0.sv" \
  "$RTL/dll/vibe_dll_tx.sv" "$RTL/dll/vibe_bcrc.sv" "$RTL/dll/vibe_dll_credit.sv"
run_cluster vl_rr tc_vl_rr_0_15 "$T/tc_vl_rr_0_15.sv" "$RTL/fabric/vibe_vl_rr.sv"
run_cluster fecn tc_fecn_mark "$T/tc_fecn_mark.sv" "$RTL/fabric/vibe_fecn_mark.sv"
run_cluster afifo tc_afifo_afull10 "$T/tc_afifo_afull10.sv" "$RTL/cdc/vibe_afifo.sv" "$RTL/cdc/vibe_sync2.sv"
run_cluster gear_tx tc_gear_160_128 "$T/tc_gear_160_128.sv" "$RTL/cdc/vibe_gear_160_128.sv"
run_cluster gear_rx tc_gear_128_160 "$T/tc_gear_128_160.sv" "$RTL/cdc/vibe_gear_128_160.sv"
run_cluster pma tc_pma_512b_slice "$T/tc_pma_512b_slice.sv" "$RTL/pma/vibe_pma_bnd.sv"
run_cluster pma922 tc_pma_922mhz "$T/tc_pma_922mhz.sv" "$RTL/pma/vibe_pma_bnd.sv"
run_cluster rstsync tc_rst_sync "$T/tc_rst_sync.sv" "$RTL/cdc/vibe_rst_sync.sv"
run_cluster rstctl tc_rst_port_device "$T/tc_rst_port_device.sv" "$RTL/mgmt/vibe_rst_ctl.sv"
run_cluster cfgspace tc_identity_cfg_space "$T/tc_identity_cfg_space.sv" "$RTL/mgmt/vibe_cfg_space.sv"
run_cluster mgmtbyp tc_mgmt_byp "$T/tc_mgmt_byp.sv" "$RTL/mgmt/vibe_mgmt_byp.sv"
run_cluster lmsm tc_lmsm_idle_discovery "$T/tc_lmsm_idle_discovery.sv" "$RTL/lmsm/vibe_lmsm.sv"
run_cluster nw tc_nw_adapt_linkready "$T/tc_nw_adapt_linkready.sv" "$RTL/nw/vibe_nw_adapt.sv"
run_cluster icrc tc_icrc_txrx_vs_transit "$T/tc_icrc_txrx_vs_transit.sv" "$RTL/nw/vibe_icrc.sv"
run_cluster ebch tc_ebch16_lut "$T/tc_ebch16_lut.sv" "$RTL/pcs/vibe_ebch16.sv"
run_cluster amctl tc_pcs_amctl "$T/tc_pcs_amctl.sv" "$RTL/pcs/vibe_pcs_tx_amctl.sv" "$RTL/pcs/vibe_ebch16.sv"
run_cluster scramble tc_pcs_scramble "$T/tc_pcs_scramble.sv" "$RTL/pcs/vibe_pcs_scramble.sv"
run_cluster g1win tc_pcs_tx_g1_window "$T/tc_pcs_tx_g1_window.sv" "$RTL/pcs/vibe_pcs_tx_g1.sv"
run_cluster cw2beat tc_pcs_cw2beat "$T/tc_pcs_cw2beat.sv" "$RTL/pcs/vibe_pcs_tx_cw2beat.sv"
run_cluster fec_t4 tc_pcs_fec_dual_enc "$T/tc_pcs_fec_dual_enc.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run_cluster fec_t2 tc_pcs_fec_t2 "$T/tc_pcs_fec_t2.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run_cluster fec_byp tc_pcs_fec_bypass "$T/tc_pcs_fec_bypass.sv" \
  "$RTL/pcs/vibe_pcs_tx_fec.sv" "$RTL/pcs/vibe_rs128_120_enc.sv"
run_cluster rsdec tc_rs_dec_syndrome "$T/tc_rs_dec_syndrome.sv" "$RTL/pcs/vibe_rs128_120_dec.sv"
run_cluster voq tc_deadlock_timeout_1us "$T/tc_deadlock_timeout_1us.sv" "$RTL/fabric/vibe_voq_egr.sv"
run_cluster psel tc_psel_cov "$TB/cov/tc_psel_cov.sv" "$RTL/fabric/vibe_port_sel.sv"

# Fabric suite (BLKLOOPINIT waived). May be slow due to VOQ age loops.
run_cluster suite vibe_suite \
  "$TB/env/vibe_fabric_harness.sv" "$TB/env/vibe_psel_harness.sv" \
  "$TB/env/vibe_suite.sv" "${FAB_RTL[@]}"

# Merge
dats=()
for f in "$COV"/*.dat; do
  [ -f "$f" ] || continue
  dats+=("$f")
done

if [ "${#dats[@]}" -eq 0 ]; then
  echo "NOTE cov: no coverage.dat produced (honest: 0 collected files)"
  echo "COV_TOOL=verilator $($VERILATOR --version | head -1)"
  exit 0
fi

echo "COV merging ${#dats[@]} files"
verilator_coverage --write "$COV/merged.dat" "${dats[@]}" | tee "$RES/cov_merge.txt"
verilator_coverage "$COV/merged.dat" | tee "$RES/cov_raw.txt"
mkdir -p "$COV/annotate"
verilator_coverage --annotate "$COV/annotate" --annotate-all --annotate-min 1 "$COV/merged.dat" \
  | tee "$RES/cov_annotate.txt" || true

python3 "$TB/scripts/cov_report.py" "$COV/merged.dat" "$RTL" "$RES/cov_report.md" \
  | tee "$RES/cov_summary.txt"

echo "COV_TOOL=verilator $($VERILATOR --version | head -1)"
echo "COV_DAT=$COV/merged.dat"
echo "COV clusters=${#dats[@]}"
