"""Module-level uvm-python TC for Decision-I leaf vibe_sync2.

Covers reset-cleared q, 2-FF latency (not 1), walk-1 on W=5,
streaming delay vs golden, async rst_n mid-pipe, hold-through
posedge, and a pin scan (no ready/valid). Not a full-chip
consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/cdc/vibe_sync2.sv: dest-domain 2-FF
(q1 <= d; q <= q1), async-low rst_n clears both stages.
Parameter W=5 (product AFIFO instantiation). Instantiated by
vibe_afifo u_r2w / u_w2r. This is not vibe_rst_sync and not
gear. There is no stock Icarus tc_sync2; this module-level
TC is the leaf scorer. ovf_l (F1) is not in this module.
CHILDREN: none (leaf cell; no FSM child).
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

W = 5
MASK = (1 << W) - 1
STABLE = 0x15
ONES = MASK
STREAM = (0x01, 0x1A, 0x05, 0x1F, 0x0A, 0x11, 0x07)
HIER = "u_u.q / u_u.q1"

ABSENT = (
    "ready", "valid", "in_vld", "out_vld", "en", "ce",
    "set", "clr", "async_set", "rst", "almost_full",
)


class Golden:
    """Cycle-accurate 2-FF vs product NBA (q1 <= d; q <= q1)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.q1 = 0
        self.q = 0

    def step(self, d, rst_n=1):
        if not rst_n:
            self.q1 = 0
            self.q = 0
            return
        d = int(d) & MASK
        self.q, self.q1 = self.q1, d


