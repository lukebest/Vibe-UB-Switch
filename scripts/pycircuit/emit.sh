#!/bin/sh
# Emit a Decision I leaf: MLIR via pycircuit.cli when possible; always land
# hand-finished SystemVerilog that matches tip ports/behavior.
# Usage: emit.sh [vibe_afifo|vibe_pma_bnd|vibe_sync2|vibe_rst_sync|vibe_gear_128_160|vibe_gear_160_128]
# Default remains vibe_afifo (stage-1).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
# shellcheck disable=SC1091
. "$ROOT/pycircuit/TOOLCHAIN.lock"

LEAF="${1:-vibe_afifo}"
case "$LEAF" in
  vibe_afifo)
    SRC="$ROOT/pycircuit/cdc/vibe_afifo.py"
    HANDFINISH="$ROOT/pycircuit/cdc/handfinish_vibe_afifo.py"
    RTL="$ROOT/rtl/cdc/vibe_afifo.sv"
    ;;
  vibe_pma_bnd)
    SRC="$ROOT/pycircuit/pma/vibe_pma_bnd.py"
    HANDFINISH="$ROOT/pycircuit/pma/handfinish_vibe_pma_bnd.py"
    RTL="$ROOT/rtl/pma/vibe_pma_bnd.sv"
    ;;
  vibe_sync2)
    SRC="$ROOT/pycircuit/cdc/vibe_sync2.py"
    HANDFINISH="$ROOT/pycircuit/cdc/handfinish_vibe_sync2.py"
    RTL="$ROOT/rtl/cdc/vibe_sync2.sv"
    ;;
  vibe_rst_sync)
    SRC="$ROOT/pycircuit/cdc/vibe_rst_sync.py"
    HANDFINISH="$ROOT/pycircuit/cdc/handfinish_vibe_rst_sync.py"
    RTL="$ROOT/rtl/cdc/vibe_rst_sync.sv"
    ;;
  vibe_gear_128_160)
    SRC="$ROOT/pycircuit/cdc/vibe_gear_128_160.py"
    HANDFINISH="$ROOT/pycircuit/cdc/handfinish_vibe_gear_128_160.py"
    RTL="$ROOT/rtl/cdc/vibe_gear_128_160.sv"
    ;;
  vibe_gear_160_128)
    SRC="$ROOT/pycircuit/cdc/vibe_gear_160_128.py"
    HANDFINISH="$ROOT/pycircuit/cdc/handfinish_vibe_gear_160_128.py"
    RTL="$ROOT/rtl/cdc/vibe_gear_160_128.sv"
    ;;
  *)
    echo "unknown leaf: $LEAF (vibe_afifo|vibe_pma_bnd|vibe_sync2|vibe_rst_sync|vibe_gear_128_160|vibe_gear_160_128)" >&2
    exit 2
    ;;
esac

OUT_DIR="${PYC_OUT_DIR:-$ROOT/.pycircuit_out/$LEAF}"
mkdir -p "$OUT_DIR"

# Never put the Vibe repo root on PYTHONPATH — it would shadow the toolchain
# package named pycircuit. The design tree itself may be added.
export PYTHONPATH="${ROOT}/pycircuit${PYTHONPATH:+:$PYTHONPATH}"

echo "toolchain pin: ${PYCIRCUIT_REPO} @ ${PYCIRCUIT_COMMIT} (${PYCIRCUIT_RELEASE})"
echo "leaf: $LEAF"

if python3 -c "import pycircuit" >/dev/null 2>&1; then
  if python3 -m pycircuit.cli emit "$SRC" -o "$OUT_DIR/${LEAF}.pyc"; then
    echo "frontend emit: $OUT_DIR/${LEAF}.pyc"
  else
    echo "frontend emit failed (see above); continuing with hand-finish" >&2
  fi
else
  echo "pycircuit not importable; run scripts/pycircuit/setup_toolchain.sh" >&2
fi

if command -v pycc >/dev/null 2>&1 && [ -f "$OUT_DIR/${LEAF}.pyc" ]; then
  mkdir -p "$OUT_DIR/verilog"
  pycc "$OUT_DIR/${LEAF}.pyc" --emit=verilog --out-dir "$OUT_DIR/verilog" || \
    echo "pycc --emit=verilog failed; product SV stays hand-finished" >&2
else
  echo "pycc not available (needs LLVM 19 + flows/scripts/pyc build); skip prototype Verilog"
fi

python3 "$HANDFINISH"
echo "product RTL: $RTL"
