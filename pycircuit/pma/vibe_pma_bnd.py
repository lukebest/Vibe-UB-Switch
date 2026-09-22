"""vibe_pma_bnd — product PMA boundary (AS-0.1 §3).

Product module: ``rtl/pma/vibe_pma_bnd.sv``. Ports and fire rules match
tip ``ef3f121`` / historical freeze ``302ac943`` (PRBS23 + dest-domain
``txrst_n`` / ``rxrst_n`` + ``PMA_IDLE_MARK`` idle-PRBS, issue #115 / PR116).
SPEC / CR-B names are unchanged. No PMA ready.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``txrst_n`` / ``rxrst_n``. Landed SV
is hand-finished to keep those freeze semantics and the product PRBS
functions (128-step word / adv / recurrence). Do not sample ``txclk``
into the RX idle check (closed CDC; loopback stays ``pma_pcs_rxdata`` /
``rxclk`` only).
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycircuit import Circuit, module, u

_TREE = Path(__file__).resolve().parent.parent
if str(_TREE) not in sys.path:
    sys.path.insert(0, str(_TREE))

from common.params import VIBE_LANE_PMA_W, VIBE_N_LANE, VIBE_PMA_W
from pma.prbs23 import (
    PMA_IDLE_MARK,
    decorate_idle_int,
    prbs23_adv128,
    prbs23_seed_int,
    prbs23_word,
    prbs23_word_int,
    prbs23_word_ok,
)


def _idle_pack_from_seeds() -> int:
    """Reset / first-idle 512b: {idle3, idle2, idle1, idle0}."""
    acc = 0
    for lid in range(VIBE_N_LANE):
        lane = decorate_idle_int(prbs23_word_int(prbs23_seed_int(lid)))
        acc |= lane << (lid * VIBE_LANE_PMA_W)
    return acc


@module(name="vibe_pma_bnd")
def build(m: Circuit) -> None:
    """512b PMA slice. Default widths match ``vibe_ub_params.vh``.

    Product ports (hand-finished SV)::

        txclk, rxclk, txrst_n, rxrst_n
        afifo_pma_lane0..3, afifo_pma_lane_vld
        pcs_pma_txdata
        pma_pcs_rxdata
        pma_afifo_lane0..3, pma_afifo_lane_vld

    pyCircuit clocks are ``txclk`` / ``rxclk``. Resets here are ``txrst`` /
    ``rxrst`` (active-high). Finish maps them to async-low ``txrst_n`` /
    ``rxrst_n``.
    """
    lane_w = VIBE_LANE_PMA_W
    pma_w = VIBE_PMA_W
    n_lane = VIBE_N_LANE
    mark = u(lane_w, PMA_IDLE_MARK)

    txclk = m.clock("txclk")
    txrst = m.reset("txrst")
    rxclk = m.clock("rxclk")
    rxrst = m.reset("rxrst")

    lanes_in = [
        m.input(f"afifo_pma_lane{i}", width=lane_w) for i in range(n_lane)
    ]
    lane_vld = m.input("afifo_pma_lane_vld", width=1)
    rxdata = m.input("pma_pcs_rxdata", width=pma_w)

    packed = m.cat(lanes_in[3], lanes_in[2], lanes_in[1], lanes_in[0])

    lfsrs = []
    idle_lanes = []
    for i in range(n_lane):
        seed = prbs23_seed_int(i)
        lfsr = m.out(
            f"lfsr{i}",
            clk=txclk,
            rst=txrst,
            width=23,
            init=u(23, seed),
        )
        word = prbs23_word(m, lfsr.out())
        idle_lanes.append(word ^ mark)
        lfsrs.append(lfsr)

    idle_pack = m.cat(idle_lanes[3], idle_lanes[2], idle_lanes[1], idle_lanes[0])

    txdata = m.out(
        "pcs_pma_txdata",
        clk=txclk,
        rst=txrst,
        width=pma_w,
        init=u(pma_w, _idle_pack_from_seeds()),
    )
    txdata.set(packed, when=lane_vld)
    txdata.set(idle_pack, when=~lane_vld)
    for lfsr in lfsrs:
        lfsr.set(prbs23_adv128(m, lfsr.out()), when=~lane_vld)

    # RX: same-domain combo idle check. Un-XOR mark, then recurrence.
    # Do not fan in txclk / pcs_pma_txdata (was unsanctioned CDC).
    ok = u(1, 1)
    rx_slices = []
    for i in range(n_lane):
        sl = rxdata.slice(lsb=i * lane_w, width=lane_w)
        rx_slices.append(sl)
        ok = ok & prbs23_word_ok(m, sl ^ mark)
    idle_prbs = ok

    rx_outs = []
    for i in range(n_lane):
        r = m.out(
            f"pma_afifo_lane{i}",
            clk=rxclk,
            rst=rxrst,
            width=lane_w,
            init=u(lane_w, 0),
        )
        r.set(rx_slices[i])
        rx_outs.append(r)

    rx_vld = m.out(
        "pma_afifo_lane_vld",
        clk=rxclk,
        rst=rxrst,
        width=1,
        init=u(1, 0),
    )
    rx_vld.set(~idle_prbs)

    m.output("pcs_pma_txdata", txdata.out())
    for i, r in enumerate(rx_outs):
        m.output(f"pma_afifo_lane{i}", r.out())
    m.output("pma_afifo_lane_vld", rx_vld.out())


build.__pycircuit_name__ = "vibe_pma_bnd"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pma_bnd").emit_mlir())
