"""vibe_dll_rx — DLL RX unpack (AS-0.1.2 / FS-0.2.7 overlay B).

Product module: ``rtl/dll/vibe_dll_rx.sv``. Ports match tip
``7543c944`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``link_up`` /
``fec_fail`` / 640b ``pcs_dll_data`` / ``pcs_dll_vld`` /
``pcs_dll_ready`` / 512b ``dll_nw_data`` / ``dll_nw_vld`` /
``dll_nw_ready`` / ``cfg0_hit`` / 640b ``cfg0_data`` / ``bcrc_fail`` /
``start_retry`` / ``rx_ovf`` / ``start_ack``). Parameter ``RXBUF``
default 1024 (dll_rxbuf = 1024 flit/VL). Fourth DLL leaf after
``vibe_bcrc`` / ``vibe_dll_credit`` / ``vibe_dll_sm``. 640b PCS →
4 flits, unBCRC, pack to 512b NW with remainder. LPH is the first
160b flit. After EOP drop intra-group leftover. CFG0 terminate.
FEC/BCRC fail → Go-Back-N. ``start_ack`` tied 0 as stock.
Self-contained (no child instances). Instantiated by ``vibe_dll``
(``u_rx``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_fn.vh"`` for ``vibe_lph_cfg`` / ``vibe_lph_vl`` /
``vibe_pkt_bytes``, the 16-VL ``wptr`` / ``rptr`` (and unused
``rbuf``), and the variable byte-lane pack / emit shift. Landed SV
is hand-finished to keep those freeze semantics. Leave PCS tx / rx
tops, ``vibe_dll_retry_*``, ``vibe_dll_tx``, and ``vibe_dll`` top
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PCS_W = 640
NW_W = 512
BY_W = 1280
FLIT_W = 160
N_W = 8
LEFT_W = 16
PTR_W = 11
VL_N = 16
RXBUF = 1024
# First 20B of the 1280b lane is LPH (FS-0.2.7 overlay B).
LPH_W = 160
# 640b / 8 = 80B packed per accepted PCS beat.
PACK_B = 80
# 512b NW beat = 64B.
EMIT_B = 64
# Abort marker in the low 32b of a flushed NW beat.
ABORT_LO_W = 32


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


def _lph_vl(m: Circuit, f0):
    """``vibe_lph_vl``: ``{flit[15:13], flit[0]}``."""
    return m.cat(f0.slice(lsb=13, width=3), f0.slice(lsb=0, width=1))


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


@module(name="vibe_dll_rx")
def build(m: Circuit) -> None:
    """640b PCS → 4 flits → 512b NW; CFG0 term; FEC → GBN.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, link_up, fec_fail
        pcs_dll_data[639:0], pcs_dll_vld, pcs_dll_ready
        dll_nw_data[511:0], dll_nw_vld, dll_nw_ready
        cfg0_hit, cfg0_data[639:0], bcrc_fail, start_retry
        rx_ovf, start_ack

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``pcs_dll_ready`` /
    ``start_retry`` / ``start_ack`` are combo (``start_ack`` tied
    0). ``port_rst || !link_up`` clears have / vld / cfg0 / pkt
    and the byte lane; ``!link_up`` with leftover also emits the
    abort beat. CFG0 does not enter the flit lane. EOP drops
    intra-group leftover. Variable-offset pack / emit and the
    unused ``rbuf`` stay in the hand-finished SV.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    link_up = m.input("link_up", width=1)
    fec_fail = m.input("fec_fail", width=1)
    pcs_dll_data = m.input("pcs_dll_data", width=PCS_W)
    pcs_dll_vld = m.input("pcs_dll_vld", width=1)
    dll_nw_ready = m.input("dll_nw_ready", width=1)

    have = m.out("have", clk=clk, rst=rst, width=1, init=u(1, 0))
    hold = m.out("hold", clk=clk, rst=rst, width=PCS_W, init=u(PCS_W, 0))
    dll_nw_data = m.out("dll_nw_data", clk=clk, rst=rst, width=NW_W, init=u(NW_W, 0))
    dll_nw_vld = m.out("dll_nw_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    cfg0_hit = m.out("cfg0_hit", clk=clk, rst=rst, width=1, init=u(1, 0))
    cfg0_data = m.out("cfg0_data", clk=clk, rst=rst, width=PCS_W, init=u(PCS_W, 0))
    bcrc_fail = m.out("bcrc_fail", clk=clk, rst=rst, width=1, init=u(1, 0))
    rx_ovf = m.out("rx_ovf", clk=clk, rst=rst, width=1, init=u(1, 0))
    by_lj = m.out("by_lj", clk=clk, rst=rst, width=BY_W, init=u(BY_W, 0))
    by_n = m.out("by_n", clk=clk, rst=rst, width=N_W, init=u(N_W, 0))
    pkt_act = m.out("pkt_act", clk=clk, rst=rst, width=1, init=u(1, 0))
    pkt_left = m.out("pkt_left", clk=clk, rst=rst, width=LEFT_W, init=u(LEFT_W, 0))
    wptrs = [
        m.out(f"wptr_{i}", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
        for i in range(VL_N)
    ]

    f0 = pcs_dll_data.slice(lsb=PCS_W - FLIT_W, width=FLIT_W)
    cfg = _lph_cfg(f0)
    vl = _lph_vl(m, f0)
    is_cfg0 = cfg == 0
    idle_lane = ~have.out() & (by_n.out() == 0) & ~pkt_act.out()
    pcs_dll_ready = _mux(m, link_up, is_cfg0 | idle_lane, u(1, 1), 1)

    wptr_vl = u(PTR_W, 0)
    for i in range(VL_N):
        wptr_vl = _mux(m, vl == i, wptrs[i].out(), wptr_vl, PTR_W)
    occ_full = wptr_vl >= RXBUF

    lph = by_lj.out().slice(lsb=BY_W - LPH_W, width=LPH_W)
    hdr_bytes = _pkt_bytes(m, lph)
    need_hdr = ~pkt_act.out() & (by_n.out() >= 20)
    left_now = _mux(m, need_hdr, hdr_bytes, pkt_left.out(), LEFT_W)
    have_pkt = pkt_act.out() | need_hdr
    full_beat = have_pkt & (left_now >= EMIT_B) & (by_n.out() >= EMIT_B)
    last_beat = (
        have_pkt
        & (left_now > 0)
        & (left_now <= EMIT_B)
        & (by_n.out() >= left_now.slice(lsb=0, width=N_W))
    )
    emit_n = _mux(
        m,
        full_beat,
        u(N_W, EMIT_B),
        _mux(m, last_beat, left_now.slice(lsb=0, width=N_W), u(N_W, 0), N_W),
        N_W,
    )
    can_emit = ~(emit_n == 0) & (~dll_nw_vld.out() | dll_nw_ready)

    take = pcs_dll_vld & pcs_dll_ready
    take_cfg0 = take & is_cfg0
    take_ovf = take & ~is_cfg0 & occ_full
    take_data = take & ~is_cfg0 & ~occ_full
    pack = have.out() & (by_n.out() <= PACK_B)
    do_emit = ~pack & can_emit
    arm_hdr = ~pack & ~can_emit & need_hdr
    eop = do_emit & (left_now <= m.cat(u(LEFT_W - N_W, 0), emit_n))
    mid = do_emit & ~eop
    port_clear = port_rst | ~link_up
    flush = ~link_up & (have.out() | ~(by_n.out() == 0))
    ack_nw = dll_nw_vld.out() & dll_nw_ready

    # Stock order: pulse-clear, accept, pack / emit / arm hdr, then
    # fec_fail (bcrc_fail stays 0). port_rst / !link_up last so they
    # win. Entity rst is async-low in the product SV.
    cfg0_hit.set(u(1, 0))
    bcrc_fail.set(u(1, 0))
    dll_nw_vld.set(u(1, 0), when=ack_nw)

    cfg0_hit.set(u(1, 1), when=take_cfg0)
    cfg0_data.set(pcs_dll_data, when=take_cfg0)
    rx_ovf.set(u(1, 1), when=take_ovf)
    hold.set(pcs_dll_data, when=take_data)
    have.set(u(1, 1), when=take_data)
    for i in range(VL_N):
        wptrs[i].set(wptrs[i].out() + 4, when=take_data & (vl == i))

    # Pack at by_n==0 / 80 (empty or one 80B group). Other offsets
    # use the product SV variable shift ``({hold,640'b0} >> by_n*8)``.
    packed0 = m.cat(hold.out(), u(PCS_W, 0))
    packed80 = by_lj.out() | m.cat(u(PCS_W, 0), hold.out())
    packed = _mux(m, by_n.out() == 0, packed0, by_lj.out(), BY_W)
    packed = _mux(m, by_n.out() == PACK_B, packed80, packed, BY_W)
    by_lj.set(packed, when=pack)
    by_n.set(by_n.out() + PACK_B, when=pack)
    have.set(u(1, 0), when=pack)

    beat = by_lj.out().slice(lsb=BY_W - NW_W, width=NW_W)
    dll_nw_data.set(beat, when=do_emit)
    dll_nw_vld.set(u(1, 1), when=do_emit)
    by_lj.set(m.cat(by_lj.out().slice(lsb=0, width=BY_W - NW_W), u(NW_W, 0)), when=do_emit)
    by_n.set(by_n.out() - emit_n, when=do_emit)
    pkt_act.set(u(1, 0), when=eop)
    pkt_left.set(u(LEFT_W, 0), when=eop)
    by_lj.set(u(BY_W, 0), when=eop)
    by_n.set(u(N_W, 0), when=eop)
    pkt_act.set(u(1, 1), when=mid)
    pkt_left.set(left_now - m.cat(u(LEFT_W - N_W, 0), emit_n), when=mid)

    pkt_act.set(u(1, 1), when=arm_hdr)
    pkt_left.set(hdr_bytes, when=arm_hdr)

    bcrc_fail.set(u(1, 0), when=fec_fail)

    abort = m.cat(
        by_lj.out().slice(lsb=800, width=BY_W - 800),
        u(1, 0),
        u(1, 1),
        u(ABORT_LO_W - 2, 0),
    )
    have.set(u(1, 0), when=port_clear)
    dll_nw_vld.set(u(1, 0), when=port_clear)
    cfg0_hit.set(u(1, 0), when=port_clear)
    pkt_act.set(u(1, 0), when=port_clear)
    dll_nw_data.set(abort, when=flush)
    dll_nw_vld.set(u(1, 1), when=flush)
    by_lj.set(u(BY_W, 0), when=port_clear)
    by_n.set(u(N_W, 0), when=port_clear)
    pkt_left.set(u(LEFT_W, 0), when=port_clear)

    m.output("pcs_dll_ready", pcs_dll_ready)
    m.output("dll_nw_data", dll_nw_data.out())
    m.output("dll_nw_vld", dll_nw_vld.out())
    m.output("cfg0_hit", cfg0_hit.out())
    m.output("cfg0_data", cfg0_data.out())
    m.output("bcrc_fail", bcrc_fail.out())
    m.output("start_retry", fec_fail | bcrc_fail.out())
    m.output("rx_ovf", rx_ovf.out())
    m.output("start_ack", u(1, 0))


build.__pycircuit_name__ = "vibe_dll_rx"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_rx").emit_mlir())
