"""vibe_pcs_scramble — PCS LTB/DLL scramble (AS-0.1 §5 / UB 3.2.2.4).

Product module: ``rtl/pcs/vibe_pcs_scramble.sv``. Ports match tip
``5087843`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``lane_id`` / ``seed_load`` /
``en`` / ready-less 160b in/out); used by ``vibe_pcs_tx``
(``u_s0``..``u_s3``) and ``vibe_pcs_rx`` (``u_d0``..``u_d3``).
Same poly + seed as PMA PRBS23 (``{19'd1, lid, 2'b01}``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
combo 160b ``xmask`` from the current LFSR, and last-NBA-wins when
``seed_load`` and ``in_vld && en`` both fire (advance wins). Landed
SV is hand-finished to keep those freeze semantics. Leave
``vibe_pcs_tx`` / rx / FEC / RS for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

SCR_W = 23
LANE_W = 160
RESET_SEED = 0x1  # {21'd0, 2'b01}


def _lfsr_step(m: Circuit, s):
    """One LFSR step: ``{s[21:0], s[22] ^ s[17]}``. ``m.cat`` is MSB-first."""
    return m.cat(s.slice(lsb=0, width=22), s[22] ^ s[17])


def _xmask160(m: Circuit, s):
    """160b window: bit *i* is LFSR[0] after *i* steps (LSB first)."""
    t = s
    bits = []
    for _ in range(LANE_W):
        bits.append(t[0])
        t = _lfsr_step(m, t)
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


def _adv160(m: Circuit, s):
    t = s
    for _ in range(LANE_W):
        t = _lfsr_step(m, t)
    return t


@module(name="vibe_pcs_scramble")
def build(m: Circuit) -> None:
    """Scramble LTB/DLL 160b; pass-through AMCTL/EEIB when ``en=0``.

    Product ports (hand-finished SV)::

        clk, rst_n, lane_id[1:0], seed_load, en
        in_vld, in_data[159:0]
        out_vld, out_data[159:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``xmask`` is combo from
    the current LFSR (used this cycle). ``en=0`` passes ``in_data``
    and does not step the LFSR. Seed is ``{19'd1, lane_id, 2'b01}``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    lane_id = m.input("lane_id", width=2)
    seed_load = m.input("seed_load", width=1)
    en = m.input("en", width=1)
    in_vld = m.input("in_vld", width=1)
    in_data = m.input("in_data", width=LANE_W)

    lfsr = m.out("lfsr", clk=clk, rst=rst, width=SCR_W, init=u(SCR_W, RESET_SEED))
    out_vld = m.out("out_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    out_data = m.out(
        "out_data", clk=clk, rst=rst, width=LANE_W, init=u(LANE_W, 0)
    )

    # {19'd1, lane_id, 2'b01} — same seed as PMA PRBS23 / issue #115.
    seed = m.cat(u(19, 1), lane_id, u(2, 1))
    xmask = _xmask160(m, lfsr.out())
    nxt = _adv160(m, lfsr.out())

    # seed_load first; in_vld&&en last so NBA last-wins matches stock
    # (advance from the *current* LFSR, not the seed loaded this cycle).
    lfsr.set(seed, when=seed_load)
    lfsr.set(nxt, when=in_vld & en)

    out_vld.set(in_vld)
    out_data.set(in_data ^ xmask, when=in_vld & en)
    out_data.set(in_data, when=in_vld & ~en)

    m.output("out_vld", out_vld.out())
    m.output("out_data", out_data.out())


build.__pycircuit_name__ = "vibe_pcs_scramble"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_scramble").emit_mlir())
