"""vibe_pcs_tx_cw2beat — 1024b codeword as two 512b beats (AS-0.1 §5 T4).

Product module: ``rtl/pcs/vibe_pcs_tx_cw2beat.sv``. Ports match tip
``c8804c0`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Streaming helper (``clk`` / ``rst_n`` / ready-valid 1024 in, 512 out);
used by ``vibe_pcs_tx`` (``u_cw``). First beat is ``cw_data[1023:512]``,
second is ``cw_data[511:0]``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and combo ``cw_ready`` / ``beat_vld`` / ``beat_data``. Landed SV is
hand-finished to keep those freeze semantics. Leave ``vibe_pcs_tx`` /
amctl / pack / FEC / RS / rx for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

CW_W = 1024
BEAT_W = 512


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _mux(m: Circuit, sel_bit, a, b):
    """Combo ``sel_bit ? a : b`` via bitwise mask."""
    mask = _widen(m, sel_bit, BEAT_W)
    return (a & mask) | (b & ~mask)


@module(name="vibe_pcs_tx_cw2beat")
def build(m: Circuit) -> None:
    """Split one 1024b codeword into two 512b beats (hi then lo).

    Product ports (hand-finished SV)::

        clk, rst_n
        cw_data[1023:0], cw_vld, cw_ready
        beat_data[511:0], beat_vld, beat_ready

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``cw_ready`` is combo
    ``!have_hi && !have_lo``. ``beat_vld`` is combo
    ``have_hi || have_lo``. ``beat_data`` is combo
    ``have_hi ? hi : lo``. Accept parks both halves; a beat handshake
    drops ``have_hi`` first, then ``have_lo``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    cw_data = m.input("cw_data", width=CW_W)
    cw_vld = m.input("cw_vld", width=1)
    beat_ready = m.input("beat_ready", width=1)

    hi = m.out("hi", clk=clk, rst=rst, width=BEAT_W, init=u(BEAT_W, 0))
    lo = m.out("lo", clk=clk, rst=rst, width=BEAT_W, init=u(BEAT_W, 0))
    have_hi = m.out("have_hi", clk=clk, rst=rst, width=1, init=u(1, 0))
    have_lo = m.out("have_lo", clk=clk, rst=rst, width=1, init=u(1, 0))

    cw_ready = ~have_hi.out() & ~have_lo.out()
    beat_vld = have_hi.out() | have_lo.out()
    beat_data = _mux(m, have_hi.out(), hi.out(), lo.out())

    accept = cw_vld & cw_ready
    take = beat_vld & beat_ready

    hi.set(cw_data.slice(lsb=512, width=BEAT_W), when=accept)
    lo.set(cw_data.slice(lsb=0, width=BEAT_W), when=accept)

    # Accept first; take last so NBA last-wins matches stock if both
    # fire (they are mutually exclusive on the combo ready/valid).
    have_hi.set(u(1, 1), when=accept)
    have_lo.set(u(1, 1), when=accept)
    have_hi.set(u(1, 0), when=take & have_hi.out())
    have_lo.set(u(1, 0), when=take & ~have_hi.out())

    m.output("cw_ready", cw_ready)
    m.output("beat_vld", beat_vld)
    m.output("beat_data", beat_data)


build.__pycircuit_name__ = "vibe_pcs_tx_cw2beat"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx_cw2beat").emit_mlir())
