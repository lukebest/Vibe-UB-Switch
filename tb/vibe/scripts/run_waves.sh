#!/usr/bin/env bash
# Dump Luke-audit TCs and render annotated PNG windows.
# Usage: make -C tb/vibe waves
#        make -C tb/vibe waves TC=tc_nw_pkt_pma_loopback
set -euo pipefail
TB="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$TB/../.." && pwd)"
WAVES="$TB/waves"
RTL="$ROOT/rtl"
RES="$TB/results"
IVERILOG="${IVERILOG:-iverilog}"
VVP="${VVP:-vvp}"
INC="-I$RTL/common -I$TB/common -I$TB/env -I$TB/tests"
WANT_TC="${TC:-}"
mkdir -p "$WAVES" "$RES"
cd "$TB"

want() {
  local name="$1"
  [ -z "$WANT_TC" ] || [ "$WANT_TC" = "$name" ]
}

pass_or_die() {
    local log="$1" name="$2"
    if ! grep -q "PASS ${name}" "$log"; then
        echo "FAIL: ${name} did not PASS (see $log)" >&2
        tail -40 "$log" >&2
        exit 1
    fi
    grep "PASS ${name}" "$log" | tail -1
}

if want tc_rt10_must_drop; then
echo "== suite tc_rt10_must_drop =="
make -C "$TB" suite TC=tc_rt10_must_drop \
    VVPFLAGS="+DUMP +DUMPFILE=${WAVES}/g1_rt10.vcd" \
    >"$WAVES/g1_rt10.log" 2>&1
pass_or_die "$WAVES/g1_rt10.log" tc_rt10_must_drop
fi

if want tc_cfg6_term_vs_fwd; then
echo "== suite tc_cfg6_term_vs_fwd =="
make -C "$TB" suite TC=tc_cfg6_term_vs_fwd \
    VVPFLAGS="+DUMP +DUMPFILE=${WAVES}/cfg6_term_vs_fwd.vcd" \
    >"$WAVES/cfg6_term_vs_fwd.log" 2>&1
pass_or_die "$WAVES/cfg6_term_vs_fwd.log" tc_cfg6_term_vs_fwd
fi

run_unit() {
    local name="$1" src="$2" vcd="$3" log="$4"
    shift 4
    local out="$RES/${name}_waves.vvp"
    echo "UNIT $name (+DUMP)"
    # shellcheck disable=SC2086
    "$IVERILOG" -g2012 $INC -o "$out" "$src" "$@"
    "$VVP" "$out" +DUMP "+DUMPFILE=${vcd}" >"$log" 2>&1
}

if want tc_credit_1024_flit_bp; then
echo "== unit tc_credit_1024_flit_bp =="
run_unit tc_credit_1024_flit_bp "$TB/tests/tc_credit_1024_flit_bp.sv" \
    "$WAVES/credit_1024_flit.vcd" "$WAVES/credit_1024_flit.log" \
    "$RTL/dll/vibe_dll_credit.sv"
pass_or_die "$WAVES/credit_1024_flit.log" tc_credit_1024_flit_bp
fi

if want tc_credit_timeout_1us; then
echo "== unit tc_credit_timeout_1us =="
run_unit tc_credit_timeout_1us "$TB/tests/tc_credit_timeout_1us.sv" \
    "$WAVES/credit_timeout_1us.vcd" "$WAVES/credit_timeout_1us.log" \
    "$RTL/dll/vibe_dll_credit.sv"
pass_or_die "$WAVES/credit_timeout_1us.log" tc_credit_timeout_1us
fi

if want tc_deadlock_timeout_1us; then
echo "== unit tc_deadlock_timeout_1us =="
run_unit tc_deadlock_timeout_1us "$TB/tests/tc_deadlock_timeout_1us.sv" \
    "$WAVES/voq_deadlock_1us.vcd" "$WAVES/voq_deadlock_1us.log" \
    "$RTL/fabric/vibe_voq_egr.sv"
pass_or_die "$WAVES/voq_deadlock_1us.log" tc_deadlock_timeout_1us
fi

PORT_RTL="\
  $RTL/cdc/vibe_sync2.sv $RTL/cdc/vibe_afifo.sv $RTL/cdc/vibe_rst_sync.sv \
  $RTL/cdc/vibe_gear_160_128.sv $RTL/cdc/vibe_gear_128_160.sv \
  $RTL/pma/vibe_pma_bnd.sv \
  $RTL/pcs/vibe_pcs_tx.sv $RTL/pcs/vibe_pcs_tx_g1.sv \
  $RTL/pcs/vibe_pcs_tx_fec.sv $RTL/pcs/vibe_rs128_120_enc.sv \
  $RTL/pcs/vibe_pcs_tx_cw2beat.sv $RTL/pcs/vibe_pcs_tx_pack.sv \
  $RTL/pcs/vibe_pcs_tx_amctl.sv $RTL/pcs/vibe_ebch16.sv \
  $RTL/pcs/vibe_pcs_scramble.sv \
  $RTL/pcs/vibe_pcs_rx.sv $RTL/pcs/vibe_pcs_rx_amctl_lock.sv \
  $RTL/pcs/vibe_pcs_rx_deskew.sv $RTL/pcs/vibe_pcs_rx_unpack.sv \
  $RTL/pcs/vibe_pcs_rx_fec.sv $RTL/pcs/vibe_rs128_120_dec.sv \
  $RTL/lmsm/vibe_lmsm.sv \
  $RTL/dll/vibe_dll.sv $RTL/dll/vibe_dll_sm.sv $RTL/dll/vibe_dll_credit.sv \
  $RTL/dll/vibe_dll_retry_buf.sv $RTL/dll/vibe_dll_retry_req_sm.sv \
  $RTL/dll/vibe_dll_retry_ack_sm.sv $RTL/dll/vibe_dll_tx.sv \
  $RTL/dll/vibe_dll_rx.sv $RTL/dll/vibe_bcrc.sv \
  $RTL/nw/vibe_nw_adapt.sv $RTL/port/vibe_port.sv"

if want tc_nw_pkt_pma_loopback; then
echo "== unit tc_nw_pkt_pma_loopback (TP-PHY-012) 512b data =="
# shellcheck disable=SC2086
run_unit tc_nw_pkt_pma_loopback "$TB/tests/tc_nw_pkt_pma_loopback.sv" \
    "$WAVES/nw_pkt_pma_loopback_data512.vcd" "$WAVES/nw_pkt_pma_loopback_data512.log" \
    $PORT_RTL
pass_or_die "$WAVES/nw_pkt_pma_loopback_data512.log" tc_nw_pkt_pma_loopback
fi

echo "== render PNGs =="
python3 "$TB/scripts/vcd_to_png.py" --waves "$WAVES"

# Keep PNGs uncompressed. Gzip large VCDs except the Luke 512b dump
# (README documents the .vcd path; do not rename it to .vcd.gz).
shopt -s nullglob
for vcd in "$WAVES"/*.vcd; do
    case "$(basename "$vcd")" in
      nw_pkt_pma_loopback_data512.vcd) continue ;;
    esac
    sz=$(wc -c < "$vcd")
    if [ "$sz" -gt 1000000 ]; then
        gzip -f "$vcd"
        echo "gzipped $(basename "$vcd") ($sz bytes)"
    fi
done
echo "Waves written under $WAVES"
