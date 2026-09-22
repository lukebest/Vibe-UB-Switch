"""Module-level uvm-python TC for Decision-I leaf vibe_afifo.

Covers reset flags, CDC data integrity, fill/almost_full@10, and drain.
Not a full-chip consecutive-green gate.
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

DEPTH = 16
AFULL_OCC = 10
N_INTEGRITY = 8


def _word160(i: int) -> int:
    """Distinct 160-bit pattern (i in low bits of each 32-bit slice)."""
    return (
        ((0xC0DE0000 + i) << 128)
        | ((0xBEEF0000 + i) << 96)
        | ((0xA5A50000 + i) << 64)
        | ((0x11110000 + i) << 32)
        | (0x00000000 + i)
    )


class tc_vibe_afifo(VibeUnitBaseTest):
    def clk(self):
        return self.dut.wclk

    async def _idle(self):
        d = self.dut
        sset(d.wen, 0)
        sset(d.ren, 0)
        sset(d.wdata, 0)

    async def _hold_reset(self, n_w=4, n_r=4):
        d = self.dut
        sset(d.wrst_n, 0)
        sset(d.rrst_n, 0)
        await self._idle()
        for _ in range(n_w):
            await RisingEdge(d.wclk)
        for _ in range(n_r):
            await RisingEdge(d.rclk)

    async def _release_reset(self, n_w=6, n_r=6):
        d = self.dut
        sset(d.wrst_n, 1)
        sset(d.rrst_n, 1)
        # 2-FF gray sync + margin on both domains.
        for _ in range(n_w):
            await RisingEdge(d.wclk)
        for _ in range(n_r):
            await RisingEdge(d.rclk)

    async def _write_one(self, data: int):
        d = self.dut
        await FallingEdge(d.wclk)
        sset(d.wdata, data)
        sset(d.wen, 1)
        await RisingEdge(d.wclk)

    async def _write_stop(self):
        d = self.dut
        await FallingEdge(d.wclk)
        sset(d.wen, 0)
        await RisingEdge(d.wclk)

    async def _read_one(self):
        d = self.dut
        await FallingEdge(d.rclk)
        val = ival(d.rdata, -1)
        empty = ival(d.rempty, 1)
        sset(d.ren, 0 if empty else 1)
        await RisingEdge(d.rclk)
        return empty, val

    async def _read_stop(self):
        d = self.dut
        await FallingEdge(d.rclk)
        sset(d.ren, 0)
        await RisingEdge(d.rclk)

    async def _wait_w(self, n=4):
        for _ in range(n):
            await RisingEdge(self.dut.wclk)

    async def _wait_r(self, n=4):
        for _ in range(n):
            await RisingEdge(self.dut.rclk)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_afifo"

        await self._hold_reset()
        await self._release_reset()

        # 1. reset → rempty, not wfull (NBA-stable on falling edge).
        await FallingEdge(d.wclk)
        wfull = ival(d.wfull, 1)
        afull = ival(d.almost_full, 1)
        wocc = ival(d.wocc, -1)
        if wfull or afull or wocc not in (0, None):
            self.bad(name, "reset (both domains)",
                     "wfull=0 almost_full=0 wocc=0",
                     f"wfull={wfull} afull={afull} wocc={wocc}",
                     "u_afifo.wfull")
            phase.drop_objection(self)
            return
        await FallingEdge(d.rclk)
        if not ival(d.rempty, 0):
            self.bad(name, "reset (both domains)", "rempty=1",
                     str(ival(d.rempty, -1)), "u_afifo.rempty")
            phase.drop_objection(self)
            return

        # 2. write/read data integrity across clock domains (wclk:rclk = 1:2).
        words = [_word160(i) for i in range(N_INTEGRITY)]
        for w in words:
            await self._write_one(w)
        await self._write_stop()
        await self._wait_r(6)
        await FallingEdge(d.rclk)
        if ival(d.rempty, 1):
            self.bad(name, f"{N_INTEGRITY} writes then CDC settle",
                     "rempty=0", "1", "u_afifo.rempty")
            phase.drop_objection(self)
            return
        got = []
        for i in range(N_INTEGRITY):
            empty, val = await self._read_one()
            if empty:
                self.bad(name, f"read[{i}] after {N_INTEGRITY} writes",
                         "rempty=0", "1", "u_afifo.rempty")
                phase.drop_objection(self)
                return
            got.append(val)
        await self._read_stop()
        if got != words:
            exp = " ".join(f"{w:x}" for w in words)
            act = " ".join(f"{v:x}" if v is not None else "x" for v in got)
            self.bad(name, f"{N_INTEGRITY} unique 160b words, async clocks",
                     exp, act, "u_afifo.rdata")
            phase.drop_objection(self)
            return

        # Wait for rptr to sync back so write-domain occupancy is 0.
        await self._wait_w(8)
        await FallingEdge(d.wclk)
        if ival(d.wocc, -1) != 0 or ival(d.wfull, 1) or ival(d.almost_full, 1):
            self.bad(name, "after integrity drain + rptr sync",
                     "wocc=0 wfull=0 almost_full=0",
                     f"wocc={ival(d.wocc, -1)} wfull={ival(d.wfull, -1)} "
                     f"afull={ival(d.almost_full, -1)}",
                     "u_afifo.wocc")
            phase.drop_objection(self)
            return

        # 3. fill: almost_full at occ>=10, wfull at DEPTH.
        for i in range(AFULL_OCC - 1):
            await self._write_one(0x10 + i)
        await self._write_stop()
        await FallingEdge(d.wclk)
        if ival(d.almost_full, 1) or ival(d.wocc, -1) != AFULL_OCC - 1:
            self.bad(name, f"{AFULL_OCC - 1} writes no reads",
                     f"almost_full=0 wocc={AFULL_OCC - 1}",
                     f"afull={ival(d.almost_full, -1)} wocc={ival(d.wocc, -1)}",
                     "u_afifo.almost_full")
            phase.drop_objection(self)
            return
        await self._write_one(0x10 + AFULL_OCC - 1)
        await self._write_stop()
        await FallingEdge(d.wclk)
        if not ival(d.almost_full, 0) or ival(d.wocc, -1) != AFULL_OCC:
            self.bad(name, f"{AFULL_OCC} writes no reads",
                     f"almost_full=1 (occ>={AFULL_OCC}) wocc={AFULL_OCC}",
                     f"afull={ival(d.almost_full, -1)} wocc={ival(d.wocc, -1)}",
                     "u_afifo.almost_full")
            phase.drop_objection(self)
            return
        for i in range(AFULL_OCC, DEPTH):
            await self._write_one(0x10 + i)
        await self._write_stop()
        await FallingEdge(d.wclk)
        if not ival(d.wfull, 0) or ival(d.wocc, -1) != DEPTH:
            self.bad(name, f"{DEPTH} writes no reads",
                     f"wfull=1 wocc={DEPTH}",
                     f"wfull={ival(d.wfull, -1)} wocc={ival(d.wocc, -1)}",
                     "u_afifo.wfull")
            phase.drop_objection(self)
            return
        # Write while full must not increment occupancy.
        await self._write_one(0xDEAD)
        await self._write_stop()
        await FallingEdge(d.wclk)
        if not ival(d.wfull, 0) or ival(d.wocc, -1) != DEPTH:
            self.bad(name, "wen while wfull",
                     f"wfull stays 1 wocc={DEPTH}",
                     f"wfull={ival(d.wfull, -1)} wocc={ival(d.wocc, -1)}",
                     "u_afifo.wbin")
            phase.drop_objection(self)
            return

        # 4. empty after drain.
        await self._wait_r(6)
        n_pop = 0
        for _ in range(DEPTH + 2):
            empty, _ = await self._read_one()
            if empty:
                break
            n_pop += 1
        await self._read_stop()
        await self._wait_r(4)
        await FallingEdge(d.rclk)
        if n_pop != DEPTH or not ival(d.rempty, 0):
            self.bad(name, f"drain after fill ({n_pop} pops)",
                     f"pop {DEPTH} then rempty=1",
                     f"pops={n_pop} rempty={ival(d.rempty, -1)}",
                     "u_afifo.rempty")
            phase.drop_objection(self)
            return
        await self._wait_w(8)
        await FallingEdge(d.wclk)
        if ival(d.wocc, -1) != 0 or ival(d.wfull, 1) or ival(d.almost_full, 1):
            self.bad(name, "after drain + rptr sync",
                     "wocc=0 wfull=0 almost_full=0",
                     f"wocc={ival(d.wocc, -1)} wfull={ival(d.wfull, -1)} "
                     f"afull={ival(d.almost_full, -1)}",
                     "u_afifo.wocc")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_afifo)
