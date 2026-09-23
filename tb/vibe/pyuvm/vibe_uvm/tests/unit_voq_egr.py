"""Module-level uvm-python TC for Decision-I leaf vibe_voq_egr.

Covers reset clearing deadlock_* / wptr / rptr (combo wr_ready=1,
nonempty=0, occ_vl0=0); wr then rd same VL data/sop/eop; wr_ready
backpressure when occ==DEPTH; nonempty bit per VL; short
deadlock_drop after VIBE_US_CYC aging (1250 clk, included — sim
time stays a few microseconds). Not a full-chip consecutive-green
gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/fabric/vibe_voq_egr.sv: async-low rst_n, combo
occ/wr_ready/rd_*/nonempty/occ_vl0, DEPTH=32, 16 VLs, age load
VIBE_US_CYC[10:0] on accepted write. Instantiated by vibe_fabric
g_egr.u_voq. Stock Icarus tc_voq_rd / tc_deadlock_timeout_1us
remain the official TP scorers. Header-only vs stock; no invented
protocol. ovf_l (F1) is not in this module.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

DEPTH = 32
NVL = 16
MASK4 = 0xF
MASK5 = 0x1F
MASK6 = 0x3F
MASK11 = 0x7FF
MASK16 = 0xFFFF
MASK32 = 0xFFFFFFFF
MASK512 = (1 << 512) - 1
VIBE_US_CYC = 1250
HIER = "u_u.wr_ready / nonempty / occ_vl0 / rd_* / deadlock_*"


def flit(tag, hi=0):
    """Distinct 512-bit body: tag in [31:0] and [511:496], hi in [63:32]."""
    tag = int(tag) & 0xFFFFFFFF
    hi = int(hi) & 0xFFFFFFFF
    return tag | (hi << 32) | ((tag & 0xFFFF) << 496)


class Golden:
    """Cycle-accurate pointers / mem / age / deadlock vs product NBA."""

    def __init__(self):
        self.mem = [[0] * DEPTH for _ in range(NVL)]
        self.sopm = [[0] * DEPTH for _ in range(NVL)]
        self.eopm = [[0] * DEPTH for _ in range(NVL)]
        self.age = [[0] * DEPTH for _ in range(NVL)]
        self.reset()

    def reset(self):
        # Product reset does not wipe mem / sop / eop / age.
        self.wptr = [0] * NVL
        self.rptr = [0] * NVL
        self.deadlock_drop = 0
        self.deadlock_cnt = 0

    def occ(self, vl):
        return (self.wptr[int(vl) & MASK4] - self.rptr[int(vl) & MASK4]) & MASK6

    def wr_ready(self, wr_vl):
        return int(self.occ(wr_vl) < DEPTH)

    def nonempty(self):
        n = 0
        for v in range(NVL):
            if self.wptr[v] != self.rptr[v]:
                n |= 1 << v
        return n

    def occ_vl0(self):
        return (self.wptr[0] - self.rptr[0]) & MASK6

    def rd_word(self, rd_vl):
        vl = int(rd_vl) & MASK4
        slot = self.rptr[vl] & MASK5
        return (self.mem[vl][slot], self.sopm[vl][slot], self.eopm[vl][slot])

    def step(self, wr_vl=0, wr_en=0, wr_data=0, wr_sop=0, wr_eop=0,
             rd_vl=0, rd_en=0):
        wr_vl = int(wr_vl) & MASK4
        rd_vl = int(rd_vl) & MASK4
        old_wptr = self.wptr[:]
        old_rptr = self.rptr[:]
        old_age = [row[:] for row in self.age]
        self.deadlock_drop = 0
        do_wr = bool(wr_en) and bool(self.wr_ready(wr_vl))
        wr_slot = self.wptr[wr_vl] & MASK5 if do_wr else None
        if do_wr:
            self.mem[wr_vl][wr_slot] = int(wr_data) & MASK512
            self.sopm[wr_vl][wr_slot] = 1 if wr_sop else 0
            self.eopm[wr_vl][wr_slot] = 1 if wr_eop else 0
            self.wptr[wr_vl] = (self.wptr[wr_vl] + 1) & MASK6
        if rd_en:
            self.rptr[rd_vl] = (self.rptr[rd_vl] + 1) & MASK6
        # Age NBA: write schedules VIBE_US_CYC; later decrement wins
        # when the old value was nonzero (product last-assignment).
        for v in range(NVL):
            for j in range(DEPTH):
                if old_age[v][j] != 0:
                    self.age[v][j] = (old_age[v][j] - 1) & MASK11
                elif do_wr and v == wr_vl and j == wr_slot:
                    self.age[v][j] = VIBE_US_CYC & MASK11
            # Deadlock uses pre-NBA wptr/rptr/age. Last rptr NBA wins
            # vs rd_en (same +1).
            if (old_wptr[v] != old_rptr[v]
                    and old_age[v][old_rptr[v] & MASK5] == 0):
                self.rptr[v] = (old_rptr[v] + 1) & MASK6
                self.deadlock_drop = 1
                self.deadlock_cnt = (self.deadlock_cnt + 1) & MASK32


class tc_vibe_voq_egr(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.wr_vl, 0)
        sset(d.wr_en, 0)
        sset(d.wr_data, 0)
        sset(d.wr_sop, 0)
        sset(d.wr_eop, 0)
        sset(d.rd_vl, 0)
        sset(d.rd_en, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        self.g.reset()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def _drive(self, wr_vl=0, wr_en=0, wr_data=0, wr_sop=0, wr_eop=0,
                     rd_vl=0, rd_en=0):
        d = self.dut
        sset(d.wr_vl, int(wr_vl) & MASK4)
        sset(d.wr_en, 1 if wr_en else 0)
        sset(d.wr_data, int(wr_data) & MASK512)
        sset(d.wr_sop, 1 if wr_sop else 0)
        sset(d.wr_eop, 1 if wr_eop else 0)
        sset(d.rd_vl, int(rd_vl) & MASK4)
        sset(d.rd_en, 1 if rd_en else 0)
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return (
            ival(d.wr_ready, -1),
            ival(d.nonempty, -1),
            ival(d.occ_vl0, -1),
            ival(d.rd_data, -1),
            ival(d.rd_sop, -1),
            ival(d.rd_eop, -1),
            ival(d.deadlock_drop, -1),
            ival(d.deadlock_cnt, -1),
        )

    def _fmt(self, s):
        rdy, ne, occ, data, sop, eop, drop, cnt = s
        return (f"wr_ready={rdy} nonempty=0x{ne:x} occ_vl0={occ} "
                f"rd={data}/{sop}/{eop} drop={drop} cnt={cnt}")

    def _peek_ptrs(self):
        try:
            u = self.dut.u_u
        except Exception:
            return None, None
        wptr, rptr = [], []
        try:
            for k in range(NVL):
                wptr.append(ival(u.wptr[k], None))
                rptr.append(ival(u.rptr[k], None))
        except Exception:
            return None, None
        return wptr, rptr

    def _score(self, name, stim, got, score_rd=True):
        exp_rdy = self.g.wr_ready(ival(self.dut.wr_vl, 0))
        exp_ne = self.g.nonempty()
        exp_occ = self.g.occ_vl0()
        exp_drop = self.g.deadlock_drop
        exp_cnt = self.g.deadlock_cnt & MASK32
        rdy, ne, occ, data, sop, eop, drop, cnt = got
        if rdy != exp_rdy or (ne & MASK16) != exp_ne or (occ & MASK6) != exp_occ:
            self.bad(name, stim,
                     f"wr_ready={exp_rdy} nonempty=0x{exp_ne:x} occ_vl0={exp_occ}",
                     self._fmt(got), HIER)
            return False
        if drop != exp_drop or (cnt & MASK32) != exp_cnt:
            self.bad(name, stim + " (deadlock)",
                     f"drop={exp_drop} cnt={exp_cnt}",
                     self._fmt(got), "u_u.deadlock_drop / deadlock_cnt")
            return False
        if score_rd and exp_ne & (1 << (ival(self.dut.rd_vl, 0) & MASK4)):
            ed, es, ee = self.g.rd_word(ival(self.dut.rd_vl, 0))
            if data != ed or sop != es or eop != ee:
                self.bad(name, stim + " (rd head)",
                         f"rd={ed}/{es}/{ee}",
                         self._fmt(got), "u_u.rd_data / rd_sop / rd_eop")
                return False
        wptr, rptr = self._peek_ptrs()
        if wptr is not None:
            for k in range(NVL):
                if wptr[k] is not None and (wptr[k] & MASK6) != self.g.wptr[k]:
                    self.bad(name, stim + f" (u_u.wptr[{k}])",
                             f"wptr[{k}]={self.g.wptr[k]}",
                             f"u_u.wptr[{k}]={wptr[k]}", "u_u.wptr")
                    return False
                if rptr[k] is not None and (rptr[k] & MASK6) != self.g.rptr[k]:
                    self.bad(name, stim + f" (u_u.rptr[{k}])",
                             f"rptr[{k}]={self.g.rptr[k]}",
                             f"u_u.rptr[{k}]={rptr[k]}", "u_u.rptr")
                    return False
        return True

    async def _cycle(self, wr_vl=0, wr_en=0, wr_data=0, wr_sop=0, wr_eop=0,
                     rd_vl=0, rd_en=0):
        await self._drive(wr_vl, wr_en, wr_data, wr_sop, wr_eop, rd_vl, rd_en)
        self.g.step(wr_vl, wr_en, wr_data, wr_sop, wr_eop, rd_vl, rd_en)
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, wr_vl=0, wr_en=0, wr_data=0,
                      wr_sop=0, wr_eop=0, rd_vl=0, rd_en=0, score_rd=True):
        got = await self._cycle(wr_vl, wr_en, wr_data, wr_sop, wr_eop,
                                rd_vl, rd_en)
        if not self._score(name, stim, got, score_rd=score_rd):
            return None
        return got

    def _golden_selfcheck(self, name):
        gchk = Golden()
        if gchk.wr_ready(0) != 1 or gchk.nonempty() or gchk.occ_vl0():
            self.bad(name, "golden reset empty",
                     "wr_ready=1 nonempty=0 occ_vl0=0",
                     f"rdy={gchk.wr_ready(0)} ne={gchk.nonempty()}",
                     "golden")
            return False
        data = flit(0xA5, 0x11)
        gchk.step(wr_vl=0, wr_en=1, wr_data=data, wr_sop=1, wr_eop=1)
        if gchk.nonempty() != 1 or gchk.occ_vl0() != 1:
            self.bad(name, "golden wr VL0",
                     "nonempty=1 occ_vl0=1",
                     f"ne={gchk.nonempty()} occ={gchk.occ_vl0()}",
                     "golden")
            return False
        rd, sop, eop = gchk.rd_word(0)
        if rd != data or sop != 1 or eop != 1:
            self.bad(name, "golden rd head after wr",
                     f"rd={data}/1/1", f"rd={rd}/{sop}/{eop}", "golden")
            return False
        gchk.step(rd_vl=0, rd_en=1)
        if gchk.nonempty() or gchk.occ_vl0():
            self.bad(name, "golden rd empties VL0",
                     "nonempty=0 occ_vl0=0",
                     f"ne={gchk.nonempty()} occ={gchk.occ_vl0()}",
                     "golden")
            return False
        gchk.reset()
        for i in range(DEPTH):
            gchk.step(wr_vl=0, wr_en=1, wr_data=i, wr_sop=1, wr_eop=0)
        if gchk.wr_ready(0) != 0 or gchk.occ_vl0() != DEPTH:
            self.bad(name, "golden full",
                     f"wr_ready=0 occ_vl0={DEPTH}",
                     f"rdy={gchk.wr_ready(0)} occ={gchk.occ_vl0()}",
                     "golden")
            return False
        held = gchk.wptr[0]
        gchk.step(wr_vl=0, wr_en=1, wr_data=0xFF, wr_sop=1, wr_eop=1)
        if gchk.wptr[0] != held:
            self.bad(name, "golden full rejects wr",
                     f"wptr={held}", f"wptr={gchk.wptr[0]}", "golden")
            return False
        if gchk.wr_ready(1) != 1:
            self.bad(name, "golden VL0 full does not block VL1",
                     "wr_ready(1)=1", f"rdy={gchk.wr_ready(1)}", "golden")
            return False
        gchk.reset()
        gchk.step(wr_vl=3, wr_en=1, wr_data=0x33, wr_sop=0, wr_eop=1)
        if gchk.nonempty() != (1 << 3) or gchk.occ_vl0() != 0:
            self.bad(name, "golden VL3 nonempty, VL0 empty",
                     "nonempty=8 occ_vl0=0",
                     f"ne={gchk.nonempty()} occ={gchk.occ_vl0()}",
                     "golden")
            return False
        gchk.reset()
        if (gchk.deadlock_drop or gchk.deadlock_cnt or any(gchk.wptr)
                or any(gchk.rptr)):
            self.bad(name, "golden reset pointers",
                     "wptr/rptr/drop/cnt=0",
                     f"drop={gchk.deadlock_drop}", "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_voq_egr"
        self.g = Golden()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: combo empty, deadlock cleared.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got,
                           score_rd=False):
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[1] != 0 or got[2] != 0 or got[6] != 0 or got[7] != 0:
            self.bad(name, "reset idle ports",
                     "wr_ready=1 nonempty=0 occ_vl0=0 drop=0 cnt=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. wr then rd same VL: data / sop / eop.
        data0 = flit(0xA5A5A5A5, 0x11111111)
        got = await self._expect(
            name, "wr VL0 data/sop/eop",
            wr_vl=0, wr_en=1, wr_data=data0, wr_sop=1, wr_eop=1, rd_vl=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 1 or got[2] != 1 or got[3] != data0 or got[4] != 1 or got[5] != 1:
            self.bad(name, "wr VL0 must present head",
                     f"nonempty=1 occ=1 rd={data0}/1/1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "idle hold after wr (head stays)",
            rd_vl=0)
        if got is None or got[3] != data0 or got[1] != 1:
            if got is not None:
                self.bad(name, "head must hold without rd_en",
                         f"nonempty=1 rd={data0}/1/1",
                         self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "rd VL0 pops the flit",
            rd_vl=0, rd_en=1, score_rd=False)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 0 or got[2] != 0:
            self.bad(name, "rd empties VL0",
                     "nonempty=0 occ_vl0=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # SOP-only then EOP-only on VL3 (independent of VL0).
        data3 = flit(0x33333333, 0xDEADBEEF)
        got = await self._expect(
            name, "wr VL3 sop=1 eop=0",
            wr_vl=3, wr_en=1, wr_data=data3, wr_sop=1, wr_eop=0, rd_vl=3)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] & MASK16) != (1 << 3) or got[2] != 0:
            self.bad(name, "VL3 nonempty, VL0 still empty",
                     "nonempty=0x8 occ_vl0=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if got[3] != data3 or got[4] != 1 or got[5] != 0:
            self.bad(name, "VL3 head sop/eop",
                     f"rd={data3}/1/0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        data3b = flit(0x34, 0xB)
        got = await self._expect(
            name, "wr VL3 second beat sop=0 eop=1",
            wr_vl=3, wr_en=1, wr_data=data3b, wr_sop=0, wr_eop=1, rd_vl=3)
        if got is None or got[3] != data3 or got[4] != 1 or got[5] != 0:
            if got is not None:
                self.bad(name, "VL3 head still first beat",
                         f"rd={data3}/1/0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "rd VL3 first beat",
            rd_vl=3, rd_en=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != data3b or got[4] != 0 or got[5] != 1:
            self.bad(name, "VL3 second beat becomes head",
                     f"rd={data3b}/0/1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "rd VL3 second beat empties",
            rd_vl=3, rd_en=1, score_rd=False)
        if got is None or (got[1] & MASK16) != 0:
            if got is not None:
                self.bad(name, "VL3 empty after two rds",
                         "nonempty=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. wr_ready / backpressure when full (DEPTH=32).
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        for i in range(DEPTH):
            word = flit(0x100 + i, 0x200 + i)
            sop = 1 if i == 0 else 0
            eop = 1 if i == DEPTH - 1 else 0
            got = await self._expect(
                name, f"fill VL0 [{i}]",
                wr_vl=0, wr_en=1, wr_data=word, wr_sop=sop, wr_eop=eop,
                rd_vl=0)
            if got is None:
                phase.drop_objection(self)
                return
        if got[0] != 0 or got[2] != DEPTH:
            self.bad(name, "full after 32 wr",
                     f"wr_ready=0 occ_vl0={DEPTH}",
                     self._fmt(got), "u_u.wr_ready")
            phase.drop_objection(self)
            return

        # Full reject: wr_en must not move wptr / change occ.
        held_occ = self.g.occ_vl0()
        got = await self._expect(
            name, "wr while full rejected",
            wr_vl=0, wr_en=1, wr_data=flit(0xEE, 0xFF), wr_sop=1, wr_eop=1,
            rd_vl=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 0 or got[2] != held_occ:
            self.bad(name, "full must keep wr_ready=0 and occ",
                     f"wr_ready=0 occ_vl0={held_occ}",
                     self._fmt(got), "u_u.wr_ready")
            phase.drop_objection(self)
            return

        # VL0 full must not backpressure a different VL.
        await self._drive(wr_vl=1, wr_en=0)
        await Timer(100, "PS")
        if ival(d.wr_ready, 0) != 1:
            self.bad(name, "VL0 full, wr_vl=1 combo wr_ready",
                     "wr_ready=1", f"wr_ready={ival(d.wr_ready, -1)}",
                     "u_u.wr_ready")
            phase.drop_objection(self)
            return

        data1 = flit(0x51, 0x15)
        got = await self._expect(
            name, "wr VL1 while VL0 full",
            wr_vl=1, wr_en=1, wr_data=data1, wr_sop=1, wr_eop=1, rd_vl=1)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] & (1 << 1)) == 0 or (got[1] & 1) == 0 or got[2] != DEPTH:
            self.bad(name, "VL1 enqueue while VL0 full",
                     f"nonempty bits 0+1, occ_vl0={DEPTH}",
                     self._fmt(got), "u_u.nonempty")
            phase.drop_objection(self)
            return

        # Pop one from VL0 → wr_ready returns.
        head0 = flit(0x100, 0x200)
        got = await self._expect(
            name, "rd VL0 one slot while full",
            rd_vl=0, rd_en=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[2] != DEPTH - 1:
            self.bad(name, "one rd after full reopens wr_ready",
                     f"wr_ready=1 occ_vl0={DEPTH - 1}",
                     self._fmt(got), "u_u.wr_ready")
            phase.drop_objection(self)
            return
        if got[3] != head0 or got[4] != 1 or got[5] != 0:
            self.bad(name, "full-queue head was first fill beat",
                     f"rd={head0}/1/0", self._fmt(got), "u_u.rd_data")
            phase.drop_objection(self)
            return

        # Drain remaining VL0 + VL1 so deadlock wait starts empty-ish.
        for i in range(DEPTH - 1):
            if await self._expect(
                    name, f"drain VL0 [{i}]",
                    rd_vl=0, rd_en=1,
                    score_rd=(self.g.nonempty() & 1) != 0) is None:
                phase.drop_objection(self)
                return
        if await self._expect(
                name, "drain VL1",
                rd_vl=1, rd_en=1, score_rd=False) is None:
            phase.drop_objection(self)
            return
        if self.g.nonempty() != 0:
            self.bad(name, "queues empty before deadlock path",
                     "nonempty=0", f"nonempty=0x{self.g.nonempty():x}",
                     "u_u.nonempty")
            phase.drop_objection(self)
            return

        # 4. Async rst_n mid-stream clears pointers / deadlock (no posedge).
        data7 = flit(0x77, 0x70)
        got = await self._expect(
            name, "wr VL7 before async rst",
            wr_vl=7, wr_en=1, wr_data=data7, wr_sop=1, wr_eop=1, rd_vl=7)
        if got is None or (got[1] & (1 << 7)) == 0:
            if got is not None:
                self.bad(name, "pre-rst VL7 nonempty",
                         "nonempty bit7", self._fmt(got), "u_u.nonempty")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got, score_rd=False):
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[1] != 0 or got[2] != 0 or got[6] != 0 or got[7] != 0:
            self.bad(name, "async rst_n mid-stream",
                     "wr_ready=1 nonempty=0 occ=0 drop=0 cnt=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 5. Short deadlock_drop path (VIBE_US_CYC=1250 @ 2 ns ≈ 2.5 us).
        # Stock tc_deadlock_timeout_1us: no drop before US_CYC-4, then
        # cnt>0 within +16. Age countdown is product RTL; no poke.
        got = await self._expect(
            name, "wr VL2 to start age=VIBE_US_CYC",
            wr_vl=2, wr_en=1, wr_data=flit(0xD1, 0xA6), wr_sop=1, wr_eop=1,
            rd_vl=2)
        if got is None or (got[1] & (1 << 2)) == 0:
            if got is not None:
                self.bad(name, "deadlock setup nonempty[2]",
                         "nonempty bit2", self._fmt(got), "u_u.nonempty")
            phase.drop_objection(self)
            return
        await self._idle()
        # Bulk wait: one golden step per posedge (no per-cycle peek).
        for i in range(VIBE_US_CYC - 4):
            self.g.step()
            await RisingEdge(d.clk)
            if ival(d.deadlock_drop, 0):
                self.bad(name, f"deadlock_drop too early at cycle {i}",
                         "deadlock_drop=0",
                         f"drop=1 cnt={ival(d.deadlock_cnt, -1)}",
                         "u_u.deadlock_drop")
                phase.drop_objection(self)
                return
        await FallingEdge(d.clk)
        saw = False
        for i in range(16):
            got = await self._expect(
                name, f"age expire wait[{i}]",
                rd_vl=2, score_rd=False)
            if got is None:
                phase.drop_objection(self)
                return
            if got[6] == 1 or got[7] >= 1:
                saw = True
                break
        if not saw:
            self.bad(name, "VOQ occupied >=1250 without drain",
                     "deadlock_drop pulse / cnt>0",
                     self._fmt(got), "u_u.age / rptr")
            phase.drop_objection(self)
            return
        if self.g.deadlock_cnt < 1:
            self.bad(name, "deadlock_cnt after expire",
                     "cnt>=1", f"cnt={self.g.deadlock_cnt}",
                     "u_u.deadlock_cnt")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_voq_egr)
