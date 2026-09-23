"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_rx_amctl_lock.

Covers reset/idle (locked=0, no spurious is_amctl/sdf/edf), AMCTL
detect (combo is_amctl on match_w0 / match_w1 / match_pair),
CONFIRM_N=3 lock, UNLOCK_N=3 legacy unlock, TX-layout sticky lock,
all four LID mux arms, lid_bad (U24, no swap), sdf/edf pulses,
async rst_n, and in_vld stall without a confirm/unlock step.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/pcs/vibe_pcs_rx_amctl_lock.sv: async-low rst_n,
combo is_amctl = in_vld && (match_pair || match_w0 || match_w1),
lock when conf >= CONFIRM_N-1, unlock only for via_leg hunt.
Pairs with stage-10 vibe_pcs_tx_amctl and stage-13 deskew. Used by
vibe_pcs_rx u_l0..u_l3. Stock Icarus tc_pcs_rx_amctl remains the
official 4-pair / LID / unlock / lid_bad scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# Table 3-5 eBCH (16, 5) plus default (sel 31). Same as unit_ebch16 / stock.
EBCH16 = (
    0x0000, 0x0A6F, 0x14DD, 0x1EB2, 0x23D6, 0x29B9, 0x370B, 0x3D64,
    0x47AC, 0x4DC3, 0x5371, 0x591E, 0x647A, 0x6E15, 0x70A7, 0x7AC8,
    0x8537, 0x8F58, 0x91EA, 0x9B85, 0xA6E1, 0xAC8E, 0xB23C, 0xB853,
    0xC29B, 0xC8F4, 0xD646, 0xDC29, 0xE14D, 0xEB22, 0xF590, 0xFFFF,
)

CW3, CW8, CW9, CW10 = EBCH16[3], EBCH16[8], EBCH16[9], EBCH16[10]
CW21, CW22, CW28 = EBCH16[21], EBCH16[22], EBCH16[28]

MASK160 = (1 << 160) - 1
END_TX = ((CW22 & 0xFFFF) << 16) | (CW22 & 0xFFFF)
CTRL_TYPE = (
    ((CW8 & 0xFFFF) << 48)
    | ((CW9 & 0xFFFF) << 32)
    | ((CW8 & 0xFFFF) << 16)
    | (CW9 & 0xFFFF)
)
CTRL_DETAIL = (
    ((CW10 & 0xFFFF) << 48)
    | ((CW22 & 0xFFFF) << 32)
    | ((CW10 & 0xFFFF) << 16)
    | (CW22 & 0xFFFF)
)
LID_CW = (CW3, CW8, CW9, CW10)
CONFIRM_TH = 2  # lock when conf >= CONFIRM_N-1; CONFIRM_N=3
UNLOCK_TH = 2   # unlock when unlk >= UNLOCK_N-1; UNLOCK_N=3
HIER = "u_l.locked / u_l.is_amctl"


def _word160(v: int) -> int:
    return int(v) & MASK160


def _bits(word: int, hi: int, lo: int) -> int:
    return (_word160(word) >> lo) & ((1 << (hi - lo + 1)) - 1)


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:040x}"


def dec_lid(sym: int) -> int:
    if sym == CW3:
        return 0
    if sym == CW8:
        return 1
    if sym == CW9:
        return 2
    if sym == CW10:
        return 3
    return 0


def tx_word0(body_cw: int, lid0: int) -> int:
    """TX AMCTL am[319:160]: BODY at [159:144], END at [63:32], LID0 at [15:0]."""
    w = (body_cw & 0xFFFF) << 144
    w |= END_TX << 32
    w |= (CW3 & 0xFFFF) << 16
    w |= lid0 & 0xFFFF
    return w & MASK160


def tx_word1() -> int:
    """TX AMCTL am[159:0]: CTRL_TYPE [127:64] + CTRL_DETAIL x4 SDF [63:0]."""
    return ((CTRL_TYPE << 64) | CTRL_DETAIL) & MASK160


def legacy_w0(body_cw: int) -> int:
    """Stock pair word0: BODY only at [159:144] (no TX END)."""
    return (body_cw & 0xFFFF) << 144


def legacy_w1(endw: int, lidw: int, sdf: bool = False) -> int:
    """Stock pair word1: END at [127:112], LID at [79:64], optional SDF."""
    w = ((endw & 0xFFFF) << 112) | ((lidw & 0xFFFF) << 64)
    if sdf:
        w |= CTRL_DETAIL
    return w & MASK160


