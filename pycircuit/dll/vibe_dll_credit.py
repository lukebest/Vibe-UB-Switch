"""vibe_dll_credit — DLL credit / backpressure / 1µs timeout (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll_credit.sv``. Ports match tip
``ad36bf66`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``link_up`` /
``grain_n`` / ``consume_vld`` / ``consume_flits`` / ``is_cfg0`` /
``credit_ret`` / ``credit_ret_n`` / ``pending`` / ``credit_low`` /
``force_crd_ack`` / ``bp_nw`` / ``proto_err`` / ``fc_ovf``). Second
DLL leaf after ``vibe_bcrc``. Consume ``ceil(DLLDP_flits/n)``
(n default 8); pending is a cell count; thresh 1024 → ``bp_nw`` +
force Crd_Ack. CFG0 does not consume. Credit return is already
cells. Timeout 1µs → ``proto_err``. 17-bit cells sum overflow →
``fc_ovf``. No credit underflow code. Self-contained (no child
instances). Instantiated by ``vibe_dll`` (``u_crd``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"`` for ``VIBE_CREDIT_THRESH`` /
``VIBE_US_CYC``, and the stock ``ceil_div`` function. Landed SV is
hand-finished to keep those freeze semantics. Leave PCS tx / rx
tops and the rest of DLL for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

CELL_W = 16
FLIT_W = 10
GRAIN_W = 8
TO_W = 11
# vibe_ub_params.vh — FS-must (not 1024×n flits)
VIBE_CREDIT_THRESH = 1024
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


def _ceil_div(m: Circuit, flits, n):
    """Stock ``ceil(flits/n)``; ``n==0`` → 0.

    Product SV uses the ``ceil_div`` function
    ``({1'b0, flits} + {9'd0, n} - 17'd1) / {9'd0, n}``. Grain is
    1,2,4,...,128 (default 8); the DSL muxes those powers of two
    as ``(flits + n - 1) >> log2(n)``.
    """
    num = m.cat(u(1, 0), flits) + m.cat(u(9, 0), n) - u(17, 1)

    def _shr(k: int):
        avail = 17 - k
        take = avail if avail < CELL_W else CELL_W
        sl = num.slice(lsb=k, width=take)
        if take < CELL_W:
            return m.cat(u(CELL_W - take, 0), sl)
        return sl

    z = u(CELL_W, 0)
    r = z
    for g, k in ((1, 0), (2, 1), (4, 2), (8, 3), (16, 4), (32, 5), (64, 6), (128, 7)):
        r = _mux(m, n == g, _shr(k), r, CELL_W)
    return _mux(m, n == 0, z, r, CELL_W)


@module(name="vibe_dll_credit")
def build(m: Circuit) -> None:
    """Credit consume / pending / thresh / 1µs timeout / CFG0 skip.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, link_up, grain_n[7:0]
        consume_vld, consume_flits[9:0], is_cfg0
        credit_ret, credit_ret_n[15:0]
        pending[15:0], credit_low, force_crd_ack, bp_nw
        proto_err, fc_ovf

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``port_rst || !link_up``
    clears ``cells`` / ``pend`` / ``to`` and does not clear
    ``proto_err`` / ``fc_ovf``. ``pending`` / ``credit_low`` /
    ``force_crd_ack`` / ``bp_nw`` are combo. CFG0 skips consume.
    Credit return is cells (not flits). No underflow subtract.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    link_up = m.input("link_up", width=1)
    grain_n = m.input("grain_n", width=GRAIN_W)
    consume_vld = m.input("consume_vld", width=1)
    consume_flits = m.input("consume_flits", width=FLIT_W)
    is_cfg0 = m.input("is_cfg0", width=1)
    credit_ret = m.input("credit_ret", width=1)
    credit_ret_n = m.input("credit_ret_n", width=CELL_W)

    cells = m.out("cells", clk=clk, rst=rst, width=CELL_W, init=u(CELL_W, 0))
    pend = m.out("pend", clk=clk, rst=rst, width=CELL_W, init=u(CELL_W, 0))
    to = m.out("to", clk=clk, rst=rst, width=TO_W, init=u(TO_W, 0))
    proto_err = m.out("proto_err", clk=clk, rst=rst, width=1, init=u(1, 0))
    fc_ovf = m.out("fc_ovf", clk=clk, rst=rst, width=1, init=u(1, 0))

    flits16 = m.cat(u(6, 0), consume_flits)
    consume_cells = _ceil_div(m, flits16, grain_n)
    do_consume = consume_vld & ~is_cfg0
    port_clear = port_rst | ~link_up
    pend_nz = ~(pend.out() == 0)
    cells_nz = ~(cells.out() == 0)
    at_thresh = pend.out() >= VIBE_CREDIT_THRESH

    cells_sum = m.cat(u(1, 0), cells.out()) + m.cat(u(1, 0), consume_cells)
    cells_ovf = cells_sum[16]
    ret_add = _mux(m, credit_ret, credit_ret_n, u(CELL_W, 0), CELL_W)
    cons_add = _mux(m, do_consume, consume_cells, u(CELL_W, 0), CELL_W)
    pend_sum = (
        m.cat(u(1, 0), pend.out())
        + m.cat(u(1, 0), ret_add)
        + m.cat(u(1, 0), cons_add)
    )

    reload_to = credit_ret | (do_consume & ~(consume_cells == 0))
    tick_to = ~reload_to & pend_nz & ~(to.out() == 0)
    to_expire = ~reload_to & pend_nz & (to.out() == 0)

    # Normal NBA first; port_rst / !link_up last so they win (stock if/else).
    cells.set(cells_sum.slice(lsb=0, width=CELL_W), when=do_consume)
    cells.set(u(CELL_W, 65535), when=do_consume & cells_ovf)
    fc_ovf.set(u(1, 1), when=do_consume & cells_ovf)

    pend.set(pend_sum.slice(lsb=0, width=CELL_W))

    to.set(to.out() - 1, when=tick_to)
    to.set(u(TO_W, VIBE_US_CYC), when=reload_to)
    proto_err.set(u(1, 1), when=to_expire)

    cells.set(u(CELL_W, 0), when=port_clear)
    pend.set(u(CELL_W, 0), when=port_clear)
    to.set(u(TO_W, 0), when=port_clear)

    m.output("pending", pend.out())
    m.output("credit_low", ~cells_nz)
    m.output("force_crd_ack", at_thresh | (~consume_vld & pend_nz))
    m.output("bp_nw", at_thresh)
    m.output("proto_err", proto_err.out())
    m.output("fc_ovf", fc_ovf.out())


build.__pycircuit_name__ = "vibe_dll_credit"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_credit").emit_mlir())
