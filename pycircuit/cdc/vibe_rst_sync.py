"""vibe_rst_sync — async assert, sync deassert into dest clock (AS-0.1 §3).

Product module: ``rtl/cdc/vibe_rst_sync.sv``. Ports match tip
``49421f9`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n_in`` / ``rst_n_out``); used by
``vibe_port`` (``u_txrst`` / ``u_rxrst``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n_in``
(``or negedge rst_n_in``). Landed SV is hand-finished to keep those
freeze semantics. This leaf *is* the product 2-FF reset cell
(``r1`` then ``rst_n_out``); the frontend models two dest-domain
flops that release to 1.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u


@module(name="vibe_rst_sync")
def build(m: Circuit) -> None:
    """2-FF dest-domain reset sync. Async assert, sync deassert.

    Product ports (hand-finished SV)::

        clk, rst_n_in, rst_n_out

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n_in``. Both stages clear to 0
    and release toward 1.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")

    r1 = m.out("r1", clk=clk, rst=rst, width=1, init=u(1, 0))
    rst_n_out = m.out("rst_n_out", clk=clk, rst=rst, width=1, init=u(1, 0))
    r1.set(u(1, 1))
    rst_n_out.set(r1.out())

    m.output("rst_n_out", rst_n_out.out())


build.__pycircuit_name__ = "vibe_rst_sync"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_rst_sync").emit_mlir())
