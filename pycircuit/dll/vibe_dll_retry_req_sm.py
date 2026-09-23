"""vibe_dll_retry_req_sm — DLL RETRY_REQ_SM (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll_retry_req_sm.sv``. Ports match tip
``1891dec0`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``device_rst`` /
``start_retry`` / ``phy_retrain`` / ``wait_done_ack`` /
``state[2:0]`` / ``drop_data`` / ``retrain_req`` / ``retry_error`` /
``send_idle`` / ``send_req`` / ``send_cnt[4:0]``). Seventh DLL leaf
after ``vibe_bcrc`` / ``vibe_dll_credit`` / ``vibe_dll_sm`` /
``vibe_dll_rx`` / ``vibe_dll_retry_ack_sm`` /
``vibe_dll_retry_buf``. NORMAL / REQ (1 Idle + burst Req) / WAIT
(``RETRY_WAIT_CYC``, default 12500) / RETRAIN / ERROR.
``VIBE_NUM_RETRY`` / ``VIBE_NUM_PHY_REINIT`` from
``vibe_ub_params.vh``. Self-contained (no child instances).
Instantiated by ``vibe_dll`` (``u_req``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and ``include "vibe_ub_params.vh"``. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_tx``, and ``vibe_dll`` top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

ST_W = 3
BURST_W = 6
RETRY_W = 4
PHY_W = 3
WTMR_W = 24
CNT_W = 5
ST_N = 0
ST_Q = 1
ST_W_ST = 2
ST_R = 3
ST_E = 4
REQ_BURST = 32
RETRY_WAIT_CYC = 12500
VIBE_NUM_RETRY = 15
VIBE_NUM_PHY_REINIT = 4


@module(name="vibe_dll_retry_req_sm")
def build(m: Circuit) -> None:
    """RETRY_REQ_SM: NORMAL / REQ / WAIT / RETRAIN / ERROR.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, device_rst, start_retry, phy_retrain
        wait_done_ack, state[2:0], drop_data, retrain_req
        retry_error, send_idle, send_req, send_cnt[4:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``start_retry`` in
    ``ST_N`` → ``ST_Q`` with ``burst=0`` (Idle). Then burst Req
    (``burst`` 1..32). At ``burst==32`` increment ``num_retry``;
    if ``num_retry+1==VIBE_NUM_RETRY`` or ``phy_retrain`` enter
    ``ST_R``, else ``ST_W`` with ``wtmr=RETRY_WAIT_CYC``. WAIT:
    ``wait_done_ack`` → ``ST_N``; ``wtmr==0`` → ``ST_Q``.
    RETRAIN increments ``num_phy``; ``==VIBE_NUM_PHY_REINIT`` →
    ``ST_E`` else ``ST_N``. ``port_rst || device_rst`` clears
    (not ``wtmr``). Combo: ``drop_data`` REQ|WAIT,
    ``retrain_req=(st==ST_R)``, ``retry_error=(st==ST_E)``,
    ``send_idle=(st==ST_Q)&&(burst==0)``,
    ``send_req=(st==ST_Q)&&(burst!=0)``, ``send_cnt=burst[4:0]``.
    Default (illegal ``st``) → ``ST_N``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    device_rst = m.input("device_rst", width=1)
    start_retry = m.input("start_retry", width=1)
    phy_retrain = m.input("phy_retrain", width=1)
    wait_done_ack = m.input("wait_done_ack", width=1)

    st = m.out("st", clk=clk, rst=rst, width=ST_W, init=u(ST_W, ST_N))
    num_retry = m.out("num_retry", clk=clk, rst=rst, width=RETRY_W, init=u(RETRY_W, 0))
    num_phy = m.out("num_phy", clk=clk, rst=rst, width=PHY_W, init=u(PHY_W, 0))
    wtmr = m.out("wtmr", clk=clk, rst=rst, width=WTMR_W, init=u(WTMR_W, 0))
    burst = m.out("burst", clk=clk, rst=rst, width=BURST_W, init=u(BURST_W, 0))

    is_n = st.out() == ST_N
    is_q = st.out() == ST_Q
    is_w = st.out() == ST_W_ST
    is_r = st.out() == ST_R
    is_e = st.out() == ST_E
    is_default = ~(is_n | is_q | is_w | is_r | is_e)
    burst_done = burst.out() == REQ_BURST
    retry_cap = (num_retry.out() + 1) == VIBE_NUM_RETRY
    phy_cap = (num_phy.out() + 1) == VIBE_NUM_PHY_REINIT
    to_retrain = retry_cap | phy_retrain
    wtmr_zero = wtmr.out() == 0
    enter_req = is_n & start_retry
    q_done = is_q & burst_done
    w_ack = is_w & wait_done_ack
    w_to = is_w & ~wait_done_ack & wtmr_zero
    port_clear = port_rst | device_rst

    # Case NBA first; port_rst / device_rst last so they win
    # (stock if/else). wtmr is *not* cleared on port_clear
    # (stock). Entity rst is async-low in the product SV, not
    # a pin here.
    st.set(u(ST_W, ST_Q), when=enter_req)
    burst.set(u(BURST_W, 0), when=enter_req)

    burst.set(burst.out() + 1, when=is_q & ~burst_done)
    num_retry.set(num_retry.out() + 1, when=q_done)
    st.set(u(ST_W, ST_R), when=q_done & to_retrain)
    st.set(u(ST_W, ST_W_ST), when=q_done & ~to_retrain)
    wtmr.set(u(WTMR_W, RETRY_WAIT_CYC), when=q_done & ~to_retrain)

    st.set(u(ST_W, ST_N), when=w_ack)
    st.set(u(ST_W, ST_Q), when=w_to)
    burst.set(u(BURST_W, 0), when=w_to)
    wtmr.set(wtmr.out() - 1, when=is_w & ~wait_done_ack & ~wtmr_zero)

    num_phy.set(num_phy.out() + 1, when=is_r)
    st.set(u(ST_W, ST_E), when=is_r & phy_cap)
    st.set(u(ST_W, ST_N), when=is_r & ~phy_cap)

    st.set(u(ST_W, ST_N), when=is_default)

    st.set(u(ST_W, ST_N), when=port_clear)
    num_retry.set(u(RETRY_W, 0), when=port_clear)
    num_phy.set(u(PHY_W, 0), when=port_clear)
    burst.set(u(BURST_W, 0), when=port_clear)

    m.output("state", st.out())
    m.output("drop_data", is_q | is_w)
    m.output("retrain_req", is_r)
    m.output("retry_error", is_e)
    m.output("send_idle", is_q & (burst.out() == 0))
    m.output("send_req", is_q & ~(burst.out() == 0))
    m.output("send_cnt", burst.out().slice(lsb=0, width=CNT_W))


build.__pycircuit_name__ = "vibe_dll_retry_req_sm"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_retry_req_sm").emit_mlir())
