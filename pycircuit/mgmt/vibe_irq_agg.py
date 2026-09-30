"""vibe_irq_agg — sticky OR of observable errors (AS-0.1 §10/§15).

Product module: ``rtl/mgmt/vibe_irq_agg.sv``. Ports match tip
``7dbac272`` / current main ``7969257`` (TB-only #232 on top;
RTL body unchanged). Decision I UNFROZEN (do not re-pin freeze).
SPEC / CR-B names are unchanged. Internal leaf
(``clk`` / ``rst_n`` / ``irq_clr`` / 4b ``rx_ovf`` / 4b
``fc_ovf`` / 4b ``proto_err`` / 4b ``retry_error`` /
``icrc_fail`` / 4b ``len_err`` / 4b ``deadlock_drop`` /
``drop_g1`` / 4b ``afifo_ovf`` / ``irq_logic``). Third mgmt
leaf after stage-38 ``vibe_rst_ctl`` and stage-39
``vibe_mgmt_byp``. Sticky OR of CDC/port-side error inputs
(``afifo_ovf``, ``rx_ovf``, … plus G1 ``drop_g1``). Clear on
``irq_clr`` or reset. Single ``irq_logic`` out; no extra
product IRQ pins and no per-cause status register. Port
Reset is **not** a clear. ``device_rst`` is OR'd into
``irq_clr`` by the ``vibe_mgmt`` wrap (held). Self-contained
(no child instances). Instantiated by ``vibe_mgmt``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and the stock sticky ``always`` (``if irq_clr / else if any``).
Landed SV is hand-finished to keep those tip semantics.
Leave ``vibe_cfg_space``, ``vibe_cna_ep``, and the
``vibe_mgmt`` / ``vibe_port`` / ``vibe_top`` wraps for later
stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4


def _or_reduce(vec, nbits: int = PORT_N):
    """Combo ``|vec``."""
    acc = vec.slice(lsb=0, width=1)
    for j in range(1, nbits):
        acc = acc | vec.slice(lsb=j, width=1)
    return acc


@module(name="vibe_irq_agg")
def build(m: Circuit) -> None:
    """Sticky OR of observable errors. Clear on ``irq_clr`` or reset.

    Product ports (hand-finished SV)::

        clk, rst_n, irq_clr
        rx_ovf[3:0], fc_ovf[3:0], proto_err[3:0], retry_error[3:0]
        icrc_fail, len_err[3:0], deadlock_drop[3:0], drop_g1
        afifo_ovf[3:0], irq_logic

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``irq_clr`` wins over
    set (stock ``if / else if``). Any reduction-OR of the error
    inputs (or the 1-bit ``icrc_fail`` / ``drop_g1``) sets sticky.
    ``irq_logic`` is the sticky flop.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    irq_clr = m.input("irq_clr", width=1)
    rx_ovf = m.input("rx_ovf", width=PORT_N)
    fc_ovf = m.input("fc_ovf", width=PORT_N)
    proto_err = m.input("proto_err", width=PORT_N)
    retry_error = m.input("retry_error", width=PORT_N)
    icrc_fail = m.input("icrc_fail", width=1)
    len_err = m.input("len_err", width=PORT_N)
    deadlock_drop = m.input("deadlock_drop", width=PORT_N)
    drop_g1 = m.input("drop_g1", width=1)
    afifo_ovf = m.input("afifo_ovf", width=PORT_N)

    any_err = (
        _or_reduce(rx_ovf)
        | _or_reduce(fc_ovf)
        | _or_reduce(proto_err)
        | _or_reduce(retry_error)
        | icrc_fail
        | _or_reduce(len_err)
        | _or_reduce(deadlock_drop)
        | drop_g1
        | _or_reduce(afifo_ovf)
    )

    sticky = m.out("sticky", clk=clk, rst=rst, width=1, init=u(1, 0))
    # Set first; irq_clr last so it wins (stock if / else if).
    sticky.set(u(1, 1), when=any_err)
    sticky.set(u(1, 0), when=irq_clr)

    m.output("irq_logic", sticky.out())


build.__pycircuit_name__ = "vibe_irq_agg"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_irq_agg").emit_mlir())
