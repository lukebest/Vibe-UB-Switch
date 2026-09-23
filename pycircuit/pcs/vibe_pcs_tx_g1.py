"""vibe_pcs_tx_g1 — PCS TX G1 (AS-0.1 §5 T2).

Product module: ``rtl/pcs/vibe_pcs_tx_g1.sv``. Ports match tip
``24f7239a`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``link_up`` / 640b ``in_data`` /
``in_vld`` / ``in_ready`` / 960b ``win_data`` / ``win_vld`` /
``win_ready``); used by ``vibe_pcs_tx`` (``u_g1``). Collect 6 flits
into a 960b FEC window (640b = 4 flits → 1.5 beats + 320b rem).
Idle Null Block fill when ``link_up``. Self-contained (no child
instances). After stage-17 ``vibe_pcs_tx_fec`` / stage-18
``vibe_pcs_rx_fec``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
combo ``in_ready`` / ``win_data`` / ``win_vld``, ``NULL_FLIT = 160'd0``,
and the collect / rem leftover / idle-fill always-block. Landed SV
is hand-finished to keep those freeze semantics. Leave tx / rx tops
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

IN_W = 640
WIN_W = 960
REM_W = 320
NFLIT_W = 3
# 0,2,4,6 collected in the current window (pairs of 2 from rem).
NFLIT0 = 0
NFLIT4 = 4
NFLIT6 = 6


@module(name="vibe_pcs_tx_g1")
def build(m: Circuit) -> None:
    """Collect 6 flits / 960b FEC window; rem leftover; idle Null fill.

    Product ports (hand-finished SV)::

        clk, rst_n, link_up
        in_data[639:0], in_vld, in_ready
        win_data[959:0], win_vld, win_ready

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``in_ready`` is combo
    ``link_up && (!have || win_ready) && !((nflit >= 4) && rem_vld)``.
    ``win_data`` / ``win_vld`` are combo ``acc`` / ``have``.
    ``NULL_FLIT`` is 160'd0 (CFG=0, CLENGTH=0). NBA last-wins
    matches stock (ack window, then take 4+2, else rem leftover,
    else 2-Null complete, else idle 6-Null fill).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    link_up = m.input("link_up", width=1)
    in_data = m.input("in_data", width=IN_W)
    in_vld = m.input("in_vld", width=1)
    win_ready = m.input("win_ready", width=1)

    rem = m.out("rem", clk=clk, rst=rst, width=REM_W, init=u(REM_W, 0))
    rem_vld = m.out("rem_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    nflit = m.out("nflit", clk=clk, rst=rst, width=NFLIT_W, init=u(NFLIT_W, 0))
    acc = m.out("acc", clk=clk, rst=rst, width=WIN_W, init=u(WIN_W, 0))
    have = m.out("have", clk=clk, rst=rst, width=1, init=u(1, 0))

    blocked = (nflit.out() >= NFLIT4) & rem_vld.out()
    in_ready = link_up & (~have.out() | win_ready) & ~blocked
    win_data = acc.out()
    win_vld = have.out()

    ack = have.out() & win_ready
    take = in_vld & in_ready
    take_ok = take & ~rem_vld.out()
    nflit0 = nflit.out() == NFLIT0
    nflit4 = nflit.out() == NFLIT4
    take_fresh = take_ok & (nflit0 | ack)
    take_mid = take_ok & nflit4 & ~ack
    rem_fill = ~take & rem_vld.out() & ~have.out()
    idle_base = ~take & ~have.out() & ~in_vld & link_up & win_ready
    idle_2null = idle_base & nflit4
    idle_6null = idle_base & nflit0 & ~rem_vld.out()

    # Stock order: ack have/nflit, then take (fresh 4 or mid 4+2),
    # else rem leftover, else 2-Null complete, else idle 6-Null.
    have.set(u(1, 0), when=ack)
    nflit.set(u(NFLIT_W, NFLIT0), when=ack)

    acc.set(
        m.cat(in_data, acc.out().slice(lsb=0, width=REM_W)),
        when=take_fresh,
    )
    rem.set(u(REM_W, 0), when=take_fresh)
    rem_vld.set(u(1, 0), when=take_fresh)
    nflit.set(u(NFLIT_W, NFLIT4), when=take_fresh)

    acc.set(
        m.cat(
            acc.out().slice(lsb=REM_W, width=IN_W),
            in_data.slice(lsb=REM_W, width=REM_W),
        ),
        when=take_mid,
    )
    rem.set(in_data.slice(lsb=0, width=REM_W), when=take_mid)
    rem_vld.set(u(1, 1), when=take_mid)
    nflit.set(u(NFLIT_W, NFLIT6), when=take_mid)
    have.set(u(1, 1), when=take_mid)

    acc.set(m.cat(rem.out(), u(IN_W, 0)), when=rem_fill)
    rem_vld.set(u(1, 0), when=rem_fill)
    nflit.set(u(NFLIT_W, NFLIT6), when=rem_fill)
    have.set(u(1, 1), when=rem_fill)

    acc.set(
        m.cat(acc.out().slice(lsb=REM_W, width=IN_W), u(REM_W, 0)),
        when=idle_2null,
    )
    nflit.set(u(NFLIT_W, NFLIT6), when=idle_2null)
    have.set(u(1, 1), when=idle_2null)

    acc.set(u(WIN_W, 0), when=idle_6null)
    nflit.set(u(NFLIT_W, NFLIT6), when=idle_6null)
    have.set(u(1, 1), when=idle_6null)

    m.output("in_ready", in_ready)
    m.output("win_data", win_data)
    m.output("win_vld", win_vld)


build.__pycircuit_name__ = "vibe_pcs_tx_g1"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx_g1").emit_mlir())
