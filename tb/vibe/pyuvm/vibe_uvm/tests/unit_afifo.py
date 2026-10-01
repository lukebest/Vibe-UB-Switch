"""Module-level uvm-python TC for Decision-I leaf vibe_afifo.

Covers dual-clock reset (wrst_n/rrst_n), CDC data integrity
across wclk/rclk, fill / almost_full@10, drain / empty,
write-while-full, read-while-empty, async mid-run reset,
and a pin scan (no ready/valid / ovf_l / CFG6). Not a
full-chip consecutive-green gate. Not 1/3, 4/3, freeze,
or signoff.

Matches product rtl/cdc/vibe_afifo.sv: per-lane gray-pointer
AFIFO, depth 16, ptr 5 bits, W=160 TX config. Write-domain
almost_full at occupancy >= 10. Independent wrst_n / rrst_n.
u_r2w / u_w2r are product vibe_sync2 children (stage-51).
ovf_l (F1) is not in this module — do not ECO. CFG6 packing
is 未知 — do not invent. Stock Icarus tc_afifo_afull10 remains
optional control. This is not vibe_sync2 / vibe_rst_sync / gear.
CHILDREN from product SV: u_r2w, u_w2r (leaf cell otherwise).
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import hier, ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

W = 160
DEPTH = 16
AFULL_OCC = 10
N_INTEGRITY = 8
ONES = (1 << W) - 1
WALK = (0, 1, 31, 32, 63, 64, 95, 96, 127, 128, 159)
HIER = "u_u.wocc / u_u.wfull / u_u.almost_full / u_u.rempty / u_u.rdata"
WRAP = "vibe_afifo_cocotb_top"
CHILDREN = ("u_r2w", "u_w2r")
PINS = (
    "wclk", "wrst_n", "wen", "wdata", "wfull", "almost_full", "wocc",
    "rclk", "rrst_n", "ren", "rdata", "rempty",
)
ABSENT = (
    "ready", "valid", "in_vld", "out_vld", "en", "ce",
    "ovf_l", "afifo_ovf", "cfg_wr", "cfg_rd", "cfg6",
    "clk", "rst_n",
)


def _word160(i: int) -> int:
    """Distinct 160-bit pattern (i in low bits of each 32-bit slice)."""
    return (
        ((0xC0DE0000 + i) << 128)
        | ((0xBEEF0000 + i) << 96)
        | ((0xA5A50000 + i) << 64)
        | ((0x11110000 + i) << 32)
        | (0x00000000 + i)
    )


def _walk_words():
    return [1 << b for b in WALK]


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

    async def _release_wrst(self, n=6):
        sset(self.dut.wrst_n, 1)
        for _ in range(n):
            await RisingEdge(self.dut.wclk)

    async def _release_rrst(self, n=6):
        sset(self.dut.rrst_n, 1)
        for _ in range(n):
            await RisingEdge(self.dut.rclk)

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

    def _wflags(self):
        d = self.dut
        return (
            ival(d.wfull, 1),
            ival(d.almost_full, 1),
            ival(d.wocc, -1),
        )

    def _score_w(self, name, stim, full=0, afull=0, occ=0):
        wfull, afull_v, wocc = self._wflags()
        if bool(wfull) != bool(full) or bool(afull_v) != bool(afull) or wocc != occ:
            self.bad(name, stim,
                     f"wfull={int(bool(full))} almost_full={int(bool(afull))} "
                     f"wocc={occ}",
                     f"wfull={wfull} afull={afull_v} wocc={wocc}",
                     HIER)
            return False
        return True

    def _score_empty(self, name, stim, empty=1):
        got = ival(self.dut.rempty, 0 if empty else 1)
        if bool(got) != bool(empty):
            self.bad(name, stim,
                     f"rempty={int(bool(empty))}",
                     f"rempty={got}",
                     HIER)
            return False
        return True

    async def _sample_w(self, name, stim, full=0, afull=0, occ=0):
        await FallingEdge(self.dut.wclk)
        return self._score_w(name, stim, full=full, afull=afull, occ=occ)

    async def _sample_r(self, name, stim, empty=1):
        await FallingEdge(self.dut.rclk)
        return self._score_empty(name, stim, empty=empty)

    def _exists(self, path) -> bool:
        try:
            hier(self.dut, path)
            return True
        except Exception:
            return False

    def _score_children(self, name):
        """CHILDREN from product SV. Observe; VPI hide is not a fail."""
        if not self._exists("u_u"):
            return True
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_u.{inst}")]
        if missing and len(missing) != len(CHILDREN):
            self.bad(name, "product SV children u_r2w / u_w2r",
                     "both present or both hidden (VPI)",
                     f"missing={missing}", "u_u")
            return False
        return True

    async def _push_burst(self, words):
        for w in words:
            await self._write_one(w)
        await self._write_stop()

    async def _pop_n(self, name, tag, n):
        got = []
        for i in range(n):
            empty, val = await self._read_one()
            if empty:
                self.bad(name, f"{tag} read[{i}]",
                         "rempty=0", "1", HIER)
                return None
            got.append(val)
        await self._read_stop()
        return got

    async def _integrity(self, name, tag, words):
        await self._push_burst(words)
        await self._wait_r(6)
        await FallingEdge(self.dut.rclk)
        if ival(self.dut.rempty, 1):
            self.bad(name, f"{tag}: {len(words)} writes then CDC settle",
                     "rempty=0", "1", HIER)
            return False
        got = await self._pop_n(name, tag, len(words))
        if got is None:
            return False
        if got != words:
            exp = " ".join(f"{w:x}" for w in words)
            act = " ".join(f"{v:x}" if v is not None else "x" for v in got)
            self.bad(name, f"{tag}: unique 160b words, async clocks",
                     exp, act, HIER)
            return False
        await self._wait_w(8)
        await FallingEdge(self.dut.wclk)
        if not self._score_w(name, f"{tag}: after drain + rptr sync",
                             full=0, afull=0, occ=0):
            return False
        if not await self._sample_r(name, f"{tag}: rempty after drain"):
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_afifo"

        await self._hold_reset()

        # 1. Dual-clock reset: both domains held, then wrst_n first.
        if not await self._sample_w(name, "reset both held",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        if not await self._sample_r(name, "reset both held"):
            phase.drop_objection(self)
            return

        await self._release_wrst()
        if not await self._sample_w(name, "wrst_n released, rrst_n held",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        if not await self._sample_r(name, "rrst_n held (u_w2r cleared)"):
            phase.drop_objection(self)
            return

        # Write while read domain is still in reset: wocc tracks wbin,
        # rempty stays 1 (rbin=0 and wgray_s held 0).
        held = [_word160(0x40 + i) for i in range(3)]
        await self._push_burst(held)
        if not await self._sample_w(name, "3 writes, rrst_n held",
                                    full=0, afull=0, occ=3):
            phase.drop_objection(self)
            return
        if not await self._sample_r(name, "3 writes, rrst_n held"):
            phase.drop_objection(self)
            return

        await self._release_rrst()
        await self._wait_r(4)
        if not await self._sample_r(name, "rrst_n released, 3 words pending",
                                    empty=0):
            phase.drop_objection(self)
            return
        got = await self._pop_n(name, "after independent rrst_n", 3)
        if got is None:
            phase.drop_objection(self)
            return
        if got != held:
            exp = " ".join(f"{w:x}" for w in held)
            act = " ".join(f"{v:x}" if v is not None else "x" for v in got)
            self.bad(name, "CDC words written under rrst_n held",
                     exp, act, HIER)
            phase.drop_objection(self)
            return
        await self._wait_w(8)
        if not await self._sample_w(name, "after independent-reset drain",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        if not await self._sample_r(name, "after independent-reset drain"):
            phase.drop_objection(self)
            return

        # 2. write/read data integrity across clock domains (wclk:rclk = 1:2).
        words = [_word160(i) for i in range(N_INTEGRITY)]
        if not await self._integrity(name, f"{N_INTEGRITY} unique", words):
            phase.drop_objection(self)
            return

        # Distinctive 160b patterns (all-0, all-1s, walk-1). No CFG6 packing.
        extra = [0, ONES] + _walk_words()
        if not await self._integrity(name, "0/ones/walk-1", extra):
            phase.drop_objection(self)
            return

        # 3. fill: almost_full at occ>=10, wfull at DEPTH. Score every step.
        for i in range(DEPTH):
            await self._write_one(0x10 + i)
            await self._write_stop()
            occ = i + 1
            if not await self._sample_w(
                    name, f"{occ} writes no reads",
                    full=(occ == DEPTH),
                    afull=(occ >= AFULL_OCC),
                    occ=occ):
                phase.drop_objection(self)
                return

        # Write while full must not increment occupancy.
        await self._write_one(0xDEAD)
        await self._write_stop()
        if not await self._sample_w(name, "wen while wfull",
                                    full=1, afull=1, occ=DEPTH):
            phase.drop_objection(self)
            return

        # 4. empty after drain.
        await self._wait_r(6)
        n_pop = 0
        popped = []
        for _ in range(DEPTH + 2):
            empty, val = await self._read_one()
            if empty:
                break
            popped.append(val)
            n_pop += 1
        await self._read_stop()
        await self._wait_r(4)
        await FallingEdge(d.rclk)
        if n_pop != DEPTH or not ival(d.rempty, 0):
            self.bad(name, f"drain after fill ({n_pop} pops)",
                     f"pop {DEPTH} then rempty=1",
                     f"pops={n_pop} rempty={ival(d.rempty, -1)}",
                     HIER)
            phase.drop_objection(self)
            return
        expect_fill = [0x10 + i for i in range(DEPTH)]
        if popped != expect_fill:
            exp = " ".join(f"{w:x}" for w in expect_fill)
            act = " ".join(f"{v:x}" if v is not None else "x" for v in popped)
            self.bad(name, "drain data after fill",
                     exp, act, HIER)
            phase.drop_objection(self)
            return
        await self._wait_w(8)
        if not await self._sample_w(name, "after drain + rptr sync",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return

        # Read while empty must not pop (ren && rempty is a no-op).
        await FallingEdge(d.rclk)
        sset(d.ren, 1)
        await RisingEdge(d.rclk)
        await self._read_stop()
        if not await self._sample_r(name, "ren while rempty"):
            phase.drop_objection(self)
            return
        await self._wait_w(8)
        if not await self._sample_w(name, "ren while rempty (wocc stays 0)",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return

        # 5. Async dual-clock reset mid-run (100ps, no posedge).
        mid = [_word160(0x80 + i) for i in range(4)]
        await self._push_burst(mid)
        if not await self._sample_w(name, "pre-async-rst (4 writes)",
                                    full=0, afull=0, occ=4):
            phase.drop_objection(self)
            return
        sset(d.wrst_n, 0)
        sset(d.rrst_n, 0)
        await Timer(100, "PS")
        if not self._score_w(name, "async wrst_n/rrst_n mid-cycle (100ps)",
                             full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        if not self._score_empty(name, "async wrst_n/rrst_n mid-cycle (100ps)"):
            phase.drop_objection(self)
            return

        # Hold through one posedge on each domain while still reset.
        await RisingEdge(d.wclk)
        await FallingEdge(d.wclk)
        if not self._score_w(name, "rst held through wclk posedge",
                             full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        await RisingEdge(d.rclk)
        await FallingEdge(d.rclk)
        if not self._score_empty(name, "rst held through rclk posedge"):
            phase.drop_objection(self)
            return

        await self._release_reset()
        if not await self._sample_w(name, "after async re-release",
                                    full=0, afull=0, occ=0):
            phase.drop_objection(self)
            return
        if not await self._sample_r(name, "after async re-release"):
            phase.drop_objection(self)
            return

        # 6. Leaf pins match product SV (no ready/valid / ovf_l / CFG6).
        if not self._score_children(name):
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_afifo product port",
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


uvm_component_utils(tc_vibe_afifo)
