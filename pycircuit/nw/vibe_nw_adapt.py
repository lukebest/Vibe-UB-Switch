"""vibe_nw_adapt — NW 512b vld/ready adapter (AS-0.1).

Product module: ``rtl/nw/vibe_nw_adapt.sv``. Ports match tip
``2b4a8408`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Combo leaf (``clk`` / ``rst_n`` unused in the body;
``link_ready``; FAB→NW VOQ 512b ``fab_nw_data`` / ``fab_nw_vld`` /
``fab_nw_ready``; mgmt inject priority ``mgmt_nw_data`` /
``mgmt_nw_vld`` / ``mgmt_nw_ready``; NW→DLL ``nw_dll_data`` /
``nw_dll_vld`` / ``nw_dll_ready``; DLL→NW ``dll_nw_data`` /
``dll_nw_vld`` / ``dll_nw_ready``; NW→FAB SAF ingress
``nw_fab_data`` / ``nw_fab_vld`` / ``nw_fab_ready``). Second NW
leaf after stage-36 ``vibe_icrc``. LinkReady in ready (U21 /
FS-0.2.7). Mgmt reply injects on ingress TX before
``nw_adapt_tx``, priority over VOQ. Self-contained (no child
instances). Instantiated by ``vibe_port`` (``u_nw``).

pyCircuit expresses the combo mux / ready tree. Product RTL
keeps the stock ``assign`` body. ``clk`` / ``rst_n`` stay on
the pin list (port wires them); the combo body does not
sample them. Landed SV is hand-finished to keep those freeze
semantics. Leave PCS tx / rx tops, ``vibe_port`` /
``vibe_ub_switch`` tops, other NW helpers, and ``vibe_fabric``
top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DATA_W = 512


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


@module(name="vibe_nw_adapt")
def build(m: Circuit) -> None:
    """512b NW vld/ready. LinkReady in ready; mgmt pri over VOQ.

    Product ports (hand-finished SV)::

        clk, rst_n, link_ready
        fab_nw_data[511:0], fab_nw_vld, fab_nw_ready
        mgmt_nw_data[511:0], mgmt_nw_vld, mgmt_nw_ready
        nw_dll_data[511:0], nw_dll_vld, nw_dll_ready
        dll_nw_data[511:0], dll_nw_vld, dll_nw_ready
        nw_fab_data[511:0], nw_fab_vld, nw_fab_ready

    ``clk`` / ``rst_n`` are unused in the combo body (stock).
    Finish keeps the pins so ``vibe_port`` wiring stays.
    TX: ``mgmt_nw_ready = link_ready && nw_dll_ready``;
    ``fab_nw_ready = link_ready && nw_dll_ready && !mgmt_nw_vld``;
    ``nw_dll_vld = link_ready && (mgmt_nw_vld || fab_nw_vld)``;
    ``nw_dll_data = mgmt_nw_vld ? mgmt_nw_data : fab_nw_data``.
    RX: ``dll_nw_ready = nw_fab_ready``; ``nw_fab_vld = dll_nw_vld``;
    ``nw_fab_data = dll_nw_data``.
    """
    # Product pin list. Combo mux does not clock or reset.
    m.input("clk", width=1)
    m.input("rst_n", width=1)
    link_ready = m.input("link_ready", width=1)
    fab_nw_data = m.input("fab_nw_data", width=DATA_W)
    fab_nw_vld = m.input("fab_nw_vld", width=1)
    mgmt_nw_data = m.input("mgmt_nw_data", width=DATA_W)
    mgmt_nw_vld = m.input("mgmt_nw_vld", width=1)
    nw_dll_ready = m.input("nw_dll_ready", width=1)
    dll_nw_data = m.input("dll_nw_data", width=DATA_W)
    dll_nw_vld = m.input("dll_nw_vld", width=1)
    nw_fab_ready = m.input("nw_fab_ready", width=1)

    dll_ok = link_ready & nw_dll_ready
    mgmt_nw_ready = dll_ok
    fab_nw_ready = dll_ok & ~mgmt_nw_vld
    nw_dll_vld = link_ready & (mgmt_nw_vld | fab_nw_vld)
    nw_dll_data = _mux(m, mgmt_nw_vld, mgmt_nw_data, fab_nw_data, DATA_W)

    dll_nw_ready = nw_fab_ready
    nw_fab_vld = dll_nw_vld
    nw_fab_data = dll_nw_data

    m.output("fab_nw_ready", fab_nw_ready)
    m.output("mgmt_nw_ready", mgmt_nw_ready)
    m.output("nw_dll_data", nw_dll_data)
    m.output("nw_dll_vld", nw_dll_vld)
    m.output("dll_nw_ready", dll_nw_ready)
    m.output("nw_fab_data", nw_fab_data)
    m.output("nw_fab_vld", nw_fab_vld)


build.__pycircuit_name__ = "vibe_nw_adapt"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_nw_adapt").emit_mlir())
