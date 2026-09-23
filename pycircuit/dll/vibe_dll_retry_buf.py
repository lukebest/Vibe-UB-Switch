"""vibe_dll_retry_buf — DLL RETRY buffer (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll_retry_buf.sv``. Ports match tip
``fc7c0151`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``link_up`` /
``wr_en`` / ``is_null`` / ``is_retry`` / ``wr_flit[159:0]`` /
``send_size[7:0]`` / ``ack_rel`` / ``rel_size[7:0]`` /
``rd_ptr_i[7:0]`` / ``rd_flit[159:0]`` / ``wr_ptr[7:0]`` /
``tail_ptr[7:0]`` / ``rcv_ptr[7:0]`` / ``num_free[8:0]`` /
``proto_err`` / ``can_send``). Sixth DLL leaf after
``vibe_bcrc`` / ``vibe_dll_credit`` / ``vibe_dll_sm`` /
``vibe_dll_rx`` / ``vibe_dll_retry_ack_sm``. Depth 256
FS-must. Null and Retry blocks do not enter.
``NumFreeBuf + ReleaseSize > 256`` → DL Protocol Error.
Self-contained (no child instances). Instantiated by
``vibe_dll`` (``u_rbuf``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and ``include "vibe_ub_params.vh"``. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_retry_req_sm``, ``vibe_dll_tx``, and ``vibe_dll`` top
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

FLIT_W = 160
PTR_W = 8
FREE_W = 9
DEPTH = 256


@module(name="vibe_dll_retry_buf")
def build(m: Circuit) -> None:
    """RETRY buffer: 256-deep flit RAM + free/ptr/proto_err.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, link_up, wr_en, is_null, is_retry
        wr_flit[159:0], send_size[7:0], ack_rel, rel_size[7:0]
        rd_ptr_i[7:0], rd_flit[159:0], wr_ptr[7:0], tail_ptr[7:0]
        rcv_ptr[7:0], num_free[8:0], proto_err, can_send

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Write when
    ``wr_en && !is_null && !is_retry && can_send``: ``mem[wrp]``,
    ``wrp+1``, ``freeb-1``. Release ``ack_rel``: if
    ``freeb+rel_size>256`` set sticky ``proto_err``; else
    ``freeb+=rel_size``, ``tail+=rel_size``, ``rcv+=rel_size``.
    ``port_rst || !link_up`` clears pointers/free (not
    ``proto_err``). Combo: ptrs / ``num_free`` / ``can_send``
    ``(freeb>={1'b0,send_size})`` / ``rd_flit=mem[rd_ptr_i]``.
    Same-cycle write then legal release: last NBA to ``freeb``
    wins (release), matching stock. Memory is not cleared on
    reset (hand-finished SV).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    link_up = m.input("link_up", width=1)
    wr_en = m.input("wr_en", width=1)
    is_null = m.input("is_null", width=1)
    is_retry = m.input("is_retry", width=1)
    wr_flit = m.input("wr_flit", width=FLIT_W)
    send_size = m.input("send_size", width=PTR_W)
    ack_rel = m.input("ack_rel", width=1)
    rel_size = m.input("rel_size", width=PTR_W)
    rd_ptr_i = m.input("rd_ptr_i", width=PTR_W)

    wrp = m.out("wrp", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    tail = m.out("tail", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    rcv = m.out("rcv", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))
    freeb = m.out("freeb", clk=clk, rst=rst, width=FREE_W, init=u(FREE_W, DEPTH))
    proto_err = m.out("proto_err", clk=clk, rst=rst, width=1, init=u(1, 0))

    can_send = freeb.out() >= m.cat(u(1, 0), send_size)
    do_wr = wr_en & ~is_null & ~is_retry & can_send
    port_clear = port_rst | ~link_up
    rel_w = m.cat(u(1, 0), rel_size)
    rel_ovf = (freeb.out() + rel_w) > u(FREE_W, DEPTH)

    # Product RAM: combo rd_flit = mem[rd_ptr_i]; write on do_wr.
    # Memory contents are *not* cleared on reset (hand-finished SV).
    # Cells exist so the frontend can elaborate a storage array.
    rd_flit = u(FLIT_W, 0)
    for i in range(DEPTH):
        cell = m.out(f"mem_{i}", clk=clk, rst=rst, width=FLIT_W, init=u(FLIT_W, 0))
        cell.set(wr_flit, when=do_wr & (wrp.out() == i))
        rd_flit = cell.out() if (rd_ptr_i == i) else rd_flit

    # Write / release NBA first; port_rst / !link_up last so they
    # win (stock if/else). proto_err is sticky across port_clear.
    # Entity rst is async-low in the product SV, not a pin here.
    wrp.set(wrp.out() + 1, when=do_wr)
    freeb.set(freeb.out() - 1, when=do_wr)

    proto_err.set(u(1, 1), when=ack_rel & rel_ovf)
    freeb.set(freeb.out() + rel_w, when=ack_rel & ~rel_ovf)
    tail.set(tail.out() + rel_size, when=ack_rel & ~rel_ovf)
    rcv.set(rcv.out() + rel_size, when=ack_rel & ~rel_ovf)

    wrp.set(u(PTR_W, 0), when=port_clear)
    tail.set(u(PTR_W, 0), when=port_clear)
    rcv.set(u(PTR_W, 0), when=port_clear)
    freeb.set(u(FREE_W, DEPTH), when=port_clear)

    m.output("rd_flit", rd_flit)
    m.output("wr_ptr", wrp.out())
    m.output("tail_ptr", tail.out())
    m.output("rcv_ptr", rcv.out())
    m.output("num_free", freeb.out())
    m.output("proto_err", proto_err.out())
    m.output("can_send", can_send)


build.__pycircuit_name__ = "vibe_dll_retry_buf"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_retry_buf").emit_mlir())
