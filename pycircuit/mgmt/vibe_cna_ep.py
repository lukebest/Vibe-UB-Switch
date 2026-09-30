"""vibe_cna_ep — CFG6 terminate / echo (AS-0.1.2 §9/§13).

Product module: ``rtl/mgmt/vibe_cna_ep.sv``. Ports match tip
``cf64951b``. Decision I UNFROZEN (do not re-pin freeze).
SPEC / CR-B names are unchanged. Combo leaf
(``clk`` / ``rst_n`` unused in the body; 16b ``cna`` /
``cna_written``; 4b ``fab_mgmt_cfg6_hit``; unpacked
``fab_mgmt_cfg6_data[511:0][0:3]``; 4b
``mgmt_fab_cfg6_consume``; unpacked
``mgmt_nw_data[511:0][0:3]``; 4b ``mgmt_nw_vld``; 4b
``mgmt_nw_ready`` unused; ``icrc_fail``). Fourth mgmt
leaf after stage-38 ``vibe_rst_ctl``, stage-39
``vibe_mgmt_byp``, and stage-40 ``vibe_irq_agg``.
CFG6 terminate if DCNA==mgmt CNA AND CNA written, OR
NLP=1, OR opcode 0x10 (stock: ``opc==8'h10 && us``).
ICRC only as sender/receiver (this leaf drives
``icrc_fail=0``; no ICRC unit). Power-on CNA UNKNOWN
until static write. Echos the request — does **not**
assemble a CFG6 CSR read. Official opcode 0x10 /
Appendix D packing is 未知 — do not invent.
Self-contained (no child instances). Instantiated by
``vibe_mgmt``.

pyCircuit expresses the combo terminate / echo tree.
Unpacked product arrays are flattened here
(``fab_mgmt_cfg6_data_0..3``, ``mgmt_nw_data_0..3``).
``clk`` / ``rst_n`` / ``mgmt_nw_ready`` stay on the pin
list (wrap wires them); the combo body does not sample
them. Landed SV is hand-finished to keep those tip
semantics. Leave ``vibe_cfg_space`` and the
``vibe_mgmt`` / ``vibe_port`` / ``vibe_top`` wraps for
later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
DATA_W = 512
FLIT0_W = 160
CNA_W = 16
NLP_W = 3
OPC_W = 8
OPC_CFG = 0x10


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


def _cat_lsb_first(m: Circuit, bits):
    """Pack ``bits[0]`` as LSB (``m.cat`` is MSB-first)."""
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


def _nw512_flit0(beat):
    """Stock ``vibe_nw512_flit0``: first 20 B at ``beat[511:352]``."""
    return beat.slice(lsb=352, width=FLIT0_W)


def _nth_dcna(flit):
    """Stock ``vibe_nth_dcna``: ``flit[63:48]``."""
    return flit.slice(lsb=48, width=CNA_W)


def _nth_nlp(flit):
    """Stock ``vibe_nth_nlp``: ``flit[95:93]``."""
    return flit.slice(lsb=93, width=NLP_W)


def _opcode(flit):
    """Opcode in first assembled flit: ``flit[103:96]``."""
    return flit.slice(lsb=96, width=OPC_W)


def _cfg6_should_term(cna_written, cna, flit):
    """Stock ``vibe_cfg6_should_term`` / leaf ``term``.

    ``us || (nlp==1) || ((opc==8'h10) && us)``. Do not invent
    opcode 0x10 / Appendix D packing beyond this match.
    """
    dcna = _nth_dcna(flit)
    nlp = _nth_nlp(flit)
    opc = _opcode(flit)
    us = cna_written & (dcna == cna)
    return us | (nlp == u(NLP_W, 1)) | ((opc == u(OPC_W, OPC_CFG)) & us)


@module(name="vibe_cna_ep")
def build(m: Circuit) -> None:
    """CFG6 terminate / echo. Power-on CNA UNKNOWN until written.

    Product ports (hand-finished SV)::

        clk, rst_n, cna[15:0], cna_written
        fab_mgmt_cfg6_hit[3:0], fab_mgmt_cfg6_data[511:0][0:3]
        mgmt_fab_cfg6_consume[3:0], mgmt_nw_data[511:0][0:3]
        mgmt_nw_vld[3:0], mgmt_nw_ready[3:0], icrc_fail

    ``clk`` / ``rst_n`` / ``mgmt_nw_ready`` are unused in the
    combo body (stock). Finish keeps the pins so ``vibe_mgmt``
    wiring stays. Per port: on ``fab_mgmt_cfg6_hit[p]``, take
    flit0, compute ``us`` / ``term``. On ``term``: consume,
    ``mgmt_nw_vld``, echo ``fab_mgmt_cfg6_data`` (no CFG6 CSR
    read assemble). ``icrc_fail`` is tied 0.
    """
    # Product pin list. Combo terminate does not clock or reset.
    m.input("clk", width=1)
    m.input("rst_n", width=1)
    cna = m.input("cna", width=CNA_W)
    cna_written = m.input("cna_written", width=1)
    fab_mgmt_cfg6_hit = m.input("fab_mgmt_cfg6_hit", width=PORT_N)
    fab_mgmt_cfg6_data = [
        m.input(f"fab_mgmt_cfg6_data_{p}", width=DATA_W) for p in range(PORT_N)
    ]
    # Wrap wires ready; combo echo does not sample it.
    m.input("mgmt_nw_ready", width=PORT_N)

    consume_bits = []
    vld_bits = []
    for p in range(PORT_N):
        hit = fab_mgmt_cfg6_hit.slice(lsb=p, width=1)
        beat = fab_mgmt_cfg6_data[p]
        flit = _nw512_flit0(beat)
        term = hit & _cfg6_should_term(cna_written, cna, flit)
        consume_bits.append(term)
        vld_bits.append(term)
        m.output(f"mgmt_nw_data_{p}", _mux(m, term, beat, u(DATA_W, 0), DATA_W))

    m.output("mgmt_fab_cfg6_consume", _cat_lsb_first(m, consume_bits))
    m.output("mgmt_nw_vld", _cat_lsb_first(m, vld_bits))
    m.output("icrc_fail", u(1, 0))


build.__pycircuit_name__ = "vibe_cna_ep"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_cna_ep").emit_mlir())
