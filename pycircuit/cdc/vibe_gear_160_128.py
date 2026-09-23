"""vibe_gear_160_128 — TX 160→128 residue gearbox (AS-0.1 §5 T7).

Product module: ``rtl/cdc/vibe_gear_160_128.sv``. Ports match tip
``cb4549f`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ready-valid 160 in, 128 out);
used by ``vibe_port`` (``u_g0``..``u_g3``). 4×160 = 5×128.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and a single always-block ``case (rbits)`` with combo ``in_ready``.
Landed SV is hand-finished to keep those freeze semantics. This is
the TX pair of stage-5 ``vibe_gear_128_160``.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u


@module(name="vibe_gear_160_128")
def build(m: Circuit) -> None:
    """4-beat residue 160→128 gearbox. Same-layer (not a CDC cell).

    Product ports (hand-finished SV)::

        clk, rst_n
        in_vld, in_ready, in_data[159:0]
        out_vld, out_ready, out_data[127:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``can_load`` is combo
    ``!hold_vld || out_ready``. ``in_ready`` is combo
    ``can_load && (rbits != 4)`` — a full 128-bit residue (rbits==4)
    emits without taking a new 160. rbits 0..4 = 0/32/64/96/128
    valid bits in ``res``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    in_vld = m.input("in_vld", width=1)
    in_data = m.input("in_data", width=160)
    out_ready = m.input("out_ready", width=1)

    res = m.out("res", clk=clk, rst=rst, width=128, init=u(128, 0))
    rbits = m.out("rbits", clk=clk, rst=rst, width=3, init=u(3, 0))
    hold = m.out("hold", clk=clk, rst=rst, width=128, init=u(128, 0))
    hold_vld = m.out("hold_vld", clk=clk, rst=rst, width=1, init=u(1, 0))

    can_load = ~hold_vld.out() | out_ready
    in_ready = can_load & ~(rbits.out() == 4)
    accept = in_vld & in_ready

    rb0 = rbits.out() == 0
    rb1 = rbits.out() == 1
    rb2 = rbits.out() == 2
    rb3 = rbits.out() == 3
    rb4 = rbits.out() == 4
    flush_res = rb4 & can_load

    # rbits==4: emit the parked 128 without taking input.
    res.set(u(128, 0), when=flush_res)
    hold.set(res.out(), when=flush_res)
    rbits.set(u(3, 0), when=flush_res)

    # rbits 0..3: take 160, emit 128, park leftover 32/64/96/128.
    res.set(
        m.cat(u(96, 0), in_data.slice(lsb=128, width=32)),
        when=accept & rb0,
    )
    res.set(
        m.cat(u(64, 0), in_data.slice(lsb=96, width=64)),
        when=accept & rb1,
    )
    res.set(
        m.cat(u(32, 0), in_data.slice(lsb=64, width=96)),
        when=accept & rb2,
    )
    res.set(in_data.slice(lsb=32, width=128), when=accept & rb3)

    hold.set(in_data.slice(lsb=0, width=128), when=accept & rb0)
    hold.set(
        m.cat(in_data.slice(lsb=0, width=96), res.out().slice(lsb=0, width=32)),
        when=accept & rb1,
    )
    hold.set(
        m.cat(in_data.slice(lsb=0, width=64), res.out().slice(lsb=0, width=64)),
        when=accept & rb2,
    )
    hold.set(
        m.cat(in_data.slice(lsb=0, width=32), res.out().slice(lsb=0, width=96)),
        when=accept & rb3,
    )

    produce = accept | flush_res
    hold_vld.set(produce | (hold_vld.out() & ~out_ready))

    rbits.set(u(3, 1), when=accept & rb0)
    rbits.set(u(3, 2), when=accept & rb1)
    rbits.set(u(3, 3), when=accept & rb2)
    rbits.set(u(3, 4), when=accept & rb3)

    m.output("in_ready", in_ready)
    m.output("out_vld", hold_vld.out())
    m.output("out_data", hold.out())


build.__pycircuit_name__ = "vibe_gear_160_128"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_gear_160_128").emit_mlir())
