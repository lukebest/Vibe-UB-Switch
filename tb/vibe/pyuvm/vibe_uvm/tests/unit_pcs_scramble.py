"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_scramble.

Covers reset/idle clean, known LID seed vs golden xmask, AMCTL/EEIB
pass-through (LFSR does not advance), and XOR round-trip.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_scramble.sv and stock tc_pcs_scramble
en=0 pass-through / en=1 nonzero-mask semantics. Same poly + seed as
PMA PRBS23: step {s[21:0], s[22]^s[17]}, seed {19'd1, lane_id, 2'b01}.
TX-side only in this leaf (one XOR cell; RX descramble is the same
module with the same seed).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
MASK23 = (1 << 23) - 1
RESET_SEED = 0x1  # {21'd0, 2'b01}

# Short distinctive 160b vector (stock 0x55 plus nonzero LTB-like beats).
VECTOR = (
    0x0,
    0x55,
    int("A5" * 20, 16),
    int("0123456789ABCDEF0123456789ABCDEF01234567", 16),
)
AMCTL0 = 0x55
AMCTL1 = 0xAA
LTB0 = 0x0
LTB1 = int("C3" * 20, 16)
LID_A = 2
LID_B = 1


def seed_from_lid(lid: int) -> int:
    """Product seed: {19'd1, lane_id[1:0], 2'b01}."""
    return (1 << 4) | ((lid & 3) << 2) | 1


def lfsr_step(s: int) -> int:
    """One LFSR step: {s[21:0], s[22] ^ s[17]}."""
    fb = ((s >> 22) ^ (s >> 17)) & 1
    return ((s << 1) | fb) & MASK23


def xmask160(s):
    """160b window: bit i is LFSR[0] after i steps. Returns (mask, advanced)."""
    t = s & MASK23
    mask = 0
    for i in range(160):
        mask |= (t & 1) << i
        t = lfsr_step(t)
    return mask, t


def scramble_words(seed: int, words):
    """Golden en=1 stream from a starting LFSR seed."""
    state = seed & MASK23
    outs = []
    for w in words:
        mask, state = xmask160(state)
        outs.append((w & MASK160) ^ mask)
    return outs


def _word160(v: int) -> int:
    return v & MASK160


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:040x}"


