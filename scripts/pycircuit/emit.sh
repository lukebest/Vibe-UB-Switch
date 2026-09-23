#!/bin/sh
# Emit a Decision I leaf: MLIR via pycircuit.cli when possible; always land
# hand-finished SystemVerilog that matches tip ports/behavior.
# Usage: emit.sh [vibe_afifo|vibe_pma_bnd|vibe_sync2|vibe_rst_sync|vibe_gear_128_160|vibe_gear_160_128|vibe_pcs_scramble|vibe_ebch16|vibe_pcs_tx_cw2beat|vibe_pcs_tx_amctl|vibe_rs128_120_enc|vibe_rs128_120_dec|vibe_pcs_rx_deskew|vibe_pcs_rx_amctl_lock|vibe_pcs_rx_unpack|vibe_pcs_tx_pack|vibe_pcs_tx_fec|vibe_pcs_rx_fec|vibe_pcs_tx_g1|vibe_bcrc|vibe_dll_credit|vibe_dll_sm|vibe_dll_rx|vibe_dll_retry_ack_sm|vibe_dll_retry_buf|vibe_dll_retry_req_sm|vibe_dll_tx|vibe_dll|vibe_fecn_mark|vibe_vl_rr|vibe_route_lu|vibe_port_sel|vibe_voq_egr|vibe_saf_ing|vibe_xbar]
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
  vibe_pcs_scramble)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_scramble.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_scramble.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_scramble.sv"
    ;;
  vibe_ebch16)
    SRC="$ROOT/pycircuit/pcs/vibe_ebch16.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_ebch16.py"
    RTL="$ROOT/rtl/pcs/vibe_ebch16.sv"
    ;;
  vibe_pcs_tx_cw2beat)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_tx_cw2beat.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_tx_cw2beat.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_tx_cw2beat.sv"
    ;;
  vibe_pcs_tx_amctl)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_tx_amctl.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_tx_amctl.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_tx_amctl.sv"
    ;;
  vibe_rs128_120_enc)
    SRC="$ROOT/pycircuit/pcs/vibe_rs128_120_enc.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_rs128_120_enc.py"
    RTL="$ROOT/rtl/pcs/vibe_rs128_120_enc.sv"
    ;;
  vibe_rs128_120_dec)
    SRC="$ROOT/pycircuit/pcs/vibe_rs128_120_dec.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_rs128_120_dec.py"
    RTL="$ROOT/rtl/pcs/vibe_rs128_120_dec.sv"
    ;;
  vibe_pcs_rx_deskew)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_rx_deskew.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_rx_deskew.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_rx_deskew.sv"
    ;;
  vibe_pcs_rx_amctl_lock)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_rx_amctl_lock.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_rx_amctl_lock.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_rx_amctl_lock.sv"
    ;;
  vibe_pcs_rx_unpack)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_rx_unpack.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_rx_unpack.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_rx_unpack.sv"
    ;;
  vibe_pcs_tx_pack)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_tx_pack.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_tx_pack.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_tx_pack.sv"
    ;;
  vibe_pcs_tx_fec)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_tx_fec.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_tx_fec.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_tx_fec.sv"
    ;;
  vibe_pcs_rx_fec)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_rx_fec.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_rx_fec.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_rx_fec.sv"
    ;;
  vibe_pcs_tx_g1)
    SRC="$ROOT/pycircuit/pcs/vibe_pcs_tx_g1.py"
    HANDFINISH="$ROOT/pycircuit/pcs/handfinish_vibe_pcs_tx_g1.py"
    RTL="$ROOT/rtl/pcs/vibe_pcs_tx_g1.sv"
    ;;
  vibe_bcrc)
    SRC="$ROOT/pycircuit/dll/vibe_bcrc.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_bcrc.py"
    RTL="$ROOT/rtl/dll/vibe_bcrc.sv"
    ;;
  vibe_dll_credit)
    SRC="$ROOT/pycircuit/dll/vibe_dll_credit.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_credit.py"
    RTL="$ROOT/rtl/dll/vibe_dll_credit.sv"
    ;;
  vibe_dll_sm)
    SRC="$ROOT/pycircuit/dll/vibe_dll_sm.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_sm.py"
    RTL="$ROOT/rtl/dll/vibe_dll_sm.sv"
    ;;
  vibe_dll_rx)
    SRC="$ROOT/pycircuit/dll/vibe_dll_rx.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_rx.py"
    RTL="$ROOT/rtl/dll/vibe_dll_rx.sv"
    ;;
  vibe_dll_retry_ack_sm)
    SRC="$ROOT/pycircuit/dll/vibe_dll_retry_ack_sm.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_retry_ack_sm.py"
    RTL="$ROOT/rtl/dll/vibe_dll_retry_ack_sm.sv"
    ;;
  vibe_dll_retry_buf)
    SRC="$ROOT/pycircuit/dll/vibe_dll_retry_buf.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_retry_buf.py"
    RTL="$ROOT/rtl/dll/vibe_dll_retry_buf.sv"
    ;;
  vibe_dll_retry_req_sm)
    SRC="$ROOT/pycircuit/dll/vibe_dll_retry_req_sm.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_retry_req_sm.py"
    RTL="$ROOT/rtl/dll/vibe_dll_retry_req_sm.sv"
    ;;
  vibe_dll_tx)
    SRC="$ROOT/pycircuit/dll/vibe_dll_tx.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll_tx.py"
    RTL="$ROOT/rtl/dll/vibe_dll_tx.sv"
    ;;
  vibe_dll)
    SRC="$ROOT/pycircuit/dll/vibe_dll.py"
    HANDFINISH="$ROOT/pycircuit/dll/handfinish_vibe_dll.py"
    RTL="$ROOT/rtl/dll/vibe_dll.sv"
    ;;
  vibe_fecn_mark)
    SRC="$ROOT/pycircuit/fabric/vibe_fecn_mark.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_fecn_mark.py"
    RTL="$ROOT/rtl/fabric/vibe_fecn_mark.sv"
    ;;
  vibe_vl_rr)
    SRC="$ROOT/pycircuit/fabric/vibe_vl_rr.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_vl_rr.py"
    RTL="$ROOT/rtl/fabric/vibe_vl_rr.sv"
    ;;
  vibe_route_lu)
    SRC="$ROOT/pycircuit/fabric/vibe_route_lu.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_route_lu.py"
    RTL="$ROOT/rtl/fabric/vibe_route_lu.sv"
    ;;
  vibe_port_sel)
    SRC="$ROOT/pycircuit/fabric/vibe_port_sel.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_port_sel.py"
    RTL="$ROOT/rtl/fabric/vibe_port_sel.sv"
    ;;
  vibe_voq_egr)
    SRC="$ROOT/pycircuit/fabric/vibe_voq_egr.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_voq_egr.py"
    RTL="$ROOT/rtl/fabric/vibe_voq_egr.sv"
    ;;
  vibe_saf_ing)
    SRC="$ROOT/pycircuit/fabric/vibe_saf_ing.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_saf_ing.py"
    RTL="$ROOT/rtl/fabric/vibe_saf_ing.sv"
    ;;
  vibe_xbar)
    SRC="$ROOT/pycircuit/fabric/vibe_xbar.py"
    HANDFINISH="$ROOT/pycircuit/fabric/handfinish_vibe_xbar.py"
    RTL="$ROOT/rtl/fabric/vibe_xbar.sv"
    ;;
  *)
    echo "unknown leaf: $LEAF (vibe_afifo|vibe_pma_bnd|vibe_sync2|vibe_rst_sync|vibe_gear_128_160|vibe_gear_160_128|vibe_pcs_scramble|vibe_ebch16|vibe_pcs_tx_cw2beat|vibe_pcs_tx_amctl|vibe_rs128_120_enc|vibe_rs128_120_dec|vibe_pcs_rx_deskew|vibe_pcs_rx_amctl_lock|vibe_pcs_rx_unpack|vibe_pcs_tx_pack|vibe_pcs_tx_fec|vibe_pcs_rx_fec|vibe_pcs_tx_g1|vibe_bcrc|vibe_dll_credit|vibe_dll_sm|vibe_dll_rx|vibe_dll_retry_ack_sm|vibe_dll_retry_buf|vibe_dll_retry_req_sm|vibe_dll_tx|vibe_dll|vibe_fecn_mark|vibe_vl_rr|vibe_route_lu|vibe_port_sel|vibe_voq_egr|vibe_saf_ing|vibe_xbar)" >&2
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
