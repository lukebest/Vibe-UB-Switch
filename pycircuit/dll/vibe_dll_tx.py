"""vibe_dll_tx — DLL TX pack (AS-0.1.2 / FS-0.2.7 overlay B).

Product module: ``rtl/dll/vibe_dll_tx.sv``. Ports match tip
``dfa505a6`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``link_up`` / ``status_up`` /
``credit_low`` / ``bp_pending`` / ``drop_data`` / ``can_send`` /
``replay`` / 160b ``replay_flit`` / ``send_idle`` / ``send_req`` /
``send_ack`` / 512b ``nw_dll_data`` / ``nw_dll_vld`` /
``nw_dll_ready`` / 640b ``dll_pcs_data`` / ``dll_pcs_vld`` /
``dll_pcs_ready`` / ``wr_en`` / 160b ``wr_flit`` / ``is_null`` /
``is_retry`` / 10b ``consume_flits`` / ``consume_vld`` /
``consume_cfg0``). Eighth DLL leaf after ``vibe_bcrc`` /
``vibe_dll_credit`` / ``vibe_dll_sm`` / ``vibe_dll_rx`` /
``vibe_dll_retry_ack_sm`` / ``vibe_dll_retry_buf`` /
``vibe_dll_retry_req_sm``. 512b NW byte stream → 20B flits
with cross-beat remainder (64B beat, 20B flit, rem 4B). Emit
one 640b beat (4 flits + BCRC in last 32b) when a group is
ready. Short EOP that leaves ``fq_n % 4 != 0`` is Null-padded
to the next 4-flit group (UB T2 / AS T1). Credit consume
counts data flits only. CFG0 does not consume credit.
Backpressure if credit low / retry full / REQ|WAIT dropping
data / pending >= 1024 cell. Self-contained (no child
instances). Instantiated by ``vibe_dll`` (``u_tx``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"`` for ``VIBE_BCRC_POLY``,
``include "vibe_ub_fn.vh"`` for ``vibe_nw512_flit0`` /
``vibe_pkt_bytes`` / ``vibe_lph_cfg``, the 8-deep ``fq`` /
remainder pack, CRC30 over 4 flits, and EOP Null-pad. Landed
SV is hand-finished to keep those freeze semantics. Leave
PCS tx / rx tops, ``vibe_dll`` top, and ``vibe_fabric`` top
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

NW_W = 512
PCS_W = 640
FLIT_W = 160
FQ_N = 8
FQ_W = 4
REM_W = 5
LEFT_W = 16
NFLIT_W = 3
CONS_W = 10
VAL_W = 7
TOT_W = 8
CRC_W = 30
# 512b NW beat = 64B.
BEAT_B = 64
# 20B flit.
FLIT_B = 20
# Replay beat is one flit + 480b pad.
REPLAY_PAD_W = 480


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


def _lph_cfg(f0):
    """``vibe_lph_cfg``: LPH CFG = flit[11:8]."""
    return f0.slice(lsb=8, width=4)


def _pkt_bytes(m: Circuit, flit):
    """``vibe_pkt_bytes``: ``vibe_decl_flits(PLENGTH) * 20``.

    ``PLENGTH = {flit[21:16], flit[31:24]}``. Declared flits
    ``(plen[13:10]+1-1)*32 + (plen[9:5]+1)`` clamped 1..512,
    then ``n*20``. Product SV calls ``vibe_pkt_bytes`` from
    ``vibe_ub_fn.vh``.
    """
    plen_hi = flit.slice(lsb=16, width=6)
    plen_lo = flit.slice(lsb=24, width=8)
    plen = m.cat(plen_hi, plen_lo)
    nblk_m1 = plen.slice(lsb=10, width=4)
    lastn_m1 = plen.slice(lsb=5, width=5)
    n_raw = m.cat(nblk_m1, u(5, 0)) + m.cat(u(4, 0), lastn_m1) + u(9, 1)
    n_lo = _mux(m, n_raw == 0, u(9, 1), n_raw, 9)
    n = m.cat(u(LEFT_W - 9, 0), n_lo)
    # n*20 = (n<<4) + (n<<2); product SV uses vibe_pkt_bytes.
    return m.cat(n.slice(lsb=0, width=LEFT_W - 4), u(4, 0)) + m.cat(
        n.slice(lsb=0, width=LEFT_W - 2), u(2, 0)
    )


def _div20(m: Circuit, tot):
    """``tot / 20`` for ``tot`` in 0..83 (rem 19 + val 64).

    Product SV uses ``tot_b / 8'd20``. Threshold mux is
    exact on that range (n_flits 0..4).
    """
    n = u(NFLIT_W, 0)
    n = _mux(m, tot >= 20, u(NFLIT_W, 1), n, NFLIT_W)
    n = _mux(m, tot >= 40, u(NFLIT_W, 2), n, NFLIT_W)
    n = _mux(m, tot >= 60, u(NFLIT_W, 3), n, NFLIT_W)
    n = _mux(m, tot >= 80, u(NFLIT_W, 4), n, NFLIT_W)
    return n


@module(name="vibe_dll_tx")
def build(m: Circuit) -> None:
    """512b NW → 20B flits → 640b PCS; CFG0 skip; Null-pad EOP.

    Product ports (hand-finished SV)::

        clk, rst_n, link_up, status_up, credit_low, bp_pending,
        drop_data, can_send, replay, replay_flit[159:0],
        send_idle, send_req, send_ack,
        nw_dll_data[511:0], nw_dll_vld, nw_dll_ready,
        dll_pcs_data[639:0], dll_pcs_vld, dll_pcs_ready,
        wr_en, wr_flit[159:0], is_null, is_retry,
        consume_flits[9:0], consume_vld, consume_cfg0

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Combo: ``nw_dll_ready``
    when link/status up, not credit-low / pending / drop / replay
    / AMCTL, ``can_send``, and ``fq_occ <= 4``. ``emitting`` when
    ``fq_n >= 4`` and the PCS slot is free and not AMCTL/replay.
    ``consume_vld`` is accept; ``consume_cfg0`` is SOP CFG0;
    ``consume_flits`` is ``n_flits`` this beat. Seq: ``!link_up``
    clears rem / pkt / ``fq_n`` / ``dll_pcs_vld``. Idle/Req/Ack
    emit a zero 640b beat; replay emits ``{replay_flit, 480'0}``;
    data emit takes four flits. Variable-offset rem||NW pack,
    8-deep ``fq`` enqueue + EOP Null-pad, and CRC30 over the
    group stay in the hand-finished SV.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    link_up = m.input("link_up", width=1)
    status_up = m.input("status_up", width=1)
    credit_low = m.input("credit_low", width=1)
    bp_pending = m.input("bp_pending", width=1)
    drop_data = m.input("drop_data", width=1)
    can_send = m.input("can_send", width=1)
    replay = m.input("replay", width=1)
    replay_flit = m.input("replay_flit", width=FLIT_W)
    send_idle = m.input("send_idle", width=1)
    send_req = m.input("send_req", width=1)
    send_ack = m.input("send_ack", width=1)
    nw_dll_data = m.input("nw_dll_data", width=NW_W)
    nw_dll_vld = m.input("nw_dll_vld", width=1)
    dll_pcs_ready = m.input("dll_pcs_ready", width=1)

    rem_lj = m.out("rem_lj", clk=clk, rst=rst, width=FLIT_W, init=u(FLIT_W, 0))
    rem_b = m.out("rem_b", clk=clk, rst=rst, width=REM_W, init=u(REM_W, 0))
    pkt_act = m.out("pkt_act", clk=clk, rst=rst, width=1, init=u(1, 0))
    pkt_left = m.out("pkt_left", clk=clk, rst=rst, width=LEFT_W, init=u(LEFT_W, 0))
    fq_n = m.out("fq_n", clk=clk, rst=rst, width=FQ_W, init=u(FQ_W, 0))
    dll_pcs_data = m.out(
        "dll_pcs_data", clk=clk, rst=rst, width=PCS_W, init=u(PCS_W, 0)
    )
    dll_pcs_vld = m.out("dll_pcs_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    fqs = [
        m.out(f"fq_{i}", clk=clk, rst=rst, width=FLIT_W, init=u(FLIT_W, 0))
        for i in range(FQ_N)
    ]

    ctl = send_idle | send_req | send_ack
    pcs_slot = dll_pcs_ready | ~dll_pcs_vld.out()
    emitting = (fq_n.out() >= 4) & pcs_slot & ~ctl & ~replay
    fq_occ = fq_n.out() - _mux(m, emitting, u(FQ_W, 4), u(FQ_W, 0), FQ_W)
    nw_dll_ready = (
        link_up
        & status_up
        & ~credit_low
        & ~bp_pending
        & ~drop_data
        & can_send
        & ~replay
        & ~ctl
        & (fq_occ <= 4)
    )

    sop_flit = nw_dll_data.slice(lsb=NW_W - FLIT_W, width=FLIT_W)
    sop_bytes = _pkt_bytes(m, sop_flit)
    cur_left = _mux(m, pkt_act.out(), pkt_left.out(), sop_bytes, LEFT_W)
    val_b = _mux(
        m,
        cur_left > BEAT_B,
        u(VAL_W, BEAT_B),
        cur_left.slice(lsb=0, width=VAL_W),
        VAL_W,
    )
    tot_b = m.cat(u(TOT_W - REM_W, 0), rem_b.out()) + m.cat(
        u(TOT_W - VAL_W, 0), val_b
    )
    n_flits = _div20(m, tot_b)
    n20 = _mux(m, n_flits == 1, u(TOT_W, 20), u(TOT_W, 0), TOT_W)
    n20 = _mux(m, n_flits == 2, u(TOT_W, 40), n20, TOT_W)
    n20 = _mux(m, n_flits == 3, u(TOT_W, 60), n20, TOT_W)
    n20 = _mux(m, n_flits == 4, u(TOT_W, 80), n20, TOT_W)
    new_rem_b = tot_b - n20

    is_null = send_idle
    is_retry = send_req | send_ack
    wr_en = emitting & ~is_null & ~is_retry
    wr_flit = fqs[0].out()
    consume_cfg0 = ~pkt_act.out() & (_lph_cfg(sop_flit) == 0)
    consume_flits = m.cat(u(CONS_W - NFLIT_W, 0), n_flits)
    consume_vld = nw_dll_vld & nw_dll_ready

    # Prototype PCS beat: four flits, CRC word left 0. Product SV
    # runs crc30_flit over fq[0..3] and packs {0,0,crc3} in the
    # last 32b (``include vibe_ub_params.vh`` VIBE_BCRC_POLY).
    pcs_beat = m.cat(
        fqs[0].out(),
        fqs[1].out(),
        fqs[2].out(),
        fqs[3].out().slice(lsb=32, width=FLIT_W - 32),
        u(32, 0),
    )
    replay_beat = m.cat(replay_flit, u(REPLAY_PAD_W, 0))

    accept = nw_dll_vld & nw_dll_ready
    val_left = m.cat(u(LEFT_W - VAL_W, 0), val_b)
    eop = accept & (cur_left <= val_left)
    mid = accept & ~eop
    ctl_slot = ctl & pcs_slot
    replay_slot = ~ctl & replay & pcs_slot
    ack_pcs = dll_pcs_vld.out() & dll_pcs_ready
    link_clear = ~link_up

    # Stock order: emit-shift fq, then AMCTL / replay / data /
    # deassert vld, then accept rem/pkt. !link_up last so it
    # wins (clears rem / pkt / fq_n / vld; leaves fq data and
    # dll_pcs_data). Entity rst is async-low in the product SV.
    for i in range(4):
        fqs[i].set(fqs[i + 4].out(), when=emitting)
    for i in range(4, FQ_N):
        fqs[i].set(u(FLIT_W, 0), when=emitting)
    fq_n.set(fq_n.out() - u(FQ_W, 4), when=emitting)

    dll_pcs_data.set(u(PCS_W, 0), when=ctl_slot)
    dll_pcs_vld.set(u(1, 1), when=ctl_slot)
    dll_pcs_data.set(replay_beat, when=replay_slot)
    dll_pcs_vld.set(u(1, 1), when=replay_slot)
    dll_pcs_data.set(pcs_beat, when=emitting)
    dll_pcs_vld.set(u(1, 1), when=emitting)
    dll_pcs_vld.set(u(1, 0), when=~ctl & ~replay & ~emitting & ack_pcs)

    rem_lj.set(u(FLIT_W, 0), when=eop)
    rem_b.set(u(REM_W, 0), when=eop)
    pkt_act.set(u(1, 0), when=eop)
    pkt_left.set(u(LEFT_W, 0), when=eop)
    pkt_act.set(u(1, 1), when=mid)
    pkt_left.set(cur_left - val_left, when=mid)
    rem_b.set(new_rem_b.slice(lsb=0, width=REM_W), when=mid)
    # new_rem_lj is stream<<(n_flits*160)[671:512] in product SV.

    rem_lj.set(u(FLIT_W, 0), when=link_clear)
    rem_b.set(u(REM_W, 0), when=link_clear)
    pkt_act.set(u(1, 0), when=link_clear)
    pkt_left.set(u(LEFT_W, 0), when=link_clear)
    fq_n.set(u(FQ_W, 0), when=link_clear)
    dll_pcs_vld.set(u(1, 0), when=link_clear)

    m.output("nw_dll_ready", nw_dll_ready)
    m.output("dll_pcs_data", dll_pcs_data.out())
    m.output("dll_pcs_vld", dll_pcs_vld.out())
    m.output("wr_en", wr_en)
    m.output("wr_flit", wr_flit)
    m.output("is_null", is_null)
    m.output("is_retry", is_retry)
    m.output("consume_flits", consume_flits)
    m.output("consume_vld", consume_vld)
    m.output("consume_cfg0", consume_cfg0)


build.__pycircuit_name__ = "vibe_dll_tx"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_tx").emit_mlir())
