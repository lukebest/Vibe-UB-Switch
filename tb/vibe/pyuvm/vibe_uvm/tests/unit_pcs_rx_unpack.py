"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_rx_unpack.

Covers reset/idle (beat_vld=0, no spurious beat), AMCTL skip (am0..am3),
4×640 → exactly 5×512 unpack (inverse G2 / upcoming TX pack),
beat_ready backpressure without drop/dup, am_gap n-reset that keeps an
in-flight emit, dual-buffer nxt_full / acc swap, lane_vld stall without
a take, and a second group after drain. Not a full-chip consecutive-green
gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_rx_unpack.sv: async-low rst_n,
combo beat_vld=have, beat_data=acc[511:0], din={lane3,lane2,lane1,lane0},
take = lane_vld && !skip && !am_gap && !nxt_full, 4×640=2560=5×512
dual-buffer. Used by vibe_pcs_rx u_un. Stock Icarus tc_pcs_rx_unpack
remains the official beat_vld / am_gap / nxt_full scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
MASK1920 = (1 << 1920) - 1
MASK2560 = (1 << 2560) - 1
HIER = "u_u.have / u_u.acc"

ZEROS = (0, 0, 0, 0)
AMS0 = (0, 0, 0, 0)


def _word160(v: int) -> int:
    return int(v) & MASK160


def _word512(v: int) -> int:
    return int(v) & MASK512


def _hex512(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0128x}"


def _pat(tag: int, lane: int) -> int:
    """40 hex digits = 160b. Tag/lane in every nibble pair so a slice swap fails."""
    return int(f"{tag & 0xFF:02X}{lane & 0xFF:02X}" * 10, 16) & MASK160


def group(tag: int):
    """One 4×160 / 640b ingress word as (lane0, lane1, lane2, lane3)."""
    return tuple(_pat(tag, i) for i in range(4))


def din_of(lanes) -> int:
    """Product din = {lane3, lane2, lane1, lane0}."""
    l0, l1, l2, l3 = (_word160(x) for x in lanes)
    return ((l3 << 480) | (l2 << 320) | (l1 << 160) | l0) & MASK640


def pack_4x640_to_5x512(lane_groups):
    """Golden 4×640 → 5×512 LSB-first (acc = {din3, din2, din1, din0}).

    stream = din0 || din1 || din2 || din3 (din0 in the LSBs).
    beat[i] = stream[512*i +: 512]. Inverse of TX 5×512 ↔ 4×640.
    """
    if len(lane_groups) != 4:
        raise ValueError("pack_4x640_to_5x512 expects 4 lane groups")
    stream = 0
    for i, lanes in enumerate(lane_groups):
        stream |= din_of(lanes) << (i * 640)
    return [((stream >> (i * 512)) & MASK512) for i in range(5)]


# Distinctive 4×640 groups. Stock Icarus uses small n / n+16 / n+32 / n+48.
STOCK = [((n, n + 16, n + 32, n + 48)) for n in range(4)]
G1 = [group(0xA0 + k) for k in range(4)]
G2 = [group(0xB0 + k) for k in range(4)]
G3 = [group(0xC0 + k) for k in range(4)]
G4 = [group(0xD0 + k) for k in range(4)]


