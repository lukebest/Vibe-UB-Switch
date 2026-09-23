"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_amctl.

Covers reset/idle ack=0, 40-symbol AMCTL insert/align vs Table 3-5
(BODY / END / LID / CTRL_TYPE / CTRL_DETAIL), all four lane_id LID
mux arms, ack=req&&link_up, and combo hold (clk / rst_n / sdf_period
unused in the assemble body). Not a full-chip consecutive-green gate.
Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_tx_amctl.sv and stock tc_pcs_amctl
nonzero / lane walk / ack semantics, plus golden eBCH-16 scoring.
Used by vibe_pcs_tx_pack u_am0..u_am3. Combo: ack = req && link_up;
amctl_40B is {3{CW21,CW28}}, {CW22,CW22}, {lid1,lid0,lid1,lid0},
{CW8,CW9,CW8,CW9}, {CW10,CW22,CW10,CW22}. lid1 is always CW3.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, Timer
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

MASK320 = (1 << 320) - 1
HIER = "u_a.amctl_40B / u_a.cw21"


def _hex320(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:080x}"


def _hex16(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:04X}"


def _pack_words(*words) -> int:
    v = 0
    for w in words:
        v = (v << 16) | (w & 0xFFFF)
    return v & MASK320


def _lid_pair(lane_id: int):
    """lid1 is always CW3; lid0 is CW3/8/9/10 for lane 0/1/2/else."""
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


def _slice(word, hi, lo) -> int:
    return (word >> lo) & ((1 << (hi - lo + 1)) - 1)


def _fields(word):
    """MSB-first: BODY[319:224] END[223:192] LID[191:128] TYPE[127:64] DET[63:0]."""
    w = word & MASK320
    return {
        "body": _slice(w, 319, 224),
        "end": _slice(w, 223, 192),
        "lid": _slice(w, 191, 128),
        "ctrl_type": _slice(w, 127, 64),
        "ctrl_detail": _slice(w, 63, 0),
    }


