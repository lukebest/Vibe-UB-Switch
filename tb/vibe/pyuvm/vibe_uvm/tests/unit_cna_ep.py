"""Module-level uvm-python TC for Decision-I leaf vibe_cna_ep.

Covers idle / no-hit (consume=0, vld=0, echo data=0, icrc_fail=0),
stock Icarus tc_cna_ep vectors (DCNA==written CNA terminate+echo,
NLP=1 miss-CNA terminate+echo, miss CNA NLP=0 forward, power-on
CNA unwritten no match), per-port walk-1 of fab_mgmt_cfg6_hit,
combo drop after hit deassert (not sticky), ready unused (term
still consume+vld+echo), NLP=1 with CNA unwritten still terms,
and RTL opcode 0x10 as flit[103:96] only: 0x10 without us does
not terminate; 0x10 with us still echos the request (no CFG6
CSR assemble, no Appendix D offsets, no identity constants).
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze,
or signoff.

Matches product rtl/mgmt/vibe_cna_ep.sv: combo terminate
us || (nlp==1) || (opc==8'h10 && us), echo
fab_mgmt_cfg6_data, icrc_fail tied 0. clk / rst_n /
mgmt_nw_ready unused in the body. Instantiated by vibe_mgmt
u_cna. Stock Icarus tc_cna_ep remains the official TP scorer
(vibe_cna_ep_cocotb_top, wrap-style). This is not the
wrap-style tc_cna_ep / tc_mgmt. ovf_l (F1) is not in this
module. CFG6 R/W / Appendix D packing is 未知 — do not invent.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

PORT_N = 4
MASK4 = 0xF
MASK512 = (1 << 512) - 1
MASK352 = (1 << 352) - 1
STOCK_CNA = 0x1111
STOCK_MISS = 0x2222
HIER = "u_u.mgmt_fab_cfg6_consume / u_u.mgmt_nw_vld / u_u.mgmt_nw_data"


def cfg6_beat(dcna, nlp=0, opc=0, tag=0):
    """Stock CFG6 flit0 + distinct payload tag. No Appendix D pack."""
    flit = lph.mk_flit(6, 0, 0, 2, dcna, lph.plen_nflit(1), 0, 0, nlp, opc)
    return lph.mk_beat(flit, int(tag) & MASK352)


def golden(cna, cna_written, hit, beats):
    """Combo vs product always @*: term → consume+vld+echo; else 0."""
    consume = 0
    vld = 0
    data = [0] * PORT_N
    hit = int(hit) & MASK4
    for p in range(PORT_N):
        beat = int(beats[p]) & MASK512
        if (hit >> p) & 1:
            flit = lph.nw512_flit0(beat)
            if lph.cfg6_should_term(bool(cna_written), int(cna) & 0xFFFF, flit):
                consume |= 1 << p
                vld |= 1 << p
                data[p] = beat
    return consume, vld, data, 0


class tc_vibe_cna_ep(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, cna=STOCK_CNA, written=1, ready=0xF):
        d = self.dut
        sset(d.cna, int(cna) & 0xFFFF)
        sset(d.cna_written, 1 if written else 0)
        sset(d.fab_mgmt_cfg6_hit, 0)
        sset(d.mgmt_nw_ready, int(ready) & MASK4)
        for p in range(PORT_N):
            sset(getattr(d, f"fab_mgmt_cfg6_data_{p}"), 0)

    async def _hold_reset(self, n=2):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=1):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _settle(self):
        await Timer(1, "NS")

    def _drive(self, cna, written, hit, beats, ready=0xF):
        d = self.dut
        sset(d.cna, int(cna) & 0xFFFF)
        sset(d.cna_written, 1 if written else 0)
        sset(d.mgmt_nw_ready, int(ready) & MASK4)
        for p in range(PORT_N):
            sset(getattr(d, f"fab_mgmt_cfg6_data_{p}"), int(beats[p]) & MASK512)
        sset(d.fab_mgmt_cfg6_hit, int(hit) & MASK4)

    def _sample(self):
        d = self.dut
        consume = ival(d.consume, None)
        vld = ival(d.mgmt_nw_vld, None)
        icrc = ival(d.icrc_fail, None)
        data = [ival(getattr(d, f"mgmt_nw_data_{p}"), None) for p in range(PORT_N)]
        return consume, vld, data, icrc

    def _score(self, name, stim, cna, written, hit, beats, ready=0xF):
        exp_c, exp_v, exp_d, exp_i = golden(cna, written, hit, beats)
        got_c, got_v, got_d, got_i = self._sample()
        if None in (got_c, got_v, got_i) or any(x is None for x in got_d):
            self.bad(name, stim,
                     f"consume={exp_c:#x} vld={exp_v:#x} echo resolved icrc=0",
                     f"consume={got_c} vld={got_v} data={got_d} icrc={got_i}",
                     HIER)
            return False
        if got_c != exp_c or got_v != exp_v or got_i != exp_i:
            self.bad(name, stim,
                     f"consume={exp_c:#x} vld={exp_v:#x} icrc_fail={exp_i}",
                     f"consume={got_c:#x} vld={got_v:#x} icrc_fail={got_i}",
                     HIER)
            return False
        for p in range(PORT_N):
            if got_d[p] != exp_d[p]:
                self.bad(name, f"{stim} (echo port {p})",
                         f"mgmt_nw_data={exp_d[p]:#x} (request echo)",
                         f"mgmt_nw_data={got_d[p]:#x}",
                         f"u_u.mgmt_nw_data[{p}]")
                return False
        ready_v = ival(self.dut.mgmt_nw_ready, None)
        if ready_v is not None and (ready_v & MASK4) != (int(ready) & MASK4):
            self.bad(name, f"{stim} (ready hold)",
                     f"mgmt_nw_ready={int(ready) & MASK4:#x} (unused)",
                     f"mgmt_nw_ready={ready_v:#x}",
                     "mgmt_nw_ready")
            return False
        return True

    async def _apply(self, name, stim, cna, written, hit, beats, ready=0xF):
        self._drive(cna, written, hit, beats, ready)
        await self._settle()
        return self._score(name, stim, cna, written, hit, beats, ready)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_cna_ep"
        zeros = [0] * PORT_N

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        await self._settle()

        # 1. Idle / no-hit after reset: all outputs 0, icrc_fail=0.
        if not await self._apply(
                name, "reset then release, hit=0",
                STOCK_CNA, 1, 0, zeros):
            phase.drop_objection(self)
            return

        # 2. Stock Icarus tc_cna_ep: DCNA==written CNA → consume+echo.
        beats = list(zeros)
        beats[0] = cfg6_beat(STOCK_CNA, tag=0xA11A)
        if not await self._apply(
                name, "stock DCNA==written CNA (Icarus tc_cna_ep)",
                STOCK_CNA, 1, 0x1, beats):
            phase.drop_objection(self)
            return
        if not await self._apply(
                name, "stock match deasserted (combo drop, not sticky)",
                STOCK_CNA, 1, 0, beats):
            phase.drop_objection(self)
            return

        # 3. Stock NLP=1 DCNA!=CNA → consume+echo.
        beats = list(zeros)
        beats[1] = cfg6_beat(STOCK_MISS, nlp=1, tag=0xB22B)
        if not await self._apply(
                name, "stock NLP=1 DCNA!=CNA (Icarus tc_cna_ep)",
                STOCK_CNA, 1, 0x2, beats):
            phase.drop_objection(self)
            return

        # 4. Stock miss CNA NLP=0 → forward (no consume, data=0).
        beats = list(zeros)
        beats[2] = cfg6_beat(STOCK_MISS, tag=0xC33C)
        if not await self._apply(
                name, "stock miss CNA NLP=0 (Icarus tc_cna_ep)",
                STOCK_CNA, 1, 0x4, beats):
            phase.drop_objection(self)
            return

        # 5. Stock CNA unwritten, DCNA==cna → no match.
        beats = list(zeros)
        beats[3] = cfg6_beat(STOCK_CNA, tag=0xD44D)
        if not await self._apply(
                name, "stock CNA unwritten (Icarus tc_cna_ep)",
                STOCK_CNA, 0, 0x8, beats):
            phase.drop_objection(self)
            return

        # 6. Walk-1 hit on every port (match + miss).
        match = cfg6_beat(STOCK_CNA, tag=0x11110001)
        miss = cfg6_beat(STOCK_MISS, tag=0x22220002)
        for p in range(PORT_N):
            beats = list(zeros)
            beats[p] = match
            if not await self._apply(
                    name, f"walk-1 hit[{p}] DCNA==written CNA",
                    STOCK_CNA, 1, 1 << p, beats):
                phase.drop_objection(self)
                return
            beats[p] = miss
            if not await self._apply(
                    name, f"walk-1 hit[{p}] miss CNA NLP=0",
                    STOCK_CNA, 1, 1 << p, beats):
                phase.drop_objection(self)
                return

        # 7. Ready unused: term still consume+vld+echo when ready=0.
        beats = list(zeros)
        beats[0] = cfg6_beat(STOCK_CNA, tag=0xE55E)
        if not await self._apply(
                name, "term while mgmt_nw_ready=0 (ready unused)",
                STOCK_CNA, 1, 0x1, beats, ready=0):
            phase.drop_objection(self)
            return

        # 8. NLP=1 with CNA unwritten still terms (nlp does not need us).
        beats = list(zeros)
        beats[2] = cfg6_beat(STOCK_MISS, nlp=1, tag=0xF66F)
        if not await self._apply(
                name, "NLP=1 CNA unwritten (still term)",
                STOCK_CNA, 0, 0x4, beats):
            phase.drop_objection(self)
            return

        # 9. Opcode 0x10 as RTL flit[103:96] only. Without us: no term.
        # Do not invent Appendix D / identity / CFG6 CSR payload.
        beats = list(zeros)
        beats[1] = cfg6_beat(STOCK_MISS, opc=0x10, tag=0x1010)
        if not await self._apply(
                name, "opc=0x10 without us (RTL opc&&us; no Appendix D term)",
                STOCK_CNA, 1, 0x2, beats):
            phase.drop_objection(self)
            return

        # 10. Opcode 0x10 with us: still echo the request (not a CSR read).
        beats = list(zeros)
        beats[0] = cfg6_beat(STOCK_CNA, opc=0x10, tag=0x1011)
        if not await self._apply(
                name, "opc=0x10 with us (echo request; no CFG6 CSR assemble)",
                STOCK_CNA, 1, 0x1, beats):
            phase.drop_objection(self)
            return

        # 11. Multi-port mix: match / NLP / miss / unwritten-port data.
        beats = [
            cfg6_beat(STOCK_CNA, tag=0x1000),
            cfg6_beat(STOCK_MISS, nlp=1, tag=0x2000),
            cfg6_beat(STOCK_MISS, tag=0x3000),
            cfg6_beat(0x3333, tag=0x4000),
        ]
        if not await self._apply(
                name, "hit=0xF mix match/NLP/miss/miss",
                STOCK_CNA, 1, 0xF, beats):
            phase.drop_objection(self)
            return

        # 12. 16-bit CNA edges (0 / 0xFFFF). Not a 24-bit window.
        for cna in (0x0000, 0xFFFF):
            beats = list(zeros)
            beats[3] = cfg6_beat(cna, tag=cna)
            if not await self._apply(
                    name, f"16-bit CNA={cna:#06x} match",
                    cna, 1, 0x8, beats):
                phase.drop_objection(self)
                return

        # 13. Leaf has no wrap / invented CFG6 CSR / Port Reset pins.
        for absent in ("port_rst", "device_rst", "cfg_rd_data", "guid0",
                       "class_code", "port_basic", "irq_logic",
                       "appendix_d"):
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_cna_ep product port",
                         f"{absent} present", "vibe_cna_ep_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("cna", "cna_written", "consume", "mgmt_nw_vld",
                     "icrc_fail", "mgmt_nw_data_0"):
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_cna_ep_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_cna_ep)
