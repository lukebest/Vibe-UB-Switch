"""vibe_vl_rr — fabric VL round-robin (AS-0.1 §8).

Product module: ``rtl/fabric/vibe_vl_rr.sv``. Ports match tip
``450ed1c2`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``nonempty[15:0]`` /
``grant`` / ``vl_sel[3:0]`` / ``valid``). Second fabric leaf
after ``vibe_fecn_mark``. RR among non-empty VOQs of an egress;
FCFS within VL; no SL. On ``grant && valid`` advance ``rr`` to
``vl_sel+1``. Reset clears ``rr``. Self-contained (no child
instances). Instantiated by ``vibe_fabric`` (``u_rr``).

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and the stock combo for-loop pick. Landed SV is hand-finished to
keep those freeze semantics. Leave PCS tx / rx tops,
``vibe_dll_tx``, and ``vibe_dll`` top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

VL_N = 16
VL_W = 4
NE_W = 16


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


def _bit_sel(m: Circuit, vec, idx, nbits: int = VL_N):
    """Combo ``vec[idx]`` via constant-slice mux (``idx`` is 4-bit)."""
    bit = vec.slice(lsb=0, width=1)
    for j in range(1, nbits):
        bit = _mux(m, idx == j, vec.slice(lsb=j, width=1), bit, 1)
    return bit


def _or_reduce(vec, nbits: int = VL_N):
    """Combo ``|vec``."""
    acc = vec.slice(lsb=0, width=1)
    for j in range(1, nbits):
        acc = acc | vec.slice(lsb=j, width=1)
    return acc


@module(name="vibe_vl_rr")
def build(m: Circuit) -> None:
    """VL RR: first nonempty VOQ from ``rr``, wrap 16 VLs.

    Product ports (hand-finished SV)::

        clk, rst_n, nonempty[15:0], grant, vl_sel[3:0], valid

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. Combo: ``valid = |nonempty``;
    scan ``p = rr, rr+1, ...`` and take the first ``nonempty[p]``
    as ``vl_sel`` (default ``rr`` if none). Seq: ``!rst_n`` →
    ``rr=0``; else ``grant && valid`` → ``rr <= vl_sel+1``.
    No SL. FCFS within VL is the VOQ, not this leaf.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    nonempty = m.input("nonempty", width=NE_W)
    grant = m.input("grant", width=1)

    rr = m.out("rr", clk=clk, rst=rst, width=VL_W, init=u(VL_W, 0))

    valid = _or_reduce(nonempty)
    found = u(1, 0)
    pick = rr.out()
    for k in range(VL_N):
        cand = rr.out() + u(VL_W, k)
        hit = _bit_sel(m, nonempty, cand)
        take = hit & ~found
        pick = _mux(m, take, cand, pick, VL_W)
        found = found | hit

    rr.set(pick + u(VL_W, 1), when=grant & valid)

    m.output("vl_sel", pick)
    m.output("valid", valid)


build.__pycircuit_name__ = "vibe_vl_rr"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_vl_rr").emit_mlir())