def junk(tag: int) -> int:
    """Non-AM 160b that cannot match BODY / END / W1."""
    return _word160((0xA5A5A5A5A5A5A5A5 ^ (tag * 0x1111111111111111)) & MASK160)


class Golden:
    """Cycle-accurate hunt / confirm / unlock vs product always-block."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.locked = 0
        self.lid = 0
        self.lid_bad = 0
        self.sdf = 0
        self.edf = 0
        self.conf = 0
        self.unlk = 0
        self.prev = 0
        self.have = 0
        self.via_leg = 0

    def _match_w0(self, d):
        body = _bits(d, 159, 144)
        return (body == CW21 or body == CW28) and _bits(d, 63, 32) == END_TX

    def _match_w1(self, d):
        return _bits(d, 127, 64) == CTRL_TYPE and _bits(d, 63, 0) == CTRL_DETAIL

    def _match_body(self):
        body = _bits(self.prev, 159, 144)
        return body == CW21 or body == CW28

    def _match_end_tx(self):
        return _bits(self.prev, 63, 32) == END_TX

    def _match_end_leg(self, d):
        return _bits(d, 127, 112) == CW22

    def _match_pair(self, d):
        return bool(
            self.have
            and self._match_body()
            and (self._match_end_tx() or self._match_end_leg(d))
        )

    def is_amctl(self, in_vld, d):
        if not in_vld:
            return 0
        return int(self._match_pair(d) or self._match_w0(d) or self._match_w1(d))

    def step(self, in_vld, d):
        self.sdf = 0
        self.edf = 0
        d = _word160(d)
        if in_vld:
            if self._match_pair(d):
                detail_sdf = _bits(d, 63, 0) == CTRL_DETAIL
                self.sdf = 1 if detail_sdf else 0
                self.edf = 0 if detail_sdf else 1
                lid_sym = (
                    _bits(self.prev, 15, 0)
                    if self._match_end_tx()
                    else _bits(d, 79, 64)
                )
                if lid_sym in LID_CW:
                    self.lid = dec_lid(lid_sym)
                else:
                    self.lid_bad = 1
                if self.conf >= CONFIRM_TH:
                    self.locked = 1
                else:
                    self.conf = (self.conf + 1) & 3
                self.via_leg = int(self._match_end_leg(d) and not self._match_end_tx())
                self.unlk = 0
                self.have = 0
            elif not self.have:
                self.prev = d
                self.have = 1
            else:
                self.prev = d
                self.have = 1
                if self.locked and self.via_leg:
                    if self.unlk >= UNLOCK_TH:
                        self.locked = 0
                        self.conf = 0
                        self.unlk = 0
                        self.via_leg = 0
                    else:
                        self.unlk = (self.unlk + 1) & 3
        return self.locked, self.lid, self.lid_bad, self.sdf, self.edf


class tc_vibe_pcs_rx_amctl_lock(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        sset(self.dut.in_vld, 0)
        sset(self.dut.in_data, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)
        self.g.reset()

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    def _sample_combo(self):
        return ival(self.dut.is_amctl, -1)

    def _sample_reg(self):
        d = self.dut
        return (
            ival(d.locked, -1),
            ival(d.lid, -1),
            ival(d.lid_bad, -1),
            ival(d.sdf, -1),
            ival(d.edf, -1),
        )

    async def _apply(self, in_vld, data):
        """Drive on falling edge; sample combo then registered after posedge.

        Returns (is_amctl, locked, lid, lid_bad, sdf, edf).
        is_amctl is combo on current pins. Others are NBA after this posedge.
        """
        d = self.dut
        word = _word160(data)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.in_data, word)
        await Timer(100, "PS")
        iam = self._sample_combo()
        exp_iam = self.g.is_amctl(1 if in_vld else 0, word)
        self.g.step(1 if in_vld else 0, word)
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        locked, lid, lid_bad, sdf, edf = self._sample_reg()
        await FallingEdge(d.clk)
        return iam, locked, lid, lid_bad, sdf, edf, exp_iam

    def _score(self, name, stim, sample):
        iam, locked, lid, lid_bad, sdf, edf, exp_iam = sample
        if iam != exp_iam:
            self.bad(name, stim,
                     f"is_amctl={exp_iam}",
                     f"is_amctl={iam}",
                     "u_l.is_amctl")
            return False
        exp = (self.g.locked, self.g.lid, self.g.lid_bad, self.g.sdf, self.g.edf)
        got = (locked, lid, lid_bad, sdf, edf)
        if any(x is None for x in got) or got != exp:
            self.bad(name, stim,
                     f"locked={exp[0]} lid={exp[1]} lid_bad={exp[2]} "
                     f"sdf={exp[3]} edf={exp[4]}",
                     f"locked={got[0]} lid={got[1]} lid_bad={got[2]} "
                     f"sdf={got[3]} edf={got[4]}",
                     HIER)
            return False
        return True

    async def _beat(self, name, stim, in_vld, data):
        sample = await self._apply(in_vld, data)
        return self._score(name, stim, sample)

    async def _legacy_pair(self, name, label, body, lidw, endw=CW22, sdf=False):
        if not await self._beat(name, f"{label} w0", 1, legacy_w0(body)):
            return False
        return await self._beat(name, f"{label} w1", 1, legacy_w1(endw, lidw, sdf))

    async def _tx_pair(self, name, label, body, lid0):
        if not await self._beat(name, f"{label} word0", 1, tx_word0(body, lid0)):
            return False
        return await self._beat(name, f"{label} word1", 1, tx_word1())

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_rx_amctl_lock"
        self.g = Golden()

        if dec_lid(CW3) != 0 or dec_lid(CW8) != 1 or dec_lid(CW9) != 2 or dec_lid(CW10) != 3:
            self.bad(name, "golden LID map",
                     "CW3/8/9/10 → 0/1/2/3",
                     f"{dec_lid(CW3)}/{dec_lid(CW8)}/{dec_lid(CW9)}/{dec_lid(CW10)}",
                     "golden")
            phase.drop_objection(self)
            return
        if dec_lid(0xFFFF) != 0:
            self.bad(name, "golden LID else",
                     "unknown → 0",
                     str(dec_lid(0xFFFF)),
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, not locked, no detect / sdf / edf.
        iam = self._sample_combo()
        locked, lid, lid_bad, sdf, edf = self._sample_reg()
        if iam != 0 or locked != 0 or lid != 0 or lid_bad != 0 or sdf != 0 or edf != 0:
            self.bad(name, "reset then release, in_vld=0",
                     "locked=0 lid=0 lid_bad=0 is_amctl=0 sdf=0 edf=0",
                     f"locked={locked} lid={lid} lid_bad={lid_bad} "
                     f"is_amctl={iam} sdf={sdf} edf={edf}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            if not await self._beat(name, f"idle cycle {i} after reset (in_vld=0)",
                                    0, junk(i)):
                phase.drop_objection(self)
                return

        # Detect without lock: two confirm pairs leave locked=0.
        if not await self._legacy_pair(name, "confirm[0] LID0", CW21, CW3):
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "confirm[1] LID0", CW21, CW3):
            phase.drop_objection(self)
            return
        if self.g.locked != 0 or ival(d.locked, -1) != 0:
            self.bad(name, "two confirm pairs (CONFIRM_N=3)",
                     "locked=0",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Async rst_n mid-hunt clears registered lock state without a posedge.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        locked, lid, lid_bad, sdf, edf = self._sample_reg()
        if locked != 0 or lid != 0 or lid_bad != 0 or sdf != 0 or edf != 0:
            self.bad(name, "async rst_n=0 mid-hunt (100ps, no posedge)",
                     "locked=0 lid=0 lid_bad=0 sdf=0 edf=0",
                     f"locked={locked} lid={lid} lid_bad={lid_bad} "
                     f"sdf={sdf} edf={edf}",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.locked, -1) != 0:
            self.bad(name, "after async re-reset release, idle",
                     "locked=0",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # 2. Stock legacy detect / lock / LID walk / unlock (tc_pcs_rx_amctl).
        for n in range(3):
            if not await self._legacy_pair(
                    name, f"stock confirm[{n}] LID0", CW21, CW3):
                phase.drop_objection(self)
                return
        if self.g.locked != 1 or ival(d.locked, -1) != 1 or ival(d.lid, -1) != 0:
            self.bad(name, "3× legacy AMCTL LID0 (CONFIRM_N=3)",
                     "locked=1 lid=0",
                     f"lock={ival(d.locked, -1)} lid={ival(d.lid, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        # Fourth pair matches stock (already locked).
        if not await self._legacy_pair(name, "stock confirm[3] extra LID0", CW21, CW3):
            phase.drop_objection(self)
            return

        if not await self._legacy_pair(name, "LID cw8", CW28, CW8):
            phase.drop_objection(self)
            return
        if ival(d.lid, -1) != 1:
            self.bad(name, "LID cw8", "lid=1", str(ival(d.lid, -1)), "u_l.lid")
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "LID cw9", CW21, CW9):
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "LID cw10", CW21, CW10):
            phase.drop_objection(self)
            return
        if ival(d.lid, -1) != 3:
            self.bad(name, "LID cw10", "lid=3", str(ival(d.lid, -1)), "u_l.lid")
            phase.drop_objection(self)
            return

        # sdf vs edf: legacy pair with CTRL_DETAIL pulses sdf; without pulses edf.
        if not await self._legacy_pair(name, "SDF pair", CW21, CW3, sdf=True):
            phase.drop_objection(self)
            return
        if ival(d.sdf, -1) != 1 or ival(d.edf, -1) != 0:
            self.bad(name, "legacy pair with CTRL_DETAIL",
                     "sdf=1 edf=0",
                     f"sdf={ival(d.sdf, -1)} edf={ival(d.edf, -1)}",
                     "u_l.sdf")
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "EDF pair", CW21, CW3, sdf=False):
            phase.drop_objection(self)
            return
        if ival(d.sdf, -1) != 0 or ival(d.edf, -1) != 1:
            self.bad(name, "legacy pair without CTRL_DETAIL",
                     "sdf=0 edf=1",
                     f"sdf={ival(d.sdf, -1)} edf={ival(d.edf, -1)}",
                     "u_l.edf")
            phase.drop_objection(self)
            return

        # Unlock: UNLOCK_N only for via_leg. Four non-AM pairs (stock).
        for n in range(4):
            if not await self._legacy_pair(name, f"non-AM unlock[{n}]", 0, 0, endw=0):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 0:
            self.bad(name, "4 non-AM pairs while via_leg locked",
                     "unlock",
                     "still locked",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # lid_bad: AMCTL LID not {0,1,2,3} (U24, no swap).
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if not await self._legacy_pair(name, "bad LID 0xFFFF", CW21, 0xFFFF):
            phase.drop_objection(self)
            return
        if ival(d.lid_bad, -1) != 1:
            self.bad(name, "AMCTL LID not {0,1,2,3}",
                     "lid_bad=1 (U24 no swap)",
                     str(ival(d.lid_bad, -1)),
                     "u_l.lid_bad")
            phase.drop_objection(self)
            return
        if ival(d.lid, -1) != 0:
            self.bad(name, "bad LID does not write lid",
                     "lid stays 0",
                     str(ival(d.lid, -1)),
                     "u_l.lid")
            phase.drop_objection(self)
            return

        # Async rst_n after lid_bad clears the sticky without a posedge.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.lid_bad, -1) != 0 or ival(d.locked, -1) != 0:
            self.bad(name, "async rst_n=0 after lid_bad (100ps, no posedge)",
                     "lid_bad=0 locked=0",
                     f"lid_bad={ival(d.lid_bad, -1)} locked={ival(d.locked, -1)}",
                     "u_l.lid_bad")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 3. TX-layout detect / lock (pairs with vibe_pcs_tx_amctl 40-symbol word).
        for n in range(3):
            if not await self._tx_pair(name, f"TX confirm[{n}] lane0", CW21, CW3):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 1 or ival(d.lid, -1) != 0:
            self.bad(name, "3× TX-layout AMCTL LID0",
                     "locked=1 lid=0",
                     f"lock={ival(d.locked, -1)} lid={ival(d.lid, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        if ival(d.sdf, -1) != 1:
            self.bad(name, "TX word1 CTRL_DETAIL after lock pair",
                     "sdf=1",
                     f"sdf={ival(d.sdf, -1)}",
                     "u_l.sdf")
            phase.drop_objection(self)
            return

        # Combo detect: isolated match_w0 / match_w1 raise is_amctl.
        if not await self._beat(name, "TX word0 detect (match_w0)", 1, tx_word0(CW28, CW8)):
            phase.drop_objection(self)
            return
        # After a TX word0 store, any following beat pair-matches (END is in prev).
        # Drive word1 explicitly so match_w1 is also high this beat.
        if not await self._beat(name, "TX word1 detect (match_w1 + pair)", 1, tx_word1()):
            phase.drop_objection(self)
            return
        if ival(d.lid, -1) != 1:
            self.bad(name, "TX-layout LID cw8 after lock",
                     "lid=1",
                     str(ival(d.lid, -1)),
                     "u_l.lid")
            phase.drop_objection(self)
            return

        # TX-layout lock is sticky through data (UNLOCK_N is via_leg only).
        for i in range(8):
            if not await self._beat(
                    name, f"TX-layout data[{i}] (sticky lock, no unlock)",
                    1, junk(0x10 + i)):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 1:
            self.bad(name, "data after TX-layout lock",
                     "locked holds (not via_leg)",
                     "unlocked",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Hold last non-AM data: TX-layout lock / is_amctl stay (clock free-runs).
        held_iam = ival(d.is_amctl, -1)
        held_reg = self._sample_reg()
        await Timer(5, "NS")
        later_iam = self._sample_combo()
        later_reg = self._sample_reg()
        if later_iam != 0 or later_iam != held_iam or later_reg != held_reg:
            self.bad(name, "hold post-lock data 5 ns (combo is_amctl / locked)",
                     f"is_amctl=0 locked=1 stay {held_reg}",
                     f"is_amctl={later_iam} locked={later_reg[0]} {later_reg}",
                     HIER)
            phase.drop_objection(self)
            return

        # Async rst_n after TX lock clears locked without a posedge.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.locked, -1) != 0:
            self.bad(name, "async rst_n=0 after TX lock (100ps, no posedge)",
                     "locked=0",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 4. Stimulus / score: in_vld=0 does not step confirm even if data is AM.
        if not await self._beat(name, "in_vld=0 with TX word0 (no confirm)",
                                0, tx_word0(CW21, CW3)):
            phase.drop_objection(self)
            return
        if not await self._beat(name, "in_vld=0 stall after ignored AM",
                                0, junk(0x20)):
            phase.drop_objection(self)
            return
        if ival(d.locked, -1) != 0:
            self.bad(name, "stall-only AM (in_vld=0)",
                     "locked=0",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Mid-confirm stall: two pairs, idle, then the third locks.
        if not await self._legacy_pair(name, "stall-confirm[0]", CW21, CW3):
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "stall-confirm[1]", CW21, CW3):
            phase.drop_objection(self)
            return
        for k in range(3):
            if not await self._beat(
                    name, f"in_vld=0 stall[{k}] mid-confirm (locked stays 0)",
                    0, junk(0x30 + k)):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 0:
            self.bad(name, "stall mid-confirm",
                     "locked=0 (need 3rd pair)",
                     "locked",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "stall-confirm[2] lock", CW21, CW3):
            phase.drop_objection(self)
            return
        if ival(d.locked, -1) != 1:
            self.bad(name, "resume confirm after stall (3rd pair)",
                     "locked=1",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Extra in_vld=0 after lock must not drop locked.
        for i in range(3):
            if not await self._beat(
                    name, f"in_vld=0 after lock[{i}] (locked holds)",
                    0, junk(0x40 + i)):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 1:
            self.bad(name, "idle after lock",
                     "locked holds",
                     "unlocked",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Hunt slip: BODY then a non-END second word does not confirm.
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if not await self._beat(name, "slip BODY w0", 1, legacy_w0(CW21)):
            phase.drop_objection(self)
            return
        if not await self._beat(name, "slip junk (no END, no confirm)", 1, junk(0x50)):
            phase.drop_objection(self)
            return
        if not await self._beat(name, "slip junk 2", 1, junk(0x51)):
            phase.drop_objection(self)
            return
        if ival(d.locked, -1) != 0:
            self.bad(name, "1-beat slip of a bad pair",
                     "locked=0",
                     "locked",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        # Real pair after slip still hunts from have=1: need BODY then END.
        if not await self._legacy_pair(name, "after-slip confirm[0]", CW21, CW3):
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "after-slip confirm[1]", CW21, CW3):
            phase.drop_objection(self)
            return
        if not await self._legacy_pair(name, "after-slip confirm[2] lock", CW21, CW3):
            phase.drop_objection(self)
            return
        if ival(d.locked, -1) != 1:
            self.bad(name, "lock after slip then 3 pairs",
                     "locked=1",
                     f"locked={ival(d.locked, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        # Second lock after unlock: via_leg miss then re-confirm.
        for n in range(4):
            if not await self._legacy_pair(name, f"re-unlock[{n}]", 0, 0, endw=0):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 0:
            self.bad(name, "unlock before second lock",
                     "locked=0",
                     "still locked",
                     "u_l.locked")
            phase.drop_objection(self)
            return
        for n in range(3):
            if not await self._legacy_pair(
                    name, f"second lock confirm[{n}]", CW28, CW8):
                phase.drop_objection(self)
                return
        if ival(d.locked, -1) != 1 or ival(d.lid, -1) != 1:
            self.bad(name, "second lock LID1 after unlock",
                     "locked=1 lid=1",
                     f"lock={ival(d.locked, -1)} lid={ival(d.lid, -1)}",
                     "u_l.locked")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_rx_amctl_lock)
