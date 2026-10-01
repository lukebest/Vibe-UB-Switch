"""Module-level uvm-python TC for Decision-I leaf vibe_gear_160_128.

Covers reset idle (no spurious out_vld), combo in_ready =
can_load && (rbits != 4) (including hold-empty + out_ready=0
and rbits==4 blocking even when can_load), 4×160 → 5×128
packing vs golden, hold-full / rbits==4 backpressure without
drop/dup, same-cycle take+accept, residue flush when
rbits==4 && can_load, phase wrap, mid-run async rst_n, and
a pin scan. Not a full-chip consecutive-green gate. Not 1/3,
4/3, freeze, or signoff.

Matches product rtl/cdc/vibe_gear_160_128.sv: LSB-first
residue packing and in_ready = can_load && (rbits != 4)
where can_load = !hold_vld || out_ready. Stock Icarus
tc_gear_160_128 remains optional count-only control.
Instantiated by vibe_port u_g0..u_g3. This is not
vibe_gear_128_160 / vibe_afifo / vibe_sync2 /
vibe_rst_sync. ovf_l (F1) is not in this module.
CHILDREN: none (leaf cell; no FSM child).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK128 = (1 << 128) - 1
MASK160 = (1 << 160) - 1
MASK32 = (1 << 32) - 1
MASK64 = (1 << 64) - 1
MASK96 = (1 << 96) - 1

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

HIER = "u_u.hold_vld / u_u.hold / u_u.rbits / u_u.in_ready"
WRAP = "vibe_gear_160_128_cocotb_top"
PINS = (
    "clk", "rst_n", "in_vld", "in_ready", "in_data",
    "out_vld", "out_ready", "out_data",
)
ABSENT = (
    "ovf_l", "almost_full", "wclk", "rclk", "wen", "ren",
    "wfull", "rempty", "wocc", "rst_n_in", "rst_n_out",
    "d", "q", "phase",
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


class Golden:
    """Cycle-accurate residue gearbox vs product NBA.

    take_out (hold_vld && out_ready) clears hold_vld first;
    then rbits==4 && can_load flushes residue into hold
    (last NBA wins); else in_vld && in_ready packs. Combo
    in_ready uses the pre-edge state:
    can_load && (rbits != 4) where
    can_load = !hold_vld || out_ready.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.res = 0
        self.rbits = 0
        self.hold = 0
        self.hold_vld = 0

    def can_load(self, out_ready):
        return (not self.hold_vld) or bool(out_ready)

    def in_ready(self, out_ready):
        return self.can_load(out_ready) and (self.rbits != 4)

    def step(self, in_vld, in_data, out_ready, rst_n=1):
        if not rst_n:
            self.reset()
            return
        in_data = _word160(in_data)
        take_out = bool(self.hold_vld) and bool(out_ready)
        can_load = self.can_load(out_ready)
        ready = self.in_ready(out_ready)
        hold_vld = 0 if take_out else self.hold_vld
        res = self.res
        rbits = self.rbits
        hold = self.hold
        if self.rbits == 4 and can_load:
            hold = self.res
            hold_vld = 1
            res = 0
            rbits = 0
        elif in_vld and ready:
            if self.rbits == 0:
                hold = in_data & MASK128
                res = (in_data >> 128) & MASK32
                hold_vld = 1
                rbits = 1
            elif self.rbits == 1:
                hold = ((in_data & MASK96) << 32) | (self.res & MASK32)
                res = (in_data >> 96) & MASK64
                hold_vld = 1
                rbits = 2
            elif self.rbits == 2:
                hold = ((in_data & MASK64) << 64) | (self.res & MASK64)
                res = (in_data >> 64) & MASK96
                hold_vld = 1
                rbits = 3
            else:
                hold = ((in_data & MASK32) << 96) | (self.res & MASK96)
                res = (in_data >> 32) & MASK128
                hold_vld = 1
                rbits = 4
        self.res = res & MASK128
        self.rbits = rbits
        self.hold = hold & MASK128
        self.hold_vld = hold_vld


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
        self.g.reset()
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

    def _score(self, name, stim, ov, od, ir, out_ready):
        exp_ov = int(self.g.hold_vld)
        exp_ir = 1 if self.g.in_ready(out_ready) else 0
        if ov != exp_ov:
            self.bad(name, stim,
                     f"out_vld={exp_ov}",
                     f"out_vld={ov}" if ov is not None else "out_vld=x",
                     HIER)
            return False
        if self.g.hold_vld and od != self.g.hold:
            self.bad(name, stim,
                     f"out_data={_hex128(self.g.hold)}",
                     f"out_data={_hex128(od)}",
                     HIER)
            return False
        if ir != exp_ir:
            self.bad(name, stim,
                     "in_ready=%d (combo can_load && rbits != 4)" % exp_ir,
                     f"in_ready={ir}",
                     HIER)
            return False
        return True

    async def _advance(self, name, stim, in_vld, in_data, out_ready):
        """On falling edge: drive, take if out_vld&&out_ready, land on next fall.

        Returns (taken_or_None, accepted, post_out_vld, post_out_data, post_in_ready)
        or None if golden score failed.
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
        if not self._score(name, stim + " (pre-edge combo)", ov, od, ir,
                           out_ready):
            return None
        taken = od if (ov == 1 and out_ready == 1) else None
        accepted = bool(in_vld) and bool(ir)
        self.g.step(in_vld, in_data, out_ready)
        await self._to_fall()
        post_ov, post_od, post_ir = self._sample()
        if not self._score(name, stim + " (post NBA)", post_ov, post_od,
                           post_ir, out_ready):
            return None
        return taken, accepted, post_ov, post_od, post_ir

    async def _drain(self, name, tag, outs, n=8):
        for i in range(n):
            step = await self._advance(name, f"{tag} drain[{i}]", 0, 0, 1)
            if step is None:
                return False
            taken, _, ov, _, _ = step
            if taken is not None:
                outs.append(taken)
            if ov == 0:
                break
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_gear_160_128"
        self.g = Golden()

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, in_ready, no spurious out_vld.
        ov, od, ir = self._sample()
        if not self._score(name, "reset then release, in_vld=0 out_ready=1",
                           ov, od, ir, 1):
            phase.drop_objection(self)
            return
        if ov != 0 or ir != 1:
            self.bad(name, "reset then release, in_vld=0 out_ready=1",
                     "out_vld=0 in_ready=1",
                     f"out_vld={ov} in_ready={ir} out_data={_hex128(od)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            step = await self._advance(name, f"idle cycle {i} after reset",
                                       0, 0, 1)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None or accepted or ov != 0 or ir != 1:
                self.bad(name, f"idle cycle {i} after reset",
                         "no out handshake, out_vld=0 in_ready=1",
                         f"taken={_hex128(taken)} accepted={accepted} "
                         f"out_vld={ov} in_ready={ir}",
                         HIER)
                phase.drop_objection(self)
                return

        # Combo in_ready stays 1 when hold is empty / rbits!=4
        # even if out_ready=0.
        sset(d.out_ready, 0)
        sset(d.in_vld, 0)
        await Timer(100, "PS")
        ir0 = ival(d.in_ready, 0)
        if ir0 != 1 or not self.g.in_ready(0):
            self.bad(name, "hold empty, rbits!=4, out_ready=0",
                     "in_ready=1 (combo can_load && rbits != 4)",
                     f"in_ready={ir0}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.out_ready, 1)
        await Timer(100, "PS")

        # 2. Four consecutive 160b beats, out_ready=1 → exactly 5×128b.
        # Same-cycle take+accept after beat[0] (hold full, rbits!=4).
        exp1 = pack_160_to_128(GROUP1)
        outs = []
        for i, beat in enumerate(GROUP1):
            step = await self._advance(
                name, f"stream group1 beat[{i}] out_ready=1", 1, beat, 1)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None:
                outs.append(taken)
            if not accepted:
                self.bad(name, f"stream group1 beat[{i}] out_ready=1",
                         "in_ready=1 (combo can_load && rbits != 4)",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
            # After the 4th accept, residue holds a full 128b (rbits==4).
            if i == 3 and ir != 0:
                self.bad(name, "stream group1 after beat[3], rbits==4",
                         "in_ready=0 (can_load && rbits != 4)",
                         f"in_ready={ir} out_vld={ov} out_data={_hex128(od)}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "group1", outs):
            phase.drop_objection(self)
            return
        if outs != exp1:
            self.bad(name, "4×160b in, out_ready=1",
                     "exactly 5×128b: " + " ".join(_hex128(x) for x in exp1),
                     f"n={len(outs)} " + " ".join(_hex128(x) for x in outs),
                     HIER)
            phase.drop_objection(self)
            return

        # 3. Backpressure: stall when out_ready=0 and hold full; resume.
        exp_bp = pack_160_to_128(GROUP1)
        step = await self._advance(name, "bp rbits0 emit hold",
                                   1, GROUP1[0], 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, od, ir = step
        if taken is not None or not accepted or ov != 1 or od != exp_bp[0]:
            self.bad(name, "bp rbits0 emit hold",
                     f"accept, no take yet, out_vld=1 out_data={_hex128(exp_bp[0])}",
                     f"taken={_hex128(taken)} accepted={accepted} "
                     f"out_vld={ov} out_data={_hex128(od)}",
                     HIER)
            phase.drop_objection(self)
            return
        # Hold is full. out_ready=0 must stall (in_ready=0) and keep the beat.
        for i in range(3):
            step = await self._advance(
                name, f"bp stall[{i}] out_ready=0 hold full",
                1, GROUP1[1], 0)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None or accepted or ov != 1 or od != exp_bp[0] or ir != 0:
                self.bad(name, f"bp stall[{i}] out_ready=0 hold full",
                         f"no take/accept, out_vld=1 out_data={_hex128(exp_bp[0])} in_ready=0",
                         f"taken={_hex128(taken)} accepted={accepted} "
                         f"out_vld={ov} out_data={_hex128(od)} in_ready={ir}",
                         HIER)
                phase.drop_objection(self)
                return
        # Resume: take the held beat (no new input this cycle).
        step = await self._advance(name, "bp resume take hold", 0, 0, 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, _, ir = step
        if taken != exp_bp[0] or accepted:
            self.bad(name, "bp resume take hold",
                     f"take {_hex128(exp_bp[0])}, no new accept",
                     f"taken={_hex128(taken)} accepted={accepted} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        outs_bp = [taken]
        for i, beat in enumerate(GROUP1[1:]):
            step = await self._advance(
                name, f"bp resume beat[{i+1}]", 1, beat, 1)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None:
                outs_bp.append(taken)
            if not accepted:
                self.bad(name, f"bp resume beat[{i+1}]",
                         "in_ready=1 after hold drained",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
            if i == 2 and ir != 0:
                self.bad(name, "bp resume after beat[3], rbits==4",
                         "in_ready=0 (can_load && rbits != 4)",
                         f"in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
        # rbits==4 hold-full stall: can_load is 0, residue not flushed.
        for i in range(3):
            step = await self._advance(
                name, f"bp rbits4 stall[{i}] out_ready=0",
                1, GROUP2[0], 0)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None or accepted or ov != 1 or od != exp_bp[3] or ir != 0:
                self.bad(name, f"bp rbits4 stall[{i}] out_ready=0",
                         f"no take/accept, out_vld=1 out_data={_hex128(exp_bp[3])} in_ready=0",
                         f"taken={_hex128(taken)} accepted={accepted} "
                         f"out_vld={ov} out_data={_hex128(od)} in_ready={ir}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "bp resume", outs_bp):
            phase.drop_objection(self)
            return
        if outs_bp != exp_bp:
            self.bad(name, "bp resume after stall, same 4×160b",
                     "no drop/dup: " + " ".join(_hex128(x) for x in exp_bp),
                     f"n={len(outs_bp)} " + " ".join(_hex128(x) for x in outs_bp),
                     HIER)
            phase.drop_objection(self)
            return

        # 4. Phase wrap: second group of 4 also produces 5 correct outs.
        exp2 = pack_160_to_128(GROUP2)
        outs2 = []
        for i, beat in enumerate(GROUP2):
            step = await self._advance(
                name, f"stream group2 beat[{i}] (phase wrap)", 1, beat, 1)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, _, ir = step
            if taken is not None:
                outs2.append(taken)
            if not accepted:
                self.bad(name, f"stream group2 beat[{i}] (phase wrap)",
                         "in_ready=1",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "group2", outs2):
            phase.drop_objection(self)
            return
        if outs2 != exp2:
            self.bad(name, "second 4×160b group after phase wrap",
                     "exactly 5×128b: " + " ".join(_hex128(x) for x in exp2),
                     f"n={len(outs2)} " + " ".join(_hex128(x) for x in outs2),
                     HIER)
            phase.drop_objection(self)
            return

        # 5. Mid-run async rst_n clears hold_vld / rbits (no dest posedge).
        step = await self._advance(name, "pre-async-rst park beat0",
                                   1, GROUP1[0], 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, _, _ = step
        if ov != 1:
            self.bad(name, "pre-async-rst park beat0",
                     "out_vld=1 before mid-run rst_n",
                     f"out_vld={ov} taken={_hex128(taken)}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        ov, od, ir = self._sample()
        if ov != 0:
            self.bad(name, "mid-run rst_n=0 (100ps, no posedge)",
                     "out_vld=0 (async clear hold_vld)",
                     f"out_vld={ov} out_data={_hex128(od)}",
                     HIER)
            phase.drop_objection(self)
            return
        # Hold through a dest posedge while still asserted.
        await self._to_fall()
        ov, od, ir = self._sample()
        if not self._score(name, "rst_n held 0 through dest posedge",
                           ov, od, ir, 1):
            phase.drop_objection(self)
            return
        if ov != 0:
            self.bad(name, "rst_n held 0 through dest posedge",
                     "out_vld stays 0",
                     f"out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 1)
        await self._idle()
        await self.cycles(2)
        await FallingEdge(d.clk)
        ov, od, ir = self._sample()
        if not self._score(name, "after async re-release", ov, od, ir, 1):
            phase.drop_objection(self)
            return
        if ov != 0 or ir != 1:
            self.bad(name, "after async re-release",
                     "out_vld=0 in_ready=1 (rbits/hold cleared)",
                     f"out_vld={ov} in_ready={ir}",
                     HIER)
            phase.drop_objection(self)
            return

        # 6. Leaf pins match product SV (no ovf_l / dual-clock / phase).
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_gear_160_128 product port",
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


uvm_component_utils(tc_vibe_gear_160_128)
