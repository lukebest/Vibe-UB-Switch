"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_pack.

Covers reset/idle (lane_vld=0, beat_ready, no spurious emit), 5×512 →
exactly 4×640 pack (G2 / inverse of vibe_pcs_rx_unpack), lane_ready and
afifo_afull backpressure without drop/dup, beat_vld stall without a
take, AMCTL insert on the 512 / 640-symbol timer (am_word + per-lane
40B halves), AM wait until a finishing 4×640 emits, and a second group
after drain. Not a full-chip consecutive-green gate. Not 1/3, 4/3,
freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_tx_pack.sv: async-low rst_n, combo
beat_ready = !afifo_afull && lane_ready && (am_phase==0) && !pack_vld,
lane_vld = (am_phase!=0) || pack_vld, am_word = (am_phase!=0),
pack[512*acc_n +: 512], emit pack[640*emit_idx] as {lane3..lane0},
insert_am = sym_cnt >= (sdf_period ? 640 : 512). Instantiates
vibe_pcs_tx_amctl ×4. Used by vibe_pcs_tx u_pack. Stock Icarus
tc_pcs_tx_pack remains the official lane_vld scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
MASK320 = (1 << 320) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
MASK2560 = (1 << 2560) - 1
HIER = "u_u.pack_vld / u_u.am_phase"

# Table 3-5 eBCH (16, 5) plus default (sel 31). Same as unit_pcs_tx_amctl.
EBCH16 = (
    0x0000, 0x0A6F, 0x14DD, 0x1EB2, 0x23D6, 0x29B9, 0x370B, 0x3D64,
    0x47AC, 0x4DC3, 0x5371, 0x591E, 0x647A, 0x6E15, 0x70A7, 0x7AC8,
    0x8537, 0x8F58, 0x91EA, 0x9B85, 0xA6E1, 0xAC8E, 0xB23C, 0xB853,
    0xC29B, 0xC8F4, 0xD646, 0xDC29, 0xE14D, 0xEB22, 0xF590, 0xFFFF,
)
CW3, CW8, CW9, CW10 = EBCH16[3], EBCH16[8], EBCH16[9], EBCH16[10]
CW21, CW22, CW28 = EBCH16[21], EBCH16[22], EBCH16[28]

PERIOD_OTH = 512
PERIOD_SDF = 640
SYM_PER_BEAT = 16


def _word160(v: int) -> int:
    return int(v) & MASK160


def _word512(v: int) -> int:
    return int(v) & MASK512


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:040x}"


def _hex512(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0128x}"


def _pack_words(*words) -> int:
    v = 0
    for w in words:
        v = (v << 16) | (w & 0xFFFF)
    return v & MASK320


def _lid_pair(lane_id: int):
    lid0 = {0: CW3, 1: CW8, 2: CW9}.get(lane_id & 3, CW10)
    return CW3, lid0


def golden_amctl(lane_id: int) -> int:
    """Product concat: BODY 12 / END 4 / LID 8 / CTRL_TYPE 8 / CTRL_DETAIL 8."""
    lid1, lid0 = _lid_pair(lane_id)
    return _pack_words(
        CW21, CW28, CW21, CW28, CW21, CW28,
        CW22, CW22,
        lid1, lid0, lid1, lid0,
        CW8, CW9, CW8, CW9,
        CW10, CW22, CW10, CW22,
    )


def am_halves(lane_id: int):
    """am_phase 1 = AMCTL[319:160], am_phase 2 = AMCTL[159:0]."""
    w = golden_amctl(lane_id)
    return (w >> 160) & MASK160, w & MASK160


def din_of(lanes) -> int:
    """Product din = {lane3, lane2, lane1, lane0}."""
    l0, l1, l2, l3 = (_word160(x) for x in lanes)
    return ((l3 << 480) | (l2 << 320) | (l1 << 160) | l0) & MASK640


def lanes_of(word640: int):
    w = int(word640) & MASK640
    return (
        w & MASK160,
        (w >> 160) & MASK160,
        (w >> 320) & MASK160,
        (w >> 480) & MASK160,
    )


