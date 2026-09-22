"""vibe_afifo — per-lane gray-pointer AFIFO (AS-0.1 §7).

Product module: ``rtl/cdc/vibe_afifo.sv``. Ports and fire rules match freeze
``302ac943``. SPEC / CR-B names are unchanged.

pyCircuit registers are dest-domain **synchronous active-high** reset. Product
RTL uses **async active-low** ``wrst_n`` / ``rrst_n`` and instantiates
``vibe_sync2``. Landed SV is hand-finished to keep those freeze semantics.
Do not replace this leaf with ``pyc.async_fifo`` (ready/valid, no ``wocc`` /
``almost_full``).
"""

from __future__ import annotations

import sys
from pathlib import Path

from pycircuit import Circuit, module, u

_TREE = Path(__file__).resolve().parent.parent
if str(_TREE) not in sys.path:
    sys.path.insert(0, str(_TREE))

from common.gray import vibe_bin2gray5, vibe_gray2bin5
from common.params import VIBE_AFIFO_AFULL_OCC, VIBE_AFIFO_DEPTH, VIBE_AFIFO_PTR_W


@module(name="vibe_afifo")
def build(m: Circuit, W: int = 160, DEPTH: int = VIBE_AFIFO_DEPTH) -> None:
    """Gray-pointer AFIFO. Default W=160, DEPTH=16 (product).

    Product ports (hand-finished SV)::

        wclk, wrst_n, wen, wdata, wfull, almost_full, wocc
        rclk, rrst_n, ren, rdata, rempty

    pyCircuit clocks are ``wclk`` / ``rclk``. Resets here are ``wrst`` / ``rrst``
    (active-high). Finish maps them to async-low ``wrst_n`` / ``rrst_n``.
    """
    if DEPTH != VIBE_AFIFO_DEPTH:
        raise ValueError(
            f"product vibe_afifo is frozen at DEPTH={VIBE_AFIFO_DEPTH} "
            f"(5-bit gray pointers); got DEPTH={DEPTH}"
        )

    ptr_w = VIBE_AFIFO_PTR_W
    aw = 4  # rtl/cdc/vibe_afifo.sv: localparam AW = 4
    afull_occ = VIBE_AFIFO_AFULL_OCC

    wclk = m.clock("wclk")
    wrst = m.reset("wrst")
    rclk = m.clock("rclk")
    rrst = m.reset("rrst")

    wen = m.input("wen", width=1)
    wdata = m.input("wdata", width=W)
    ren = m.input("ren", width=1)

    wbin = m.out("wbin", clk=wclk, rst=wrst, width=ptr_w, init=u(ptr_w, 0))
    rbin = m.out("rbin", clk=rclk, rst=rrst, width=ptr_w, init=u(ptr_w, 0))

    wgray = vibe_bin2gray5(m, wbin.out())
    rgray = vibe_bin2gray5(m, rbin.out())

    # Product instantiates vibe_sync2 #(.W(5)). pycc lowers cdc_sync to pyc_cdc_sync.
    rgray_s = m.cdc_sync(wclk, wrst, rgray, stages=2)
    wgray_s = m.cdc_sync(rclk, rrst, wgray, stages=2)

    rbin_w = vibe_gray2bin5(m, rgray_s)
    wbin_r = vibe_gray2bin5(m, wgray_s)

    wocc = wbin.out() - rbin_w
    wfull = wocc == DEPTH
    almost_full = wocc >= afull_occ
    rempty = rbin.out() == wbin_r

    wfire = wen & ~wfull
    rfire = ren & ~rempty
    wbin.set(wbin.out() + 1, when=wfire)
    rbin.set(rbin.out() + 1, when=rfire)

    # Product RAM: combo rdata = mem[rbin[AW-1:0]]; write on wclk when wfire.
    # Memory contents are *not* cleared on reset (hand-finished SV). These
    # cells exist so the frontend can elaborate a storage array.
    waddr = wbin.out().slice(lsb=0, width=aw)
    raddr = rbin.out().slice(lsb=0, width=aw)
    rdata = u(W, 0)
    for i in range(DEPTH):
        cell = m.out(f"mem_{i}", clk=wclk, rst=wrst, width=W, init=u(W, 0))
        hit = waddr == i
        cell.set(wdata, when=wfire & hit)
        rdata = cell.out() if (raddr == i) else rdata

    m.output("wfull", wfull)
    m.output("almost_full", almost_full)
    m.output("wocc", wocc)
    m.output("rdata", rdata)
    m.output("rempty", rempty)


build.__pycircuit_name__ = "vibe_afifo"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_afifo", W=160, DEPTH=16).emit_mlir())
