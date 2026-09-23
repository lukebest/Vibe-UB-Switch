"""Module-level uvm-python TC for Decision-I leaf vibe_rst_sync.

Covers async assert of rst_n_out, 2-FF sync deassert (not 1), mid-run re-assert.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/cdc/vibe_rst_sync.sv and stock tc_rst_sync semantics:
async assert on rst_n_in, sync release into clk (r1 then rst_n_out).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest


class tc_vibe_rst_sync(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _settle_out(self):
        """NBA-stable rst_n_out on the falling edge after a posedge."""
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)
        return ival(self.dut.rst_n_out, -1)

    async def _async_assert_in(self):
        """Drive rst_n_in=0 mid-cycle (no dest posedge)."""
        sset(self.dut.rst_n_in, 0)
        await Timer(100, "PS")
        return ival(self.dut.rst_n_out, -1)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_rst_sync"

        # Start from a known async-asserted state (X-safe at time 0).
        sset(d.rst_n_in, 0)
        await self.cycles(3)
        await FallingEdge(d.clk)

        # 1. Assert async reset → rst_n_out asserted without a dest posedge.
        # Already held 0; re-assert mid-cycle and sample before the next edge.
        q0 = await self._async_assert_in()
        if q0 != 0:
            self.bad(name, "rst_n_in=0 mid-cycle (100ps, no posedge)",
                     "rst_n_out=0 (async assert)",
                     f"rst_n_out={q0}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return
        # Hold through a dest posedge while still asserted.
        qh = await self._settle_out()
        if qh != 0:
            self.bad(name, "rst_n_in held 0 through dest posedge",
                     "rst_n_out stays 0",
                     f"rst_n_out={qh}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return

        # 2. Deassert async reset → release only after 2 dest clocks (not 1).
        # Apply on this falling edge (NBA-stable sample after each posedge).
        sset(d.rst_n_in, 1)
        q1 = await self._settle_out()
        if q1 != 0:
            self.bad(name, "rst_n_in=1, 1 dest posedge",
                     "rst_n_out=0 (still in r1)",
                     f"rst_n_out={q1}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return
        q2 = await self._settle_out()
        if q2 != 1:
            self.bad(name, "rst_n_in=1, 2 dest posedges",
                     "rst_n_out=1 (2-FF sync deassert)",
                     f"rst_n_out={q2}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return

        # 3. Mid-run re-assert clears both flops again (async).
        # We are on a falling edge; rst_n_out is 1.
        qa = await self._async_assert_in()
        if qa != 0:
            self.bad(name, "mid-run rst_n_in=0 (100ps, no posedge)",
                     "rst_n_out=0 (async re-assert)",
                     f"rst_n_out={qa}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return
        qr = await self._settle_out()
        if qr != 0:
            self.bad(name, "mid-run rst_n_in held 0 through dest posedge",
                     "rst_n_out stays 0",
                     f"rst_n_out={qr}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return

        # After re-assert, pipe must be empty: first release clock still 0.
        # (If r1 were not cleared, rst_n_out would rise after 1 dest clock.)
        sset(d.rst_n_in, 1)
        q1b = await self._settle_out()
        if q1b != 0:
            self.bad(name, "after re-assert, rst_n_in=1, 1 dest posedge",
                     "rst_n_out=0 (r1 was cleared)",
                     f"rst_n_out={q1b}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return
        q2b = await self._settle_out()
        if q2b != 1:
            self.bad(name, "after re-assert, rst_n_in=1, 2 dest posedges",
                     "rst_n_out=1 (2-FF sync deassert)",
                     f"rst_n_out={q2b}", "u_rst_sync.rst_n_out")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_rst_sync)
