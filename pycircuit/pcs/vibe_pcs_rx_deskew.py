"""vibe_pcs_rx_deskew — PCS RX AMCTL deskew (AS-0.1 §6).

Product module: ``rtl/pcs/vibe_pcs_rx_deskew.sv``. Ports match tip
``ebd1671`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / 4×160b ``in*`` / ``in_vld`` /
``am0``..``am3`` / 4×160b ``out*`` / ``out_vld`` / ``aligned``);
used by ``vibe_pcs_rx`` (``u_dsk``). Factory physical=logical (U24):
no lane swap and no delay once aligned. FIFO pointers only record
first-AMCTL lock; outputs stay pass-through so a second AMCTL 160b
does not leak into the 512b stream.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
combo ``aligned`` / ``out_vld`` / pass-through ``out0``..``out3``,
and hunt FIFOs whose contents are *not* reset. Landed SV is
hand-finished to keep those freeze semantics. Leave FEC wrap /
pack / g1 / tx / rx tops / amctl_lock / unpack for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

LANE_W = 160
PTR_W = 3
FIFO_D = 8
N_LANES = 4


@module(name="vibe_pcs_rx_deskew")
def build(m: Circuit) -> None:
    """AMCTL deskew. Factory physical=logical; no lane swap (U24).

    Product ports (hand-finished SV)::

        clk, rst_n
        in0..in3[159:0], in_vld, am0..am3
        out0..out3[159:0], out_vld, aligned

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``aligned`` is combo
    ``saw0 & saw1 & saw2 & saw3``. ``out_vld`` is combo
    ``in_vld && !(am0|am1|am2|am3)`` so AMCTL is dropped (unpack
    sees a gap between 4×640 groups). ``out0``..``out3`` are
    pass-through. On ``in_vld``, hunt FIFOs store the beat at
    ``wptr``, the first AMCTL 160b latches ``a*`` / ``saw*``,
    ``am*_r`` tracks the previous marker, and ``wptr`` advances.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    ins = [m.input(f"in{i}", width=LANE_W) for i in range(N_LANES)]
    in_vld = m.input("in_vld", width=1)
    ams = [m.input(f"am{i}", width=1) for i in range(N_LANES)]

    wptr = m.out("wptr", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    a = [
        m.out(f"a{i}", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
        for i in range(N_LANES)
    ]
    saw = [
        m.out(f"saw{i}", clk=clk, rst=rst, width=1, init=u(1, 0))
        for i in range(N_LANES)
    ]
    am_r = [
        m.out(f"am{i}_r", clk=clk, rst=rst, width=1, init=u(1, 0))
        for i in range(N_LANES)
    ]

    # Product RAM: f0..f3[wptr] <= in* when in_vld. Contents are *not*
    # cleared on reset (hand-finished SV). Cells exist so the frontend
    # can elaborate the hunt array; factory physical=logical never
    # reads them onto out*.
    for lane in range(N_LANES):
        for slot in range(FIFO_D):
            cell = m.out(
                f"f{lane}_{slot}",
                clk=clk,
                rst=rst,
                width=LANE_W,
                init=u(LANE_W, 0),
            )
            cell.set(ins[lane], when=in_vld & (wptr.out() == slot))

    aligned = saw[0].out() & saw[1].out() & saw[2].out() & saw[3].out()
    any_am = ams[0] | ams[1] | ams[2] | ams[3]
    out_vld = in_vld & ~any_am

    # Latch delay on the first AMCTL 160b only. The second word would
    # shift the pointer so the next data beat reads AMCTL out of the FIFO.
    for i in range(N_LANES):
        first = in_vld & ams[i] & ~am_r[i].out()
        a[i].set(wptr.out(), when=first)
        saw[i].set(u(1, 1), when=first)
        am_r[i].set(ams[i], when=in_vld)

    wptr.set(wptr.out() + 1, when=in_vld)

    for i in range(N_LANES):
        m.output(f"out{i}", ins[i])
    m.output("out_vld", out_vld)
    m.output("aligned", aligned)


build.__pycircuit_name__ = "vibe_pcs_rx_deskew"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_rx_deskew").emit_mlir())
