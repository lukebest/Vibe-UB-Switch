"""vibe_dll_sm — DLL link SM (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll_sm.sv``. Ports match tip
``39d3aa1d`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``port_rst`` / ``link_up`` /
``param_ok`` / ``credit_ok`` / ``dll_error`` / ``state[1:0]`` /
``status_up`` / ``disabled``). Third DLL leaf after ``vibe_bcrc``
and ``vibe_dll_credit``. Disabled when ``LinkUp==0``. Entity
reset must not force Disabled via ``rst`` alone beyond async
``rst_n`` / ``port_rst``. States Disabled → Param → Credit →
Normal. ``dll_error`` → Disabled. ``status_up`` when Normal.
Self-contained (no child instances). Instantiated by
``vibe_dll`` (``u_sm``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``).
Landed SV is hand-finished to keep those freeze semantics. Leave
PCS tx / rx tops and remaining DLL wraps (retry_*, tx/rx, dll
top) for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

ST_W = 2
ST_DIS = 0
ST_PARM = 1
ST_CRD = 2
ST_NRM = 3


@module(name="vibe_dll_sm")
def build(m: Circuit) -> None:
    """DLL link SM: Disabled / Param / Credit / Normal.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, link_up, param_ok, credit_ok, dll_error
        state[1:0], status_up, disabled

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. There is no entity-reset
    pin: only ``rst_n`` / ``port_rst`` / ``!link_up`` / ``dll_error``
    force ``ST_DIS``. Else ``ST_DIS`` → ``ST_PARM`` → (``param_ok``)
    ``ST_CRD`` → (``credit_ok``) ``ST_NRM``. Combo:
    ``disabled=(st==ST_DIS)``, ``status_up=(st==ST_NRM)``,
    ``state=st``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    link_up = m.input("link_up", width=1)
    param_ok = m.input("param_ok", width=1)
    credit_ok = m.input("credit_ok", width=1)
    dll_error = m.input("dll_error", width=1)

    st = m.out("st", clk=clk, rst=rst, width=ST_W, init=u(ST_W, ST_DIS))

    is_dis = st.out() == ST_DIS
    is_parm = st.out() == ST_PARM
    is_crd = st.out() == ST_CRD
    is_default = ~(is_dis | is_parm | is_crd)
    force_dis = port_rst | ~link_up | dll_error

    # Case NBA first; port_rst / !link_up / dll_error last so they
    # win (stock if/else). Entity rst is not a pin.
    st.set(u(ST_W, ST_PARM), when=is_dis)
    st.set(u(ST_W, ST_CRD), when=is_parm & param_ok)
    st.set(u(ST_W, ST_NRM), when=is_crd & credit_ok)
    st.set(u(ST_W, ST_NRM), when=is_default)
    st.set(u(ST_W, ST_DIS), when=force_dis)

    m.output("state", st.out())
    m.output("status_up", st.out() == ST_NRM)
    m.output("disabled", is_dis)


build.__pycircuit_name__ = "vibe_dll_sm"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll_sm").emit_mlir())
