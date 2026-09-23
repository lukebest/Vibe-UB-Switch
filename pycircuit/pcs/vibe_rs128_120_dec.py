"""vibe_rs128_120_dec — RS(128,120) syndrome-check decoder, GF(256).

Product module: ``rtl/pcs/vibe_rs128_120_dec.sv``. Ports match tip
``984e3b9`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``start`` / ``in_vld`` /
``in_sym`` / ``in_ready`` / ``done`` / ``fec_fail`` / 960b
``data_out``); paired with stage-11 ``vibe_rs128_120_enc``.
``vibe_pcs_rx_fec`` uses the same Horner recurrence in one shot
(not an instance). AS-0.1 §6: nonzero syndrome → ``fec_fail``
(Go-Back-N). T=2 check is syndrome-only (no error locator).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_fn.vh"``, combo next-syndromes (last symbol
included before ``fec_fail``), and ``msg[0:119]`` pack into
``data_out``. Landed SV is hand-finished to keep those freeze
semantics. Leave FEC wrap / pack / g1 / tx / rx / amctl_lock /
deskew / unpack for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

SYM_W = 8
CNT_W = 8
CW_N = 128
MSG_N = 120
DATA_W = MSG_N * SYM_W  # 960

# Horner multipliers α^i = 2^i (ns0 is just XOR; ns1 is gf_mul2).
ALPHA = (1, 2, 4, 8, 16, 32, 64, 128)


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _mux(m: Circuit, sel_bit, a, b):
    """Combo ``sel_bit ? a : b`` via bitwise mask."""
    mask = _widen(m, sel_bit, SYM_W)
    return (a & mask) | (b & ~mask)


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


def vibe_gf256_mul(m: Circuit, a, b):
    """Bit-serial GF(256) mul, reducing poly ``0x11D`` (``vibe_ub_fn.vh``).

    Product SV calls ``vibe_gf256_mul`` from the include. The eight
    steps here are the same ``if (bb[0]) p ^= aa`` / ``aa<<1`` xor
    ``8'h1D`` recurrence.
    """
    p = u(SYM_W, 0)
    aa = a
    bb = b
    for _ in range(SYM_W):
        p = _mux(m, bb[0], p ^ aa, p)
        shl = m.cat(aa.slice(lsb=0, width=7), u(1, 0))
        aa = _mux(m, aa[7], shl ^ u(SYM_W, 0x1D), shl)
        bb = bb >> 1
    return p


def gf_mul2(m: Circuit, a):
    """Multiply by 2 in GF(256) (stock ``gf_mul2`` / ``α^1``)."""
    shl = m.cat(a.slice(lsb=0, width=7), u(1, 0))
    return _mux(m, a[7], shl ^ u(SYM_W, 0x1D), shl)


def _or_reduce(bits, width: int):
    """OR-reduce ``width`` bits to one."""
    acc = bits[0]
    for i in range(1, width):
        acc = acc | bits[i]
    return acc


@module(name="vibe_rs128_120_dec")
def build(m: Circuit) -> None:
    """RS(128,120) syndrome-check decoder over GF(256).

    Product ports (hand-finished SV)::

        clk, rst_n, start
        in_vld, in_sym[7:0], in_ready
        done, fec_fail, data_out[959:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``in_ready`` is combo
    ``busy && (cnt < 128)``. Next syndromes are combo so the last
    symbol is included before ``fec_fail``. ``start`` clears the
    syndromes and sets ``busy`` (if/else priority over a symbol
    step). A step on the last codeword symbol (``cnt==127``) drops
    ``busy``, pulses ``done``, sets ``fec_fail`` if any next
    syndrome is nonzero, and packs ``msg[0]`` as the MSB of
    ``data_out``. Message symbols (``cnt < 120``) land in ``msg``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    start = m.input("start", width=1)
    in_vld = m.input("in_vld", width=1)
    in_sym = m.input("in_sym", width=SYM_W)

    s = [
        m.out(f"s{i}", clk=clk, rst=rst, width=SYM_W, init=u(SYM_W, 0))
        for i in range(8)
    ]
    cnt = m.out("cnt", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    busy = m.out("busy", clk=clk, rst=rst, width=1, init=u(1, 0))
    done = m.out("done", clk=clk, rst=rst, width=1, init=u(1, 0))
    fec_fail = m.out("fec_fail", clk=clk, rst=rst, width=1, init=u(1, 0))
    data_out = m.out(
        "data_out", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0)
    )
    msg = [
        m.out(f"msg_{i}", clk=clk, rst=rst, width=SYM_W, init=u(SYM_W, 0))
        for i in range(MSG_N)
    ]

    # Product: busy && (cnt < 8'd128). cnt stays 0..127 in this machine.
    in_ready = busy.out() & ~(cnt.out() == CW_N)
    # start if/else-if: a step does not share the start cycle.
    step = in_vld & in_ready & ~start
    last = step & (cnt.out() == (CW_N - 1))
    # Product stores ``msg[cnt]`` when ``cnt < 120`` (120-way hit below).

    ns0 = s[0].out() ^ in_sym
    ns1 = gf_mul2(m, s[1].out()) ^ in_sym
    ns = [ns0, ns1] + [
        vibe_gf256_mul(m, s[i].out(), u(SYM_W, ALPHA[i])) ^ in_sym
        for i in range(2, 8)
    ]

    syn_or = ns[0]
    for n in ns[1:]:
        syn_or = syn_or | n
    fail = _or_reduce(syn_or, SYM_W)

    # Step first; start last so NBA last-wins matches stock if/else.
    for i in range(8):
        s[i].set(ns[i], when=step)
        s[i].set(u(SYM_W, 0), when=start)

    for i in range(MSG_N):
        hit = step & (cnt.out() == i)
        msg[i].set(in_sym, when=hit)

    cnt.set(cnt.out() + 1, when=step & ~last)
    cnt.set(u(CNT_W, 0), when=start)

    busy.set(u(1, 1), when=start)
    busy.set(u(1, 0), when=last)

    done.set(u(1, 0))
    done.set(u(1, 1), when=last)

    fec_fail.set(u(1, 0))
    fec_fail.set(fail, when=last)

    packed = _cat_all(m, *[cell.out() for cell in msg])
    data_out.set(packed, when=last)

    m.output("in_ready", in_ready)
    m.output("done", done.out())
    m.output("fec_fail", fec_fail.out())
    m.output("data_out", data_out.out())


build.__pycircuit_name__ = "vibe_rs128_120_dec"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_rs128_120_dec").emit_mlir())
