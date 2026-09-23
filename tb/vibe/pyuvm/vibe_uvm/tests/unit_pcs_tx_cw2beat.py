"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_cw2beat.

Covers reset/idle (no spurious beat_vld, cw_ready), 1024→exactly 2×512
(high beat first), hold-full backpressure without drop/dup, and a second
codeword after drain. Not a full-chip consecutive-green gate. Not 1/3,
4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_tx_cw2beat.sv and stock tc_pcs_cw2beat
count semantics, plus hi/lo data scoring. Combo: cw_ready =
!have_hi && !have_lo; beat_vld = have_hi || have_lo; beat_data =
have_hi ? hi : lo. Accept parks cw_data[1023:512] / [511:0]; consume
clears have_hi first, then have_lo. Used by vibe_pcs_tx u_cw.
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK512 = (1 << 512) - 1
MASK1024 = (1 << 1024) - 1

# Distinct 512b halves so a hi/lo swap cannot pass by accident.
# Stock Icarus tc_pcs_cw2beat uses {512'hA, 512'hB}.
STOCK_HI = 0xA
STOCK_LO = 0xB
HI1 = int("C0DE" * 32, 16)
LO1 = int("BEEF" * 32, 16)
HI2 = int("A5A5" * 32, 16)
LO2 = int("5A5A" * 32, 16)


def _word512(v: int) -> int:
    return v & MASK512


def pack_cw(hi: int, lo: int) -> int:
    """1024b codeword: {hi[511:0], lo[511:0]}."""
    return ((_word512(hi) << 512) | _word512(lo)) & MASK1024


def split_cw(cw: int):
    """Golden 1024→2×512: high beat first, then low."""
    w = cw & MASK1024
    return (w >> 512) & MASK512, w & MASK512


def _hex512(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0128x}"


