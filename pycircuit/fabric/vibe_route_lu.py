"""vibe_route_lu — fabric CFG0_ROUTE_TABLE lookup (AS-0.1 §2/§8).

Product module: ``rtl/fabric/vibe_route_lu.sv``. Ports match tip
``2841888e`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``device_rst`` / ``wr_en`` /
``wr_idx[15:0]`` / ``wr_data[31:0]`` / ``dest[15:0]`` / ``rt[1:0]`` /
``lu_vld`` / ``bitmap[3:0]`` / ``drop_g1``). Parameter ``DEPTH``
default 256. Third fabric leaf after ``vibe_fecn_mark`` /
``vibe_vl_rr``. dest → 4-bit egress bitmap. RT=10/11: DROP
(pulse ``drop_g1``). No Dijkstra, no treat-as-RT=00, no RT
rewrite. Fabric saturates ``rt_shortest_unimpl`` and
``irq_agg`` sticks ``irq_logic`` (not this leaf). Self-contained
(no child instances). Instantiated by ``vibe_fabric``
(``u_rt``, ``g_rt.u_rti``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and ``!rst_n || device_rst`` to clear the table + outputs.
Landed SV is hand-finished to keep those freeze semantics.
Leave PCS tx / rx tops, ``vibe_dll_tx``, ``vibe_dll`` top,
and ``vibe_fabric`` top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DEPTH = 256
IDX_W = 8
DATA_W = 32
DEST_W = 16
WR_IDX_W = 16
BM_W = 4
RT_W = 2
RT_DROP_10 = 0b10
RT_DROP_11 = 0b11


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


@module(name="vibe_route_lu")
def build(m: Circuit) -> None:
    """Route table: dest → 4-bit egress bitmap; RT=10/11 drop.

    Product ports (hand-finished SV)::

        clk, rst_n, device_rst, wr_en, wr_idx[15:0], wr_data[31:0],
        dest[15:0], rt[1:0], lu_vld, bitmap[3:0], drop_g1

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Parameter ``DEPTH=256``.
    Index is ``wr_idx[7:0]`` / ``dest[7:0]``. On ``wr_en``:
    ``tbl[wr_idx[7:0]] <= wr_data``. On ``lu_vld``: RT=10/11
    pulse ``drop_g1`` and ``bitmap=0``; else
    ``bitmap <= tbl[dest[7:0]][3:0]``. ``device_rst`` (or entity
    rst) clears table + outputs. No Dijkstra / RT rewrite.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    device_rst = m.input("device_rst", width=1)
    wr_en = m.input("wr_en", width=1)
    wr_idx = m.input("wr_idx", width=WR_IDX_W)
    wr_data = m.input("wr_data", width=DATA_W)
    dest = m.input("dest", width=DEST_W)
    rt = m.input("rt", width=RT_W)
    lu_vld = m.input("lu_vld", width=1)

    wr_lo = wr_idx.slice(lsb=0, width=IDX_W)
    dest_lo = dest.slice(lsb=0, width=IDX_W)
    is_drop = (rt == RT_DROP_10) | (rt == RT_DROP_11)

    # Product RAM: write on wr_en; lookup tbl[dest[7:0]][3:0].
    # !rst_n || device_rst clears every cell (hand-finished SV).
    tbl_rd = u(DATA_W, 0)
    for i in range(DEPTH):
        cell = m.out(f"tbl_{i}", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0))
        cell.set(wr_data, when=wr_en & (wr_lo == i))
        cell.set(u(DATA_W, 0), when=device_rst)
        tbl_rd = _mux(m, dest_lo == i, cell.out(), tbl_rd, DATA_W)

    bitmap = m.out("bitmap", clk=clk, rst=rst, width=BM_W, init=u(BM_W, 0))
    drop_g1 = m.out("drop_g1", clk=clk, rst=rst, width=1, init=u(1, 0))

    # Stock: drop_g1 <= 0 every cycle, then pulse on lu_vld && RT=10/11.
    drop_g1.set(u(1, 0))
    drop_g1.set(u(1, 1), when=lu_vld & is_drop)
    bitmap.set(u(BM_W, 0), when=lu_vld & is_drop)
    bitmap.set(tbl_rd.slice(lsb=0, width=BM_W), when=lu_vld & ~is_drop)
    drop_g1.set(u(1, 0), when=device_rst)
    bitmap.set(u(BM_W, 0), when=device_rst)

    m.output("bitmap", bitmap.out())
    m.output("drop_g1", drop_g1.out())


build.__pycircuit_name__ = "vibe_route_lu"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_route_lu").emit_mlir())
