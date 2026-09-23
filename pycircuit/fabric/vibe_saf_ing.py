"""vibe_saf_ing — fabric store-and-forward ingress (AS-0.1 §8).

Product module: ``rtl/fabric/vibe_saf_ing.sv``. Ports match tip
``d8fdf91f`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``in_data[511:0]`` /
``in_vld`` / ``in_ready`` / ``pkt_data[511:0]`` / ``pkt_vld`` /
``pkt_ready`` / ``pkt_sop`` / ``pkt_eop`` / ``pkt_bytes[15:0]`` /
``len_err``). Parameter ``DEPTH`` default 128. Sixth fabric
leaf after ``vibe_fecn_mark`` / ``vibe_vl_rr`` /
``vibe_route_lu`` / ``vibe_port_sel`` / ``vibe_voq_egr``.
Do not present to xbar until EOP / full declared length.
Length not in 16–4300 B → Packet Length Error, drop, irq
(``len_err`` pulse; ``wptr`` rewound to ``rptr``).
``in_ready = (wptr+1) != rptr``. ``pkt_vld = done &&
(rptr != wptr)``. ``pkt_data = mem[rptr]``. ``pkt_sop``
when ``rptr==0 || beat_cnt==0``. ``pkt_eop`` when
``rptr+1 == wptr``. Header temps ``plen`` / ``dflits``
are combo (``vibe_lph_plength`` /
``vibe_nw512_flit0`` / ``vibe_decl_flits``). 1-beat
(≤64 B) completes on SOP so ``pkt_sop && pkt_eop``
coincide. Self-contained (no child instances).
Instantiated by ``vibe_fabric`` (``g_saf.u_saf``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and ``include "vibe_ub_params.vh"`` / ``"vibe_ub_fn.vh"``.
Landed SV is hand-finished to keep those freeze semantics.
Leave PCS tx / rx tops, ``vibe_dll_tx``, ``vibe_dll`` top,
and ``vibe_fabric`` top for later stages. Do not migrate
``vibe_xbar`` here.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DEPTH = 128
PTR_W = 7
DATA_W = 512
BYTE_W = 16
PLEN_W = 14
FLIT0_W = 160
DFLIT_W = 10
BEAT_W = 7
DECL_FN_W = 8
# vibe_ub_params.vh — AS-0.1 §8 packet bounds
VIBE_PKT_LEN_MIN = 16
VIBE_PKT_LEN_MAX = 4300


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


def _sel(m: Circuit, idx, items, width: int):
    """Combo ``items[idx]`` via constant-slice mux."""
    acc = items[0]
    for i in range(1, len(items)):
        acc = _mux(m, idx == i, items[i], acc, width)
    return acc


def _zext(m: Circuit, val, src_w: int, dst_w: int):
    """Zero-extend ``val`` from ``src_w`` to ``dst_w``."""
    if dst_w == src_w:
        return val
    return m.cat(u(dst_w - src_w, 0), val)


def _nw512_flit0(in_data):
    """Stock ``vibe_nw512_flit0``: first 20 B at ``beat[511:352]``."""
    return in_data.slice(lsb=352, width=FLIT0_W)


def _lph_plength(m: Circuit, flit0):
    """Stock ``vibe_lph_plength``: ``{flit[21:16], flit[31:24]}``."""
    return m.cat(flit0.slice(lsb=16, width=6), flit0.slice(lsb=24, width=8))


def _decl_flits(m: Circuit, plen):
    """Stock ``vibe_decl_flits``: ``(nblk-1)*32 + lastn``, clamp 1..512."""
    nblk = _zext(m, plen.slice(lsb=10, width=4), 4, 5) + u(5, 1)
    lastn = _zext(m, plen.slice(lsb=5, width=5), 5, 6) + u(6, 1)
    nblk_m1 = nblk - u(5, 1)
    shifted = m.cat(nblk_m1, u(5, 0))
    raw = shifted + _zext(m, lastn, 6, 10)
    lo = _mux(m, raw < u(DFLIT_W, 1), u(DFLIT_W, 1), raw, DFLIT_W)
    return _mux(m, lo > u(DFLIT_W, 512), u(DFLIT_W, 512), lo, DFLIT_W)


def _pkt_bytes(m: Circuit, dflits):
    """Stock ``vibe_pkt_bytes``: ``n * 20`` (``n<<4 + n<<2``)."""
    times16 = m.cat(dflits, u(4, 0))
    times4 = m.cat(dflits, u(2, 0))
    return times16 + _zext(m, times4, DFLIT_W + 2, DFLIT_W + 4)


def _nw512_decl_beats(m: Circuit, pkt_len):
    """Stock ``vibe_nw512_decl_beats``: ``(b+63)>>6``, min 1."""
    b16 = _zext(m, pkt_len, DFLIT_W + 4, BYTE_W)
    raw = (b16 + u(BYTE_W, 63)).slice(lsb=6, width=DECL_FN_W)
    return _mux(m, raw == 0, u(DECL_FN_W, 1), raw, DECL_FN_W)


@module(name="vibe_saf_ing")
def build(m: Circuit) -> None:
    """Store-and-forward ingress: assemble declared beats, then present.

    Product ports (hand-finished SV)::

        clk, rst_n, in_data[511:0], in_vld, in_ready,
        pkt_data[511:0], pkt_vld, pkt_ready, pkt_sop, pkt_eop,
        pkt_bytes[15:0], len_err

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Parameter ``DEPTH=128``.
    Combo: ``in_ready = (wptr+1) != rptr``; ``pkt_vld = done &&
    (rptr != wptr)``; ``pkt_data = mem[rptr]``; ``pkt_sop`` /
    ``pkt_eop`` as stock; ``pkt_bytes = bytes``; header temps
    from ``vibe_ub_fn.vh``. Seq: ``!rst_n`` clears pointers /
    ``beat_cnt`` / ``decl_beats`` / ``bytes`` / ``assembling`` /
    ``done`` / ``len_err`` (mem not cleared). On
    ``in_vld && in_ready``: write ``mem[wptr]``, ``wptr+1``.
    SOP loads ``decl_beats`` / ``bytes`` / ``beat_cnt=1``.
    Length out of 16–4300 B: pulse ``len_err``, rewind
    ``wptr`` to ``rptr``. 1-beat completes on SOP. Mid
    beats increment ``beat_cnt``; last beat sets ``done``.
    On ``pkt_vld && pkt_ready``: ``rptr+1``; EOP clears
    ``done`` and both pointers.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    in_data = m.input("in_data", width=DATA_W)
    in_vld = m.input("in_vld", width=1)
    pkt_ready = m.input("pkt_ready", width=1)

    wptr = m.out("wptr", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    rptr = m.out("rptr", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    beat_cnt = m.out(
        "beat_cnt", clk=clk, rst=rst, width=BEAT_W, init=u(BEAT_W, 0)
    )
    decl_beats = m.out(
        "decl_beats", clk=clk, rst=rst, width=BEAT_W, init=u(BEAT_W, 0)
    )
    bytes_r = m.out(
        "bytes", clk=clk, rst=rst, width=BYTE_W, init=u(BYTE_W, 0)
    )
    assembling = m.out(
        "assembling", clk=clk, rst=rst, width=1, init=u(1, 0)
    )
    done = m.out("done", clk=clk, rst=rst, width=1, init=u(1, 0))
    len_err = m.out("len_err", clk=clk, rst=rst, width=1, init=u(1, 0))

    in_ready = (wptr.out() + u(PTR_W, 1)) != rptr.out()
    pkt_vld = done.out() & (rptr.out() != wptr.out())
    pkt_sop = pkt_vld & (
        (rptr.out() == u(PTR_W, 0)) | (beat_cnt.out() == u(BEAT_W, 0))
    )
    pkt_eop = pkt_vld & ((rptr.out() + u(PTR_W, 1)) == wptr.out())

    flit0 = _nw512_flit0(in_data)
    plen = _lph_plength(m, flit0)
    dflits = _decl_flits(m, plen)
    pkt_len = _pkt_bytes(m, dflits)
    decl_beats_c = _nw512_decl_beats(m, pkt_len)
    bytes_w = _zext(m, pkt_len, DFLIT_W + 4, BYTE_W)
    len_oor = (pkt_len < u(DFLIT_W + 4, VIBE_PKT_LEN_MIN)) | (
        pkt_len > u(DFLIT_W + 4, VIBE_PKT_LEN_MAX)
    )
    one_beat = decl_beats_c == u(DECL_FN_W, 1)

    do_wr = in_vld & in_ready
    sop_wr = do_wr & ~assembling.out()
    mid_wr = do_wr & assembling.out()
    len_bad = sop_wr & len_oor
    oneb = sop_wr & ~len_oor & one_beat
    last_mid = mid_wr & (
        (beat_cnt.out() + u(BEAT_W, 1)) >= decl_beats.out()
    )
    do_drain = pkt_vld & pkt_ready
    do_eop = do_drain & pkt_eop

    # Product RAM: combo pkt_data = mem[rptr]. Cells exist so the
    # frontend can elaborate a storage array. Combo mux is
    # hand-finished SV (DEPTH). Memory contents are *not*
    # cleared on reset (hand-finished SV).
    mem_outs = []
    for j in range(DEPTH):
        mem_c = m.out(
            f"mem_{j}", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0)
        )
        mem_c.set(in_data, when=do_wr & (wptr.out() == j))
        mem_outs.append(mem_c.out())
    pkt_data = _sel(m, rptr.out(), mem_outs, DATA_W)

    # Stock NBA last-wins: accept +1 then len_err rewind; drain
    # +1 then EOP clear. len_err pulses one cycle.
    wptr.set(wptr.out() + u(PTR_W, 1), when=do_wr)
    wptr.set(rptr.out(), when=len_bad)
    wptr.set(u(PTR_W, 0), when=do_eop)
    rptr.set(rptr.out() + u(PTR_W, 1), when=do_drain)
    rptr.set(u(PTR_W, 0), when=do_eop)
    beat_cnt.set(u(BEAT_W, 1), when=sop_wr)
    beat_cnt.set(beat_cnt.out() + u(BEAT_W, 1), when=mid_wr)
    decl_beats.set(decl_beats_c.slice(lsb=0, width=BEAT_W), when=sop_wr)
    bytes_r.set(bytes_w, when=sop_wr)
    assembling.set(u(1, 1), when=sop_wr)
    assembling.set(u(1, 0), when=len_bad | oneb | last_mid)
    done.set(u(1, 1), when=oneb | last_mid)
    done.set(u(1, 0), when=do_eop)
    len_err.set(u(1, 0))
    len_err.set(u(1, 1), when=len_bad)

    m.output("in_ready", in_ready)
    m.output("pkt_data", pkt_data)
    m.output("pkt_vld", pkt_vld)
    m.output("pkt_sop", pkt_sop)
    m.output("pkt_eop", pkt_eop)
    m.output("pkt_bytes", bytes_r.out())
    m.output("len_err", len_err.out())


build.__pycircuit_name__ = "vibe_saf_ing"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_saf_ing").emit_mlir())
