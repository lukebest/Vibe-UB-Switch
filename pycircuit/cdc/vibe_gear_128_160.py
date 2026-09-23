"""vibe_gear_128_160 — RX 128→160 dual-residue gearbox (AS-0.1 §6/§7).

Product module: ``rtl/cdc/vibe_gear_128_160.sv``. Ports match tip
``195d380`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ready-valid 128 in, 160 out);
used by ``vibe_port`` (``u_rg0``..``u_rg3``). 5×128 = 4×160.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and a single always-block ``case (phase)`` with combo ``in_ready``.
Landed SV is hand-finished to keep those freeze semantics. Leave
``vibe_gear_160_128`` (TX 160→128) for a later stage.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u


@module(name="vibe_gear_128_160")
def build(m: Circuit) -> None:
    """5-beat dual-residue 128→160 gearbox. Same-layer (not a CDC cell).

    Product ports (hand-finished SV)::

        clk, rst_n
        in_vld, in_ready, in_data[127:0]
        out_vld, out_ready, out_data[159:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``in_ready`` is combo
    ``!hold_vld || out_ready``. Phase 0 stores 128 into ``res_a``;
    phases 1..4 emit 160 and park the leftover in ``res_a`` / ``res_b``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    in_vld = m.input("in_vld", width=1)
    in_data = m.input("in_data", width=128)
    out_ready = m.input("out_ready", width=1)

    res_a = m.out("res_a", clk=clk, rst=rst, width=128, init=u(128, 0))
    res_b = m.out("res_b", clk=clk, rst=rst, width=128, init=u(128, 0))
    phase = m.out("phase", clk=clk, rst=rst, width=3, init=u(3, 0))
    hold = m.out("hold", clk=clk, rst=rst, width=160, init=u(160, 0))
    hold_vld = m.out("hold_vld", clk=clk, rst=rst, width=1, init=u(1, 0))

    in_ready = ~hold_vld.out() | out_ready
    accept = in_vld & in_ready

    ph0 = phase.out() == 0
    ph1 = phase.out() == 1
    ph2 = phase.out() == 2
    ph3 = phase.out() == 3
    ph4 = ~(ph0 | ph1 | ph2 | ph3)

    # Phase 0: park 128. Phases 1..4: emit 160 = leftover || new bits.
    res_a.set(in_data, when=accept & ph0)
    res_a.set(
        m.cat(u(64, 0), in_data.slice(lsb=64, width=64)),
        when=accept & ph2,
    )
    res_a.set(u(128, 0), when=accept & ph4)

    res_b.set(
        m.cat(u(32, 0), in_data.slice(lsb=32, width=96)),
        when=accept & ph1,
    )
    res_b.set(
        m.cat(u(96, 0), in_data.slice(lsb=96, width=32)),
        when=accept & ph3,
    )
    res_b.set(u(128, 0), when=accept & ph4)

    hold.set(
        m.cat(in_data.slice(lsb=0, width=32), res_a.out()),
        when=accept & ph1,
    )
    hold.set(
        m.cat(in_data.slice(lsb=0, width=64), res_b.out().slice(lsb=0, width=96)),
        when=accept & ph2,
    )
    hold.set(
        m.cat(in_data.slice(lsb=0, width=96), res_a.out().slice(lsb=0, width=64)),
        when=accept & ph3,
    )
    hold.set(
        m.cat(in_data, res_b.out().slice(lsb=0, width=32)),
        when=accept & ph4,
    )

    produce = accept & ~ph0
    hold_vld.set(produce | (hold_vld.out() & ~out_ready))

    phase.set(u(3, 1), when=accept & ph0)
    phase.set(u(3, 2), when=accept & ph1)
    phase.set(u(3, 3), when=accept & ph2)
    phase.set(u(3, 4), when=accept & ph3)
    phase.set(u(3, 0), when=accept & ph4)

    m.output("in_ready", in_ready)
    m.output("out_vld", hold_vld.out())
    m.output("out_data", hold.out())


build.__pycircuit_name__ = "vibe_gear_128_160"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_gear_128_160").emit_mlir())