class tc_vibe_pcs_tx_cw2beat(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.cw_vld, 0)
        sset(d.cw_data, 0)
        sset(d.beat_ready, 1)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    def _sample(self):
        d = self.dut
        return (
            ival(d.beat_vld, -1),
            ival(d.beat_data, -1),
            ival(d.cw_ready, -1),
        )

    async def _advance(self, cw_vld, cw_data, beat_ready):
        """On falling edge: drive, take if beat_vld&&beat_ready, land on next fall.

        Returns (taken_or_None, accepted, post_beat_vld, post_beat_data, post_cw_ready).
        """
        d = self.dut
        sset(d.beat_ready, 1 if beat_ready else 0)
        sset(d.cw_data, cw_data & MASK1024)
        sset(d.cw_vld, 1 if cw_vld else 0)
        # Combo cw_ready / beat_vld / beat_data need a delta after sset.
        await Timer(100, "PS")
        cr = ival(d.cw_ready, 0)
        bv = ival(d.beat_vld, 0)
        bd = ival(d.beat_data, 0)
        taken = bd if (bv == 1 and beat_ready) else None
        accepted = bool(cw_vld) and bool(cr)
        await self._to_fall()
        post_bv, post_bd, post_cr = self._sample()
        return taken, accepted, post_bv, post_bd, post_cr

    async def _drain(self, outs, n=6):
        for _ in range(n):
            taken, _, bv, _, _ = await self._advance(0, 0, 1)
            if taken is not None:
                outs.append(taken)
            if bv == 0:
                break

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_cw2beat"
        hier = "u_cw.have_hi / have_lo"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, cw_ready, no spurious beat_vld, beat_data held 0.
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "reset then release, cw_vld=0 beat_ready=1",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, accepted, bv, bd, cr = await self._advance(0, pack_cw(0x55, 0xAA), 1)
            if taken is not None or accepted or bv != 0 or cr != 1 or bd != 0:
                self.bad(name, f"idle cycle {i} after reset (cw_vld=0)",
                         "no beat handshake, beat_vld=0 cw_ready=1 beat_data=0",
                         f"taken={_hex512(taken)} accepted={accepted} "
                         f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                         hier)
                phase.drop_objection(self)
                return

        # 2. One 1024b cw, beat_ready=1 → exactly hi then lo (stock {A,B}).
        stock = pack_cw(STOCK_HI, STOCK_LO)
        exp_hi, exp_lo = split_cw(stock)
        outs = []
        taken, accepted, bv, bd, cr = await self._advance(1, stock, 1)
        if taken is not None or not accepted:
            self.bad(name, "stock {512'hA,512'hB} accept",
                     "accept, no beat yet (empty → park both halves)",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_cw.cw_ready")
            phase.drop_objection(self)
            return
        await self._drain(outs)
        if outs != [exp_hi, exp_lo]:
            self.bad(name, "one 1024b cw, beat_ready=1 (stock A/B)",
                     f"exactly 2×512: hi={_hex512(exp_hi)} lo={_hex512(exp_lo)}",
                     f"n={len(outs)} " + " ".join(_hex512(x) for x in outs),
                     "u_cw.beat_data")
            phase.drop_objection(self)
            return

        # Distinctive wide halves (not just the stock nibble pair).
        cw1 = pack_cw(HI1, LO1)
        exp1 = list(split_cw(cw1))
        outs1 = []
        taken, accepted, bv, _, cr = await self._advance(1, cw1, 1)
        if taken is not None or not accepted:
            self.bad(name, "wide cw1 accept",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_cw.cw_ready")
            phase.drop_objection(self)
            return
        await self._drain(outs1)
        if outs1 != exp1:
            self.bad(name, "one 1024b cw, beat_ready=1 (wide C0DE/BEEF)",
                     f"exactly 2×512: hi={_hex512(exp1[0])} lo={_hex512(exp1[1])}",
                     f"n={len(outs1)} " + " ".join(_hex512(x) for x in outs1),
                     "u_cw.beat_data")
            phase.drop_objection(self)
            return

        # 3. Backpressure: stall when beat_ready=0 after accept; no drop/dup.
        cw_bp = pack_cw(HI1, LO1)
        exp_bp = list(split_cw(cw_bp))
        taken, accepted, bv, bd, cr = await self._advance(1, cw_bp, 0)
        if taken is not None or not accepted:
            self.bad(name, "bp accept with beat_ready=0",
                     "accept, no take (empty at sample)",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} beat_data={_hex512(bd)} cw_ready={cr}",
                     "u_cw.cw_ready")
            phase.drop_objection(self)
            return
        # Both halves parked. beat_ready=0 must hold hi, cw_ready=0.
        for i in range(3):
            taken, accepted, bv, bd, cr = await self._advance(1, pack_cw(HI2, LO2), 0)
            if (taken is not None or accepted or bv != 1
                    or bd != exp_bp[0] or cr != 0):
                self.bad(name, f"bp stall[{i}] beat_ready=0 both halves parked",
                         f"no take/accept, beat_vld=1 beat_data={_hex512(exp_bp[0])} "
                         "cw_ready=0",
                         f"taken={_hex512(taken)} accepted={accepted} "
                         f"beat_vld={bv} beat_data={_hex512(bd)} cw_ready={cr}",
                         "u_cw.cw_ready")
                phase.drop_objection(self)
                return
        # Resume: take hi (no new input).
        taken, accepted, bv, bd, cr = await self._advance(0, 0, 1)
        if taken != exp_bp[0] or accepted:
            self.bad(name, "bp resume take hi",
                     f"take {_hex512(exp_bp[0])}, no new accept",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} beat_data={_hex512(bd)}",
                     "u_cw.beat_data")
            phase.drop_objection(self)
            return
        outs_bp = [taken]
        await self._drain(outs_bp)
        if outs_bp != exp_bp:
            self.bad(name, "bp resume after stall, same 1024b",
                     "no drop/dup: " + " ".join(_hex512(x) for x in exp_bp),
                     f"n={len(outs_bp)} " + " ".join(_hex512(x) for x in outs_bp),
                     "u_cw.beat_data")
            phase.drop_objection(self)
            return

        # 4. Second codeword after drain (phase wrap / no leftover halves).
        cw2 = pack_cw(HI2, LO2)
        exp2 = list(split_cw(cw2))
        outs2 = []
        taken, accepted, bv, _, cr = await self._advance(1, cw2, 1)
        if taken is not None or not accepted:
            self.bad(name, "second cw accept after drain",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_cw.cw_ready")
            phase.drop_objection(self)
            return
        await self._drain(outs2)
        if outs2 != exp2:
            self.bad(name, "second 1024b cw after drain (A5A5/5A5A)",
                     f"exactly 2×512: hi={_hex512(exp2[0])} lo={_hex512(exp2[1])}",
                     f"n={len(outs2)} " + " ".join(_hex512(x) for x in outs2),
                     "u_cw.beat_data")
            phase.drop_objection(self)
            return

        # Async rst_n mid-hold clears registered halves. Idle first so
        # release does not immediately consume another codeword.
        taken, accepted, _, _, _ = await self._advance(1, cw1, 0)
        if not accepted or taken is not None:
            self.bad(name, "park cw before async re-reset",
                     "accept, no take",
                     f"taken={_hex512(taken)} accepted={accepted}",
                     "u_cw.cw_ready")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "async rst_n=0 mid-hold (100ps, no posedge)",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     "u_cw.have_hi")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "after async re-reset release, idle",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     "u_cw.have_hi")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_cw2beat)