class tc_vibe_pcs_scramble(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.lane_id, 0)
        sset(d.seed_load, 0)
        sset(d.en, 0)
        sset(d.in_vld, 0)
        sset(d.in_data, 0)

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
        return ival(d.out_vld, -1), ival(d.out_data, -1)

    async def _beat(self, in_vld, in_data, en, seed_load=0, lane_id=None):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        if lane_id is not None:
            sset(d.lane_id, lane_id)
        sset(d.seed_load, 1 if seed_load else 0)
        sset(d.en, 1 if en else 0)
        sset(d.in_data, _word160(in_data))
        sset(d.in_vld, 1 if in_vld else 0)
        await self._to_fall()
        return self._sample()

    async def _load_seed(self, lid):
        """seed_load with in_vld=0 so NBA last-wins does not eat the seed."""
        ov, od = await self._beat(0, 0, 0, seed_load=1, lane_id=lid)
        sset(self.dut.seed_load, 0)
        return ov, od

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_scramble"
        hier = "u_scr.out_data"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle clean, no spurious out_vld, out_data held 0.
        ov, od = self._sample()
        if ov != 0 or od != 0:
            self.bad(name, "reset then release, in_vld=0",
                     "out_vld=0 out_data=0",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     "u_scr.out_vld")
            phase.drop_objection(self)
            return
        for i in range(4):
            ov, od = await self._beat(0, 0x55, 0)
            if ov != 0 or od != 0:
                self.bad(name, f"idle cycle {i} after reset (in_vld=0 in=0x55)",
                         "out_vld=0 out_data=0 (held)",
                         f"out_vld={ov} out_data={_hex160(od)}",
                         hier)
                phase.drop_objection(self)
                return

        # Reset seed is {21'd0, 2'b01}; first en=1 beat must use that mask.
        rst_mask, _ = xmask160(RESET_SEED)
        ov, od = await self._beat(1, 0, 1)
        if ov != 1 or od != rst_mask:
            self.bad(name, "en=1 in=0 after reset (no seed_load)",
                     f"out_vld=1 out_data={_hex160(rst_mask)} (reset seed)",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        # Async rst_n mid-cycle clears registered outs. Drop in_vld/en first
        # so release does not immediately consume more beats.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        ov, od = self._sample()
        if ov != 0 or od != 0:
            self.bad(name, "async rst_n=0 mid-cycle (100ps, no posedge)",
                     "out_vld=0 out_data=0",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     "u_scr.out_vld")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        ov, od = self._sample()
        if ov != 0 or od != 0:
            self.bad(name, "after async re-reset release, idle",
                     "out_vld=0 out_data=0",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     "u_scr.out_vld")
            phase.drop_objection(self)
            return

        # 2. Known LID seed → deterministic scrambled vs unscrambled golden.
        await self._load_seed(LID_A)
        seed_a = seed_from_lid(LID_A)
        exp_scr = scramble_words(seed_a, VECTOR)
        got_scr = []
        for i, word in enumerate(VECTOR):
            ov, od = await self._beat(1, word, 1, lane_id=LID_A)
            got_scr.append(od)
            if ov != 1 or od != exp_scr[i]:
                self.bad(name,
                         f"en=1 lid={LID_A} vec[{i}] in={_hex160(word)} after seed",
                         f"out_vld=1 out_data={_hex160(exp_scr[i])}",
                         f"out_vld={ov} out_data={_hex160(od)}",
                         hier)
                phase.drop_objection(self)
                return
        if got_scr[0] == 0:
            self.bad(name, f"en=1 in=0 after seed lid={LID_A}",
                     "scrambled nonzero mask",
                     "0", hier)
            phase.drop_objection(self)
            return

        # Same vector, en=0: unscrambled pass-through (golden = input).
        await self._load_seed(LID_A)
        for i, word in enumerate(VECTOR):
            ov, od = await self._beat(1, word, 0, lane_id=LID_A)
            if ov != 1 or od != _word160(word):
                self.bad(name,
                         f"en=0 lid={LID_A} vec[{i}] in={_hex160(word)} after seed",
                         f"pass-through out_vld=1 out_data={_hex160(word)}",
                         f"out_vld={ov} out_data={_hex160(od)}",
                         hier)
                phase.drop_objection(self)
                return

        # Distinct LIDs produce distinct seeds / masks (in=0).
        await self._load_seed(LID_B)
        mask_b, _ = xmask160(seed_from_lid(LID_B))
        ov, od = await self._beat(1, 0, 1, lane_id=LID_B)
        if ov != 1 or od != mask_b or od == exp_scr[0]:
            self.bad(name, f"en=1 in=0 after seed lid={LID_B} vs lid={LID_A}",
                     f"out={_hex160(mask_b)} != lid={LID_A} {_hex160(exp_scr[0])}",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        # 3. AMCTL/EEIB exempt: en=0 pass-through and LFSR does not advance.
        await self._load_seed(LID_A)
        mask0, state1 = xmask160(seed_a)
        mask1, _ = xmask160(state1)

        ov, od = await self._beat(1, AMCTL0, 0, lane_id=LID_A)
        if ov != 1 or od != AMCTL0:
            self.bad(name, f"en=0 AMCTL in={_hex160(AMCTL0)} after seed",
                     f"pass-through {_hex160(AMCTL0)} (AMCTL/EEIB)",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        # Idle with en=1 but in_vld=0 also must not step the LFSR.
        ov, od = await self._beat(0, 0xF00, 1, lane_id=LID_A)
        if ov != 0:
            self.bad(name, "in_vld=0 en=1 between AMCTL and LTB",
                     "out_vld=0 (no beat)",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     "u_scr.out_vld")
            phase.drop_objection(self)
            return

        ov, od = await self._beat(1, LTB0, 1, lane_id=LID_A)
        if ov != 1 or od != mask0:
            self.bad(name, "en=1 LTB in=0 after AMCTL + idle (LFSR frozen)",
                     f"first-seed mask {_hex160(mask0)}",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        ov, od = await self._beat(1, AMCTL1, 0, lane_id=LID_A)
        if ov != 1 or od != AMCTL1:
            self.bad(name, f"en=0 AMCTL in={_hex160(AMCTL1)} after one LTB",
                     f"pass-through {_hex160(AMCTL1)}",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        ov, od = await self._beat(1, LTB1, 1, lane_id=LID_A)
        exp_ltb1 = _word160(LTB1) ^ mask1
        if ov != 1 or od != exp_ltb1:
            self.bad(name, "en=1 second LTB after AMCTL (one advance only)",
                     f"out={_hex160(exp_ltb1)}",
                     f"out_vld={ov} out_data={_hex160(od)}",
                     hier)
            phase.drop_objection(self)
            return

        # 4. Round-trip: same cell + same seed is its own inverse (TX XOR).
        await self._load_seed(LID_A)
        scrambled = []
        for word in VECTOR:
            ov, od = await self._beat(1, word, 1, lane_id=LID_A)
            if ov != 1:
                self.bad(name, "round-trip scramble beat",
                         "out_vld=1", f"out_vld={ov}", "u_scr.out_vld")
                phase.drop_objection(self)
                return
            scrambled.append(od)
        await self._load_seed(LID_A)
        recovered = []
        for word in scrambled:
            ov, od = await self._beat(1, word, 1, lane_id=LID_A)
            if ov != 1:
                self.bad(name, "round-trip descramble beat",
                         "out_vld=1", f"out_vld={ov}", "u_scr.out_vld")
                phase.drop_objection(self)
                return
            recovered.append(od)
        exp_vec = [_word160(w) for w in VECTOR]
        if recovered != exp_vec:
            self.bad(name, "scramble then descramble same seed/lid",
                     " ".join(_hex160(x) for x in exp_vec),
                     " ".join(_hex160(x) for x in recovered),
                     hier)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_scramble)
