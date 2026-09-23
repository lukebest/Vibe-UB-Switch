"""vibe_pcs_tx_amctl — AMCTL 40 symbol/lane, eBCH-16 (AS-0.1 §5).

Product module: ``rtl/pcs/vibe_pcs_tx_amctl.sv``. Ports match tip
``92adf9b`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``link_up`` / ``sdf_period`` /
``lane_id`` / ``req`` / ``ack`` / 320b ``amctl_40B``); used by
``vibe_pcs_tx_pack`` (``u_am0``..``u_am3``). Combo assemble after
FEC, before G2. Seven ``vibe_ebch16`` LUT instances (sels 3/8/9/10/
21/22/28).

pyCircuit expresses the LUT lookups, lane LID mux, and 40-symbol
concat. Product RTL keeps the stock ``vibe_ebch16`` instances,
``always @*`` LID ``case (lane_id)``, and combo ``{BODY, END, LID,
CTRL_TYPE, CTRL_DETAIL}``. ``clk`` / ``rst_n`` / ``sdf_period`` stay
on the pin list (pack wires them); the combo body does not sample
them. Landed SV is hand-finished to keep those freeze semantics.
Leave ``vibe_pcs_tx`` / pack / FEC / RS / rx for later stages.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycircuit import Circuit, module, u

_PCS = Path(__file__).resolve().parent
if str(_PCS) not in sys.path:
    sys.path.insert(0, str(_PCS))

from vibe_ebch16 import CW_W, EBCH16_CW

LANE_W = 2

# Table 3-5 sels used by this-rev AMCTL (Link Width x4 SDF).
SEL_CW3 = 3
SEL_CW8 = 8
SEL_CW9 = 9
SEL_CW10 = 10
SEL_CW21 = 21
SEL_CW22 = 22
SEL_CW28 = 28


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


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


def _lid0(m: Circuit, lane_id, cw3, cw8, cw9, cw10):
    """LID low word: lane 0=CW3, 1=CW8, 2=CW9, else CW10."""
    return _mux(
        m,
        lane_id == 0,
        cw3,
        _mux(m, lane_id == 1, cw8, _mux(m, lane_id == 2, cw9, cw10)),
    )


@module(name="vibe_pcs_tx_amctl")
def build(m: Circuit) -> None:
    """Assemble one 40-symbol AMCTL from eBCH-16 LUTs.

    Product ports (hand-finished SV)::

        clk, rst_n, link_up, sdf_period
        lane_id[1:0], req
        ack, amctl_40B[319:0]

    ``clk`` / ``rst_n`` / ``sdf_period`` are unused in the combo
    body (stock). Finish keeps the pins so ``vibe_pcs_tx_pack``
    wiring stays. ``ack`` is combo ``req && link_up``. ``amctl_40B``
    is BODY ``{3{CW21,CW28}}``, END ``{CW22,CW22}``, LID
    ``{lid1,lid0,lid1,lid0}`` (``lid1`` is always CW3), CTRL_TYPE
    Link Width ``{CW8,CW9,CW8,CW9}``, CTRL_DETAIL x4 SDF
    ``{CW10,CW22,CW10,CW22}``. Product instantiates ``vibe_ebch16``.
    """
    # Product pin list. Combo assemble does not clock or reset.
    m.input("clk", width=1)
    m.input("rst_n", width=1)
    link_up = m.input("link_up", width=1)
    m.input("sdf_period", width=1)
    lane_id = m.input("lane_id", width=LANE_W)
    req = m.input("req", width=1)

    # Same Table 3-5 words as vibe_ebch16. Product instantiates the LUT.
    cw3 = u(CW_W, EBCH16_CW[SEL_CW3])
    cw8 = u(CW_W, EBCH16_CW[SEL_CW8])
    cw9 = u(CW_W, EBCH16_CW[SEL_CW9])
    cw10 = u(CW_W, EBCH16_CW[SEL_CW10])
    cw21 = u(CW_W, EBCH16_CW[SEL_CW21])
    cw22 = u(CW_W, EBCH16_CW[SEL_CW22])
    cw28 = u(CW_W, EBCH16_CW[SEL_CW28])

    lid1 = cw3
    lid0 = _lid0(m, lane_id, cw3, cw8, cw9, cw10)

    body = _cat_all(m, cw21, cw28, cw21, cw28, cw21, cw28)
    amctl_40B = _cat_all(
        m,
        body,
        cw22,
        cw22,
        lid1,
        lid0,
        lid1,
        lid0,
        cw8,
        cw9,
        cw8,
        cw9,
        cw10,
        cw22,
        cw10,
        cw22,
    )

    m.output("ack", req & link_up)
    m.output("amctl_40B", amctl_40B)


build.__pycircuit_name__ = "vibe_pcs_tx_amctl"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx_amctl").emit_mlir())
