"""Module-level uvm-python TC for Decision-I leaf vibe_vl_rr.

Covers reset rr=0 / first pick from 0; valid=|nonempty; single-bit
nonempty (incl. VL15); grant&&valid walks the pointer; hold without
grant; grant while !valid does not advance; stock FFFF 16-grant
seen=FFFF; wrap and sparse masks; async rst_n mid-stream clears rr.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/fabric/vibe_vl_rr.sv: async-low rst_n, combo
valid=|nonempty and scan from rr wrapping 16 steps (first nonempty[p]
wins as pick / vl_sel), seq !rst_n → rr=0 else grant&&valid →
rr <= vl_sel+1. Instantiated by vibe_fabric u_rr in g_egr. Stock
Icarus tc_vl_rr / tc_vl_rr_0_15 remain the official TP scorers.
Header-only vs stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK16 = 0xFFFF
MASK4 = 0xF
HIER = "u_u.rr / vl_sel"


def pick_vl(rr: int, nonempty: int):
    """Product combo: first nonempty VL from rr, wrap 16; valid=|nonempty."""
    nonempty = int(nonempty) & MASK16
    valid = 1 if nonempty else 0
    pick = int(rr) & MASK4
    p = pick
    for _ in range(16):
        if (nonempty >> p) & 1:
            pick = p
            break
        p = (p + 1) & MASK4
    return pick, valid


class Golden:
    """Cycle-accurate rr vs product NBA (grant && valid advances)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.rr = 0

    def combo(self, nonempty):
        return pick_vl(self.rr, nonempty)

    def step(self, nonempty=0, grant=0):
        pick, valid = self.combo(nonempty)
        if grant and valid:
            self.rr = (pick + 1) & MASK4