class tc_vibe_sync2(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        sset(self.dut.d, 0)

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

    def _sample(self):
        return ival(self.dut.q, -1)

    async def _cycle(self, dval, rst_n=1):
        """Drive on this falling edge; sample NBA-stable q next fall."""
        dval = int(dval) & MASK
        sset(self.dut.d, dval)
        sset(self.dut.rst_n, 1 if rst_n else 0)
        self.g.step(dval, rst_n)
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got):
        exp = self.g.q
        if got != exp:
            self.bad(name, stim,
                     f"q=0x{exp:02x}",
                     f"q=0x{got:x}" if got is not None else "q=x",
                     HIER)
            return False
        return True

    async def _drain(self, name, tag):
        for i in range(2):
            got = await self._cycle(0)
            if not self._score(name, f"{tag}: drain {i} d=0", got):
                return False
        if self.g.q != 0:
            self.bad(name, f"{tag}: after 2-cycle drain",
                     "q=0", f"q=0x{self.g.q:x}", HIER)
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_sync2"
        self.g = Golden()

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: q==0 (NBA-stable on falling edge). Quiet stays 0.
        got = self._sample()
        if got != 0:
            self.bad(name, "reset then release, d=0",
                     "q=0", f"q={got}", HIER)
            phase.drop_objection(self)
            return
        for i in range(2):
            got = await self._cycle(0)
            if not self._score(name, f"idle cycle {i} after reset", got):
                phase.drop_objection(self)
                return

        # 2. Stable d reaches q after 2 posedges (not 1).
        got = await self._cycle(STABLE)
        if not self._score(name, f"stable d=0x{STABLE:02x}, 1 posedge", got):
            phase.drop_objection(self)
            return
        if got != 0:
            self.bad(name, f"stable d=0x{STABLE:02x}, 1 posedge",
                     "q=0 (still in q1)", f"q=0x{got:x}", HIER)
            phase.drop_objection(self)
            return
        got = await self._cycle(STABLE)
        if not self._score(name, f"stable d=0x{STABLE:02x}, 2 posedges", got):
            phase.drop_objection(self)
            return
        if got != STABLE:
            self.bad(name, f"stable d=0x{STABLE:02x}, 2 posedges",
                     f"q=0x{STABLE:02x}", f"q=0x{got:x}", HIER)
            phase.drop_objection(self)
            return

        if not await self._drain(name, "after stable"):
            phase.drop_objection(self)
            return

        # 3. Walk-1 on every W=5 bit (AFIFO gray width).
        for bit in range(W):
            val = 1 << bit
            if not await self._drain(name, f"before walk[{bit}]"):
                phase.drop_objection(self)
                return
            got = await self._cycle(val)
            if not self._score(name, f"walk-1 d=0x{val:02x}, 1 posedge", got):
                phase.drop_objection(self)
                return
            if got != 0:
                self.bad(name, f"walk-1 bit{bit} 1 posedge",
                         "q=0 (still in q1)", f"q=0x{got:x}", HIER)
                phase.drop_objection(self)
                return
            got = await self._cycle(val)
            if not self._score(name, f"walk-1 d=0x{val:02x}, 2 posedges", got):
                phase.drop_objection(self)
                return
            if got != val:
                self.bad(name, f"walk-1 bit{bit} 2 posedges",
                         f"q=0x{val:02x}", f"q=0x{got:x}", HIER)
                phase.drop_objection(self)
                return

        # 4. All-1s (0x1F) then streaming d changes: q tracks with 2-cycle delay.
        if not await self._drain(name, "before ones"):
            phase.drop_objection(self)
            return
        got = await self._cycle(ONES)
        if not self._score(name, "all-1s, 1 posedge", got):
            phase.drop_objection(self)
            return
        got = await self._cycle(ONES)
        if not self._score(name, "all-1s, 2 posedges", got):
            phase.drop_objection(self)
            return
        if got != ONES:
            self.bad(name, "all-1s 2 posedges",
                     f"q=0x{ONES:02x}", f"q=0x{got:x}", HIER)
            phase.drop_objection(self)
            return
        if not await self._drain(name, "after ones"):
            phase.drop_objection(self)
            return

        for i, val in enumerate(STREAM):
            got = await self._cycle(val)
            if not self._score(name, f"stream[{i}] d=0x{val:02x} after posedge",
                               got):
                phase.drop_objection(self)
                return

        # 5. Async rst_n low clears the pipeline (mid-cycle, not a posedge).
        got = self._sample()
        if got == 0:
            self.bad(name, "pre-async-rst (expect nonzero pipe)",
                     "q!=0", f"q={got}", HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got != 0:
            self.bad(name, "async rst_n=0 mid-cycle (100ps, no posedge)",
                     "q=0", f"q={got}", HIER)
            phase.drop_objection(self)
            return

        # Hold through a dest posedge while d is still the last stream value.
        got = await self._cycle(STREAM[-1], rst_n=0)
        if not self._score(
                name, "rst_n held 0 through posedge, d still nonzero", got):
            phase.drop_objection(self)
            return
        if got != 0:
            self.bad(name, "rst_n held 0 through posedge, d still nonzero",
                     "q stays 0", f"q={got}", HIER)
            phase.drop_objection(self)
            return

        # 6. After re-release, pipe is empty: first dest clock still 0.
        sset(d.rst_n, 1)
        got = await self._cycle(STABLE)
        if not self._score(name, "after async re-release, 1 posedge", got):
            phase.drop_objection(self)
            return
        if got != 0:
            self.bad(name, "after async re-release, 1 posedge",
                     "q=0 (q1 was cleared)", f"q=0x{got:x}", HIER)
            phase.drop_objection(self)
            return
        got = await self._cycle(STABLE)
        if not self._score(name, "after async re-release, 2 posedges", got):
            phase.drop_objection(self)
            return
        if got != STABLE:
            self.bad(name, "after async re-release, 2 posedges",
                     f"q=0x{STABLE:02x}", f"q=0x{got:x}", HIER)
            phase.drop_objection(self)
            return

        # 7. Leaf has only clk / rst_n / d / q (no ready/valid).
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_sync2 product port",
                         f"{absent} present", "vibe_sync2_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n", "d", "q"):
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", "vibe_sync2_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_sync2)
