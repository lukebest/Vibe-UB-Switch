"""vibe_pcs_rx_amctl_lock — PCS RX AMCTL lock per lane (AS-0.1 §6 / §14).

Product module: ``rtl/pcs/vibe_pcs_rx_amctl_lock.sv``. Ports match tip
``263aec6`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``in_vld`` / 160b ``in_data`` /
``locked`` / ``lid`` / ``lid_bad`` / ``is_amctl`` / ``sdf`` / ``edf``);
used by ``vibe_pcs_rx`` (``u_l0``..``u_l3``). Hunt on RAW 160b
(AMCTL is not scrambled) with 1-beat slip. Factory physical=logical
(U24): LID not {0,1,2,3} sets ``lid_bad``; do not swap lanes.
Pairs with stage-10 ``vibe_pcs_tx_amctl``. Continues the RX path
after stage-13 deskew.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"``, seven ``vibe_ebch16`` LUT instances
(sels 3/8/9/10/21/22/28), combo ``is_amctl``, and the hunt /
confirm / unlock always-block. Landed SV is hand-finished to keep
those freeze semantics. Leave FEC wrap / pack / g1 / tx / rx tops /
unpack for later stages.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycircuit import Circuit, module, u

_PCS = Path(__file__).resolve().parent
if str(_PCS) not in sys.path:
    sys.path.insert(0, str(_PCS))

from vibe_ebch16 import CW_W, EBCH16_CW

LANE_W = 160
LID_W = 2
CNT_W = 2

# Table 3-5 sels used by this-rev AMCTL (Link Width x4 SDF).
SEL_CW3 = 3
SEL_CW8 = 8
SEL_CW9 = 9
SEL_CW10 = 10
SEL_CW21 = 21
SEL_CW22 = 22
SEL_CW28 = 28

# Product uses VIBE_AMCTL_CONFIRM_N = UNLOCK_N = 3 from vibe_ub_params.vh.
CONFIRM_TH = 2  # lock when conf >= CONFIRM_N-1
UNLOCK_TH = 2  # unlock when unlk >= UNLOCK_N-1


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


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


def _dec_lid(m: Circuit, lid_sym, cw3, cw8, cw9, cw10):
    """LID: CW3→0, CW8→1, CW9→2, CW10→3, else 0."""
    return _mux(
        m,
        lid_sym == cw3,
        u(LID_W, 0),
        _mux(
            m,
            lid_sym == cw8,
            u(LID_W, 1),
            _mux(
                m,
                lid_sym == cw9,
                u(LID_W, 2),
                _mux(m, lid_sym == cw10, u(LID_W, 3), u(LID_W, 0), LID_W),
                LID_W,
            ),
            LID_W,
        ),
        LID_W,
    )


@module(name="vibe_pcs_rx_amctl_lock")
def build(m: Circuit) -> None:
    """Hunt / lock one lane on RAW 160b AMCTL (CONFIRM_N=UNLOCK_N=3).

    Product ports (hand-finished SV)::

        clk, rst_n, in_vld, in_data[159:0]
        locked, lid[1:0], lid_bad, is_amctl, sdf, edf

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``is_amctl`` is combo
    ``in_vld && (match_pair || match_w0 || match_w1)`` so descramble
    ``en=!is_amctl`` sees the same beat. Product instantiates
    ``vibe_ebch16``. Hunt slips one 160b instead of committing a
    bad pair. TX-layout lock is sticky through data; ``UNLOCK_N``
    only for legacy pair-slot hunt. LID not {0,1,2,3} → ``lid_bad``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    in_vld = m.input("in_vld", width=1)
    in_data = m.input("in_data", width=LANE_W)

    locked = m.out("locked", clk=clk, rst=rst, width=1, init=u(1, 0))
    lid = m.out("lid", clk=clk, rst=rst, width=LID_W, init=u(LID_W, 0))
    lid_bad = m.out("lid_bad", clk=clk, rst=rst, width=1, init=u(1, 0))
    sdf = m.out("sdf", clk=clk, rst=rst, width=1, init=u(1, 0))
    edf = m.out("edf", clk=clk, rst=rst, width=1, init=u(1, 0))
    conf = m.out("conf", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    unlk = m.out("unlk", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    prev = m.out("prev", clk=clk, rst=rst, width=LANE_W, init=u(LANE_W, 0))
    have = m.out("have", clk=clk, rst=rst, width=1, init=u(1, 0))
    via_leg = m.out("via_leg", clk=clk, rst=rst, width=1, init=u(1, 0))

    # Same Table 3-5 words as vibe_ebch16. Product instantiates the LUT.
    cw3 = u(CW_W, EBCH16_CW[SEL_CW3])
    cw8 = u(CW_W, EBCH16_CW[SEL_CW8])
    cw9 = u(CW_W, EBCH16_CW[SEL_CW9])
    cw10 = u(CW_W, EBCH16_CW[SEL_CW10])
    cw21 = u(CW_W, EBCH16_CW[SEL_CW21])
    cw22 = u(CW_W, EBCH16_CW[SEL_CW22])
    cw28 = u(CW_W, EBCH16_CW[SEL_CW28])

    in_body = in_data.slice(lsb=144, width=CW_W)
    prev_body = prev.out().slice(lsb=144, width=CW_W)
    match_w0 = ((in_body == cw21) | (in_body == cw28)) & (
        in_data.slice(lsb=32, width=32) == m.cat(cw22, cw22)
    )
    match_body = (prev_body == cw21) | (prev_body == cw28)
    match_end_tx = prev.out().slice(lsb=32, width=32) == m.cat(cw22, cw22)
    match_end_leg = in_data.slice(lsb=112, width=CW_W) == cw22
    match_pair = have.out() & match_body & (match_end_tx | match_end_leg)
    match_w1 = (
        in_data.slice(lsb=64, width=64) == _cat_all(m, cw8, cw9, cw8, cw9)
    ) & (
        in_data.slice(lsb=0, width=64) == _cat_all(m, cw10, cw22, cw10, cw22)
    )
    is_amctl = in_vld & (match_pair | match_w0 | match_w1)

    lid_sym = _mux(
        m,
        match_end_tx,
        prev.out().slice(lsb=0, width=CW_W),
        in_data.slice(lsb=64, width=CW_W),
        CW_W,
    )
    lid_ok = (
        (lid_sym == cw3)
        | (lid_sym == cw8)
        | (lid_sym == cw9)
        | (lid_sym == cw10)
    )
    detail_sdf = in_data.slice(lsb=0, width=64) == _cat_all(
        m, cw10, cw22, cw10, cw22
    )
    lid_dec = _dec_lid(m, lid_sym, cw3, cw8, cw9, cw10)

    hit = in_vld & match_pair
    slip = in_vld & ~match_pair
    do_unlk = slip & have.out() & locked.out() & via_leg.out()
    conf_ge = (conf.out() == CONFIRM_TH) | (conf.out() == (CONFIRM_TH + 1))
    unlk_ge = (unlk.out() == UNLOCK_TH) | (unlk.out() == (UNLOCK_TH + 1))
    unlk_now = do_unlk & unlk_ge

    # sdf / edf pulse one cycle on a pair match (stock clears them first).
    sdf.set(hit & detail_sdf)
    edf.set(hit & ~detail_sdf)

    lid.set(lid_dec, when=hit & lid_ok)
    lid_bad.set(u(1, 1), when=hit & ~lid_ok)

    locked.set(u(1, 1), when=hit & conf_ge)
    locked.set(u(1, 0), when=unlk_now)

    conf.set(conf.out() + 1, when=hit & ~conf_ge)
    conf.set(u(CNT_W, 0), when=unlk_now)

    via_leg.set(match_end_leg & ~match_end_tx, when=hit)
    via_leg.set(u(1, 0), when=unlk_now)

    unlk.set(u(CNT_W, 0), when=hit)
    unlk.set(unlk.out() + 1, when=do_unlk & ~unlk_ge)
    unlk.set(u(CNT_W, 0), when=unlk_now)

    have.set(u(1, 0), when=hit)
    have.set(u(1, 1), when=slip)
    prev.set(in_data, when=slip)

    m.output("locked", locked.out())
    m.output("lid", lid.out())
    m.output("lid_bad", lid_bad.out())
    m.output("is_amctl", is_amctl)
    m.output("sdf", sdf.out())
    m.output("edf", edf.out())


build.__pycircuit_name__ = "vibe_pcs_rx_amctl_lock"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_rx_amctl_lock").emit_mlir())
