"""vibe_pcs_tx_pack — PCS TX pack (AS-0.1 §5 T5 G2).

Product module: ``rtl/pcs/vibe_pcs_tx_pack.sv``. Ports match tip
``ee5e8f4`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``sdf_period`` / ``afifo_afull``
/ 512b ``beat_data`` / ``beat_vld`` / ``beat_ready`` / 4×160b
``lane0``..``lane3`` / ``lane_vld`` / ``lane_ready`` / ``am_word``);
used by ``vibe_pcs_tx`` (``u_pack``). AMCTL on the 640 (SDF) / 512
symbol timer; ``am_phase`` 0/1/2; pack 5×512 → emit 4×640. Inverse
of stage-15 ``vibe_pcs_rx_unpack``. Instantiates stage-10
``vibe_pcs_tx_amctl`` ×4 (``u_am0``..``u_am3``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"``, four ``vibe_pcs_tx_amctl`` instances,
combo ``beat_ready`` / ``lane_vld`` / ``am_word`` / lane mux, and the
timer / pack / emit always-block. Landed SV is hand-finished to keep
those freeze semantics. Leave FEC wrap / g1 / tx / rx tops for later
stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

BEAT_W = 512
LANE_W = 160
GROUP_W = 640
ACC_W = 2560
AM_W = 320
SYM_W = 10
PHASE_W = 2
CNT_W = 3
EMIT_W = 2
PERIOD_SDF = 640
PERIOD_OTH = 512
SYM_PER_BEAT = 16


def _widen(m: Circuit, bit, width: int):
    """Replicate a 1-bit hit to ``width`` (MSB-first ``m.cat``)."""
    acc = bit
    for _ in range(width - 1):
        acc = m.cat(bit, acc)
    return acc


def _mux(m: Circuit, sel_bit, a, b, width: int):
    """Combo ``sel_bit ? a : b`` via bitwise mask."""
    mask = _widen(m, sel_bit, width)
    return (a & mask) | (b & ~mask)


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


def _pack_write(m: Circuit, pack, beat_data, slot: int):
    """``pack[512*slot +: 512] = beat_data`` (keep the other slices)."""
    lo = slot * BEAT_W
    hi = ACC_W - (slot + 1) * BEAT_W
    parts = []
    if hi:
        parts.append(pack.slice(lsb=(slot + 1) * BEAT_W, width=hi))
    parts.append(beat_data)
    if lo:
        parts.append(pack.slice(lsb=0, width=lo))
    return parts[0] if len(parts) == 1 else _cat_all(m, *parts)


def _emit_lane(m: Circuit, pack, emit_idx, offset: int):
    """``pack[640*emit_idx + offset + 159 -: 160]``."""
    s0 = pack.slice(lsb=0 * GROUP_W + offset, width=LANE_W)
    s1 = pack.slice(lsb=1 * GROUP_W + offset, width=LANE_W)
    s2 = pack.slice(lsb=2 * GROUP_W + offset, width=LANE_W)
    s3 = pack.slice(lsb=3 * GROUP_W + offset, width=LANE_W)
    e0 = emit_idx == 0
    e1 = emit_idx == 1
    e2 = emit_idx == 2
    return _mux(
        m,
        e0,
        s0,
        _mux(m, e1, s1, _mux(m, e2, s2, s3, LANE_W), LANE_W),
        LANE_W,
    )


@module(name="vibe_pcs_tx_pack")
def build(m: Circuit) -> None:
    """Insert AMCTL and pack 5×512 beats into 4×640 lane words (G2).

    Product ports (hand-finished SV)::

        clk, rst_n, sdf_period, afifo_afull
        beat_data[511:0], beat_vld, beat_ready
        lane0..lane3[159:0], lane_vld, lane_ready, am_word

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``beat_ready`` is combo
    ``!afifo_afull && lane_ready && (am_phase==0) && !pack_vld``.
    ``lane_vld`` is combo ``(am_phase!=0) || pack_vld``. ``am_word``
    is combo ``am_phase!=0``. ``insert_am`` is ``sym_cnt >=`` 640
    (SDF) / 512 (other). Product instantiates ``vibe_pcs_tx_amctl``
    ×4; this frontend parks AM words at 0 so the lane mux shape
    stays. NBA last-wins matches stock (AM phase, then take, then
    emit).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    sdf_period = m.input("sdf_period", width=1)
    afifo_afull = m.input("afifo_afull", width=1)
    beat_data = m.input("beat_data", width=BEAT_W)
    beat_vld = m.input("beat_vld", width=1)
    lane_ready = m.input("lane_ready", width=1)

    # Stock acc is reset-only (unused). Keep it so the leaf matches.
    acc = m.out("acc", clk=clk, rst=rst, width=GROUP_W, init=u(GROUP_W, 0))
    pack = m.out("pack", clk=clk, rst=rst, width=ACC_W, init=u(ACC_W, 0))
    acc_n = m.out("acc_n", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    pack_vld = m.out("pack_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    emit_idx = m.out("emit_idx", clk=clk, rst=rst, width=EMIT_W, init=u(EMIT_W, 0))
    am_phase = m.out("am_phase", clk=clk, rst=rst, width=PHASE_W, init=u(PHASE_W, 0))
    sym_cnt = m.out("sym_cnt", clk=clk, rst=rst, width=SYM_W, init=u(SYM_W, 0))

    ph0 = am_phase.out() == 0
    ph1 = am_phase.out() == 1
    ph2 = am_phase.out() == 2
    n0 = acc_n.out() == 0
    n1 = acc_n.out() == 1
    n2 = acc_n.out() == 2
    n3 = acc_n.out() == 3
    n4 = acc_n.out() == 4

    insert_am = (sdf_period & (sym_cnt.out() >= PERIOD_SDF)) | (
        ~sdf_period & (sym_cnt.out() >= PERIOD_OTH)
    )
    beat_ready = ~afifo_afull & lane_ready & ph0 & ~pack_vld.out()
    take = beat_vld & beat_ready
    completing = take & n4
    start_am = insert_am & ph0 & ~pack_vld.out() & ~completing
    am_go = lane_ready & ~afifo_afull
    adv_am1 = ph1 & am_go
    adv_am2 = ph2 & am_go
    emit = pack_vld.out() & lane_ready & ph0 & ~afifo_afull
    e3 = emit_idx.out() == 3

    # Stock order: AM phase, then take, then emit (NBA last-wins).
    am_phase.set(u(PHASE_W, 1), when=start_am)
    am_phase.set(u(PHASE_W, 2), when=adv_am1)
    am_phase.set(u(PHASE_W, 0), when=adv_am2)
    sym_cnt.set(u(SYM_W, 0), when=adv_am2)

    pack.set(_pack_write(m, pack.out(), beat_data, 0), when=take & n0)
    pack.set(_pack_write(m, pack.out(), beat_data, 1), when=take & n1)
    pack.set(_pack_write(m, pack.out(), beat_data, 2), when=take & n2)
    pack.set(_pack_write(m, pack.out(), beat_data, 3), when=take & n3)
    pack.set(_pack_write(m, pack.out(), beat_data, 4), when=take & n4)
    acc_n.set(acc_n.out() + 1, when=take & ~n4)
    acc_n.set(u(CNT_W, 0), when=take & n4)
    pack_vld.set(u(1, 1), when=take & n4)
    emit_idx.set(u(EMIT_W, 0), when=take & n4)
    sym_cnt.set(sym_cnt.out() + SYM_PER_BEAT, when=take & ~insert_am)

    pack_vld.set(u(1, 0), when=emit & e3)
    emit_idx.set(u(EMIT_W, 0), when=emit & e3)
    emit_idx.set(emit_idx.out() + 1, when=emit & ~e3)

    # Product instantiates vibe_pcs_tx_amctl ×4. Frontend AM words stay 0.
    am0 = u(AM_W, 0)
    am1 = u(AM_W, 0)
    am2 = u(AM_W, 0)
    am3 = u(AM_W, 0)
    pack_l0 = _emit_lane(m, pack.out(), emit_idx.out(), 0)
    pack_l1 = _emit_lane(m, pack.out(), emit_idx.out(), LANE_W)
    pack_l2 = _emit_lane(m, pack.out(), emit_idx.out(), 2 * LANE_W)
    pack_l3 = _emit_lane(m, pack.out(), emit_idx.out(), 3 * LANE_W)

    def _am_or_pack(am, pack_lane):
        return _mux(
            m,
            ph1,
            am.slice(lsb=LANE_W, width=LANE_W),
            _mux(m, ph2, am.slice(lsb=0, width=LANE_W), pack_lane, LANE_W),
            LANE_W,
        )

    # acc is reset-only in stock (no sequential update). Touch so
    # the frontend keeps the cell.
    _ = acc

    m.output("beat_ready", beat_ready)
    m.output("lane0", _am_or_pack(am0, pack_l0))
    m.output("lane1", _am_or_pack(am1, pack_l1))
    m.output("lane2", _am_or_pack(am2, pack_l2))
    m.output("lane3", _am_or_pack(am3, pack_l3))
    m.output("lane_vld", ~ph0 | pack_vld.out())
    m.output("am_word", ~ph0)


build.__pycircuit_name__ = "vibe_pcs_tx_pack"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx_pack").emit_mlir())
