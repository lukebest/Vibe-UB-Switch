#!/bin/sh
# Install lukebest/pyCircuit frontend (pyc4.0 / pycircuit-hisi / pycc).
# Prefer the published wheel; clone the pinned commit if PyPI has no artifact.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
# shellcheck disable=SC1091
. "$ROOT/pycircuit/TOOLCHAIN.lock"

CACHE="${PYCIRCUIT_CACHE:-$ROOT/.pycircuit_out/src}"
mkdir -p "$CACHE"

if python3 -m pip install --user "${PYCIRCUIT_PACKAGE}==${PYCIRCUIT_PACKAGE_VERSION}" 2>/dev/null; then
  echo "installed ${PYCIRCUIT_PACKAGE}==${PYCIRCUIT_PACKAGE_VERSION} from PyPI"
else
  echo "PyPI has no ${PYCIRCUIT_PACKAGE}; cloning ${PYCIRCUIT_REPO} @ ${PYCIRCUIT_COMMIT}"
  if [ ! -d "$CACHE/pyCircuit/.git" ]; then
    git clone --filter=blob:none "$PYCIRCUIT_REPO" "$CACHE/pyCircuit"
  fi
  git -C "$CACHE/pyCircuit" fetch --depth 1 origin "$PYCIRCUIT_COMMIT"
  git -C "$CACHE/pyCircuit" checkout --detach "$PYCIRCUIT_COMMIT"
  python3 -m pip install --user -e "$CACHE/pyCircuit"
fi

python3 -c "import pycircuit; print('pycircuit import ok', getattr(pycircuit, '__file__', ''))"
echo "pycc: $(command -v pycc || echo 'not on PATH — build with LLVM 19: bash <clone>/flows/scripts/pyc build')"
echo "pin: ${PYCIRCUIT_REPO} ${PYCIRCUIT_COMMIT} (${PYCIRCUIT_RELEASE})"
