"""vibe_voq_egr — fabric egress VOQ (AS-0.1 §8/§14).

Product module: ``rtl/fabric/vibe_voq_egr.sv``. Ports match tip
``8ec96a2a`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``wr_vl[3:0]`` / ``wr_en`` /
``wr_data[511:0]`` / ``wr_sop`` / ``wr_eop`` / ``wr_ready`` /
``rd_vl[3:0]`` / ``rd_en`` / ``rd_data[511:0]`` / ``rd_sop`` /
``rd_eop`` / ``nonempty[15:0]`` / ``occ_vl0[5:0]`` /
``deadlock_drop`` / ``deadlock_cnt[31:0]``). Parameter ``DEPTH``
default 32. Fifth fabric leaf after ``vibe_fecn_mark`` /
``vibe_vl_rr`` / ``vibe_route_lu`` / ``vibe_port_sel``.
16 VL × DEPTH mem + sop/eop/age. ``wr_ready`` when
``occ < DEPTH``. ``rd_*`` combo from
``mem[rd_vl][rptr[rd_vl]]``. ``occ_vl0 = wptr[0]-rptr[0]``.
``nonempty[v] = (wptr[v] != rptr[v])``. Enqueue loads
``age = VIBE_US_CYC`` (1 µs @ 1.25 GHz). If nonempty and
head age is 0: auto-advance ``rptr``, pulse
``deadlock_drop``, increment ``deadlock_cnt``.
Self-contained (no child instances). Instantiated by
``vibe_fabric`` (``g_egr.u_voq``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and ``include "vibe_ub_params.vh"``. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_tx``, ``vibe_dll`` top, and ``vibe_fabric`` top
for later stages. Do not migrate ``vibe_saf_ing`` /
``vibe_xbar`` here.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

VL_N = 16
VL_W = 4
DEPTH = 32
PTR_W = 6
IDX_W = 5
DATA_W = 512
AGE_W = 11
CNT_W = 32
# vibe_ub_params.vh — 1 us @ 1.25 GHz
VIBE_US_CYC = 1250


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


@module(name="vibe_voq_egr")
def build(m: Circuit) -> None:
    """Egress VOQ: 16 VL × DEPTH + 1 µs deadlock timeout.

    Product ports (hand-finished SV)::

        clk, rst_n, wr_vl[3:0], wr_en, wr_data[511:0], wr_sop,
        wr_eop, wr_ready, rd_vl[3:0], rd_en, rd_data[511:0],
        rd_sop, rd_eop, nonempty[15:0], occ_vl0[5:0],
        deadlock_drop, deadlock_cnt[31:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Parameter ``DEPTH=32``.
    Combo: ``wr_ready = (wptr[wr_vl]-rptr[wr_vl]) < DEPTH``;
    ``rd_* = mem/sopm/eopm[rd_vl][rptr[rd_vl][4:0]]``;
    ``occ_vl0 = wptr[0]-rptr[0]``;
    ``nonempty[v] = (wptr[v] != rptr[v])``. Seq: ``!rst_n``
    clears ``deadlock_*`` and every ``wptr`` / ``rptr`` (mem /
    sop / eop / age not cleared). On ``wr_en && wr_ready``:
    write slot, ``age = VIBE_US_CYC``, ``wptr+1``. On
    ``rd_en``: ``rptr[rd_vl]+1``. Every age cell counts down
    when nonzero. If nonempty and head age is 0: ``rptr+1``,
    pulse ``deadlock_drop``, ``deadlock_cnt+1``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    wr_vl = m.input("wr_vl", width=VL_W)
    wr_en = m.input("wr_en", width=1)
    wr_data = m.input("wr_data", width=DATA_W)
    wr_sop = m.input("wr_sop", width=1)
    wr_eop = m.input("wr_eop", width=1)
    rd_vl = m.input("rd_vl", width=VL_W)
    rd_en = m.input("rd_en", width=1)

    wptr = [
        m.out(f"wptr_{v}", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
        for v in range(VL_N)
    ]
    rptr = [
        m.out(f"rptr_{v}", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
        for v in range(VL_N)
    ]
    deadlock_drop = m.out(
        "deadlock_drop", clk=clk, rst=rst, width=1, init=u(1, 0)
    )
    deadlock_cnt = m.out(
        "deadlock_cnt", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0)
    )

    wptr_wr = _sel(m, wr_vl, [p.out() for p in wptr], PTR_W)
    rptr_wr = _sel(m, wr_vl, [p.out() for p in rptr], PTR_W)
    occ = wptr_wr - rptr_wr
    wr_ready = occ < u(PTR_W, DEPTH)
    wr_lo = wptr_wr.slice(lsb=0, width=IDX_W)
    do_wr = wr_en & wr_ready

    ne_bits = [wptr[v].out() != rptr[v].out() for v in range(VL_N)]
    nonempty = ne_bits[0]
    for v in range(1, VL_N):
        nonempty = m.cat(ne_bits[v], nonempty)

    # Product RAM: combo rd_* = mem/sopm/eopm[rd_vl][rptr[rd_vl][4:0]].
    # Cells exist so the frontend can elaborate a storage array.
    # Combo mux is hand-finished SV (16 VL × DEPTH). Memory / age
    # contents are *not* cleared on reset (hand-finished SV).
    rd_data = u(DATA_W, 0)
    rd_sop = u(1, 0)
    rd_eop = u(1, 0)
    to_any = u(1, 0)
    for v in range(VL_N):
        rlo = rptr[v].out().slice(lsb=0, width=IDX_W)
        head_age = u(AGE_W, 0)
        for j in range(DEPTH):
            mem_c = m.out(
                f"mem_{v}_{j}", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0)
            )
            sop_c = m.out(
                f"sopm_{v}_{j}", clk=clk, rst=rst, width=1, init=u(1, 0)
            )
            eop_c = m.out(
                f"eopm_{v}_{j}", clk=clk, rst=rst, width=1, init=u(1, 0)
            )
            age_c = m.out(
                f"age_{v}_{j}", clk=clk, rst=rst, width=AGE_W, init=u(AGE_W, 0)
            )
            wr_hit = do_wr & (wr_vl == v) & (wr_lo == j)
            mem_c.set(wr_data, when=wr_hit)
            sop_c.set(wr_sop, when=wr_hit)
            eop_c.set(wr_eop, when=wr_hit)
            # Stock: enqueue NBA then countdown NBA; last wins if
            # leftover age != 0 (hand-finished SV matches stock).
            age_c.set(u(AGE_W, VIBE_US_CYC), when=wr_hit)
            age_c.set(age_c.out() - u(AGE_W, 1), when=age_c.out() != 0)
            head_age = _mux(m, rlo == j, age_c.out(), head_age, AGE_W)
            # last-cell probe (same pattern as vibe_dll_retry_buf)
            rd_data = mem_c.out()
            rd_sop = sop_c.out()
            rd_eop = eop_c.out()
        timed = ne_bits[v] & (head_age == 0)
        to_any = to_any | timed
        wptr[v].set(wptr[v].out() + u(PTR_W, 1), when=do_wr & (wr_vl == v))
        rptr[v].set(rptr[v].out() + u(PTR_W, 1), when=rd_en & (rd_vl == v))
        rptr[v].set(rptr[v].out() + u(PTR_W, 1), when=timed)

    # Stock: drop <= 0 every cycle, then pulse on any VL timeout.
    # Multiple VLs in one cycle still +1 (last NBA wins).
    deadlock_drop.set(u(1, 0))
    deadlock_drop.set(u(1, 1), when=to_any)
    deadlock_cnt.set(deadlock_cnt.out() + u(CNT_W, 1), when=to_any)

    m.output("wr_ready", wr_ready)
    m.output("rd_data", rd_data)
    m.output("rd_sop", rd_sop)
    m.output("rd_eop", rd_eop)
    m.output("nonempty", nonempty)
    m.output("occ_vl0", wptr[0].out() - rptr[0].out())
    m.output("deadlock_drop", deadlock_drop.out())
    m.output("deadlock_cnt", deadlock_cnt.out())


build.__pycircuit_name__ = "vibe_voq_egr"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_voq_egr").emit_mlir())
