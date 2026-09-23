"""vibe_xbar — fabric 4-port crossbar (AS-0.1 §8).

Product module: ``rtl/fabric/vibe_xbar.sv``. Ports match tip
``782f2181`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``status_up[3:0]`` /
``in_data[511:0][0:3]`` / ``in_vld[3:0]`` / ``in_sop[3:0]`` /
``in_eop[3:0]`` / ``in_dst[1:0][0:3]`` / ``in_ready[3:0]`` /
``out_data[511:0][0:3]`` / ``out_vld[3:0]`` / ``out_sop[3:0]`` /
``out_eop[3:0]`` / ``out_ready[3:0]``). Seventh fabric leaf
after ``vibe_fecn_mark`` / ``vibe_vl_rr`` / ``vibe_route_lu`` /
``vibe_port_sel`` / ``vibe_voq_egr`` / ``vibe_saf_ing``.
Output queued. Ingress RR on conflict. One full packet per
grant (lock until EOP). Down ports get no data DLLDP.
Mgmt bypass does not enter xbar. Candidate grant
(``out_data`` / ``out_sop`` / ``out_eop`` / ``cand_*``) is
independent of ``out_ready`` so VOQ ``wr_vl`` cannot
combo-loop with ``wr_ready`` (UNOPTFLAT ``xb_r``). Accept
(``out_vld`` / ``in_ready``) still requires ``out_ready``.
Self-contained (no child instances). Instantiated by
``vibe_fabric`` (``u_xbar``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and unpacked array ports. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_tx``, ``vibe_dll`` top, and ``vibe_fabric`` top
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
PORT_W = 2
DATA_W = 512
BM_W = 4


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


def _bit_sel(m: Circuit, vec, idx, nbits: int = PORT_N):
    """Combo ``vec[idx]`` via constant-slice mux."""
    bit = vec.slice(lsb=0, width=1)
    for j in range(1, nbits):
        bit = _mux(m, idx == j, vec.slice(lsb=j, width=1), bit, 1)
    return bit


def _sel(m: Circuit, idx, items, width: int):
    """Combo ``items[idx]`` via constant-slice mux."""
    acc = items[0]
    for i in range(1, len(items)):
        acc = _mux(m, idx == i, items[i], acc, width)
    return acc


def _cat_lsb_first(m: Circuit, bits):
    """Pack ``bits[0]`` as LSB (``m.cat`` is MSB-first)."""
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


def _rr_pick(m: Circuit, start, hit_bits):
    """Stock unlocked walk: start at ``rr[e]``, first ``req[win]``."""
    found = u(1, 0)
    pick = u(PORT_W, 0)
    vld = u(1, 0)
    for k in range(PORT_N):
        cand = start + u(PORT_W, k)
        hit = _sel(m, cand, hit_bits, 1)
        take = hit & ~found
        pick = _mux(m, take, cand, pick, PORT_W)
        vld = _mux(m, take, u(1, 1), vld, 1)
        found = found | hit
    return pick, vld


@module(name="vibe_xbar")
def build(m: Circuit) -> None:
    """4-port xbar: lock one packet, ingress RR on conflict.

    Product ports (hand-finished SV)::

        clk, rst_n, status_up[3:0],
        in_data[511:0][0:3], in_vld[3:0], in_sop[3:0], in_eop[3:0],
        in_dst[1:0][0:3], in_ready[3:0],
        out_data[511:0][0:3], out_vld[3:0], out_sop[3:0],
        out_eop[3:0], out_ready[3:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Unpacked product arrays
    are flattened here (``in_data_0..3``, ``in_dst_0..3``,
    ``out_data_0..3``). Combo: candidate grant is independent of
    ``out_ready``; down ports emit zeros; locked egress holds
    ``lock[e]`` while ``in_vld && in_dst==e``; else RR from
    ``rr[e]``. Accept (``out_vld`` / ``in_ready``) needs
    ``out_ready``. Seq: ``!rst_n`` clears ``lock`` / ``locked`` /
    ``rr``. On ``out_vld && out_ready``: lock winner until EOP;
    EOP clears ``locked`` and advances ``rr <= lock+1``.
    Stock first-NBA ``lock <= in_dst[0]`` on SOP is last-won
    by the winner / hold assigns (hand-finished SV matches).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    status_up = m.input("status_up", width=BM_W)
    in_data = [
        m.input(f"in_data_{i}", width=DATA_W) for i in range(PORT_N)
    ]
    in_vld = m.input("in_vld", width=BM_W)
    in_sop = m.input("in_sop", width=BM_W)
    in_eop = m.input("in_eop", width=BM_W)
    in_dst = [m.input(f"in_dst_{i}", width=PORT_W) for i in range(PORT_N)]
    out_ready = m.input("out_ready", width=BM_W)

    lock = [
        m.out(f"lock_{e}", clk=clk, rst=rst, width=PORT_W, init=u(PORT_W, 0))
        for e in range(PORT_N)
    ]
    locked = [
        m.out(f"locked_{e}", clk=clk, rst=rst, width=1, init=u(1, 0))
        for e in range(PORT_N)
    ]
    rr = [
        m.out(f"rr_{e}", clk=clk, rst=rst, width=PORT_W, init=u(PORT_W, 0))
        for e in range(PORT_N)
    ]

    cand_vld = []
    cand_src = []
    out_data = []
    out_sop = []
    out_eop = []
    for e in range(PORT_N):
        up = _bit_sel(m, status_up, u(PORT_W, e))
        # Locked hold: grant lock[e] when still valid to this egress.
        lk = lock[e].out()
        lock_match = _bit_sel(m, in_vld, lk) & (
            _sel(m, lk, in_dst, PORT_W) == u(PORT_W, e)
        )
        use_lock = up & locked[e].out() & lock_match
        # Unlocked RR among in_vld && in_dst==e. Full combo
        # defaults (req/win) — same LATCH ECO as stock.
        req_bits = [
            _bit_sel(m, in_vld, u(PORT_W, i))
            & (in_dst[i] == u(PORT_W, e))
            for i in range(PORT_N)
        ]
        pick, pick_vld = _rr_pick(m, rr[e].out(), req_bits)
        use_rr = up & ~locked[e].out() & pick_vld
        src = _mux(m, use_lock, lk, _mux(m, use_rr, pick, u(PORT_W, 0), PORT_W), PORT_W)
        vld = use_lock | use_rr
        data = _sel(m, src, in_data, DATA_W)
        sop = _bit_sel(m, in_sop, src)
        eop = _bit_sel(m, in_eop, src)
        out_data.append(_mux(m, vld, data, u(DATA_W, 0), DATA_W))
        out_sop.append(vld & sop)
        out_eop.append(vld & eop)
        cand_vld.append(vld)
        cand_src.append(src)

    acc = [
        cand_vld[e] & _bit_sel(m, out_ready, u(PORT_W, e))
        for e in range(PORT_N)
    ]
    in_ready_bits = []
    for i in range(PORT_N):
        ir = u(1, 0)
        for e in range(PORT_N):
            ir = ir | (acc[e] & (cand_src[e] == u(PORT_W, i)))
        in_ready_bits.append(ir)

    # Stock NBA last-wins on fire. First SOP assign
    # ``lock <= in_dst[0]`` is overwritten by hold / winner.
    for e in range(PORT_N):
        fire = acc[e]
        sop_f = fire & out_sop[e]
        eop_f = fire & out_eop[e]
        lock[e].set(in_dst[0], when=sop_f)
        lock[e].set(lock[e].out(), when=fire & locked[e].out())
        for i in range(PORT_N):
            lock[e].set(
                u(PORT_W, i),
                when=fire
                & ~locked[e].out()
                & in_ready_bits[i]
                & (in_dst[i] == u(PORT_W, e)),
            )
        locked[e].set(u(1, 1), when=sop_f)
        locked[e].set(u(1, 1), when=fire & ~locked[e].out())
        locked[e].set(u(1, 0), when=eop_f)
        rr[e].set(lock[e].out() + u(PORT_W, 1), when=eop_f)

    m.output("in_ready", _cat_lsb_first(m, in_ready_bits))
    for e in range(PORT_N):
        m.output(f"out_data_{e}", out_data[e])
    m.output("out_vld", _cat_lsb_first(m, acc))
    m.output("out_sop", _cat_lsb_first(m, out_sop))
    m.output("out_eop", _cat_lsb_first(m, out_eop))


build.__pycircuit_name__ = "vibe_xbar"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_xbar").emit_mlir())
