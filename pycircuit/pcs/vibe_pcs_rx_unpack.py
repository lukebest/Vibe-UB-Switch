"""vibe_pcs_rx_unpack — PCS RX unpack (AS-0.1 §6 inverse G2).

Product module: ``rtl/pcs/vibe_pcs_rx_unpack.sv``. Ports match tip
``ebd1671`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / 4×160b ``lane*`` / ``lane_vld`` /
``am0``..``am3`` / ``am_gap`` / 512b ``beat_data`` / ``beat_vld`` /
``beat_ready``); used by ``vibe_pcs_rx`` (``u_un``). Strip AMCTL,
collect 4×640 = 2560b, emit 5×512. Dual-buffer so the next 4×640
is accepted while 5×512 drains (a single acc that dropped ingress
while ``have`` permanently slipped pairing vs TX
``vibe_pcs_tx_pack``). Continues the RX path after stage-13 deskew
and stage-14 amctl_lock.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
combo ``beat_vld`` / ``beat_data``, stock ``am_gap = 1'b0`` default,
and the dual-buffer always-block. Landed SV is hand-finished to keep
those freeze semantics. Leave FEC wrap / pack / g1 / tx / rx tops
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

LANE_W = 160
GROUP_W = 640
ACC_W = 2560
BEAT_W = 512
NXT3_W = 1920
CNT_W = 3


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


@module(name="vibe_pcs_rx_unpack")
def build(m: Circuit) -> None:
    """Strip AMCTL and unpack 4×640 into 5×512 beats (inverse G2).

    Product ports (hand-finished SV)::

        clk, rst_n
        lane0..lane3[159:0], lane_vld, am0..am3, am_gap
        beat_data[511:0], beat_vld, beat_ready

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``beat_vld`` is combo
    ``have``. ``beat_data`` is combo ``acc[511:0]``. ``take`` is
    combo ``lane_vld && !(am0|am1|am2|am3) && !am_gap && !nxt_full``.
    ``am_gap`` is a one-cycle group reset of ``n`` (keeps in-flight
    emit). Fill writes ``nxt[640*n +: 640]`` for ``n=0..2``; ``n==3``
    completes ``{din, nxt[1919:0]}`` into ``acc`` when free, else
    parks it in ``nxt`` / ``nxt_full``. Emit shifts 512 when
    ``have && beat_ready``; last beat swaps ``nxt`` in or clears
    ``have``. NBA last-wins matches stock (take can refill ``acc``
    on the last emit cycle).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    lane0 = m.input("lane0", width=LANE_W)
    lane1 = m.input("lane1", width=LANE_W)
    lane2 = m.input("lane2", width=LANE_W)
    lane3 = m.input("lane3", width=LANE_W)
    lane_vld = m.input("lane_vld", width=1)
    am0 = m.input("am0", width=1)
    am1 = m.input("am1", width=1)
    am2 = m.input("am2", width=1)
    am3 = m.input("am3", width=1)
    am_gap = m.input("am_gap", width=1)
    beat_ready = m.input("beat_ready", width=1)

    acc = m.out("acc", clk=clk, rst=rst, width=ACC_W, init=u(ACC_W, 0))
    nxt = m.out("nxt", clk=clk, rst=rst, width=ACC_W, init=u(ACC_W, 0))
    n = m.out("n", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    e = m.out("e", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    have = m.out("have", clk=clk, rst=rst, width=1, init=u(1, 0))
    nxt_full = m.out("nxt_full", clk=clk, rst=rst, width=1, init=u(1, 0))

    skip = am0 | am1 | am2 | am3
    din = _cat_all(m, lane3, lane2, lane1, lane0)
    take = lane_vld & ~skip & ~am_gap & ~nxt_full.out()

    n0 = n.out() == 0
    n1 = n.out() == 1
    n2 = n.out() == 2
    n3 = n.out() == 3

    emit = have.out() & beat_ready
    e_nz = ~(e.out() == 0)
    swap = emit & ~e_nz & nxt_full.out()
    drain = emit & ~e_nz & ~nxt_full.out()
    acc_free = ~have.out() | (have.out() & beat_ready & ~e_nz & ~nxt_full.out())
    complete = take & n3
    to_acc = complete & acc_free
    to_nxt = complete & ~acc_free
    group = m.cat(din, nxt.out().slice(lsb=0, width=NXT3_W))

    # Stock order: am_gap n-reset, then emit, then take (NBA last-wins).
    n.set(u(CNT_W, 0), when=am_gap)

    acc.set(
        m.cat(u(BEAT_W, 0), acc.out().slice(lsb=BEAT_W, width=ACC_W - BEAT_W)),
        when=emit & e_nz,
    )
    e.set(e.out() - 1, when=emit & e_nz)
    acc.set(nxt.out(), when=swap)
    e.set(u(CNT_W, 4), when=swap)
    have.set(u(1, 1), when=swap)
    nxt_full.set(u(1, 0), when=swap)
    have.set(u(1, 0), when=drain)

    nxt.set(
        m.cat(nxt.out().slice(lsb=GROUP_W, width=ACC_W - GROUP_W), din),
        when=take & n0,
    )
    nxt.set(
        _cat_all(
            m,
            nxt.out().slice(lsb=2 * GROUP_W, width=ACC_W - 2 * GROUP_W),
            din,
            nxt.out().slice(lsb=0, width=GROUP_W),
        ),
        when=take & n1,
    )
    nxt.set(
        _cat_all(
            m,
            nxt.out().slice(lsb=3 * GROUP_W, width=ACC_W - 3 * GROUP_W),
            din,
            nxt.out().slice(lsb=0, width=2 * GROUP_W),
        ),
        when=take & n2,
    )
    n.set(n.out() + 1, when=take & ~n3)

    acc.set(group, when=to_acc)
    e.set(u(CNT_W, 4), when=to_acc)
    have.set(u(1, 1), when=to_acc)
    nxt.set(group, when=to_nxt)
    nxt_full.set(u(1, 1), when=to_nxt)
    n.set(u(CNT_W, 0), when=complete)

    m.output("beat_data", acc.out().slice(lsb=0, width=BEAT_W))
    m.output("beat_vld", have.out())


build.__pycircuit_name__ = "vibe_pcs_rx_unpack"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_rx_unpack").emit_mlir())
