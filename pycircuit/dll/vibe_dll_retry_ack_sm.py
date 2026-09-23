"""vibe_dll_retry_ack_sm — DLL RETRY_ACK_SM (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll_retry_ack_sm.sv``. Ports match tip
``0b0a82db`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``start_ack`` /
``wr_ptr[7:0]`` / ``rcv_ptr[7:0]`` / ``state[2:0]`` / ``send_idle`` /
``send_ack`` / ``replay`` / ``rd_ptr[7:0]``). Fifth DLL leaf after
``vibe_bcrc`` / ``vibe_dll_credit`` / ``vibe_dll_sm`` /
``vibe_dll_rx``. NORMAL / ACK (1 Idle + 32 Ack then replay
``RdPtr=RcvPtr`` until ``WrPtr``). Self-contained (no child
instances). Instantiated by ``vibe_dll`` (``u_ack``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``).
Landed SV is hand-finished to keep those freeze semantics. Leave
PCS tx / rx tops, ``vibe_dll_tx``, other ``retry_*``
(``retry_buf``, ``retry_req_sm``), and ``vibe_dll`` top for later
stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

ST_W = 3
BURST_W = 6
PTR_W = 8
ST_N = 0
ST_A = 1
ST_P = 2
ACK_BURST = 32


@module(name="vibe_dll_retry_ack_sm")
def build(m: Circuit) -> None:
    """RETRY_ACK_SM: NORMAL / ACK / replay.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, start_ack, wr_ptr[7:0], rcv_ptr[7:0]
        state[2:0], send_idle, send_ack, replay, rd_ptr[7:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``start_ack`` in
    ``ST_N`` → ``ST_A`` with ``burst=0`` (Idle). Then 32 Ack
    (``burst`` 1..32). At ``burst==32`` enter replay
    (``ST_P``, ``rd_ptr=rcv_ptr``) until ``rd_ptr==wr_ptr``.
    Combo: ``send_idle=(st==ST_A)&&(burst==0)``,
    ``send_ack=(st==ST_A)&&(burst!=0)``, ``replay=(st==ST_P)``,
    ``state=st``, ``rd_ptr=rp``. ``port_rst`` returns to
    ``ST_N``. Default (illegal ``st``) → ``ST_N``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    start_ack = m.input("start_ack", width=1)
    wr_ptr = m.input("wr_ptr", width=PTR_W)
    rcv_ptr = m.input("rcv_ptr", width=PTR_W)

    st = m.out("st", clk=clk, rst=rst, width=ST_W, init=u(ST_W, ST_N))
    burst = m.out("burst", clk=clk, rst=rst, width=BURST_W, init=u(BURST_W, 0))
    rp = m.out("rp", clk=clk, rst=rst, width=PTR_W, init=u(PTR_W, 0))

    is_n = st.out() == ST_N
    is_a = st.out() == ST_A
    is_p = st.out() == ST_P
    is_default = ~(is_n | is_a | is_p)
    burst_done = burst.out() == ACK_BURST
    rp_at_wr = rp.out() == wr_ptr
    enter_ack = is_n & start_ack

    # Case NBA first; port_rst last so it wins (stock if/else).
    # Entity rst is async-low in the product SV, not a pin here.
    st.set(u(ST_W, ST_A), when=enter_ack)
    burst.set(u(BURST_W, 0), when=enter_ack)

    st.set(u(ST_W, ST_P), when=is_a & burst_done)
    rp.set(rcv_ptr, when=is_a & burst_done)
    burst.set(burst.out() + 1, when=is_a & ~burst_done)

    st.set(u(ST_W, ST_N), when=is_p & rp_at_wr)
    rp.set(rp.out() + 1, when=is_p & ~rp_at_wr)

    st.set(u(ST_W, ST_N), when=is_default)

    st.set(u(ST_W, ST_N), when=port_rst)
    burst.set(u(BURST_W, 0), when=port_rst)
    rp.set(u(PTR_W, 0), when=port_rst)

    m.output("state", st.out())
    m.output("send_idle", is_a & (burst.out() == 0))
    m.output("send_ack", is_a & ~(burst.out() == 0))
    m.output("replay", is_p)
    m.output("rd_ptr", rp.out())


build.__pycircuit_name__ = "vibe_dll_retry_ack_sm"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_retry_ack_sm").emit_mlir())
