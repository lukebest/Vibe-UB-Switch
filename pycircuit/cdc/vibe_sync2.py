"""vibe_sync2 — 2-FF synchronizer for gray pointers (AS-0.1 §7).

Product module: ``rtl/cdc/vibe_sync2.sv``. Ports and params match
tip ``7cf680f`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``d`` / ``q``); used by ``vibe_afifo``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``).
Landed SV is hand-finished to keep those freeze semantics. pycc lowers
``cdc_sync`` to ``pyc_cdc_sync``; this leaf *is* the product 2-FF cell
(``q1`` then ``q``), so the frontend models two dest-domain flops.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u


@module(name="vibe_sync2")
def build(m: Circuit, W: int = 5) -> None:
    """2-FF dest-domain sync. Default W=5 (product gray-pointer width).

    Product ports (hand-finished SV)::

        clk, rst_n, d[W-1:0], q[W-1:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Both stages clear to 0.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    d = m.input("d", width=W)

    q1 = m.out("q1", clk=clk, rst=rst, width=W, init=u(W, 0))
    q = m.out("q", clk=clk, rst=rst, width=W, init=u(W, 0))
    q1.set(d)
    q.set(q1.out())

    m.output("q", q.out())


build.__pycircuit_name__ = "vibe_sync2"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_sync2", W=5).emit_mlir())
