"""vibe_fecn_mark — fabric FECN mark (AS-0.1 §8).

Product module: ``rtl/fabric/vibe_fecn_mark.sv``. Ports match tip
``c33bb143`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Combo leaf (``cci_in[15:0]`` / ``voq_occ[5:0]`` /
``cci_out[15:0]`` / ``marked``). First fabric leaf after DLL
helpers (stage-20..26). If CCI.Mode is ``3'b100`` or ``3'b010``
and local congestion (``voq_occ >= FECN_WM``, default 24) is
worse than the packet FECN, rewrite FECN and LoC; else
pass-through. ``2'b00`` unmarkable; ``2'b10`` none; ``2'b01``
light; ``2'b11`` severe. Not CAQM. Self-contained (no child
instances). Instantiated by ``vibe_fabric`` (``u_fecn``).

pyCircuit expresses the combo compare / mux tree. Product RTL
keeps the stock wire / assign body and parameter ``FECN_WM``.
Landed SV is hand-finished to keep those freeze semantics.
Leave PCS tx / rx tops, ``vibe_dll_tx``, and ``vibe_dll`` top
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

CCI_W = 16
OCC_W = 6
MODE_W = 3
FECN_W = 2
RSVD_LO_W = 7
MODE_PAD_W = 3
FECN_WM = 24
MODE_FECN = 0b100
MODE_FECN_RTT = 0b010
FECN_UNMARKABLE = 0
LVL_NONE = 0b10
LVL_SEVERE = 0b11


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _mux(m: Circuit, sel_bit, a, b, width: int):
    """Combo ``sel_bit ? a : b`` via bitwise mask."""
    mask = _widen(m, sel_bit, width)
    return (a & mask) | (b & ~mask)


@module(name="vibe_fecn_mark")
def build(m: Circuit) -> None:
    """FECN mark: Mode 100/010 + local cong worse → rewrite.

    Product ports (hand-finished SV)::

        cci_in[15:0], voq_occ[5:0], cci_out[15:0], marked

    No clock. No reset. ``cong = voq_occ >= FECN_WM``.
    ``markable_mode = (mode==3'b100) || (mode==3'b010)``.
    ``local_lvl = cong ? 2'b11 : 2'b10``.
    ``worse = cong && (fecn!=2'b00) && (local_lvl>fecn)``.
    ``marked = markable_mode && worse``.
    Rewrite: ``{mode, 3'b000, LoC=0, cci_in[8:2], local_lvl}``.
    Else ``cci_out = cci_in``. Not CAQM.
    """
    cci_in = m.input("cci_in", width=CCI_W)
    voq_occ = m.input("voq_occ", width=OCC_W)

    mode = cci_in.slice(lsb=13, width=MODE_W)
    fecn = cci_in.slice(lsb=0, width=FECN_W)
    cong = voq_occ >= FECN_WM
    markable_mode = (mode == MODE_FECN) | (mode == MODE_FECN_RTT)
    local_lvl = _mux(
        m, cong, u(FECN_W, LVL_SEVERE), u(FECN_W, LVL_NONE), FECN_W
    )
    worse = cong & ~(fecn == FECN_UNMARKABLE) & (local_lvl > fecn)
    marked = markable_mode & worse
    rewritten = m.cat(
        mode,
        u(MODE_PAD_W, 0),
        u(1, 0),
        cci_in.slice(lsb=2, width=RSVD_LO_W),
        local_lvl,
    )
    cci_out = _mux(m, marked, rewritten, cci_in, CCI_W)

    m.output("cci_out", cci_out)
    m.output("marked", marked)


build.__pycircuit_name__ = "vibe_fecn_mark"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_fecn_mark").emit_mlir())
