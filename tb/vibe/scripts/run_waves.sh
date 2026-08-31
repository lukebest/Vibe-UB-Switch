#!/usr/bin/env bash
# Dump the five Luke-audit TCs and render annotated PNG windows.
# Usage: from tb/vibe — make waves   or   bash scripts/run_waves.sh
set -euo pipefail
TB="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$TB/../.." && pwd)"
WAVES="$TB/waves"
RTL="$ROOT/rtl"
RES="$TB/results"
IVERILOG="${IVERILOG:-iverilog}"
VVP="${VVP:-vvp}"
INC="-I$RTL/common -I$TB/common -I$TB/env -I$TB/tests"
mkdir -p "$WAVES" "$RES"
cd "$TB"

pass_or_die() {
    local log="$1" name="$2"
    if ! grep -q "PASS ${name}" "$log"; then
        echo "FAIL: ${name} did not PASS (see $log)" >&2
        tail -40 "$log" >&2
        exit 1
    fi
    grep "PASS ${name}" "$log" | tail -1
}

echo "== suite tc_rt10_must_drop =="
make -C "$TB" suite TC=tc_rt10_must_drop \
    VVPFLAGS="+DUMP +DUMPFILE=${WAVES}/g1_rt10.vcd" \
    >"$WAVES/g1_rt10.log" 2>&1
pass_or_die "$WAVES/g1_rt10.log" tc_rt10_must_drop

echo "== suite tc_cfg6_term_vs_fwd =="
make -C "$TB" suite TC=tc_cfg6_term_vs_fwd \
    VVPFLAGS="+DUMP +DUMPFILE=${WAVES}/cfg6_term_vs_fwd.vcd" \
    >"$WAVES/cfg6_term_vs_fwd.log" 2>&1
pass_or_die "$WAVES/cfg6_term_vs_fwd.log" tc_cfg6_term_vs_fwd

run_unit() {
    local name="$1" src="$2" vcd="$3" log="$4"
    shift 4
    local out="$RES/${name}_waves.vvp"
    echo "UNIT $name (+DUMP)"
    # shellcheck disable=SC2086
    "$IVERILOG" -g2012 $INC -o "$out" "$src" "$@"
    "$VVP" "$out" +DUMP "+DUMPFILE=${vcd}" >"$log" 2>&1
}

echo "== unit tc_credit_1024_flit_bp =="
run_unit tc_credit_1024_flit_bp "$TB/tests/tc_credit_1024_flit_bp.sv" \
    "$WAVES/credit_1024_flit.vcd" "$WAVES/credit_1024_flit.log" \
    "$RTL/dll/vibe_dll_credit.sv"
pass_or_die "$WAVES/credit_1024_flit.log" tc_credit_1024_flit_bp

echo "== unit tc_credit_timeout_1us =="
run_unit tc_credit_timeout_1us "$TB/tests/tc_credit_timeout_1us.sv" \
    "$WAVES/credit_timeout_1us.vcd" "$WAVES/credit_timeout_1us.log" \
    "$RTL/dll/vibe_dll_credit.sv"
pass_or_die "$WAVES/credit_timeout_1us.log" tc_credit_timeout_1us

echo "== unit tc_deadlock_timeout_1us =="
run_unit tc_deadlock_timeout_1us "$TB/tests/tc_deadlock_timeout_1us.sv" \
    "$WAVES/voq_deadlock_1us.vcd" "$WAVES/voq_deadlock_1us.log" \
    "$RTL/fabric/vibe_voq_egr.sv"
pass_or_die "$WAVES/voq_deadlock_1us.log" tc_deadlock_timeout_1us

echo "== render PNGs =="
python3 "$TB/scripts/vcd_to_png.py" --waves "$WAVES"

# Keep PNGs uncompressed for GitHub; gzip only large VCDs.
for vcd in "$WAVES"/*.vcd; do
    sz=$(wc -c < "$vcd")
    if [ "$sz" -gt 1000000 ]; then
        gzip -f "$vcd"
        echo "gzipped $(basename "$vcd") ($sz bytes)"
    fi
done
echo "Waves written under $WAVES"