class tc_vibe_vl_rr(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.nonempty, 0)
        sset(d.grant, 0)

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

    async def _drive(self, nonempty, grant=0):
        sset(self.dut.nonempty, int(nonempty) & MASK16)
        sset(self.dut.grant, 1 if grant else 0)
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return ival(d.vl_sel, -1), ival(d.valid, -1)

    def _fmt(self, s, rr=None):
        sel, valid = s
        extra = f" rr={rr}" if rr is not None else ""
        return f"vl_sel={sel} valid={valid}{extra}"

    def _score(self, name, stim, got, nonempty):
        exp = self.g.combo(nonempty)
        if got != exp:
            self.bad(name, stim, self._fmt(exp, self.g.rr),
                     self._fmt(got), HIER)
            return False
        sel, valid = got
        exp_v = int(bool(int(nonempty) & MASK16))
        if valid != exp_v:
            self.bad(name, stim + " (valid = |nonempty)",
                     f"valid={exp_v}", self._fmt(got), "u_u.valid")
            return False
        if valid and sel >= 0 and not ((int(nonempty) >> (sel & MASK4)) & 1):
            self.bad(name, stim + " (vl_sel must be a nonempty VL)",
                     f"nonempty bit {sel} set",
                     f"nonempty=0x{int(nonempty) & MASK16:04x} "
                     f"{self._fmt(got)}",
                     "u_u.vl_sel")
            return False
        if not valid and sel != (self.g.rr & MASK4):
            self.bad(name, stim + " (empty keeps vl_sel=rr)",
                     f"vl_sel={self.g.rr}", self._fmt(got), HIER)
            return False
        try:
            inner_rr = ival(self.dut.u_u.rr, None)
            inner_sel = ival(self.dut.u_u.vl_sel, None)
            inner_v = ival(self.dut.u_u.valid, None)
        except Exception:
            inner_rr = inner_sel = inner_v = None
        if inner_rr is not None and (inner_rr & MASK4) != (self.g.rr & MASK4):
            self.bad(name, stim + " (port vs u_u.rr)",
                     f"rr={self.g.rr}", f"u_u.rr={inner_rr}", "u_u.rr")
            return False
        if inner_sel is not None and (inner_sel & MASK4) != (sel & MASK4):
            self.bad(name, stim + " (port vs u_u.vl_sel)",
                     f"vl_sel={sel}", f"u_u.vl_sel={inner_sel}", HIER)
            return False
        if inner_v is not None and inner_v != valid:
            self.bad(name, stim + " (port vs u_u.valid)",
                     f"valid={valid}", f"u_u.valid={inner_v}", "u_u.valid")
            return False
        return True

    async def _combo(self, nonempty, grant=0):
        """Drive and sample combo; rr is not stepped."""
        await self._drive(nonempty, grant)
        return self._sample()

    async def _expect_combo(self, name, stim, nonempty, grant=0):
        got = await self._combo(nonempty, grant)
        if not self._score(name, stim, got, nonempty):
            return None
        return got

    async def _cycle(self, nonempty, grant=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        await self._drive(nonempty, grant)
        self.g.step(nonempty, grant)
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, nonempty, grant=0):
        got = await self._cycle(nonempty, grant)
        if not self._score(name, stim, got, nonempty):
            return None
        return got

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_vl_rr"
        self.g = Golden()

        if pick_vl(0, 0) != (0, 0):
            self.bad(name, "golden empty",
                     "vl_sel=0 valid=0", str(pick_vl(0, 0)), "golden")
            phase.drop_objection(self)
            return
        if pick_vl(0, 1) != (0, 1):
            self.bad(name, "golden VL0 from rr=0",
                     "vl_sel=0 valid=1", str(pick_vl(0, 1)), "golden")
            phase.drop_objection(self)
            return
        if pick_vl(0, 0x8000) != (15, 1):
            self.bad(name, "golden VL15 only from rr=0",
                     "vl_sel=15 valid=1", str(pick_vl(0, 0x8000)), "golden")
            phase.drop_objection(self)
            return
        if pick_vl(15, 1) != (0, 1):
            self.bad(name, "golden wrap VL0 from rr=15",
                     "vl_sel=0 valid=1", str(pick_vl(15, 1)), "golden")
            phase.drop_objection(self)
            return
        if pick_vl(1, 0x0005) != (2, 1):
            self.bad(name, "golden VL0|VL2 from rr=1",
                     "vl_sel=2 valid=1", str(pick_vl(1, 0x0005)), "golden")
            phase.drop_objection(self)
            return
        gchk = Golden()
        gchk.step(0xFFFF, 1)
        if gchk.rr != 1:
            self.bad(name, "golden grant&&valid advances rr",
                     "rr=1", f"rr={gchk.rr}", "golden")
            phase.drop_objection(self)
            return
        gchk.step(0, 1)
        if gchk.rr != 1:
            self.bad(name, "golden grant while !valid holds rr",
                     "rr=1", f"rr={gchk.rr}", "golden")
            phase.drop_objection(self)
            return
        gchk.step(0xFFFF, 0)
        if gchk.rr != 1:
            self.bad(name, "golden !grant holds rr",
                     "rr=1", f"rr={gchk.rr}", "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: rr=0; empty → valid=0; first pick from 0.
        got = self._sample()
        if not self._score(name, "reset then release, nonempty=0", got, 0):
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "reset idle ports",
                     "vl_sel=0 valid=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "empty after reset (valid=|nonempty)", 0, grant=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "empty valid=0",
                     "vl_sel=0 valid=0", self._fmt(got), "u_u.valid")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "VL0 only after reset (first pick from rr=0)",
            0x0001, grant=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 1):
            self.bad(name, "first pick from 0",
                     "vl_sel=0 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "VL2 only after reset (scan from rr=0)",
            0x0004, grant=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (2, 1):
            self.bad(name, "scan from rr=0 to VL2",
                     "vl_sel=2 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. Single-bit nonempty (incl. VL15) from rr=0; combo, no advance.
        for vl in range(16):
            mask = 1 << vl
            stim = f"single-bit VL{vl} only (grant=0, rr holds at 0)"
            got = await self._expect(name, stim, mask, grant=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got != (vl, 1):
                self.bad(name, stim, f"vl_sel={vl} valid=1",
                         self._fmt(got), "u_u.vl_sel")
                phase.drop_objection(self)
                return
        if self.g.rr != 0:
            self.bad(name, "single-bit walk must not advance rr",
                     "rr=0", f"rr={self.g.rr}", "u_u.rr")
            phase.drop_objection(self)
            return

        # Combo settle without a posedge (valid = |nonempty).
        got = await self._expect_combo(
            name, "combo empty (100ps, no posedge)", 0)
        if got is None or got != (0, 0):
            if got is not None:
                self.bad(name, "combo empty",
                         "valid=0", self._fmt(got), "u_u.valid")
            phase.drop_objection(self)
            return
        got = await self._expect_combo(
            name, "combo VL15 only (100ps, no posedge)", 0x8000)
        if got is None or got != (15, 1):
            if got is not None:
                self.bad(name, "combo VL15",
                         "vl_sel=15 valid=1", self._fmt(got), "u_u.vl_sel")
            phase.drop_objection(self)
            return

        # 3. RR advance: grant&&valid walks; !grant holds; grant&&!valid holds.
        got = await self._expect(
            name, "grant&&valid from rr=0 nonempty=FFFF → rr=1 vl_sel=1",
            0xFFFF, grant=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (1, 1) or self.g.rr != 1:
            self.bad(name, "first grant walk",
                     "vl_sel=1 valid=1 rr=1",
                     self._fmt(got, self.g.rr), HIER)
            phase.drop_objection(self)
            return

        held = got
        for i in range(3):
            got = await self._expect(
                name, f"hold rr without grant [{i}]",
                0xFFFF, grant=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got != held or self.g.rr != 1:
                self.bad(name, f"!grant holds rr [{i}]",
                         self._fmt(held, 1), self._fmt(got, self.g.rr),
                         "u_u.rr")
                phase.drop_objection(self)
                return

        got = await self._expect(
            name, "grant while empty must not advance rr",
            0, grant=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (1, 0) or self.g.rr != 1:
            self.bad(name, "grant && !valid holds rr",
                     "vl_sel=1 valid=0 rr=1",
                     self._fmt(got, self.g.rr), "u_u.rr")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "after empty-grant, nonempty=FFFF still from rr=1",
            0xFFFF, grant=0)
        if got is None or got != (1, 1):
            if got is not None:
                self.bad(name, "rr held through empty grant",
                         "vl_sel=1 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. Stock-like walk: nonempty=FFFF, 16 grants → every VL0-15 once.
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        seen = 0
        for i in range(16):
            got = await self._expect_combo(
                name, f"stock FFFF walk sample before grant [{i}]",
                0xFFFF, grant=0)
            if got is None:
                phase.drop_objection(self)
                return
            sel, valid = got
            if not valid:
                self.bad(name, f"stock FFFF walk valid [{i}]",
                         "valid=1", self._fmt(got), "u_u.valid")
                phase.drop_objection(self)
                return
            seen |= 1 << (sel & MASK4)
            if await self._expect(
                    name, f"stock FFFF grant pulse [{i}]",
                    0xFFFF, grant=1) is None:
                phase.drop_objection(self)
                return
            if await self._expect(
                    name, f"stock FFFF idle after grant [{i}]",
                    0xFFFF, grant=0) is None:
                phase.drop_objection(self)
                return
        if seen != MASK16:
            self.bad(name, "nonempty=FFFF, 16 grants (stock tc_vl_rr_0_15)",
                     "every VL0-15 selected once (seen=FFFF)",
                     f"seen={seen:04x}", HIER)
            phase.drop_objection(self)
            return

        got = await self._expect_combo(
            name, "stock empty after FFFF walk", 0)
        if got is None or got[1] != 0:
            if got is not None:
                self.bad(name, "nonempty=0 after walk",
                         "valid=0", self._fmt(got), "u_u.valid")
            phase.drop_objection(self)
            return
        got = await self._expect_combo(
            name, "stock only VL15 after empty", 0x8000)
        if got is None or got != (15, 1):
            if got is not None:
                self.bad(name, "only VL15",
                         "vl_sel=15 valid=1", self._fmt(got), "u_u.vl_sel")
            phase.drop_objection(self)
            return

        # 5. Stock VL0|VL2 three grants (not pinned).
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        picks = []
        for i, stim in enumerate((
                "stock VL0|VL2 sample a (rr=0 → VL0)",
                "stock VL0|VL2 sample b (after grant → VL2)",
                "stock VL0|VL2 sample c (after grant → wrap VL0)",
                )):
            got = await self._expect_combo(name, stim, 0x0005, grant=0)
            if got is None:
                phase.drop_objection(self)
                return
            picks.append(got[0])
            if await self._expect(
                    name, f"stock VL0|VL2 grant [{i}]",
                    0x0005, grant=1) is None:
                phase.drop_objection(self)
                return
            if await self._expect(
                    name, f"stock VL0|VL2 idle [{i}]",
                    0x0005, grant=0) is None:
                phase.drop_objection(self)
                return
        if picks[0] == picks[1] == picks[2]:
            self.bad(name, "nonempty VL0+VL2, three grants (stock tc_vl_rr)",
                     "RR walks both VLs (not pinned)",
                     f"vl_sel stayed {picks[0]}", HIER)
            phase.drop_objection(self)
            return
        if picks != [0, 2, 0]:
            self.bad(name, "stock VL0|VL2 walk order",
                     "vl_sel 0,2,0", f"picks={picks}", HIER)
            phase.drop_objection(self)
            return

        # 6. Wrap and sparse masks.
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        got = await self._expect(
            name, "sparse VL0|VL15 from rr=0 → VL0",
            0x8001, grant=1)
        if got is None or got != (15, 1):
            if got is not None:
                self.bad(name, "after grant VL0, next is VL15",
                         "vl_sel=15 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "sparse VL0|VL15 grant from VL15 wraps to VL0",
            0x8001, grant=1)
        if got is None or got != (0, 1):
            if got is not None:
                self.bad(name, "wrap VL15 → VL0",
                         "vl_sel=0 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Walk rr to 5, then single-bit VL0 forces wrap scan.
        for i in range(5):
            if await self._expect(
                    name, f"walk FFFF toward rr=5 [{i}]",
                    0xFFFF, grant=1) is None:
                phase.drop_objection(self)
                return
        got = await self._expect(
            name, "VL0 only with rr=5 wraps to VL0",
            0x0001, grant=0)
        if got is None or got != (0, 1):
            if got is not None:
                self.bad(name, "wrap scan from rr=5 to VL0",
                         "vl_sel=0 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        sparse = 0xA005  # VL0, VL2, VL13, VL15
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)
        exp_sparse = []
        rr = 0
        for _ in range(8):
            exp_sparse.append(pick_vl(rr, sparse)[0])
            rr = (exp_sparse[-1] + 1) & MASK4
        seen_sp = []
        for i in range(8):
            got = await self._expect_combo(
                name, f"sparse 0xA005 sample [{i}]", sparse, grant=0)
            if got is None:
                phase.drop_objection(self)
                return
            seen_sp.append(got[0])
            if await self._expect(
                    name, f"sparse 0xA005 grant [{i}]",
                    sparse, grant=1) is None:
                phase.drop_objection(self)
                return
        if seen_sp != exp_sparse:
            self.bad(name, "sparse mask 0xA005 RR walk",
                     f"picks={exp_sparse}", f"picks={seen_sp}", HIER)
            phase.drop_objection(self)
            return

        # 7. Async rst_n mid-stream clears rr (no posedge).
        if await self._expect(
                name, "FFFF grant before async rst (leave rr nonzero)",
                0xFFFF, grant=1) is None:
            phase.drop_objection(self)
            return
        if self.g.rr == 0:
            self.bad(name, "precondition: rr nonzero before async rst",
                     "rr!=0", f"rr={self.g.rr}", "u_u.rr")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.nonempty, 0xFFFF)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got, 0xFFFF):
            phase.drop_objection(self)
            return
        if got != (0, 1) or self.g.rr != 0:
            self.bad(name, "async rst_n mid-stream",
                     "vl_sel=0 valid=1 rr=0",
                     self._fmt(got, self.g.rr), "u_u.rr")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle empty",
                           got, 0):
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "after async re-reset",
                     "vl_sel=0 valid=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "after async rst, first pick still from 0",
            0x0004, grant=0)
        if got is None or got != (2, 1):
            if got is not None:
                self.bad(name, "post-async-rst scan from 0",
                         "vl_sel=2 valid=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_vl_rr)
