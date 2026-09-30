"""vibe_rst_ctl — device / port reset stretch (AS-0.1.2 §10).

Product module: ``rtl/mgmt/vibe_rst_ctl.sv``. Ports match tip
``0587aaee`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``device_rst_pulse`` /
4b ``port_rst_pulse`` / ``device_rst`` / 4b ``port_rst``).
First mgmt leaf (``pycircuit/mgmt`` was stub-only). A
write-1 pulse starts an 8-cycle stretch (load ``3'd7``,
count down; hold clears when the counter is ``3'd1``).
Device reset clears RW config (CNA unwritten) and MUST
NOT force DLL_Disabled (LMSM → Link_Idle). Port Reset is
RW1C in ``vibe_cfg_space`` (stored bit = 1 while this
hold is active); HW returns the readable bit to 0 when
this hold ends. Port p only: LMSM Link_Idle,
DLL_Disabled, retry ptrs 0, NumFreeBuf=256. Not an
``irq_agg`` clear. Self-contained (no child instances).
Instantiated by ``vibe_mgmt``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and the stock stretch ``always`` (``integer i`` / ``pct[0:3]``).
Landed SV is hand-finished to keep those freeze semantics.
Leave ``vibe_cfg_space``, ``vibe_cna_ep``, ``vibe_irq_agg``,
``vibe_mgmt_byp``, and the ``vibe_mgmt`` wrap for later
stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
CNT_W = 3
STRETCH = 7


@module(name="vibe_rst_ctl")
def build(m: Circuit) -> None:
    """Device / port reset stretch. Pulse loads hold + ``3'd7``.

    Product ports (hand-finished SV)::

        clk, rst_n, device_rst_pulse, port_rst_pulse[3:0]
        device_rst, port_rst[3:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Pulse wins over
    countdown (stock ``if / else if``). Hold clears when the
    live counter is ``3'd1``. ``device_rst`` / ``port_rst``
    are the hold flops.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    device_rst_pulse = m.input("device_rst_pulse", width=1)
    port_rst_pulse = m.input("port_rst_pulse", width=PORT_N)

    dhold = m.out("dhold", clk=clk, rst=rst, width=1, init=u(1, 0))
    dct = m.out("dct", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))

    # Countdown first; pulse last so it wins (stock if/else if).
    dct.set(dct.out() - u(CNT_W, 1), when=dct.out() != 0)
    dhold.set(u(1, 0), when=dct.out() == 1)
    dhold.set(u(1, 1), when=device_rst_pulse)
    dct.set(u(CNT_W, STRETCH), when=device_rst_pulse)

    phold_bits = []
    for i in range(PORT_N):
        pulse_i = port_rst_pulse.slice(lsb=i, width=1)
        ph = m.out(f"phold_{i}", clk=clk, rst=rst, width=1, init=u(1, 0))
        pc = m.out(f"pct_{i}", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
        pc.set(pc.out() - u(CNT_W, 1), when=pc.out() != 0)
        ph.set(u(1, 0), when=pc.out() == 1)
        ph.set(u(1, 1), when=pulse_i)
        pc.set(u(CNT_W, STRETCH), when=pulse_i)
        phold_bits.append(ph.out())

    port_rst = phold_bits[0]
    for i in range(1, PORT_N):
        port_rst = m.cat(phold_bits[i], port_rst)

    m.output("device_rst", dhold.out())
    m.output("port_rst", port_rst)


build.__pycircuit_name__ = "vibe_rst_ctl"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_rst_ctl").emit_mlir())
