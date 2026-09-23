"""vibe_rs128_120_enc — systematic RS(128,120) encoder, GF(256).

Product module: ``rtl/pcs/vibe_rs128_120_enc.sv``. Ports match tip
``984e3b9`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``start`` / ``in_vld`` /
``in_sym`` / ``in_ready`` / ``done`` / 64b ``parity``); used by
``vibe_pcs_tx_fec`` (``u_enc_a`` / ``u_enc_b``). AS-0.1 §5 T3 /
UB 2.0 §3.2.2. Generator coefficients Table 3-2. T=2 encoding
produces the same 8 parity symbols.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_fn.vh"``, and ``vibe_gf256_mul`` for the LFSR
step. Landed SV is hand-finished to keep those freeze semantics.
Leave ``vibe_pcs_tx_fec`` / pack / g1 / tx wrap / rx / decoder
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

SYM_W = 8
CNT_W = 8
MSG_N = 120

# Table 3-2 generator coefficients (g0..g7). Product uses localparam G0..G7.
G = (24, 200, 173, 239, 54, 81, 11, 255)


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


@module(name="vibe_rs128_120_enc")
def build(m: Circuit) -> None:
    """Systematic RS(128,120) LFSR encoder over GF(256).

    Product ports (hand-finished SV)::

        clk, rst_n, start
        in_vld, in_sym[7:0], in_ready
        done, parity[63:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``in_ready`` is combo
    ``busy && (cnt < 120)`` (this machine keeps ``cnt`` in 0..120,
    so ``busy && (cnt != 120)``). ``parity`` is combo
    ``{r7,r6,r5,r4,r3,r2,r1,r0}``. ``start`` clears the LFSR and
    sets ``busy`` (if/else priority over a symbol step). A step
    on the last message symbol (``cnt==119``) drops ``busy`` and
    pulses ``done``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    start = m.input("start", width=1)
    in_vld = m.input("in_vld", width=1)
    in_sym = m.input("in_sym", width=SYM_W)

    r = [
        m.out(f"r{i}", clk=clk, rst=rst, width=SYM_W, init=u(SYM_W, 0))
        for i in range(8)
    ]
    cnt = m.out("cnt", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    busy = m.out("busy", clk=clk, rst=rst, width=1, init=u(1, 0))
    done = m.out("done", clk=clk, rst=rst, width=1, init=u(1, 0))

    # Product: busy && (cnt < 8'd120). cnt stays 0..120 in this machine.
    in_ready = busy.out() & ~(cnt.out() == MSG_N)
    # start if/else-if: a step does not share the start cycle.
    step = in_vld & in_ready & ~start
    last = step & (cnt.out() == (MSG_N - 1))
    fb = in_sym ^ r[7].out()

    mul = [vibe_gf256_mul(m, fb, u(SYM_W, g)) for g in G]
    nxt = [mul[0]] + [r[i - 1].out() ^ mul[i] for i in range(1, 8)]

    # Step first; start last so NBA last-wins matches stock if/else.
    for i in range(8):
        r[i].set(nxt[i], when=step)
        r[i].set(u(SYM_W, 0), when=start)

    cnt.set(cnt.out() + 1, when=step)
    cnt.set(u(CNT_W, 0), when=start)

    busy.set(u(1, 1), when=start)
    busy.set(u(1, 0), when=last)

    # done <= 0 every cycle, then 1 on the last message symbol.
    done.set(u(1, 0))
    done.set(u(1, 1), when=last)

    m.output("in_ready", in_ready)
    m.output("done", done.out())
    m.output(
        "parity",
        _cat_all(
            m,
            r[7].out(),
            r[6].out(),
            r[5].out(),
            r[4].out(),
            r[3].out(),
            r[2].out(),
            r[1].out(),
            r[0].out(),
        ),
    )


build.__pycircuit_name__ = "vibe_rs128_120_enc"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_rs128_120_enc").emit_mlir())
