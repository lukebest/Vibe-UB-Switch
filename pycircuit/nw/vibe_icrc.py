"""vibe_icrc — NW ICRC CRC32 (AS-0.1 §13).

Product module: ``rtl/nw/vibe_icrc.sv``. Ports match tip
``186dde4e`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``start`` / ``in_vld`` /
8b ``in_byte`` / ``last`` / 32b ``crc_out`` / ``done``). First
NW leaf after PCS/CDC/DLL/fabric leaves (stage-1..35). CRC32
poly ``0x04C11DB7`` init ``0xFFFFFFFF``; per-byte bit reverse
then reverse+invert. On ``last`` emit
``~vibe_rev32(step8(crc, in_byte))``. Self-contained (no
child instances). Unit helper (TB ``u_icrc``); intended for
``cna_ep`` (sender/receiver). Transit has no ICRC unit.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"`` for ``VIBE_ICRC_POLY``,
``include "vibe_ub_fn.vh"`` for ``vibe_rev8`` / ``vibe_rev32``,
and ``step8``. Landed SV is hand-finished to keep those freeze
semantics. Leave PCS tx / rx tops, ``vibe_port`` /
``vibe_ub_switch`` tops, other NW stubs, and ``vibe_fabric``
top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

CRC_W = 32
BYTE_W = 8
# vibe_ub_params.vh VIBE_ICRC_POLY — AS-0.1 §13
# x^32+x^26+x^23+x^22+x^16+x^12+x^11+x^10+x^8+x^7+x^5+x^4+x^2+x+1
VIBE_ICRC_POLY = 0x04C11DB7
CRC_INIT = (1 << CRC_W) - 1


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _rev8(m: Circuit, b):
    """Stock ``vibe_rev8``: ``result[i] = x[7-i]``."""
    acc = b.slice(lsb=0, width=1)
    for i in range(1, BYTE_W):
        acc = m.cat(acc, b.slice(lsb=i, width=1))
    return acc


def _rev32(m: Circuit, x):
    """Stock ``vibe_rev32``: ``result[i] = x[31-i]``."""
    acc = x.slice(lsb=0, width=1)
    for i in range(1, CRC_W):
        acc = m.cat(acc, x.slice(lsb=i, width=1))
    return acc


def _crc32_step(m: Circuit, c, b):
    """One CRC32 step: ``{c[30:0], 1'b0} ^ ({32{c[31]^b}} & POLY)``."""
    fb = c[31] ^ b
    shl = m.cat(c.slice(lsb=0, width=31), u(1, 0))
    return shl ^ (_widen(m, fb, CRC_W) & u(CRC_W, VIBE_ICRC_POLY))


def _step8(m: Circuit, c, b):
    """Stock ``step8``: reverse the byte, eat MSB-first of ``br``."""
    br = _rev8(m, b)
    t = c
    for k in range(BYTE_W):
        t = _crc32_step(m, t, br.slice(lsb=7 - k, width=1))
    return t


@module(name="vibe_icrc")
def build(m: Circuit) -> None:
    """ICRC CRC32 over bytes; last word is reverse+invert.

    Product ports (hand-finished SV)::

        clk, rst_n, start, in_vld, in_byte[7:0], last
        crc_out[31:0], done

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``start`` reloads all-1s
    and wins over ``in_vld`` (stock ``if / else if``). ``done`` is
    a 1-cycle pulse: NBA default 0, last-wins 1 on ``in_vld && last``.
    ``crc_out`` is ``~vibe_rev32(step8(crc, in_byte))``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    start = m.input("start", width=1)
    in_vld = m.input("in_vld", width=1)
    in_byte = m.input("in_byte", width=BYTE_W)
    last = m.input("last", width=1)

    crc = m.out("crc", clk=clk, rst=rst, width=CRC_W, init=u(CRC_W, CRC_INIT))
    crc_out = m.out(
        "crc_out", clk=clk, rst=rst, width=CRC_W, init=u(CRC_W, 0)
    )
    done = m.out("done", clk=clk, rst=rst, width=1, init=u(1, 0))

    t = _step8(m, crc.out(), in_byte)
    eat = in_vld & ~start

    # start first; in_vld is else-if so start wins (stock).
    crc.set(u(CRC_W, CRC_INIT), when=start)
    crc.set(t, when=eat)

    # Product SV: ~vibe_rev32(step8(...)). XOR-all-1s is invert.
    crc_out.set(_rev32(m, t) ^ u(CRC_W, CRC_INIT), when=eat & last)

    # done <= 0 every cycle; last-wins 1 on the last-byte NBA.
    done.set(u(1, 0))
    done.set(u(1, 1), when=eat & last)

    m.output("crc_out", crc_out.out())
    m.output("done", done.out())


build.__pycircuit_name__ = "vibe_icrc"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_icrc").emit_mlir())
