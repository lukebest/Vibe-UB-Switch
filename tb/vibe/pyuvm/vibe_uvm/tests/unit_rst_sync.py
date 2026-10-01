"""Module-level uvm-python TC for Decision-I leaf vibe_rst_sync.

Covers async assert of rst_n_out, 2-FF sync deassert (not 1),
hold-through dest posedge, mid-run re-assert, released stay-1,
and a pin scan (no ready/valid). Not a full-chip consecutive-
green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/cdc/vibe_rst_sync.sv: async assert on
rst_n_in, sync release into clk (r1 then rst_n_out). Stock
Icarus tc_rst_sync remains optional control. Instantiated by
vibe_port u_txrst / u_rxrst. This is not vibe_sync2 / vibe_afifo
and not gear. ovf_l (F1) is not in this module.
CHILDREN: none (leaf cell; no FSM child).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

HIER = "u_u.rst_n_out / u_u.r1"
WRAP = "vibe_rst_sync_cocotb_top"
PINS = ("clk", "rst_n_in", "rst_n_out")
ABSENT = (
    "ready", "valid", "in_vld", "out_vld", "en", "ce",
    "set", "clr", "async_set", "rst", "d", "q",
    "ovf_l", "almost_full",
)


class Golden:
    """Cycle-accurate 2-FF vs product NBA (r1 <= 1; rst_n_out <= r1)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.r1 = 0
        self.rst_n_out = 0

    def step(self, rst_n_in=1):
        if not rst_n_in:
            self.r1 = 0
            self.rst_n_out = 0
            return
        self.rst_n_out, self.r1 = self.r1, 1


class tc_vibe_rst_sync(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    def _sample(self):
        return ival(self.dut.rst_n_out, -1)

    def _score(self, name, stim, got):
        exp = self.g.rst_n_out
        if got != exp:
            self.bad(name, stim,
                     f"rst_n_out={exp}",
                     f"rst_n_out={got}" if got is not None else "rst_n_out=x",
                     HIER)
            return False
        return True

    async def _settle_out(self, rst_n_in=1):
        """NBA-stable rst_n_out on the falling edge after a posedge."""
        self.g.step(rst_n_in)
        await self._to_fall()
        return self._sample()

    async def _async_assert_in(self):
        """Drive rst_n_in=0 mid-cycle (no dest posedge)."""
        sset(self.dut.rst_n_in, 0)
        await Timer(100, "PS")
        self.g.reset()
        return self._sample()

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_rst_sync"
        self.g = Golden()

        # Start from a known async-asserted state (X-safe at time 0).
        sset(d.rst_n_in, 0)
        self.g.reset()
        await self.cycles(3)
        await FallingEdge(d.clk)

        # 1. Assert async reset → rst_n_out asserted without a dest posedge.
        # Already held 0; re-assert mid-cycle and sample before the next edge.
        q0 = await self._async_assert_in()
        if q0 != 0:
            self.bad(name, "rst_n_in=0 mid-cycle (100ps, no posedge)",
                     "rst_n_out=0 (async assert)",
                     f"rst_n_out={q0}", HIER)
            phase.drop_objection(self)
            return
        # Hold through a dest posedge while still asserted.
        qh = await self._settle_out(rst_n_in=0)
        if not self._score(name, "rst_n_in held 0 through dest posedge", qh):
            phase.drop_objection(self)
            return
        if qh != 0:
            self.bad(name, "rst_n_in held 0 through dest posedge",
                     "rst_n_out stays 0",
                     f"rst_n_out={qh}", HIER)
            phase.drop_objection(self)
            return

        # 2. Deassert async reset → release only after 2 dest clocks (not 1).
        # Apply on this falling edge (NBA-stable sample after each posedge).
        sset(d.rst_n_in, 1)
        q1 = await self._settle_out()
        if not self._score(name, "rst_n_in=1, 1 dest posedge", q1):
            phase.drop_objection(self)
            return
        if q1 != 0:
            self.bad(name, "rst_n_in=1, 1 dest posedge",
                     "rst_n_out=0 (still in r1)",
                     f"rst_n_out={q1}", HIER)
            phase.drop_objection(self)
            return
        q2 = await self._settle_out()
        if not self._score(name, "rst_n_in=1, 2 dest posedges", q2):
            phase.drop_objection(self)
            return
        if q2 != 1:
            self.bad(name, "rst_n_in=1, 2 dest posedges",
                     "rst_n_out=1 (2-FF sync deassert)",
                     f"rst_n_out={q2}", HIER)
            phase.drop_objection(self)
            return

        # Released output stays 1 while rst_n_in is held 1.
        for i in range(2):
            qhld = await self._settle_out()
            if not self._score(name, f"released stay-1 cycle {i}", qhld):
                phase.drop_objection(self)
                return
            if qhld != 1:
                self.bad(name, f"released stay-1 cycle {i}",
                         "rst_n_out=1",
                         f"rst_n_out={qhld}", HIER)
                phase.drop_objection(self)
                return

        # 3. Mid-run re-assert clears both flops again (async).
        # We are on a falling edge; rst_n_out is 1.
        qa = await self._async_assert_in()
        if qa != 0:
            self.bad(name, "mid-run rst_n_in=0 (100ps, no posedge)",
                     "rst_n_out=0 (async re-assert)",
                     f"rst_n_out={qa}", HIER)
            phase.drop_objection(self)
            return
        qr = await self._settle_out(rst_n_in=0)
        if not self._score(name, "mid-run rst_n_in held 0 through dest posedge",
                           qr):
            phase.drop_objection(self)
            return
        if qr != 0:
            self.bad(name, "mid-run rst_n_in held 0 through dest posedge",
                     "rst_n_out stays 0",
                     f"rst_n_out={qr}", HIER)
            phase.drop_objection(self)
            return

        # After re-assert, pipe must be empty: first release clock still 0.
        # (If r1 were not cleared, rst_n_out would rise after 1 dest clock.)
        sset(d.rst_n_in, 1)
        q1b = await self._settle_out()
        if not self._score(name, "after re-assert, rst_n_in=1, 1 dest posedge",
                           q1b):
            phase.drop_objection(self)
            return
        if q1b != 0:
            self.bad(name, "after re-assert, rst_n_in=1, 1 dest posedge",
                     "rst_n_out=0 (r1 was cleared)",
                     f"rst_n_out={q1b}", HIER)
            phase.drop_objection(self)
            return
        q2b = await self._settle_out()
        if not self._score(name, "after re-assert, rst_n_in=1, 2 dest posedges",
                           q2b):
            phase.drop_objection(self)
            return
        if q2b != 1:
            self.bad(name, "after re-assert, rst_n_in=1, 2 dest posedges",
                     "rst_n_out=1 (2-FF sync deassert)",
                     f"rst_n_out={q2b}", HIER)
            phase.drop_objection(self)
            return

        # 4. Leaf has only clk / rst_n_in / rst_n_out (no ready/valid).
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_rst_sync product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_rst_sync)