class Golden:
    """Cycle-accurate dual-buffer vs product always-block (emit then take)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.acc = 0
        self.nxt = 0
        self.n = 0
        self.e = 0
        self.have = 0
        self.nxt_full = 0

    @property
    def beat_vld(self) -> int:
        return int(self.have)

    @property
    def beat_data(self) -> int:
        return int(self.acc) & MASK512

    def step(self, lane_vld, lanes, ams, am_gap, beat_ready):
        skip = any(ams)
        din = din_of(lanes)
        take = bool(lane_vld) and not skip and not am_gap and not self.nxt_full

        acc, nxt = self.acc, self.nxt
        n, e, have, nxt_full = self.n, self.e, self.have, self.nxt_full
        have0, e0, nxt0, nxt_full0, n0 = (
            self.have, self.e, self.nxt, self.nxt_full, self.n
        )

        if am_gap:
            n = 0

        if have0 and beat_ready:
            if e0 != 0:
                acc = (acc >> 512) & MASK2560
                e = e0 - 1
            elif nxt_full0:
                acc = nxt0
                e = 4
                have = 1
                nxt_full = 0
            else:
                have = 0

        if take:
            if n0 == 3:
                assembled = ((din << 1920) | (nxt0 & MASK1920)) & MASK2560
                if (not have0) or (have0 and beat_ready and e0 == 0
                                   and not nxt_full0):
                    acc = assembled
                    e = 4
                    have = 1
                    n = 0
                else:
                    nxt = assembled
                    nxt_full = 1
                    n = 0
            else:
                shift = 640 * n0
                mask = MASK640 << shift
                nxt = ((nxt0 & ~mask) | ((din & MASK640) << shift)) & MASK2560
                n = n0 + 1

        self.acc = acc & MASK2560
        self.nxt = nxt & MASK2560
        self.n = n & 7
        self.e = e & 7
        self.have = have & 1
        self.nxt_full = nxt_full & 1


class tc_vibe_pcs_rx_unpack(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.lane_vld, 0)
        sset(d.am_gap, 0)
        sset(d.beat_ready, 1)
        for i in range(4):
            sset(getattr(d, f"lane{i}"), 0)
            sset(getattr(d, f"am{i}"), 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)
        self.g.reset()

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    def _sample(self):
        d = self.dut
        return ival(d.beat_vld, -1), ival(d.beat_data, -1)

    def _score_now(self, name, stim, bv, bd):
        exp_bv = self.g.beat_vld
        exp_bd = self.g.beat_data
        if bv != exp_bv:
            self.bad(name, stim,
                     f"beat_vld={exp_bv}",
                     f"beat_vld={bv}",
                     "u_u.have")
            return False
        if bv == 1 and (bd is None or bd != exp_bd):
            self.bad(name, stim + " (unpack 4×640→5×512)",
                     f"beat_data={_hex512(exp_bd)}",
                     f"beat_data={_hex512(bd)}",
                     "u_u.acc")
            return False
        if bv == 0 and bd not in (0, exp_bd) and bd is None:
            self.bad(name, stim,
                     "beat_data resolved",
                     "x",
                     "u_u.acc")
            return False
        return True

    async def _apply(self, name, stim, lane_vld, lanes,
                     ams=AMS0, am_gap=0, beat_ready=1):
        """Drive on falling edge; score registers then NBA after the posedge.

        Returns (taken_or_None, post_beat_vld, post_beat_data).
        taken is pre-posedge beat_data when beat_vld && beat_ready.
        """
        d = self.dut
        sset(d.lane_vld, 1 if lane_vld else 0)
        sset(d.am_gap, 1 if am_gap else 0)
        sset(d.beat_ready, 1 if beat_ready else 0)
        for i in range(4):
            sset(getattr(d, f"lane{i}"), _word160(lanes[i]))
            sset(getattr(d, f"am{i}"), 1 if ams[i] else 0)
        await Timer(100, "PS")
        pre_bv, pre_bd = self._sample()
        if not self._score_now(name, stim + " (pre-posedge)", pre_bv, pre_bd):
            return None, pre_bv, pre_bd
        taken = pre_bd if (pre_bv == 1 and beat_ready) else None
        self.g.step(1 if lane_vld else 0, lanes, ams,
                    1 if am_gap else 0, 1 if beat_ready else 0)
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        post_bv, post_bd = self._sample()
        if not self._score_now(name, stim + " (post-NBA)", post_bv, post_bd):
            return None, post_bv, post_bd
        await FallingEdge(d.clk)
        return taken, post_bv, post_bd

    async def _feed_groups(self, name, label, groups, outs, beat_ready=1):
        for gi, lanes in enumerate(groups):
            taken, _, _ = await self._apply(
                name, f"{label} 640[{gi}]", 1, lanes, beat_ready=beat_ready)
            if taken is None and self.fail_n:
                return False
            if taken is not None:
                outs.append(taken)
        return True

    async def _drain(self, name, label, outs, n=8):
        for i in range(n):
            taken, bv, _ = await self._apply(
                name, f"{label} drain[{i}]", 0, ZEROS, beat_ready=1)
            if taken is None and self.fail_n:
                return False
            if taken is not None:
                outs.append(taken)
            if bv == 0:
                break
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_rx_unpack"
        self.g = Golden()

        exp1 = pack_4x640_to_5x512(G1)
        exp2 = pack_4x640_to_5x512(G2)
        exp_stock = pack_4x640_to_5x512(STOCK)
        if len(set(exp1)) != 5 or len(set(exp2)) != 5:
            self.bad(name, "golden 5×512 uniqueness",
                     "5 distinct beats per group",
                     f"G1={len(set(exp1))} G2={len(set(exp2))}",
                     "golden")
            phase.drop_objection(self)
            return
        if (exp1[0] & MASK160) != G1[0][0]:
            self.bad(name, "golden beat0 LSBs are lane0 of first 640",
                     _hex512(G1[0][0]),
                     _hex512(exp1[0] & MASK160),
                     "golden")
            phase.drop_objection(self)
            return
        if exp1 == exp2:
            self.bad(name, "golden G1 vs G2",
                     "distinct groups",
                     "equal",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, no spurious beat_vld, beat_data held 0.
        bv, bd = self._sample()
        if bv != 0 or bd != 0:
            self.bad(name, "reset then release, lane_vld=0 beat_ready=1",
                     "beat_vld=0 beat_data=0",
                     f"beat_vld={bv} beat_data={_hex512(bd)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, bv, bd = await self._apply(
                name, f"idle cycle {i} after reset (lane_vld=0)",
                0, G1[0], beat_ready=1)
            if taken is not None or bv != 0:
                self.bad(name, f"idle cycle {i} after reset",
                         "no beat handshake, beat_vld=0",
                         f"taken={_hex512(taken)} beat_vld={bv}",
                         HIER)
                phase.drop_objection(self)
                return

        # AMCTL skip: any am* drops take. Each lane, then all four.
        for lane in range(4):
            ams = tuple(1 if i == lane else 0 for i in range(4))
            taken, bv, _ = await self._apply(
                name, f"AM skip lane{lane} (no take)",
                1, G1[0], ams=ams, beat_ready=1)
            if taken is not None or bv != 0 or self.g.n != 0:
                self.bad(name, f"AM skip lane{lane}",
                         "beat_vld=0 n stays 0",
                         f"taken={_hex512(taken)} beat_vld={bv} n={self.g.n}",
                         "u_u.n")
                phase.drop_objection(self)
                return
        taken, bv, _ = await self._apply(
            name, "AM skip all lanes",
            1, G1[0], ams=(1, 1, 1, 1), beat_ready=1)
        if taken is not None or bv != 0 or self.fail_n:
            if self.fail_n:
                phase.drop_objection(self)
                return
            self.bad(name, "AM skip all lanes",
                     "beat_vld=0",
                     f"taken={_hex512(taken)} beat_vld={bv}",
                     "u_u.have")
            phase.drop_objection(self)
            return

        # 2. Stock-like 4×640 → exactly 5×512 (Icarus n / n+16 / n+32 / n+48).
        outs = []
        if not await self._feed_groups(name, "stock", STOCK, outs):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "stock", outs):
            phase.drop_objection(self)
            return
        if outs != exp_stock:
            self.bad(name, "one 4×640 group, beat_ready=1 (stock n/n+16/…)",
                     f"exactly 5×512: {' '.join(_hex512(x) for x in exp_stock)}",
                     f"n={len(outs)} " + " ".join(_hex512(x) for x in outs),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # Wide distinctive lanes (not just the stock nibble pair).
        outs1 = []
        if not await self._feed_groups(name, "wide G1", G1, outs1):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "wide G1", outs1):
            phase.drop_objection(self)
            return
        if outs1 != exp1:
            self.bad(name, "one 4×640 group, beat_ready=1 (wide G1)",
                     f"exactly 5×512 n=5 first={_hex512(exp1[0])}",
                     f"n={len(outs1)} first={_hex512(outs1[0]) if outs1 else 'x'}",
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # Async rst_n mid-fill clears have / n without a posedge.
        if not await self._feed_groups(name, "pre-async 640", G2[:2], []):
            phase.drop_objection(self)
            return
        if self.g.n != 2:
            self.bad(name, "pre-async fill",
                     "n=2",
                     f"n={self.g.n}",
                     "u_u.n")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        bv, _ = self._sample()
        if bv != 0:
            self.bad(name, "async rst_n=0 mid-fill (100ps, no posedge)",
                     "beat_vld=0",
                     f"beat_vld={bv}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.beat_vld, -1) != 0:
            self.bad(name, "after async re-reset release, idle",
                     "beat_vld=0",
                     f"beat_vld={ival(d.beat_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return

        # 3. Backpressure: hold first beat; no drop/dup.
        outs_bp = []
        if not await self._feed_groups(name, "bp fill G1", G1, outs_bp,
                                       beat_ready=0):
            phase.drop_objection(self)
            return
        if outs_bp:
            self.bad(name, "bp fill with beat_ready=0",
                     "no take",
                     f"taken {len(outs_bp)}",
                     "u_u.beat_ready")
            phase.drop_objection(self)
            return
        if ival(d.beat_vld, -1) != 1:
            self.bad(name, "bp after 4×640 (have, held)",
                     "beat_vld=1",
                     f"beat_vld={ival(d.beat_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        held = ival(d.beat_data, -1)
        for i in range(3):
            taken, bv, bd = await self._apply(
                name, f"bp hold[{i}] beat_ready=0",
                0, ZEROS, beat_ready=0)
            if taken is not None or bv != 1 or bd != held:
                self.bad(name, f"bp hold[{i}]",
                         f"no take, beat_vld=1 data stay {_hex512(held)}",
                         f"taken={_hex512(taken)} beat_vld={bv} "
                         f"data={_hex512(bd)}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "bp", outs_bp):
            phase.drop_objection(self)
            return
        if outs_bp != exp1:
            self.bad(name, "bp drain after hold (no drop/dup)",
                     f"exactly 5×512 first={_hex512(exp1[0])}",
                     f"n={len(outs_bp)} first="
                     f"{_hex512(outs_bp[0]) if outs_bp else 'x'}",
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # Dual-buffer: keep feeding while emitting so n==3 hits nxt_full / swap.
        stream = G1 + G2 + G3 + G4[:1]  # 9×640: two full + one extra
        outs_d = []
        if not await self._feed_groups(name, "dual-buffer stream", stream,
                                       outs_d, beat_ready=1):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "dual-buffer", outs_d, n=16):
            phase.drop_objection(self)
            return
        exp_d = (pack_4x640_to_5x512(G1)
                 + pack_4x640_to_5x512(G2)
                 + pack_4x640_to_5x512(G3))
        if outs_d != exp_d:
            self.bad(name, "dual-buffer 3 groups while emitting",
                     f"exactly 15×512 n=15",
                     f"n={len(outs_d)}",
                     "u_u.nxt_full")
            phase.drop_objection(self)
            return

        # nxt_full blocks take: fill acc + nxt with beat_ready=0, extra 640 ignored.
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        parked = []
        if not await self._feed_groups(name, "park G1", G1, parked,
                                       beat_ready=0):
            phase.drop_objection(self)
            return
        if not await self._feed_groups(name, "park G2 → nxt_full", G2, parked,
                                       beat_ready=0):
            phase.drop_objection(self)
            return
        if parked or not self.g.nxt_full:
            self.bad(name, "park two groups beat_ready=0",
                     "nxt_full=1 no take",
                     f"taken={len(parked)} nxt_full={self.g.nxt_full}",
                     "u_u.nxt_full")
            phase.drop_objection(self)
            return
        n_before = self.g.n
        taken, _, _ = await self._apply(
            name, "nxt_full blocks take (extra 640 dropped)",
            1, G3[0], beat_ready=0)
        if taken is not None or self.g.n != n_before or not self.g.nxt_full:
            self.bad(name, "take while nxt_full",
                     f"no take, n stays {n_before}",
                     f"taken={_hex512(taken)} n={self.g.n}",
                     "u_u.nxt_full")
            phase.drop_objection(self)
            return
        if not await self._drain(name, "park", parked, n=16):
            phase.drop_objection(self)
            return
        if parked != exp1 + exp2:
            self.bad(name, "drain after nxt_full park (G1 then G2)",
                     "exactly 10×512 G1||G2",
                     f"n={len(parked)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # 4. am_gap: one-cycle n reset. Partial fill is discarded.
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if not await self._feed_groups(name, "am_gap prefill", G1[:2], []):
            phase.drop_objection(self)
            return
        taken, bv, _ = await self._apply(
            name, "am_gap=1 (n←0, no take, in-flight keep)",
            1, G1[2], am_gap=1, beat_ready=1)
        if taken is not None or self.g.n != 0 or self.fail_n:
            if not self.fail_n:
                self.bad(name, "am_gap mid-partial",
                         "n=0 no take",
                         f"taken={_hex512(taken)} n={self.g.n}",
                         "u_u.n")
            phase.drop_objection(self)
            return
        outs_gap = []
        if not await self._feed_groups(name, "post-am_gap G2", G2, outs_gap):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "post-am_gap", outs_gap):
            phase.drop_objection(self)
            return
        if outs_gap != exp2:
            self.bad(name, "am_gap discarded partial G1; new G2 at n=0",
                     f"exactly G2 5×512",
                     f"n={len(outs_gap)}",
                     "u_u.n")
            phase.drop_objection(self)
            return

        # am_gap during emit: keep draining 5×512 (comment :46–47).
        outs_em = []
        if not await self._feed_groups(name, "emit-gap fill G1", G1, outs_em):
            phase.drop_objection(self)
            return
        if not outs_em and ival(d.beat_vld, -1) != 1:
            self.bad(name, "emit-gap have after 4×640",
                     "beat_vld=1",
                     f"beat_vld={ival(d.beat_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        taken, bv, _ = await self._apply(
            name, "am_gap during emit (keep have/acc)",
            0, ZEROS, am_gap=1, beat_ready=1)
        if taken is not None:
            outs_em.append(taken)
        if bv == 0 and len(outs_em) < 5:
            # last-beat drain this cycle is OK; otherwise have must hold
            if self.g.have != 0 and not self.fail_n:
                self.bad(name, "am_gap wiped in-flight emit",
                         "have holds until 5×512 drain",
                         "have=0",
                         "u_u.have")
                phase.drop_objection(self)
                return
        if self.fail_n:
            phase.drop_objection(self)
            return
        if not await self._drain(name, "emit-gap", outs_em):
            phase.drop_objection(self)
            return
        if outs_em != exp1:
            self.bad(name, "am_gap during emit still yields G1 5×512",
                     f"exactly 5×512",
                     f"n={len(outs_em)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Combo hold: same pins, no drift (5 ns, clock free-runs).
        # Re-fill one group and hold the first beat.
        if not await self._feed_groups(name, "hold fill G3", G3, [],
                                       beat_ready=0):
            phase.drop_objection(self)
            return
        held_bv, held_bd = self._sample()
        await Timer(5, "NS")
        later_bv, later_bd = self._sample()
        if later_bv != 1 or later_bv != held_bv or later_bd != held_bd:
            self.bad(name, "hold first beat 5 ns (combo beat_vld / beat_data)",
                     f"beat_vld=1 data stay {_hex512(held_bd)}",
                     f"beat_vld={later_bv} data={_hex512(later_bd)}",
                     HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.beat_vld, -1) != 0:
            self.bad(name, "async rst_n=0 after hold (100ps, no posedge)",
                     "beat_vld=0",
                     f"beat_vld={ival(d.beat_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 5. Stimulus / score: lane_vld=0 does not take even if lanes are data.
        taken, bv, _ = await self._apply(
            name, "lane_vld=0 with G1[0] (no take)",
            0, G1[0], beat_ready=1)
        if taken is not None or bv != 0 or self.g.n != 0:
            self.bad(name, "stall-only data (lane_vld=0)",
                     "beat_vld=0 n=0",
                     f"taken={_hex512(taken)} beat_vld={bv} n={self.g.n}",
                     "u_u.n")
            phase.drop_objection(self)
            return

        # Mid-group stall: two 640s, idle, then the rest.
        if not await self._feed_groups(name, "stall-fill[0:2]", G1[:2], []):
            phase.drop_objection(self)
            return
        for k in range(3):
            taken, bv, _ = await self._apply(
                name, f"lane_vld=0 stall[{k}] mid-group (n stays 2)",
                0, G2[0], beat_ready=1)
            if taken is not None or self.g.n != 2:
                self.bad(name, f"stall[{k}] mid-group",
                         "n stays 2, no beat",
                         f"taken={_hex512(taken)} n={self.g.n}",
                         "u_u.n")
                phase.drop_objection(self)
                return
        outs_st = []
        if not await self._feed_groups(name, "stall-fill[2:4]", G1[2:],
                                       outs_st):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "stall", outs_st):
            phase.drop_objection(self)
            return
        if outs_st != exp1:
            self.bad(name, "resume after mid-group stall (G1)",
                     "exactly G1 5×512",
                     f"n={len(outs_st)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Extra lane_vld=0 after drain must not emit.
        for i in range(3):
            taken, bv, _ = await self._apply(
                name, f"lane_vld=0 after drain[{i}]",
                0, G2[0], beat_ready=1)
            if taken is not None or bv != 0:
                self.bad(name, f"idle after drain[{i}]",
                         "beat_vld=0",
                         f"taken={_hex512(taken)} beat_vld={bv}",
                         "u_u.have")
                phase.drop_objection(self)
                return

        # Second group after drain (phase wrap).
        outs2 = []
        if not await self._feed_groups(name, "second G2", G2, outs2):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "second G2", outs2):
            phase.drop_objection(self)
            return
        if outs2 != exp2:
            self.bad(name, "second group after drain (G2)",
                     "exactly G2 5×512",
                     f"n={len(outs2)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # AM beat between 640s does not count toward n (skip, not am_gap).
        if not await self._feed_groups(name, "am-mid G3[0]", G3[:1], []):
            phase.drop_objection(self)
            return
        taken, _, _ = await self._apply(
            name, "AM lane2 between 640s (skip, n holds)",
            1, G1[0], ams=(0, 0, 1, 0), beat_ready=1)
        if taken is not None or self.g.n != 1:
            self.bad(name, "AM between 640s",
                     "n stays 1",
                     f"taken={_hex512(taken)} n={self.g.n}",
                     "u_u.n")
            phase.drop_objection(self)
            return
        outs_am = []
        if not await self._feed_groups(name, "am-mid G3[1:]", G3[1:], outs_am):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "am-mid", outs_am):
            phase.drop_objection(self)
            return
        if outs_am != pack_4x640_to_5x512(G3):
            self.bad(name, "AM skip mid-group still packs G3",
                     "exactly G3 5×512",
                     f"n={len(outs_am)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_rx_unpack)
