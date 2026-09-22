#!/bin/sh
# Emit vibe_afifo: MLIR via pycircuit.cli when possible; always land
# hand-finished SystemVerilog that matches freeze ports/behavior.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
# shellcheck disable=SC1091
. "$ROOT/pycircuit/TOOLCHAIN.lock"

SRC="$ROOT/pycircuit/cdc/vibe_afifo.py"
OUT_DIR="${PYC_OUT_DIR:-$ROOT/.pycircuit_out/vibe_afifo}"
RTL="$ROOT/rtl/cdc/vibe_afifo.sv"
mkdir -p "$OUT_DIR"

# Never put the Vibe repo root on PYTHONPATH — it would shadow the toolchain
# package named pycircuit. The design tree itself may be added.
export PYTHONPATH="${ROOT}/pycircuit${PYTHONPATH:+:$PYTHONPATH}"

echo "toolchain pin: ${PYCIRCUIT_REPO} @ ${PYCIRCUIT_COMMIT} (${PYCIRCUIT_RELEASE})"

if python3 -c "import pycircuit" >/dev/null 2>&1; then
  if python3 -m pycircuit.cli emit "$SRC" -o "$OUT_DIR/vibe_afifo.pyc"; then
    echo "frontend emit: $OUT_DIR/vibe_afifo.pyc"
  else
    echo "frontend emit failed (see above); continuing with hand-finish" >&2
  fi
else
  echo "pycircuit not importable; run scripts/pycircuit/setup_toolchain.sh" >&2
fi

if command -v pycc >/dev/null 2>&1 && [ -f "$OUT_DIR/vibe_afifo.pyc" ]; then
  mkdir -p "$OUT_DIR/verilog"
  pycc "$OUT_DIR/vibe_afifo.pyc" --emit=verilog --out-dir "$OUT_DIR/verilog" || \
    echo "pycc --emit=verilog failed; product SV stays hand-finished" >&2
else
  echo "pycc not available (needs LLVM 19 + flows/scripts/pyc build); skip prototype Verilog"
fi

python3 "$ROOT/pycircuit/cdc/handfinish_vibe_afifo.py"
echo "product RTL: $RTL"
