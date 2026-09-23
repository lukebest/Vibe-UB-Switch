"""Module-level uvm-python TC for Decision-I leaf vibe_gear_160_128.

Covers reset idle (no spurious out_vld), 4×160 → 5×128 packing integrity,
hold-full / rbits==4 backpressure without drop/dup, and phase wrap on a
second group. Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze,
or signoff.

Matches product rtl/cdc/vibe_gear_160_128.sv and stock tc_gear_160_128
count semantics, plus residue packing and
in_ready = can_load && (rbits != 4).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK128 = (1 << 128) - 1
MASK160 = (1 << 160) - 1

# Distinct 160b beats so residue slices cannot collide by accident.
GROUP1 = (
    0xA1A1A1A1_11111111_22222222_33333333_44444440,
    0xB2B2B2B2_55555555_66666666_77777777_88888881,
    0xC3C3C3C3_99999999_AAAAAAAA_BBBBBBBB_CCCCCCC2,
    0xD4D4D4D4_DDDDDDDD_EEEEEEEE_FFFFFFFF_00000013,
)
GROUP2 = (
    0x10101010_01010101_02020202_03030303_04040415,
    0x20202020_05050505_06060606_07070707_08080826,
    0x30303030_09090909_0A0A0A0A_0B0B0B0B_0C0C0C37,
    0x40404040_0D0D0D0D_0E0E0E0E_0F0F0F0F_10101048,
)


def _word160(v: int) -> int:
    return v & MASK160


def pack_160_to_128(beats):
    """Golden 4×160 → 5×128 LSB-first residue packing (AS-0.1 §5 T7).

    stream = beat0 || beat1 || … || beat3 (beat0 in the LSBs).
    out[i] = stream[128*i +: 128]. Matches rtl case(rbits):
      out0 = b0[127:0]
      out1 = {b1[95:0],  b0[159:128]}
      out2 = {b2[63:0],  b1[159:96]}
      out3 = {b3[31:0],  b2[159:64]}
      out4 = b3[159:32]
    """
    if len(beats) != 4:
        raise ValueError("pack_160_to_128 expects 4 beats")
    stream = 0
    for i, b in enumerate(beats):
        stream |= _word160(b) << (i * 160)
    return [(stream >> (i * 128)) & MASK128 for i in range(5)]


def _hex128(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:032x}"


class tc_vibe_gear_160_128(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.in_vld, 0)
        sset(d.in_data, 0)
        sset(d.out_ready, 1)

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
            ival(d.out_vld, -1),
            ival(d.out_data, -1),
            ival(d.in_ready, -1),
        )

    async def _advance(self, in_vld, in_data, out_ready):
        """On falling edge: drive, take if out_vld&&out_ready, land on next fall.

        Returns (taken_or_None, accepted, post_out_vld, post_out_data, post_in_ready).
        """
        d = self.dut
        sset(d.out_ready, out_ready)
        sset(d.in_data, _word160(in_data))
        sset(d.in_vld, 1 if in_vld else 0)
        # Combo in_ready = can_load && (rbits != 4) needs a delta after sset.
        await Timer(100, "PS")
        ir = ival(d.in_ready, 0)
        ov = ival(d.out_vld, 0)
        od = ival(d.out_data, 0)
        taken = od if (ov == 1 and out_ready == 1) else None
        accepted = bool(in_vld) and bool(ir)
        await self._to_fall()
        post_ov, post_od, post_ir = self._sample()
        return taken, accepted, post_ov, post_od, post_ir

    async def _drain(self, outs, n=8):
        for _ in range(n):
            taken, _, ov, _, _ = await self._advance(0, 0, 1)
            if taken is not None:
                outs.append(taken)
            if ov == 0:
                break

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_gear_160_128"
        hier = "u_gear.hold_vld"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, in_ready, no spurious out_vld.
        ov, od, ir = self._sample()
        if ov != 0 or ir != 1:
            self.bad(name, "reset then release, in_vld=0 out_ready=1",
                     "out_vld=0 in_ready=1",
                     f"out_vld={ov} in_ready={ir} out_data={_hex128(od)}",
                     hier)
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, accepted, ov, od, ir = await self._advance(0, 0, 1)
            if taken is not None or accepted or ov != 0 or ir != 1:
                self.bad(name, f"idle cycle {i} after reset",
                         "no out handshake, out_vld=0 in_ready=1",
                         f"taken={_hex128(taken)} accepted={accepted} "
                         f"out_vld={ov} in_ready={ir}",
                         hier)
                phase.drop_objection(self)
                return

        # 2. Four consecutive 160b beats, out_ready=1 → exactly 5×128b.
        exp1 = pack_160_to_128(GROUP1)
        outs = []
        for i, beat in enumerate(GROUP1):
            taken, accepted, ov, od, ir = await self._advance(1, beat, 1)
            if taken is not None:
                outs.append(taken)
            if not accepted:
                self.bad(name, f"stream group1 beat[{i}] out_ready=1",
                         "in_ready=1 (combo can_load && rbits != 4)",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         "u_gear.in_ready")
                phase.drop_objection(self)
                return
            # After the 4th accept, residue holds a full 128b (rbits==4).
            if i == 3 and ir != 0:
                self.bad(name, "stream group1 after beat[3], rbits==4",
                         "in_ready=0 (can_load && rbits != 4)",
                         f"in_ready={ir} out_vld={ov} out_data={_hex128(od)}",
                         "u_gear.in_ready")
                phase.drop_objection(self)
                return
        await self._drain(outs)
        if outs != exp1:
            self.bad(name, "4×160b in, out_ready=1",
                     "exactly 5×128b: " + " ".join(_hex128(x) for x in exp1),
                     f"n={len(outs)} " + " ".join(_hex128(x) for x in outs),
                     "u_gear.hold")
            phase.drop_objection(self)
            return

        # 3. Backpressure: stall when out_ready=0 and hold full; resume.
        exp_bp = pack_160_to_128(GROUP1)
        taken, accepted, ov, od, ir = await self._advance(1, GROUP1[0], 1)
        if taken is not None or not accepted or ov != 1 or od != exp_bp[0]:
            self.bad(name, "bp rbits0 emit hold",
                     f"accept, no take yet, out_vld=1 out_data={_hex128(exp_bp[0])}",
                     f"taken={_hex128(taken)} accepted={accepted} "
                     f"out_vld={ov} out_data={_hex128(od)}",
                     "u_gear.hold")
            phase.drop_objection(self)
            return
        # Hold is full. out_ready=0 must stall (in_ready=0) and keep the beat.
        for i in range(3):
            taken, accepted, ov, od, ir = await self._advance(1, GROUP1[1], 0)
            if taken is not None or accepted or ov != 1 or od != exp_bp[0] or ir != 0:
                self.bad(name, f"bp stall[{i}] out_ready=0 hold full",
                         f"no take/accept, out_vld=1 out_data={_hex128(exp_bp[0])} in_ready=0",
                         f"taken={_hex128(taken)} accepted={accepted} "
                         f"out_vld={ov} out_data={_hex128(od)} in_ready={ir}",
                         "u_gear.in_ready")
                phase.drop_objection(self)
                return
        # Resume: take the held beat (no new input this cycle).
        taken, accepted, ov, _, ir = await self._advance(0, 0, 1)
        if taken != exp_bp[0] or accepted:
            self.bad(name, "bp resume take hold",
                     f"take {_hex128(exp_bp[0])}, no new accept",
                     f"taken={_hex128(taken)} accepted={accepted} out_vld={ov}",
                     "u_gear.hold")
            phase.drop_objection(self)
            return
        outs_bp = [taken]
        for i, beat in enumerate(GROUP1[1:]):
            taken, accepted, ov, od, ir = await self._advance(1, beat, 1)
            if taken is not None:
                outs_bp.append(taken)
            if not accepted:
                self.bad(name, f"bp resume beat[{i+1}]",
                         "in_ready=1 after hold drained",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         "u_gear.in_ready")
                phase.drop_objection(self)
                return
        await self._drain(outs_bp)
        if outs_bp != exp_bp:
            self.bad(name, "bp resume after stall, same 4×160b",
                     "no drop/dup: " + " ".join(_hex128(x) for x in exp_bp),
                     f"n={len(outs_bp)} " + " ".join(_hex128(x) for x in outs_bp),
                     "u_gear.hold")
            phase.drop_objection(self)
            return

        # 4. Phase wrap: second group of 4 also produces 5 correct outs.
        exp2 = pack_160_to_128(GROUP2)
        outs2 = []
        for i, beat in enumerate(GROUP2):
            taken, accepted, ov, _, ir = await self._advance(1, beat, 1)
            if taken is not None:
                outs2.append(taken)
            if not accepted:
                self.bad(name, f"stream group2 beat[{i}] (phase wrap)",
                         "in_ready=1",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         "u_gear.rbits")
                phase.drop_objection(self)
                return
        await self._drain(outs2)
        if outs2 != exp2:
            self.bad(name, "second 4×160b group after phase wrap",
                     "exactly 5×128b: " + " ".join(_hex128(x) for x in exp2),
                     f"n={len(outs2)} " + " ".join(_hex128(x) for x in outs2),
                     "u_gear.rbits")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_gear_160_128)
