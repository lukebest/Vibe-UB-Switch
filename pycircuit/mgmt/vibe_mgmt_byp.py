"""vibe_mgmt_byp — mgmt bypass FIFO 16×512b (AS-0.1 §14).

Product module: ``rtl/mgmt/vibe_mgmt_byp.sv``. Ports match tip
``23718d19``. Decision I UNFROZEN (do not re-pin freeze).
SPEC / CR-B names are unchanged. Internal leaf
(``clk`` / ``rst_n`` / ``in_data[511:0]`` / ``in_vld`` /
``in_ready`` / ``out_data[511:0]`` / ``out_vld`` /
``out_ready``). Parameter ``DEPTH`` default 16. Second mgmt
leaf after stage-38 ``vibe_rst_ctl``. Sync FIFO, one unused
slot: ``in_ready = (wptr+1) != rptr``; ``out_vld = wptr !=
rptr``; ``out_data = mem[rptr[3:0]]``. Does not enter xbar;
mgmt reply injects on the ingress port TX before
``nw_adapt``, priority over VOQ. Self-contained (no child
instances). Instantiated by ``vibe_ub_switch``
(``g_byp.u_byp``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and the stock 5-bit pointer / ``mem[ptr[3:0]]`` body.
Landed SV is hand-finished to keep those tip semantics.
Leave ``vibe_cfg_space``, ``vibe_cna_ep``, ``vibe_irq_agg``,
and the ``vibe_mgmt`` wrap for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DEPTH = 16
PTR_W = 5
AW = 4
DATA_W = 512


@module(name="vibe_mgmt_byp")
def build(m: Circuit) -> None:
    """Mgmt bypass FIFO 16×512b. One unused slot. Does not enter xbar.

    Product ports (hand-finished SV)::

        clk, rst_n, in_data[511:0], in_vld, in_ready
        out_data[511:0], out_vld, out_ready

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Parameter ``DEPTH=16``.
    Combo: ``in_ready = (wptr+1) != rptr``; ``out_vld = wptr !=
    rptr``; ``out_data = mem[rptr[3:0]]``. Seq: ``!rst_n``
    clears ``wptr`` / ``rptr`` (mem not cleared). On
    ``in_vld && in_ready``: write ``mem[wptr[3:0]]``,
    ``wptr+1``. On ``out_vld && out_ready``: ``rptr+1``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    in_data = m.input("in_data", width=DATA_W)
    in_vld = m.input("in_vld", width=1)
    out_ready = m.input("out_ready", width=1)

    wptr = m.out("wptr", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    rptr = m.out("rptr", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))

    in_ready = (wptr.out() + u(PTR_W, 1)) != rptr.out()
    out_vld = wptr.out() != rptr.out()

    do_wr = in_vld & in_ready
    do_rd = out_vld & out_ready

    # Product RAM: combo out_data = mem[rptr[3:0]]. Cells exist so
    # the frontend can elaborate a storage array. Memory contents
    # are *not* cleared on reset (hand-finished SV).
    waddr = wptr.out().slice(lsb=0, width=AW)
    raddr = rptr.out().slice(lsb=0, width=AW)
    out_data = u(DATA_W, 0)
    for i in range(DEPTH):
        cell = m.out(f"mem_{i}", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0))
        cell.set(in_data, when=do_wr & (waddr == i))
        out_data = cell.out() if (raddr == i) else out_data

    wptr.set(wptr.out() + u(PTR_W, 1), when=do_wr)
    rptr.set(rptr.out() + u(PTR_W, 1), when=do_rd)

    m.output("in_ready", in_ready)
    m.output("out_data", out_data)
    m.output("out_vld", out_vld)


build.__pycircuit_name__ = "vibe_mgmt_byp"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_mgmt_byp").emit_mlir())
