"""Module-level uvm-python TC for Decision-I leaf vibe_gear_128_160.

Covers reset idle (no spurious out_vld), combo in_ready =
!hold_vld || out_ready (including hold-empty + out_ready=0),
5×128 → 4×160 packing vs golden, hold-full backpressure
without drop/dup, same-cycle take+accept, phase wrap, mid-run
async rst_n, and a pin scan. Not a full-chip consecutive-
green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/cdc/vibe_gear_128_160.sv: LSB-first
residue packing and in_ready = !hold_vld || out_ready.
Stock Icarus tc_gear_128_160 remains optional count-only
control. Instantiated by vibe_port u_rg0..u_rg3. This is
not vibe_gear_160_128 / vibe_afifo / vibe_sync2 /
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

# Distinct 128b beats so residue slices cannot collide by accident.
GROUP1 = (
    0xA1A10000_11111111_22222222_33333330,
    0xB2B20000_44444444_55555555_66666661,
    0xC3C30000_77777777_88888888_99999992,
    0xD4D40000_AAAAAA00_BBBBBB00_CCCCCC03,
    0xE5E50000_DDDDDD00_EEEEEE00_FFFFFF04,
)
GROUP2 = (
    0x10100000_01010101_02020202_03030315,
    0x20200000_04040404_05050505_06060626,
    0x30300000_07070707_08080808_09090937,
    0x40400000_0A0A0A0A_0B0B0B0B_0C0C0C48,
    0x50500000_0D0D0D0D_0E0E0E0E_0F0F0F59,
)

HIER = "u_u.hold_vld / u_u.hold / u_u.phase / u_u.in_ready"
WRAP = "vibe_gear_128_160_cocotb_top"
PINS = (
    "clk", "rst_n", "in_vld", "in_ready", "in_data",
    "out_vld", "out_ready", "out_data",
)
ABSENT = (
    "ovf_l", "almost_full", "wclk", "rclk", "wen", "ren",
    "wfull", "rempty", "wocc", "rst_n_in", "rst_n_out",
    "d", "q", "rbits",
)


def _word128(v: int) -> int:
    return v & MASK128


def pack_128_to_160(beats):
    """Golden 5×128 → 4×160 LSB-first residue packing (AS-0.1 §6/§7).

    stream = beat0 || beat1 || … || beat4 (beat0 in the LSBs).
    out[i] = stream[160*i +: 160]. Matches rtl case(phase):
      out0 = {b1[31:0],  b0}
      out1 = {b2[63:0],  b1[127:32]}
      out2 = {b3[95:0],  b2[127:64]}
      out3 = {b4,        b3[127:96]}
    """
    if len(beats) != 5:
        raise ValueError("pack_128_to_160 expects 5 beats")
    stream = 0
    for i, b in enumerate(beats):
        stream |= _word128(b) << (i * 128)
    return [(stream >> (i * 160)) & MASK160 for i in range(4)]


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:040x}"


class Golden:
    """Cycle-accurate residue gearbox vs product NBA.

    hold_vld && out_ready clears hold_vld first; then
    in_vld && in_ready may set hold_vld again in the same
    always block (last NBA wins). Combo in_ready uses the
    pre-edge hold_vld: !hold_vld || out_ready.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.res_a = 0
        self.res_b = 0
        self.phase = 0
        self.hold = 0
        self.hold_vld = 0

    def in_ready(self, out_ready):
        return (not self.hold_vld) or bool(out_ready)

    def step(self, in_vld, in_data, out_ready, rst_n=1):
        if not rst_n:
            self.reset()
            return
        in_data = _word128(in_data)
        ready = self.in_ready(out_ready)
        hold_vld = 0 if (self.hold_vld and out_ready) else self.hold_vld
        res_a = self.res_a
        res_b = self.res_b
        phase = self.phase
        hold = self.hold
        if in_vld and ready:
            if self.phase == 0:
                res_a = in_data
                phase = 1
            elif self.phase == 1:
                hold = ((in_data & MASK32) << 128) | (self.res_a & MASK128)
                res_b = (in_data >> 32) & MASK96
                hold_vld = 1
                phase = 2
            elif self.phase == 2:
                hold = ((in_data & MASK64) << 96) | (self.res_b & MASK96)
                res_a = (in_data >> 64) & MASK64
                hold_vld = 1
                phase = 3
            elif self.phase == 3:
                hold = ((in_data & MASK96) << 64) | (self.res_a & MASK64)
                res_b = (in_data >> 96) & MASK32
                hold_vld = 1
                phase = 4
            else:
                hold = (in_data << 32) | (self.res_b & MASK32)
                hold_vld = 1
                res_a = 0
                res_b = 0
                phase = 0
        self.res_a = res_a
        self.res_b = res_b
        self.phase = phase
        self.hold = hold & MASK160
        self.hold_vld = hold_vld


