"""vibe_bcrc — DLL BCRC CRC30 (AS-0.1 §12).

Product module: ``rtl/dll/vibe_bcrc.sv``. Ports match tip
``1e57f2a5`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``start`` / ``in_vld`` /
160b ``in_flit`` / ``last`` / ``error_flag`` / 32b ``crc_word`` /
``done``). First DLL leaf after PCS leaf cells (stage-1..19).
CRC30 init all-1s; no invert. On ``last`` emit
``{1'b0, error_flag, crc[29:0]}`` (bit31 reserved, bit30
``ERROR_FLAG``). Self-contained (no child instances). Unit helper
(TB ``u_bcrc``); ``vibe_dll_tx`` inlines the same CRC30.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"`` for ``VIBE_BCRC_POLY``, ``crc30_step``,
and the 160-bit eat loop when ``in_vld``. Landed SV is hand-finished
to keep those freeze semantics. Leave PCS tx / rx tops and the rest
of DLL for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

CRC_W = 30
FLIT_W = 160
WORD_W = 32
# vibe_ub_params.vh VIBE_BCRC_POLY — AS-0.1 §12
# x^30+x^28+x^26+x^24+x^23+x^21+x^19+x^16+x^14+x^11+x^9+x^7+x^6+x^4+x^2+1
VIBE_BCRC_POLY = 0x15A94AD5
CRC_INIT = (1 << CRC_W) - 1


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _crc30_step(m: Circuit, c, b):
    """One CRC30 step: ``{c[28:0], 1'b0} ^ ({30{c[29]^b}} & POLY)``."""
    fb = c[29] ^ b
    shl = m.cat(c.slice(lsb=0, width=29), u(1, 0))
    return shl ^ (_widen(m, fb, CRC_W) & u(CRC_W, VIBE_BCRC_POLY))


def _crc30_flit(m: Circuit, c, flit):
    """Eat 160 flit bits LSB-first (stock ``for (i = 0; i < 160)``)."""
    t = c
    for i in range(FLIT_W):
        t = _crc30_step(m, t, flit.slice(lsb=i, width=1))
    return t


@module(name="vibe_bcrc")
def build(m: Circuit) -> None:
    """BCRC CRC30 over 160b flits; last word packs ERROR_FLAG.

    Product ports (hand-finished SV)::

        clk, rst_n, start, in_vld, in_flit[159:0], last, error_flag
        crc_word[31:0], done

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``start`` reloads all-1s
    and wins over ``in_vld`` (stock ``if / else if``). ``done`` is
    a 1-cycle pulse: NBA default 0, last-wins 1 on ``in_vld && last``.
    ``crc_word`` is ``{1'b0, error_flag, t}`` with no invert.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    start = m.input("start", width=1)
    in_vld = m.input("in_vld", width=1)
    in_flit = m.input("in_flit", width=FLIT_W)
    last = m.input("last", width=1)
    error_flag = m.input("error_flag", width=1)

    crc = m.out("crc", clk=clk, rst=rst, width=CRC_W, init=u(CRC_W, CRC_INIT))
    crc_word = m.out(
        "crc_word", clk=clk, rst=rst, width=WORD_W, init=u(WORD_W, 0)
    )
    done = m.out("done", clk=clk, rst=rst, width=1, init=u(1, 0))

    t = _crc30_flit(m, crc.out(), in_flit)
    eat = in_vld & ~start

    # start first; in_vld is else-if so start wins (stock).
    crc.set(u(CRC_W, CRC_INIT), when=start)
    crc.set(t, when=eat)

    crc_word.set(m.cat(u(1, 0), error_flag, t), when=eat & last)

    # done <= 0 every cycle; last-wins 1 on the last flit NBA.
    done.set(u(1, 0))
    done.set(u(1, 1), when=eat & last)

    m.output("crc_word", crc_word.out())
    m.output("done", done.out())


build.__pycircuit_name__ = "vibe_bcrc"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_bcrc").emit_mlir())
