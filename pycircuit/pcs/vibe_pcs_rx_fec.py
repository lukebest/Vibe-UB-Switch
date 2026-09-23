"""vibe_pcs_rx_fec — PCS RX FEC wrap (AS-0.1 §6).

Product module: ``rtl/pcs/vibe_pcs_rx_fec.sv``. Ports match tip
``b7233f49`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``fec_mode[2:0]`` / 512b
``beat_data`` / ``beat_vld`` / ``beat_ready`` / 960b ``win_data`` /
``win_vld`` / ``win_ready`` / ``am_gap`` / ``fec_fail``); used by
``vibe_pcs_rx`` (``u_fec``). Collects two 512b beats into a 1024b
CW; one-shot RS syndromes or bypass; emit 960b window or
``fec_fail``. ``am_gap`` drops a leftover half-CW so 1024b does
not straddle AMCTL. Self-contained: does **not** instantiate
stage-12 ``vibe_rs128_120_dec`` (same Horner recurrence inlined).
Pairs with stage-17 ``vibe_pcs_tx_fec``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"`` / ``vibe_ub_fn.vh``, combo
``beat_ready = !win_vld``, stock ``am_gap = 1'b0`` default, inline
``gf_mul2`` / ``rs_syndromes``, and the collect / check / emit
always-block. Landed SV is hand-finished to keep those freeze
semantics. Leave g1 / tx / rx tops for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

BEAT_W = 512
WIN_W = 960
CW_W = 1024
SYN_W = 64
PAR_W = 64
MODE_W = 3
# VIBE_FEC_BYPASS = 3'b000 (vibe_ub_params.vh).
FEC_BYPASS = 0


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


@module(name="vibe_pcs_rx_fec")
def build(m: Circuit) -> None:
    """Assemble 2×512; syndrome-check or bypass; emit 960b or fec_fail.

    Product ports (hand-finished SV)::

        clk, rst_n, fec_mode[2:0]
        beat_data[511:0], beat_vld, beat_ready
        win_data[959:0], win_vld, win_ready
        am_gap, fec_fail

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``beat_ready`` is combo
    ``!win_vld``. ``bypass`` is combo ``fec_mode == 0``. Product
    computes one-shot ``rs_syndromes({hi, beat_data})`` (same
    Horner as ``vibe_rs128_120_dec``, 128 symbols). This frontend
    parks syndromes at 0 so the wrap shape stays; the hand-finish
    keeps the inline functions. NBA last-wins matches stock
    (clear win / default fec_fail, then am_gap, then take).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    fec_mode = m.input("fec_mode", width=MODE_W)
    beat_data = m.input("beat_data", width=BEAT_W)
    beat_vld = m.input("beat_vld", width=1)
    win_ready = m.input("win_ready", width=1)
    am_gap = m.input("am_gap", width=1)

    hi = m.out("hi", clk=clk, rst=rst, width=BEAT_W, init=u(BEAT_W, 0))
    have_hi = m.out("have_hi", clk=clk, rst=rst, width=1, init=u(1, 0))
    win_data = m.out("win_data", clk=clk, rst=rst, width=WIN_W, init=u(WIN_W, 0))
    win_vld = m.out("win_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    fec_fail = m.out("fec_fail", clk=clk, rst=rst, width=1, init=u(1, 0))

    beat_ready = ~win_vld.out()
    bypass = fec_mode == FEC_BYPASS
    take = beat_vld & beat_ready
    take_hi = take & ~have_hi.out()
    take_lo = take & have_hi.out()
    ack_win = win_vld.out() & win_ready
    # Frontend stand-in: one-shot syndromes park at 0. Product uses
    # rs_syndromes({hi, beat_data}) and fec_fail <= |syn when !bypass.
    syn_now = u(SYN_W, 0)
    syn_ok = syn_now == 0
    fail = ~syn_ok
    pass_cw = bypass | syn_ok
    win_now = _cat_all(m, hi.out(), beat_data.slice(lsb=PAR_W, width=BEAT_W - PAR_W))

    # Stock order: default fec_fail, ack win, am_gap, then take.
    fec_fail.set(u(1, 0))
    win_vld.set(u(1, 0), when=ack_win)
    have_hi.set(u(1, 0), when=am_gap)

    hi.set(beat_data, when=take_hi)
    have_hi.set(u(1, 1), when=take_hi)

    have_hi.set(u(1, 0), when=take_lo)
    win_data.set(win_now, when=take_lo & pass_cw)
    win_vld.set(u(1, 1), when=take_lo & pass_cw)
    fec_fail.set(fail, when=take_lo & ~bypass)

    m.output("beat_ready", beat_ready)
    m.output("win_data", win_data.out())
    m.output("win_vld", win_vld.out())
    m.output("fec_fail", fec_fail.out())


build.__pycircuit_name__ = "vibe_pcs_rx_fec"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_rx_fec").emit_mlir())