class tc_vibe_gear_128_160(VibeUnitBaseTest):
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
                     f"out_data={_hex160(self.g.hold)}",
                     f"out_data={_hex160(od)}",
                     HIER)
            return False
        if ir != exp_ir:
            self.bad(name, stim,
                     f"in_ready={exp_ir} (combo !hold_vld || out_ready)",
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
        sset(d.in_data, _word128(in_data))
        sset(d.in_vld, 1 if in_vld else 0)
        # Combo in_ready = !hold_vld || out_ready needs a delta after sset.
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
        name = "tc_vibe_gear_128_160"
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
                     f"out_vld={ov} in_ready={ir} out_data={_hex160(od)}",
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
                         f"taken={_hex160(taken)} accepted={accepted} "
                         f"out_vld={ov} in_ready={ir}",
                         HIER)
                phase.drop_objection(self)
                return

        # Combo in_ready stays 1 when hold is empty even if out_ready=0.
        sset(d.out_ready, 0)
        sset(d.in_vld, 0)
        await Timer(100, "PS")
        ir0 = ival(d.in_ready, 0)
        if ir0 != 1 or not self.g.in_ready(0):
            self.bad(name, "hold empty, out_ready=0",
                     "in_ready=1 (combo !hold_vld || out_ready)",
                     f"in_ready={ir0}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.out_ready, 1)
        await Timer(100, "PS")

        # 2. Five consecutive 128b beats, out_ready=1 → exactly 4×160b.
        exp1 = pack_128_to_160(GROUP1)
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
                         "in_ready=1 (combo !hold_vld || out_ready)",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "group1", outs):
            phase.drop_objection(self)
            return
        if outs != exp1:
            self.bad(name, "5×128b in, out_ready=1",
                     "exactly 4×160b: " + " ".join(_hex160(x) for x in exp1),
                     f"n={len(outs)} " + " ".join(_hex160(x) for x in outs),
                     HIER)
            phase.drop_objection(self)
            return

        # 3. Backpressure: stall when out_ready=0 and hold full; resume.
        exp_bp = pack_128_to_160(GROUP1)
        step = await self._advance(name, "bp phase0 park res_a",
                                   1, GROUP1[0], 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, _, ir = step
        if taken is not None or not accepted:
            self.bad(name, "bp phase0 park res_a",
                     "accept, no out yet",
                     f"taken={_hex160(taken)} accepted={accepted} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        step = await self._advance(name, "bp phase1 emit hold",
                                   1, GROUP1[1], 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, od, ir = step
        if taken is not None or not accepted or ov != 1 or od != exp_bp[0]:
            self.bad(name, "bp phase1 emit hold",
                     f"accept, out_vld=1 out_data={_hex160(exp_bp[0])}",
                     f"taken={_hex160(taken)} accepted={accepted} "
                     f"out_vld={ov} out_data={_hex160(od)}",
                     HIER)
            phase.drop_objection(self)
            return
        # Hold is full. out_ready=0 must stall (in_ready=0) and keep the beat.
        for i in range(3):
            step = await self._advance(
                name, f"bp stall[{i}] out_ready=0 hold full",
                1, GROUP1[2], 0)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None or accepted or ov != 1 or od != exp_bp[0] or ir != 0:
                self.bad(name, f"bp stall[{i}] out_ready=0 hold full",
                         f"no take/accept, out_vld=1 out_data={_hex160(exp_bp[0])} in_ready=0",
                         f"taken={_hex160(taken)} accepted={accepted} "
                         f"out_vld={ov} out_data={_hex160(od)} in_ready={ir}",
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
                     f"take {_hex160(exp_bp[0])}, no new accept",
                     f"taken={_hex160(taken)} accepted={accepted} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        outs_bp = [taken]
        for i, beat in enumerate(GROUP1[2:]):
            step = await self._advance(
                name, f"bp resume beat[{i+2}]", 1, beat, 1)
            if step is None:
                phase.drop_objection(self)
                return
            taken, accepted, ov, od, ir = step
            if taken is not None:
                outs_bp.append(taken)
            if not accepted:
                self.bad(name, f"bp resume beat[{i+2}]",
                         "in_ready=1 after hold drained",
                         f"accepted=0 in_ready={ir} out_vld={ov}",
                         HIER)
                phase.drop_objection(self)
                return
        if not await self._drain(name, "bp resume", outs_bp):
            phase.drop_objection(self)
            return
        if outs_bp != exp_bp:
            self.bad(name, "bp resume after stall, same 5×128b",
                     "no drop/dup: " + " ".join(_hex160(x) for x in exp_bp),
                     f"n={len(outs_bp)} " + " ".join(_hex160(x) for x in outs_bp),
                     HIER)
            phase.drop_objection(self)
            return

        # 4. Phase wrap: second group of 5 also produces 4 correct outs.
        exp2 = pack_128_to_160(GROUP2)
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
            self.bad(name, "second 5×128b group after phase wrap",
                     "exactly 4×160b: " + " ".join(_hex160(x) for x in exp2),
                     f"n={len(outs2)} " + " ".join(_hex160(x) for x in outs2),
                     HIER)
            phase.drop_objection(self)
            return

        # 5. Mid-run async rst_n clears hold_vld / phase (no dest posedge).
        step = await self._advance(name, "pre-async-rst park beat0",
                                   1, GROUP1[0], 1)
        if step is None:
            phase.drop_objection(self)
            return
        step = await self._advance(name, "pre-async-rst emit hold",
                                   1, GROUP1[1], 1)
        if step is None:
            phase.drop_objection(self)
            return
        taken, accepted, ov, _, _ = step
        if ov != 1:
            self.bad(name, "pre-async-rst emit hold",
                     "out_vld=1 before mid-run rst_n",
                     f"out_vld={ov} taken={_hex160(taken)}",
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
                     f"out_vld={ov} out_data={_hex160(od)}",
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
                     "out_vld=0 in_ready=1 (phase/hold cleared)",
                     f"out_vld={ov} in_ready={ir}",
                     HIER)
            phase.drop_objection(self)
            return

        # 6. Leaf pins match product SV (no ovf_l / dual-clock / rbits).
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_gear_128_160 product port",
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


uvm_component_utils(tc_vibe_gear_128_160)