def pack_5x512_to_4x640(beats):
    """Golden 5×512 → 4×640 LSB-first (pack[512*i +: 512] = beat[i]).

    stream = beat0 || beat1 || beat2 || beat3 || beat4 (beat0 in the LSBs).
    word[i] = stream[640*i +: 640] as (lane0, lane1, lane2, lane3).
    Inverse of RX unpack 4×640 → 5×512.
    """
    if len(beats) != 5:
        raise ValueError("pack_5x512_to_4x640 expects 5 beats")
    stream = 0
    for i, beat in enumerate(beats):
        stream |= (_word512(beat) << (i * 512))
    return [lanes_of(stream >> (i * 640)) for i in range(4)]


def pack_4x640_to_5x512(lane_groups):
    """RX unpack golden (same as unit_pcs_rx_unpack) for inverse check."""
    if len(lane_groups) != 4:
        raise ValueError("pack_4x640_to_5x512 expects 4 lane groups")
    stream = 0
    for i, lanes in enumerate(lane_groups):
        stream |= din_of(lanes) << (i * 640)
    return [((stream >> (i * 512)) & MASK512) for i in range(5)]


def beat_pat(tag: int) -> int:
    """128 hex digits = 512b. Tag/index in every byte so a slice swap fails."""
    parts = [f"{(tag & 0xFF):02X}{(i & 0xFF):02X}" for i in range(32)]
    return int("".join(parts), 16) & MASK512


# Stock Icarus uses {i[7:0], 504'd0}. Wide groups are distinctive.
STOCK = [((i & 0xFF) << 504) for i in range(5)]
G1 = [beat_pat(0xA0 + k) for k in range(5)]
G2 = [beat_pat(0xB0 + k) for k in range(5)]
G3 = [beat_pat(0xC0 + k) for k in range(5)]


