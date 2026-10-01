"""vibe_lmsm — LMSM this-rev subset wrap (AS-0.1 §11).

Product module: ``rtl/lmsm/vibe_lmsm.sv``. Ports match tip
``eb452e32`` (product DUT after PR256 TB-only; RTL same as
``f8ed45ac`` / PR255 stage-48). Decision I
UNFROZEN (do not re-pin freeze). SPEC / CR-B names are
unchanged. Leaf FSM wrap (``clk`` / ``rst_n`` / ``port_rst`` /
``lmsm_go`` / 4b ``am_locked`` / ``lid_bad`` /
``lane0_fail`` / ``eq_negotiated`` / ``retrain_req`` /
``link_up`` / ``link_ready`` / ``sdf_period`` / 5b
``state`` / ``width_fail``). First LMSM wrap after
stage-48 ``vibe_pcs_rx``. Tip stock has **zero** child
instances — ``CHILDREN`` is empty; do not invent
hierarchy or split the FSM. Do not invent Probe,
RXEQ_Optimize, Change_Speed, or QDLWS. Preserve the
stock FSM (states, ``tmr_load``, always blocks, assigns,
``vibe_ub_params.vh`` include) byte-identical. Do not
invent CFG6 packing, Appendix D, or opcode 0x10. Do not
rewrite F1 ``ovf_l`` (lives under ``vibe_port``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own in the frontend.
Product RTL keeps **async active-low** ``rst_n`` and the
stock FSM. Landed SV is hand-finished so the stock
module body (ports / states / ``tmr_load`` / always
blocks / assigns / include) stays byte-identical.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

AM_LOCKED_W = 4
STATE_W = 5

# Product is a leaf FSM (hand-finished SV). pycc prototype
# does not emit the FSM; CHILDREN is empty — do not invent
# hierarchy or split the stock state machine.
CHILDREN = ()


@module(name="vibe_lmsm")
def build(m: Circuit) -> None:
    """LMSM this-rev subset wrap: leaf FSM, no children.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, lmsm_go, am_locked[3:0],
        lid_bad, lane0_fail, eq_negotiated, retrain_req,
        link_up, link_ready, sdf_period, state[4:0],
        width_fail

    pyCircuit clock is ``clk``. Reset here is ``rst``
    (active-high). Product SV keeps async-low ``rst_n``.
    Frontend parks FSM-driven outputs at 0 (same pattern
    as stage-47 ``vibe_pcs_tx`` / stage-48 ``vibe_pcs_rx``).
    Product SV is the stock FSM; ``CHILDREN`` is empty.
    Do not invent Probe / RXEQ / Change_Speed / QDLWS.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    lmsm_go = m.input("lmsm_go", width=1)
    am_locked = m.input("am_locked", width=AM_LOCKED_W)
    lid_bad = m.input("lid_bad", width=1)
    lane0_fail = m.input("lane0_fail", width=1)
    eq_negotiated = m.input("eq_negotiated", width=1)
    retrain_req = m.input("retrain_req", width=1)

    # Keep wrap inputs in the frontend graph. Product SV is
    # the stock leaf FSM; this prototype does not emit it.
    _keep = (
        port_rst
        | lmsm_go
        | lid_bad
        | lane0_fail
        | eq_negotiated
        | retrain_req
        | (am_locked == 0)
    )
    _ = (clk, rst, _keep, CHILDREN)

    m.output("link_up", u(1, 0))
    m.output("link_ready", u(1, 0))
    m.output("sdf_period", u(1, 0))
    m.output("state", u(STATE_W, 0))
    m.output("width_fail", u(1, 0))


build.__pycircuit_name__ = "vibe_lmsm"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_lmsm").emit_mlir())
