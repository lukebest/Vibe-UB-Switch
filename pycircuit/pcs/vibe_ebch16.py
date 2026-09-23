"""vibe_ebch16 — eBCH-16 codeword LUT (AS-0.1 §5 / UB 3.2.4.1).

Product module: ``rtl/pcs/vibe_ebch16.sv``. Ports match tip
``9f86cba`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Combo leaf (``cw_sel[4:0]`` → ``cw[15:0]``); used by
``vibe_pcs_tx_amctl`` and ``vibe_pcs_rx_amctl_lock``. Table 3-5
plus default ``16'hFFFF`` (sel 31).

pyCircuit expresses a 32-way combo mux tree. Product RTL keeps the
stock ``always @* case (cw_sel)`` LUT. Landed SV is hand-finished
to keep that freeze body. Leave ``vibe_pcs_tx`` / rx / FEC / RS /
amctl for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

SEL_W = 5
CW_W = 16

# Table 3-5 eBCH (16, 5) plus default (sel 31).
EBCH16_CW = (
    0x0000,
    0x0A6F,
    0x14DD,
    0x1EB2,
    0x23D6,
    0x29B9,
    0x370B,
    0x3D64,
    0x47AC,
    0x4DC3,
    0x5371,
    0x591E,
    0x647A,
    0x6E15,
    0x70A7,
    0x7AC8,
    0x8537,
    0x8F58,
    0x91EA,
    0x9B85,
    0xA6E1,
    0xAC8E,
    0xB23C,
    0xB853,
    0xC29B,
    0xC8F4,
    0xD646,
    0xDC29,
    0xE14D,
    0xEB22,
    0xF590,
    0xFFFF,
)


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _mux(m: Circuit, sel_bit, a, b):
    """Combo ``sel_bit ? a : b`` via bitwise mask."""
    mask = _widen(m, sel_bit, CW_W)
    return (a & mask) | (b & ~mask)


def _lut(m: Circuit, sel):
    """32-way combo mux. Product SV is ``case (cw_sel)``."""
    acc = u(CW_W, EBCH16_CW[31])
    for i in range(31):
        acc = _mux(m, sel == i, u(CW_W, EBCH16_CW[i]), acc)
    return acc


@module(name="vibe_ebch16")
def build(m: Circuit) -> None:
    """eBCH-16 codeword LUT (Table 3-5). Combo ``case (cw_sel)``.

    Product ports (hand-finished SV)::

        cw_sel[4:0]
        cw[15:0]

    No clock. No reset. Sel 0..30 are Table 3-5; default is
    ``16'hFFFF``. Used as a same-layer PCS helper, not a CDC cell.
    """
    cw_sel = m.input("cw_sel", width=SEL_W)
    m.output("cw", _lut(m, cw_sel))


build.__pycircuit_name__ = "vibe_ebch16"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_ebch16").emit_mlir())
