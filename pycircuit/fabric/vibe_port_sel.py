"""vibe_port_sel — fabric port select (AS-0.1 §2/§8).

Product module: ``rtl/fabric/vibe_port_sel.sv``. Ports match tip
``89c388cb`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``bitmap[3:0]`` /
``status_up[3:0]`` / ``default_bm[3:0]`` / ``rt[1:0]`` /
``drop_g1`` / ``sel_vld`` / ``cfg[3:0]`` / ``src[15:0]`` /
``dest[15:0]`` / ``vl[3:0]`` / ``egr[1:0]`` / ``drop`` /
``drop_down_cnt[31:0]``). Fourth fabric leaf after
``vibe_fecn_mark`` / ``vibe_vl_rr`` / ``vibe_route_lu``.
``available = bitmap & status_up`` (forced 0 if ``drop_g1``).
Empty after filter → Default; Default all-0 → port 0 bitmap
``4'b0001``; AND with ``status_up``. If still empty → drop +
increment ``drop_down_cnt``, no flood. RT=00: per-flow sticky
RR; flow slot ``fidx=vl`` (compact); sticky table ``[0:15]``.
RT=01 (else): per-packet RR via ``rr``. ``pick_rr(bm, start)``
walks 4 ports from start. Self-contained (no child instances).
Instantiated by ``vibe_fabric`` (``u_ps``, ``g_rt.u_psi``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and the stock ``pick_rr`` walk. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_tx``, ``vibe_dll`` top, and ``vibe_fabric`` top
for later stages. Do not migrate ``vibe_voq_egr`` /
``vibe_saf_ing`` / ``vibe_xbar`` here.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

BM_W = 4
PORT_W = 2
RT_W = 2
CFG_W = 4
ADDR_W = 16
VL_W = 4
CNT_W = 32
STICKY_N = 16
PORT_N = 4
RT_STICKY = 0
PORT0_BM = 0b0001


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


def _pick_rr(m: Circuit, bm, start):
    """Stock ``pick_rr(bm, start)``: walk 4 ports from ``start``."""
    found = u(1, 0)
    pick = u(PORT_W, 0)
    for k in range(PORT_N):
        cand = start + u(PORT_W, k)
        hit = _bit_sel(m, bm, cand)
        take = hit & ~found
        pick = _mux(m, take, cand, pick, PORT_W)
        found = found | hit
    return pick


@module(name="vibe_port_sel")
def build(m: Circuit) -> None:
    """Port select: filter bitmap, then sticky or per-packet RR.

    Product ports (hand-finished SV)::

        clk, rst_n, bitmap[3:0], status_up[3:0], default_bm[3:0],
        rt[1:0], drop_g1, sel_vld, cfg[3:0], src[15:0], dest[15:0],
        vl[3:0], egr[1:0], drop, drop_down_cnt[31:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Combo: ``avail =
    drop_g1 ? 0 : (bitmap & status_up)``; empty → Default (all-0
    → ``4'b0001``) AND ``status_up``. ``fidx = vl`` (compact;
    ``cfg`` / ``src`` / ``dest`` are product ports, unused in
    the compact slot). Seq: ``!rst_n`` clears ``egr`` / ``drop``
    / ``drop_down_cnt`` / ``rr`` / ``sticky[0:15]``. On
    ``sel_vld``: empty (or ``drop_g1``) → ``drop``; empty and
    not ``drop_g1`` increments ``drop_down_cnt`` (no flood).
    RT=00: sticky RR at ``sticky[fidx]``. Else: per-packet RR
    via ``rr``. No flood.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    bitmap = m.input("bitmap", width=BM_W)
    status_up = m.input("status_up", width=BM_W)
    default_bm = m.input("default_bm", width=BM_W)
    rt = m.input("rt", width=RT_W)
    drop_g1 = m.input("drop_g1", width=1)
    sel_vld = m.input("sel_vld", width=1)
    # Product ports (flow key); compact slot is vl only.
    m.input("cfg", width=CFG_W)
    m.input("src", width=ADDR_W)
    m.input("dest", width=ADDR_W)
    vl = m.input("vl", width=VL_W)

    fidx = vl
    avail = _mux(m, drop_g1, u(BM_W, 0), bitmap & status_up, BM_W)
    def_or_p0 = _mux(
        m, default_bm == 0, u(BM_W, PORT0_BM), default_bm, BM_W
    )
    use_bm = _mux(m, avail == 0, def_or_p0 & status_up, avail, BM_W)
    empty_use = use_bm == 0
    is_drop = drop_g1 | empty_use
    is_rt00 = rt == RT_STICKY

    rr = m.out("rr", clk=clk, rst=rst, width=PORT_W, init=u(PORT_W, 0))
    sticky = [
        m.out(f"sticky_{i}", clk=clk, rst=rst, width=PORT_W, init=u(PORT_W, 0))
        for i in range(STICKY_N)
    ]
    egr = m.out("egr", clk=clk, rst=rst, width=PORT_W, init=u(PORT_W, 0))
    drop = m.out("drop", clk=clk, rst=rst, width=1, init=u(1, 0))
    drop_down_cnt = m.out(
        "drop_down_cnt", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0)
    )

    sticky_cur = u(PORT_W, 0)
    for i in range(STICKY_N):
        sticky_cur = _mux(m, fidx == i, sticky[i].out(), sticky_cur, PORT_W)
    sticky_hit = _bit_sel(m, use_bm, sticky_cur)
    pick_sticky = _pick_rr(m, use_bm, sticky_cur)
    pick_pkt = _pick_rr(m, use_bm, rr.out())
    egr_sticky = _mux(m, sticky_hit, sticky_cur, pick_sticky, PORT_W)

    # Stock: drop <= 0 every cycle, then pulse on sel_vld drop path.
    drop.set(u(1, 0))
    drop.set(u(1, 1), when=sel_vld & is_drop)
    drop_down_cnt.set(
        drop_down_cnt.out() + u(CNT_W, 1),
        when=sel_vld & ~drop_g1 & empty_use,
    )
    egr.set(egr_sticky, when=sel_vld & ~is_drop & is_rt00)
    for i in range(STICKY_N):
        sticky[i].set(
            pick_sticky,
            when=sel_vld & ~is_drop & is_rt00 & ~sticky_hit & (fidx == i),
        )
    egr.set(pick_pkt, when=sel_vld & ~is_drop & ~is_rt00)
    rr.set(pick_pkt + u(PORT_W, 1), when=sel_vld & ~is_drop & ~is_rt00)

    m.output("egr", egr.out())
    m.output("drop", drop.out())
    m.output("drop_down_cnt", drop_down_cnt.out())


build.__pycircuit_name__ = "vibe_port_sel"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_port_sel").emit_mlir())