class Golden:
    """Cycle-accurate pack / AM / emit vs product always-block (AM, take, emit)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.sym_cnt = 0
        self.am_phase = 0
        self.acc_n = 0
        self.pack = 0
        self.pack_vld = 0
        self.emit_idx = 0

    def combo(self, sdf_period, afifo_afull, lane_ready):
        beat_ready = (not afifo_afull) and bool(lane_ready) and (
            self.am_phase == 0) and (not self.pack_vld)
        lane_vld = (self.am_phase != 0) or bool(self.pack_vld)
        am_word = self.am_phase != 0
        period = PERIOD_SDF if sdf_period else PERIOD_OTH
        insert_am = self.sym_cnt >= period
        return int(beat_ready), int(lane_vld), int(am_word), int(insert_am)

    def lanes(self):
        if self.am_phase == 1:
            return tuple(am_halves(i)[0] for i in range(4))
        if self.am_phase == 2:
            return tuple(am_halves(i)[1] for i in range(4))
        base = 640 * self.emit_idx
        return lanes_of(self.pack >> base)

    def step(self, sdf_period, afifo_afull, beat_data, beat_vld, lane_ready):
        beat_ready, _, _, insert_am = self.combo(
            sdf_period, afifo_afull, lane_ready)
        completing = bool(beat_vld) and beat_ready and (self.acc_n == 4)

        am_phase = self.am_phase
        pack_vld = self.pack_vld
        emit_idx = self.emit_idx
        acc_n = self.acc_n
        pack = self.pack

        if insert_am and am_phase == 0 and not pack_vld and not completing:
            self.am_phase = 1
        elif am_phase == 1 and lane_ready and not afifo_afull:
            self.am_phase = 2
        elif am_phase == 2 and lane_ready and not afifo_afull:
            self.am_phase = 0
            self.sym_cnt = 0

        if beat_vld and beat_ready:
            shift = 512 * acc_n
            mask = MASK512 << shift
            pack = (pack & ~mask) | ((_word512(beat_data) << shift))
            self.pack = pack & MASK2560
            if acc_n == 4:
                self.acc_n = 0
                self.pack_vld = 1
                self.emit_idx = 0
            else:
                self.acc_n = (acc_n + 1) & 7
            if not insert_am:
                self.sym_cnt = (self.sym_cnt + SYM_PER_BEAT) & 0x3FF

        if pack_vld and lane_ready and am_phase == 0 and not afifo_afull:
            if emit_idx == 3:
                self.pack_vld = 0
                self.emit_idx = 0
            else:
                self.emit_idx = (emit_idx + 1) & 3


class tc_vibe_pcs_tx_pack(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.sdf_period, 0)
        sset(d.afifo_afull, 0)
        sset(d.beat_vld, 0)
        sset(d.beat_data, 0)
        sset(d.lane_ready, 1)

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
        return (
            ival(d.beat_ready, -1),
            ival(d.lane_vld, -1),
            ival(d.am_word, -1),
            (
                ival(d.lane0, -1),
                ival(d.lane1, -1),
                ival(d.lane2, -1),
                ival(d.lane3, -1),
            ),
        )

    def _score_now(self, name, stim, sdf, afull, lready, br, lv, aw, lanes):
        exp_br, exp_lv, exp_aw, _ = self.g.combo(sdf, afull, lready)
        exp_lanes = self.g.lanes()
        if br != exp_br:
            self.bad(name, stim,
                     f"beat_ready={exp_br}",
                     f"beat_ready={br}",
                     "u_u.beat_ready")
            return False
        if lv != exp_lv:
            self.bad(name, stim,
                     f"lane_vld={exp_lv}",
                     f"lane_vld={lv}",
                     "u_u.lane_vld")
            return False
        if aw != exp_aw:
            self.bad(name, stim,
                     f"am_word={exp_aw}",
                     f"am_word={aw}",
                     "u_u.am_word")
            return False
        if lv == 1:
            if lanes is None or any(x is None for x in lanes):
                self.bad(name, stim + " (lanes unresolved)",
                         "lane0..3 resolved",
                         "x",
                         "u_u.lane0")
                return False
            if tuple(_word160(x) for x in lanes) != exp_lanes:
                self.bad(name, stim + " (5×512→4×640 / AM mux)",
                         " ".join(_hex160(x) for x in exp_lanes),
                         " ".join(_hex160(x) for x in lanes),
                         "u_u.pack / u_am*.amctl_40B")
                return False
        return True

    async def _apply(self, name, stim, beat_vld, beat_data,
                     sdf=0, afull=0, lane_ready=1):
        """Drive on falling edge; score combo then NBA after the posedge.

        Returns (taken_or_None, emit_kind_or_None, lanes_or_None).
        emit_kind is 'data' or 'am' when lane_vld && lane_ready && !afull.
        """
        d = self.dut
        sset(d.sdf_period, 1 if sdf else 0)
        sset(d.afifo_afull, 1 if afull else 0)
        sset(d.lane_ready, 1 if lane_ready else 0)
        sset(d.beat_vld, 1 if beat_vld else 0)
        sset(d.beat_data, _word512(beat_data))
        await Timer(100, "PS")
        br, lv, aw, lanes = self._sample()
        if not self._score_now(name, stim + " (pre-posedge)",
                               sdf, afull, lane_ready, br, lv, aw, lanes):
            return None, None, lanes
        taken = _word512(beat_data) if (beat_vld and br == 1) else None
        emit = None
        if lv == 1 and lane_ready and not afull:
            emit = "am" if aw == 1 else "data"
        self.g.step(sdf, afull, beat_data, 1 if beat_vld else 0,
                    1 if lane_ready else 0)
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        br2, lv2, aw2, lanes2 = self._sample()
        if not self._score_now(name, stim + " (post-NBA)",
                               sdf, afull, lane_ready, br2, lv2, aw2, lanes2):
            return None, None, lanes
        await FallingEdge(d.clk)
        return taken, emit, lanes

    async def _accept_beats(self, name, label, beats, sdf=0):
        """Take each beat (wait for beat_ready). Does not drain a following emit."""
        for i, beat in enumerate(beats):
            taken = None
            for spin in range(16):
                offer = ival(self.dut.beat_ready, 0) == 1
                taken, kind, _ = await self._apply(
                    name, f"{label} accept[{i}] spin[{spin}]",
                    1 if offer else 0, beat if offer else 0, sdf=sdf)
                if taken is not None:
                    break
                if kind is None and self.fail_n:
                    return False
            if taken is None:
                self.bad(name, f"{label} accept[{i}]",
                         "beat accepted",
                         "beat_ready stayed 0",
                         "u_u.beat_ready")
                return False
        return True

    async def _feed_beats(self, name, label, beats, outs, ams=None,
                          sdf=0, afull=0, lane_ready=1):
        qi = 0
        for spin in range(128):
            if qi >= len(beats):
                # Held emit (lane_ready=0 / afull): stop; drain collects later.
                if (not lane_ready or afull
                        or ival(self.dut.lane_vld, 0) == 0):
                    break
            offer = qi < len(beats)
            taken, kind, lanes = await self._apply(
                name,
                f"{label} spin[{spin}] q={qi}/{len(beats)}",
                1 if offer else 0,
                beats[qi] if offer else 0,
                sdf=sdf, afull=afull, lane_ready=lane_ready)
            if taken is None and offer and kind is None and self.fail_n:
                return False
            if taken is not None:
                qi += 1
            if kind == "data" and lanes is not None:
                outs.append(tuple(_word160(x) for x in lanes))
            elif kind == "am" and ams is not None and lanes is not None:
                ams.append(tuple(_word160(x) for x in lanes))
        if qi != len(beats):
            self.bad(name, f"{label} feed",
                     f"accepted {len(beats)} beats",
                     f"accepted {qi}",
                     "u_u.acc_n")
            return False
        return True

    async def _drain(self, name, label, outs, ams=None, n=16, sdf=0):
        for i in range(n):
            _, kind, lanes = await self._apply(
                name, f"{label} drain[{i}]", 0, 0, sdf=sdf)
            if kind is None and self.fail_n:
                return False
            if kind == "data" and lanes is not None:
                outs.append(tuple(_word160(x) for x in lanes))
            elif kind == "am" and ams is not None and lanes is not None:
                ams.append(tuple(_word160(x) for x in lanes))
            if (ival(self.dut.lane_vld, 0) == 0
                    and ival(self.dut.beat_ready, 0) == 1
                    and self.g.am_phase == 0 and not self.g.pack_vld):
                break
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_pack"
        self.g = Golden()

        exp1 = pack_5x512_to_4x640(G1)
        exp2 = pack_5x512_to_4x640(G2)
        exp3 = pack_5x512_to_4x640(G3)
        exp_stock = pack_5x512_to_4x640(STOCK)
        if pack_4x640_to_5x512(exp1) != G1:
            self.bad(name, "golden inverse of RX unpack (G1)",
                     "round-trip 5×512",
                     "mismatch",
                     "golden")
            phase.drop_objection(self)
            return
        if pack_4x640_to_5x512(exp_stock) != STOCK:
            self.bad(name, "golden inverse of RX unpack (stock)",
                     "round-trip 5×512",
                     "mismatch",
                     "golden")
            phase.drop_objection(self)
            return
        if exp1 == exp2 or len(set(G1)) != 5:
            self.bad(name, "golden G1 vs G2 uniqueness",
                     "distinct groups / 5 distinct beats",
                     "collision",
                     "golden")
            phase.drop_objection(self)
            return
        if din_of(exp1[0]) & MASK512 != G1[0]:
            self.bad(name, "golden first 640 LSBs are beat0",
                     _hex512(G1[0]),
                     _hex512(din_of(exp1[0]) & MASK512),
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, beat_ready, no spurious lane_vld / am_word.
        br, lv, aw, lanes = self._sample()
        if br != 1 or lv != 0 or aw != 0:
            self.bad(name, "reset then release, beat_vld=0 lane_ready=1",
                     "beat_ready=1 lane_vld=0 am_word=0",
                     f"beat_ready={br} lane_vld={lv} am_word={aw}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, kind, _ = await self._apply(
                name, f"idle cycle {i} after reset (beat_vld=0)",
                0, G1[0])
            if taken is not None or kind is not None or ival(d.lane_vld, -1) != 0:
                self.bad(name, f"idle cycle {i} after reset",
                         "no emit, lane_vld=0",
                         f"taken={taken is not None} kind={kind} "
                         f"lane_vld={ival(d.lane_vld, -1)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Combo afifo_afull / lane_ready drop beat_ready immediately.
        sset(d.afifo_afull, 1)
        await Timer(100, "PS")
        if ival(d.beat_ready, -1) != 0:
            self.bad(name, "afifo_afull=1 combo (idle)",
                     "beat_ready=0",
                     f"beat_ready={ival(d.beat_ready, -1)}",
                     "u_u.beat_ready")
            phase.drop_objection(self)
            return
        sset(d.afifo_afull, 0)
        sset(d.lane_ready, 0)
        await Timer(100, "PS")
        if ival(d.beat_ready, -1) != 0:
            self.bad(name, "lane_ready=0 combo (idle)",
                     "beat_ready=0",
                     f"beat_ready={ival(d.beat_ready, -1)}",
                     "u_u.beat_ready")
            phase.drop_objection(self)
            return
        sset(d.lane_ready, 1)
        await Timer(100, "PS")

        # 2. Stock-like 5×512 → exactly 4×640 (Icarus {i[7:0], 504'd0}).
        outs = []
        if not await self._feed_beats(name, "stock", STOCK, outs):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "stock", outs):
            phase.drop_objection(self)
            return
        if outs != exp_stock:
            self.bad(name, "one 5×512 group, lane_ready=1 (stock i<<504)",
                     f"exactly 4×640 n=4 first0={_hex160(exp_stock[0][0])}",
                     f"n={len(outs)} first0="
                     f"{_hex160(outs[0][0]) if outs else 'x'}",
                     "u_u.lane0")
            phase.drop_objection(self)
            return

        # Wide distinctive beats (not just the stock nibble pair).
        outs1 = []
        if not await self._feed_beats(name, "wide G1", G1, outs1):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "wide G1", outs1):
            phase.drop_objection(self)
            return
        if outs1 != exp1:
            self.bad(name, "one 5×512 group, lane_ready=1 (wide G1)",
                     f"exactly 4×640 n=4 first0={_hex160(exp1[0][0])}",
                     f"n={len(outs1)} first0="
                     f"{_hex160(outs1[0][0]) if outs1 else 'x'}",
                     "u_u.lane0")
            phase.drop_objection(self)
            return

        # Async rst_n mid-fill clears acc_n / pack_vld without a posedge.
        if not await self._feed_beats(name, "pre-async beats", G2[:2], []):
            phase.drop_objection(self)
            return
        if self.g.acc_n != 2:
            self.bad(name, "pre-async fill",
                     "acc_n=2",
                     f"acc_n={self.g.acc_n}",
                     "u_u.acc_n")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.lane_vld, -1) != 0 or ival(d.am_word, -1) != 0:
            self.bad(name, "async rst_n=0 mid-fill (100ps, no posedge)",
                     "lane_vld=0 am_word=0",
                     f"lane_vld={ival(d.lane_vld, -1)} "
                     f"am_word={ival(d.am_word, -1)}",
                     "u_u.pack_vld")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.lane_vld, -1) != 0 or ival(d.beat_ready, -1) != 1:
            self.bad(name, "after async re-reset release, idle",
                     "lane_vld=0 beat_ready=1",
                     f"lane_vld={ival(d.lane_vld, -1)} "
                     f"beat_ready={ival(d.beat_ready, -1)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 3. Backpressure: take 5 beats (lane_ready must stay 1 — it is in
        # beat_ready), then hold the first 640; no drop/dup.
        if not await self._accept_beats(name, "bp fill G1", G1):
            phase.drop_objection(self)
            return
        outs_bp = []
        # After 5 takes, pack_vld=1: lane_vld=1, beat_ready=0. Hold emit.
        if ival(d.lane_vld, -1) != 1 or ival(d.beat_ready, -1) != 0:
            self.bad(name, "bp after 5×512 (pack_vld, held)",
                     "lane_vld=1 beat_ready=0",
                     f"lane_vld={ival(d.lane_vld, -1)} "
                     f"beat_ready={ival(d.beat_ready, -1)}",
                     "u_u.pack_vld")
            phase.drop_objection(self)
            return
        held = tuple(ival(getattr(d, f"lane{i}"), -1) for i in range(4))
        for i in range(3):
            taken, kind, lanes = await self._apply(
                name, f"bp hold[{i}] lane_ready=0",
                0, 0, lane_ready=0)
            now = tuple(ival(getattr(d, f"lane{j}"), -1) for j in range(4))
            if taken is not None or kind is not None or now != held:
                self.bad(name, f"bp hold[{i}]",
                         f"no take/emit, lanes stay {_hex160(held[0])}",
                         f"taken={taken is not None} kind={kind} "
                         f"lane0={_hex160(now[0])}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "bp", outs_bp):
            phase.drop_objection(self)
            return
        if outs_bp != exp1:
            self.bad(name, "bp drain after hold (no drop/dup)",
                     f"exactly 4×640 first0={_hex160(exp1[0][0])}",
                     f"n={len(outs_bp)} first0="
                     f"{_hex160(outs_bp[0][0]) if outs_bp else 'x'}",
                     "u_u.lane0")
            phase.drop_objection(self)
            return

        # afifo_afull during emit: same hold, then drain G2.
        if not await self._accept_beats(name, "afull fill G2", G2):
            phase.drop_objection(self)
            return
        outs_af = []
        if ival(d.lane_vld, -1) != 1:
            self.bad(name, "afull have after 5×512",
                     "lane_vld=1",
                     f"lane_vld={ival(d.lane_vld, -1)}",
                     "u_u.pack_vld")
            phase.drop_objection(self)
            return
        held = tuple(ival(getattr(d, f"lane{i}"), -1) for i in range(4))
        for i in range(2):
            taken, kind, _ = await self._apply(
                name, f"afifo_afull hold[{i}]",
                0, 0, afull=1, lane_ready=1)
            now = tuple(ival(getattr(d, f"lane{j}"), -1) for j in range(4))
            if taken is not None or kind is not None or now != held:
                self.bad(name, f"afifo_afull hold[{i}]",
                         "no emit, lanes stay",
                         f"taken={taken is not None} kind={kind}",
                         "u_u.afifo_afull")
                phase.drop_objection(self)
                return
        if not await self._drain(name, "afull", outs_af):
            phase.drop_objection(self)
            return
        if outs_af != exp2:
            self.bad(name, "afull drain after hold (G2, no drop/dup)",
                     "exactly G2 4×640",
                     f"n={len(outs_af)}",
                     "u_u.lane0")
            phase.drop_objection(self)
            return

        # 4. beat_vld=0 stall mid-group (acc_n holds).
        if not await self._feed_beats(name, "stall-fill[0:2]", G3[:2], []):
            phase.drop_objection(self)
            return
        for k in range(3):
            taken, kind, _ = await self._apply(
                name, f"beat_vld=0 stall[{k}] mid-group (acc_n stays 2)",
                0, G1[0])
            if taken is not None or kind is not None or self.g.acc_n != 2:
                self.bad(name, f"stall[{k}] mid-group",
                         "acc_n stays 2, no emit",
                         f"taken={taken is not None} acc_n={self.g.acc_n}",
                         "u_u.acc_n")
                phase.drop_objection(self)
                return
        outs_st = []
        if not await self._feed_beats(name, "stall-fill[2:5]", G3[2:], outs_st):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "stall", outs_st):
            phase.drop_objection(self)
            return
        if outs_st != exp3:
            self.bad(name, "resume after mid-group stall (G3)",
                     "exactly G3 4×640",
                     f"n={len(outs_st)}",
                     "u_u.pack")
            phase.drop_objection(self)
            return

        # Extra beat_vld=0 after drain must not emit.
        for i in range(3):
            taken, kind, _ = await self._apply(
                name, f"beat_vld=0 after drain[{i}]",
                0, G2[0])
            if taken is not None or kind is not None or ival(d.lane_vld, -1) != 0:
                self.bad(name, f"idle after drain[{i}]",
                         "lane_vld=0",
                         f"taken={taken is not None} kind={kind} "
                         f"lane_vld={ival(d.lane_vld, -1)}",
                         "u_u.pack_vld")
                phase.drop_objection(self)
                return

        # Second group after drain (phase wrap).
        outs2 = []
        if not await self._feed_beats(name, "second G2", G2, outs2):
            phase.drop_objection(self)
            return
        if not await self._drain(name, "second G2", outs2):
            phase.drop_objection(self)
            return
        if outs2 != exp2:
            self.bad(name, "second group after drain (G2)",
                     "exactly G2 4×640",
                     f"n={len(outs2)}",
                     "u_u.pack")
            phase.drop_objection(self)
            return

        # Combo hold: same pins, no drift (5 ns, clock free-runs).
        if not await self._accept_beats(name, "hold fill G1", G1):
            phase.drop_objection(self)
            return
        sset(d.lane_ready, 0)
        await Timer(100, "PS")
        held_lv = ival(d.lane_vld, -1)
        held_br = ival(d.beat_ready, -1)
        held_l0 = ival(d.lane0, -1)
        await Timer(5, "NS")
        if (ival(d.lane_vld, -1) != 1 or ival(d.lane_vld, -1) != held_lv
                or ival(d.beat_ready, -1) != held_br
                or ival(d.lane0, -1) != held_l0):
            self.bad(name, "hold first 640 5 ns (combo lane_vld / lanes)",
                     f"lane_vld=1 lane0 stay {_hex160(held_l0)}",
                     f"lane_vld={ival(d.lane_vld, -1)} "
                     f"lane0={_hex160(ival(d.lane0, -1))}",
                     HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.lane_vld, -1) != 0:
            self.bad(name, "async rst_n=0 after hold (100ps, no posedge)",
                     "lane_vld=0",
                     f"lane_vld={ival(d.lane_vld, -1)}",
                     "u_u.pack_vld")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 5. AMCTL insert: 32 accepted beats → sym_cnt=512 (!sdf). Idle, then
        # two AM words (high then low) with per-lane Table 3-5 40B halves.
        n_am = PERIOD_OTH // SYM_PER_BEAT
        stream = []
        for g in range((n_am + 4) // 5):
            stream.extend(beat_pat(0x10 + ((g * 5 + k) & 0xF)) for k in range(5))
        stream = stream[:n_am]
        outs_am = []
        ams = []
        if not await self._feed_beats(name, "pre-AM 32 beats", stream, outs_am,
                                      ams=ams):
            phase.drop_objection(self)
            return
        if ams:
            self.bad(name, "AM should not fire before 32 accepted beats",
                     "no am_word handshake yet",
                     f"am cycles={len(ams)}",
                     "u_u.sym_cnt")
            phase.drop_objection(self)
            return
        if self.g.sym_cnt != PERIOD_OTH:
            self.bad(name, "sym_cnt after 32 beats (!sdf)",
                     f"sym_cnt={PERIOD_OTH}",
                     f"sym_cnt={self.g.sym_cnt}",
                     "u_u.sym_cnt")
            phase.drop_objection(self)
            return
        # Idle: insert_am && !pack_vld && !completing → am_phase 1 then 2.
        if not await self._drain(name, "AM insert !sdf", outs_am, ams=ams, n=8):
            phase.drop_objection(self)
            return
        exp_am = [
            tuple(am_halves(i)[0] for i in range(4)),
            tuple(am_halves(i)[1] for i in range(4)),
        ]
        if ams != exp_am:
            self.bad(name, "AMCTL 2×160b/lane after 32 beats (!sdf)",
                     f"high then low n=2 lane0={_hex160(exp_am[0][0])}",
                     f"n={len(ams)} lane0="
                     f"{_hex160(ams[0][0]) if ams else 'x'}",
                     "u_u.u_am0.amctl_40B")
            phase.drop_objection(self)
            return
        if self.g.sym_cnt != 0 or self.g.am_phase != 0:
            self.bad(name, "after AM pair, resume data",
                     "am_phase=0 sym_cnt=0",
                     f"am_phase={self.g.am_phase} sym_cnt={self.g.sym_cnt}",
                     "u_u.am_phase")
            phase.drop_objection(self)
            return

        # afifo_afull stalls AM phase advance. Re-arm with 32 more beats.
        # Idle once to enter phase 1 (no pre-edge handshake), then hold.
        stream2 = [beat_pat(0x20 + (k & 0xF)) for k in range(n_am)]
        outs_am2 = []
        ams2 = []
        if not await self._feed_beats(name, "pre-AM stall 32", stream2, outs_am2,
                                      ams=ams2):
            phase.drop_objection(self)
            return
        taken, kind, _ = await self._apply(
            name, "AM start cycle (NBA 0→1, no handshake yet)", 0, 0)
        if kind is not None or ival(d.am_word, -1) != 1:
            self.bad(name, "AM start after 32 (phase 1 live)",
                     "no handshake yet, am_word=1",
                     f"kind={kind} am_word={ival(d.am_word, -1)}",
                     "u_u.am_phase")
            phase.drop_objection(self)
            return
        held_aw = ival(d.am_word, -1)
        held = tuple(ival(getattr(d, f"lane{i}"), -1) for i in range(4))
        exp_hi = tuple(am_halves(i)[0] for i in range(4))
        if tuple(_word160(x) for x in held) != exp_hi:
            self.bad(name, "AM phase-1 lanes while held",
                     f"high halves lane0={_hex160(exp_hi[0])}",
                     f"lane0={_hex160(held[0])}",
                     "u_u.u_am0.amctl_40B")
            phase.drop_objection(self)
            return
        for i in range(2):
            taken, kind, _ = await self._apply(
                name, f"AM afull hold[{i}]", 0, 0, afull=1)
            now = tuple(ival(getattr(d, f"lane{j}"), -1) for j in range(4))
            if (kind is not None or ival(d.am_word, -1) != held_aw
                    or now != held):
                self.bad(name, f"AM afull hold[{i}]",
                         "am_word holds, no phase advance",
                         f"kind={kind} am_word={ival(d.am_word, -1)}",
                         "u_u.am_phase")
                phase.drop_objection(self)
                return
        if not await self._drain(name, "AM afull resume", outs_am2, ams=ams2,
                                 n=6):
            phase.drop_objection(self)
            return
        if ams2 != exp_am:
            self.bad(name, "AM pair after afull stall",
                     "high then low",
                     f"n={len(ams2)}",
                     "u_u.am_phase")
            phase.drop_objection(self)
            return

        # SDF period=1: 40 beats complete exactly 8 groups. Last completing
        # sets pack_vld; AM waits until the 4×640 emits, then two AM words.
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        n_sdf = PERIOD_SDF // SYM_PER_BEAT
        sdf_stream = []
        for g in range(n_sdf // 5):
            sdf_stream.extend(beat_pat(0x30 + ((g * 5 + k) & 0xF))
                              for k in range(5))
        outs_sdf = []
        ams_sdf = []
        if not await self._feed_beats(name, "SDF 40 beats", sdf_stream, outs_sdf,
                                      ams=ams_sdf, sdf=1):
            phase.drop_objection(self)
            return
        # Completing the 8th group parks pack_vld; AM must not have started.
        if ams_sdf:
            self.bad(name, "SDF AM waits for finishing 4×640 (completing)",
                     "no AM during the 40th-beat completing / emit",
                     f"am cycles={len(ams_sdf)}",
                     "u_u.am_phase")
            phase.drop_objection(self)
            return
        if not await self._drain(name, "SDF emit-then-AM", outs_sdf,
                                 ams=ams_sdf, n=12, sdf=1):
            phase.drop_objection(self)
            return
        exp_sdf = []
        for g in range(n_sdf // 5):
            exp_sdf.extend(pack_5x512_to_4x640(
                [beat_pat(0x30 + ((g * 5 + k) & 0xF)) for k in range(5)]))
        if outs_sdf != exp_sdf:
            self.bad(name, "SDF 8×(5×512→4×640) before AM",
                     f"exactly {len(exp_sdf)}×640",
                     f"n={len(outs_sdf)}",
                     "u_u.pack")
            phase.drop_objection(self)
            return
        if ams_sdf != exp_am:
            self.bad(name, "SDF AM after last 4×640 emit (period 640)",
                     "high then low",
                     f"n={len(ams_sdf)}",
                     "u_u.am_phase")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_pack)
