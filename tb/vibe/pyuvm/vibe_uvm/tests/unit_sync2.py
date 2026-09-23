"""Module-level uvm-python TC for Decision-I leaf vibe_sync2.

Covers reset-cleared q, 2-FF latency (not 1), streaming delay, async rst_n.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

W = 5
MASK = (1 << W) - 1
STABLE = 0x15
STREAM = (0x01, 0x1A, 0x05, 0x1F, 0x0A, 0x11, 0x07)


class tc_vibe_sync2(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        sset(self.dut.d, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _settle_q(self):
        """NBA-stable q on the falling edge after a posedge."""
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)
        return ival(self.dut.q, -1)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_sync2"

        await self._hold_reset()
        await self._release_reset()

        # 1. After reset: q==0 (NBA-stable on falling edge).
        await FallingEdge(d.clk)
        q0 = ival(d.q, -1)
        if q0 != 0:
            self.bad(name, "reset then release, d=0",
                     "q=0", f"q={q0}", "u_sync2.q")
            phase.drop_objection(self)
            return

        # 2. Stable d reaches q after 2 posedges (not 1).
        sset(d.d, STABLE)
        q1 = await self._settle_q()
        if q1 != 0:
            self.bad(name, f"stable d=0x{STABLE:02x}, 1 posedge",
                     "q=0 (still in q1)", f"q=0x{q1:x}", "u_sync2.q")
            phase.drop_objection(self)
            return
        q2 = await self._settle_q()
        if q2 != STABLE:
            self.bad(name, f"stable d=0x{STABLE:02x}, 2 posedges",
                     f"q=0x{STABLE:02x}", f"q=0x{q2:x}", "u_sync2.q")
            phase.drop_objection(self)
            return

        # Drain so streaming starts from a zero pipe (else q still holds STABLE).
        sset(d.d, 0)
        await self._settle_q()
        qz = await self._settle_q()
        if qz != 0:
            self.bad(name, "d=0 for 2 posedges after stable",
                     "q=0", f"q={qz}", "u_sync2.q")
            phase.drop_objection(self)
            return

        # 3. Streaming d changes: q tracks with 2-cycle delay.
        # Apply on this falling edge; after the next posedge, q is hist[-2]
        # (value applied two falling edges / two posedges ago).
        hist = []
        for i, val in enumerate(STREAM):
            val &= MASK
            sset(d.d, val)
            hist.append(val)
            qv = await self._settle_q()
            exp = hist[-2] if len(hist) >= 2 else 0
            if qv != exp:
                self.bad(name, f"stream[{i}] d=0x{val:02x} after posedge",
                         f"q=0x{exp:02x} (2-cycle delay)",
                         f"q=0x{qv:x}" if qv is not None else "q=x",
                         "u_sync2.q")
                phase.drop_objection(self)
                return

        # 4. Async rst_n low clears the pipeline (mid-cycle, not a posedge).
        # We are on a falling edge; q is STREAM[-2] (nonzero).
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        qa = ival(d.q, -1)
        if qa != 0:
            self.bad(name, "async rst_n=0 mid-cycle (100ps, no posedge)",
                     "q=0", f"q={qa}", "u_sync2.q")
            phase.drop_objection(self)
            return
        # Hold through a dest posedge while d is still the last stream value.
        qh = await self._settle_q()
        if qh != 0:
            self.bad(name, "rst_n held 0 through posedge, d still nonzero",
                     "q stays 0", f"q={qh}", "u_sync2.q")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_sync2)