class tc_vibe_pcs_tx_amctl(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.link_up, 0)
        sset(d.sdf_period, 0)
        sset(d.lane_id, 0)
        sset(d.req, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _apply(self, lane_id, req, link_up, sdf_period=1):
        """Drive combo pins and settle (#1 like stock tc_pcs_amctl)."""
        d = self.dut
        sset(d.lane_id, lane_id & 3)
        sset(d.req, 1 if req else 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.sdf_period, 1 if sdf_period else 0)
        await Timer(1, "NS")
        return ival(d.ack, -1), ival(d.amctl_40B, -1)

    def _score_word(self, name, stim, lane_id, ack, word, exp_ack):
        exp = golden_amctl(lane_id)
        if ack != exp_ack:
            self.bad(name, stim, f"ack={exp_ack}", f"ack={ack}", "u_a.ack")
            return False
        if word is None or word != exp:
            self.bad(name, stim,
                     f"amctl_40B={_hex320(exp)}",
                     f"amctl_40B={_hex320(word)}",
                     HIER)
            return False
        got_f = _fields(word)
        exp_f = _fields(exp)
        for key in ("body", "end", "lid", "ctrl_type", "ctrl_detail"):
            if got_f[key] != exp_f[key]:
                self.bad(name, f"{stim} field {key}",
                         f"{key}={_hex320(exp_f[key])}",
                         f"{key}={_hex320(got_f[key])}",
                         HIER)
                return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_amctl"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: req=0 → ack=0. Combo AMCTL is already lane-0 golden
        # (rst_n / clk unused in the assemble body; do not expect a 0 word).
        ack, word = await self._apply(0, 0, 1, sdf_period=1)
        if not self._score_word(
                name, "reset then release, req=0 link_up=1 lane0",
                0, ack, word, 0):
            phase.drop_objection(self)
            return
        for i in range(4):
            ack, word = await self._apply(0, 0, 1, sdf_period=1)
            if not self._score_word(
                    name, f"idle cycle {i} after reset (req=0 lane0)",
                    0, ack, word, 0):
                phase.drop_objection(self)
                return

        # Async rst_n does not clear combo AMCTL / ack (unused pin).
        await self._idle()
        sset(d.lane_id, 0)
        sset(d.link_up, 1)
        sset(d.req, 1)
        sset(d.sdf_period, 1)
        await Timer(1, "NS")
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        ack = ival(d.ack, -1)
        word = ival(d.amctl_40B, -1)
        if not self._score_word(
                name, "async rst_n=0 mid-cycle (100ps, combo hold)",
                0, ack, word, 1):
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        ack, word = await self._apply(0, 1, 1, sdf_period=1)
        if not self._score_word(
                name, "after async re-reset release, req=1 lane0",
                0, ack, word, 1):
            phase.drop_objection(self)
            return

        # 2. Insert / align: every lane_id vs golden 40-symbol eBCH-16 word.
        seen = []
        for lid in range(4):
            ack, word = await self._apply(lid, 1, 1, sdf_period=1)
            if not self._score_word(
                    name, f"link_up sdf_period lane_id={lid} req=1",
                    lid, ack, word, 1):
                phase.drop_objection(self)
                return
            seen.append(word)
            lid1, lid0 = _lid_pair(lid)
            exp_lid = _pack_words(lid1, lid0, lid1, lid0)
            got_lid = _fields(word)["lid"]
            if got_lid != exp_lid:
                self.bad(name, f"LID field lane_id={lid}",
                         f"{{CW3,{_hex16(lid0)},CW3,{_hex16(lid0)}}}=0x{exp_lid:016x}",
                         f"0x{got_lid:016x}",
                         "u_a.lid0")
                phase.drop_objection(self)
                return

        if len(set(seen)) != 4:
            self.bad(name, "lane_id 0..3 AMCTL uniqueness",
                     "4 distinct 40-symbol words (LID mux)",
                     f"{len(set(seen))} distinct",
                     "u_a.lid0")
            phase.drop_objection(self)
            return

        # Lanes share BODY / END / CTRL_*; only LID changes.
        f0 = _fields(seen[0])
        for lid in range(1, 4):
            fl = _fields(seen[lid])
            for key in ("body", "end", "ctrl_type", "ctrl_detail"):
                if fl[key] != f0[key]:
                    self.bad(name, f"lane_id={lid} {key} vs lane0",
                             "same as lane0 (LID-only mux)",
                             f"{key} differs",
                             HIER)
                    phase.drop_objection(self)
                    return
            if fl["lid"] == f0["lid"]:
                self.bad(name, f"lane_id={lid} LID vs lane0",
                         "distinct LID field",
                         "same LID",
                         "u_a.lid0")
                phase.drop_objection(self)
                return

        # Named BODY / END / CTRL constants (independent of lane).
        exp_body = _pack_words(CW21, CW28, CW21, CW28, CW21, CW28)
        exp_end = _pack_words(CW22, CW22)
        exp_type = _pack_words(CW8, CW9, CW8, CW9)
        exp_det = _pack_words(CW10, CW22, CW10, CW22)
        if f0["body"] != exp_body or f0["end"] != exp_end:
            self.bad(name, "BODY/END align (lane0)",
                     f"BODY={{3{{CW21,CW28}}}} END={{CW22,CW22}}",
                     f"body={_hex320(f0['body'])} end={_hex320(f0['end'])}",
                     HIER)
            phase.drop_objection(self)
            return
        if f0["ctrl_type"] != exp_type or f0["ctrl_detail"] != exp_det:
            self.bad(name, "CTRL_TYPE/CTRL_DETAIL align (lane0)",
                     "TYPE={CW8,CW9,CW8,CW9} DET={CW10,CW22,CW10,CW22}",
                     f"type={_hex320(f0['ctrl_type'])} "
                     f"det={_hex320(f0['ctrl_detail'])}",
                     HIER)
            phase.drop_objection(self)
            return

        # 3. ack = req && link_up (stock: req=1 link_up=0 → ack=0).
        for req in (0, 1):
            for link_up in (0, 1):
                ack, word = await self._apply(3, req, link_up, sdf_period=1)
                exp_ack = 1 if (req and link_up) else 0
                if not self._score_word(
                        name, f"req={req} link_up={link_up} lane_id=3",
                        3, ack, word, exp_ack):
                    phase.drop_objection(self)
                    return

        # sdf_period is unused in the combo body (pack owns 640/512 timing).
        ack0, word0 = await self._apply(1, 1, 1, sdf_period=0)
        ack1, word1 = await self._apply(1, 1, 1, sdf_period=1)
        if ack0 != 1 or ack1 != 1 or word0 != word1 or word0 != golden_amctl(1):
            self.bad(name, "sdf_period 0 then 1, same lane1 req/link_up",
                     f"ack=1 amctl stays {_hex320(golden_amctl(1))}",
                     f"ack={ack0}/{ack1} amctl={_hex320(word0)}/{_hex320(word1)}",
                     HIER)
            phase.drop_objection(self)
            return

        # Combo hold: same pins, no drift (5 ns, no new drive).
        held_ack, held = await self._apply(2, 1, 1, sdf_period=1)
        if not self._score_word(
                name, "lane_id=2 before hold",
                2, held_ack, held, 1):
            phase.drop_objection(self)
            return
        await Timer(5, "NS")
        later_ack = ival(d.ack, -1)
        later = ival(d.amctl_40B, -1)
        if later != held or later_ack != held_ack or later != golden_amctl(2):
            self.bad(name, "hold lane_id=2 req=1 link_up=1 for 5 ns",
                     f"ack=1 amctl stays {_hex320(golden_amctl(2))}",
                     f"ack={later_ack} amctl={_hex320(later)}",
                     HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_amctl)
