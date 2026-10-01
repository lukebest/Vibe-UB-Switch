"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_rx_deskew.

Covers reset/idle (aligned=0, no spurious out_vld), lane-skew AMCTL
absorb / first-AMCTL lock / align, factory physical=logical pass-
through (no lane swap), AM drop (out_vld=0), in_vld stall without a
saw step, a second data group after lock, mid-run async rst_n
through dest posedge, and a pin scan with instance u_u. Not a
full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_rx_deskew.sv: async-low rst_n,
combo aligned = saw0&saw1&saw2&saw3, combo out_vld =
in_vld && !(am0|am1|am2|am3), out0..out3 = in0..in3 (U24, no
delay once aligned). First AMCTL 160b on a lane (amX && !amX_r
while in_vld) sets sawX; FIFO pointers only record lock. Used by
vibe_pcs_rx u_dsk. This is not vibe_pcs_tx / vibe_pcs_rx /
vibe_pcs_scramble / vibe_ebch16 / vibe_pcs_tx_cw2beat /
vibe_pcs_tx_amctl / vibe_pcs_tx_g1 / vibe_pcs_tx_fec /
vibe_rs128_120_enc / vibe_rs128_120_dec / vibe_pcs_rx_unpack /
vibe_pcs_tx_pack / vibe_pcs_rx_amctl_lock / gear / vibe_afifo /
vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module.
CHILDREN: none.
Stock Icarus tc_pcs_rx_deskew remains the official staggered-AM /
out_vld scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
HIER = "u_u.aligned / u_u.out_vld"
WRAP = "vibe_pcs_rx_deskew_cocotb_top"
PINS = (
    "clk", "rst_n",
    "in0", "in1", "in2", "in3", "in_vld",
    "am0", "am1", "am2", "am3",
    "out0", "out1", "out2", "out3", "out_vld", "aligned",
)
ABSENT = (
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld", "u_l", "u_dsk",
    "lane_id", "seed_load", "en", "cw_sel", "cw", "u_cw", "u_a",
    "cw_data", "cw_vld", "cw_ready", "beat_data", "beat_vld", "beat_ready",
    "amctl_40B", "sdf_period", "in_ready", "link_up",
    "start", "in_sym", "parity", "u_enc", "u_g", "u_g1", "u_fec",
    "u_pack", "u_un", "locked", "lid", "lid_bad", "is_amctl", "sdf", "edf",
    "fec_fail", "data_out",
)

# Stock Icarus tc_pcs_rx_deskew: staggered AM 0xA..0xD, then data 1..4.
STOCK_AM = (0xA, 0xB, 0xC, 0xD)
STOCK_DATA = (0x1, 0x2, 0x3, 0x4)

# Distinctive 160b so a lane swap cannot pass by accident.
WIDE = (
    int("A0" * 20, 16),
    int("B1" * 20, 16),
    int("C2" * 20, 16),
    int("D3" * 20, 16),
)
WIDE2 = (
    int("0123456789ABCDEF0123456789ABCDEF01234567", 16),
    int("FEDCBA9876543210FEDCBA9876543210FEDCBA98", 16),
    int("C0DE" * 10, 16),
    int("BEEF" * 10, 16),
)
HUNT = (
    int("11" * 20, 16),
    int("22" * 20, 16),
    int("33" * 20, 16),
    int("44" * 20, 16),
)


def _word160(v: int) -> int:
    return int(v) & MASK160


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:040x}"


def _ams(*bits):
    return tuple(1 if b else 0 for b in bits)


def _zeros():
    return (0, 0, 0, 0)


def exp_out_vld(in_vld, ams) -> int:
    """Product combo: in_vld && !(am0|am1|am2|am3)."""
    return 1 if (in_vld and not any(ams)) else 0


class tc_vibe_pcs_rx_deskew(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.in_vld, 0)
        for i in range(4):
            sset(getattr(d, f"am{i}"), 0)
            sset(getattr(d, f"in{i}"), 0)

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

    def _inner_sample(self):
        u = getattr(self.dut, "u_u", None)
        if u is None:
            return None
        return (
            ival(u.out_vld, -1),
            ival(u.out0, -1),
            ival(u.out1, -1),
            ival(u.out2, -1),
            ival(u.out3, -1),
            ival(u.aligned, -1),
        )

    def _score_inner(self, name, stim, ov, outs, aligned):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + " (u_u)",
                     "u_u present", "missing", WRAP)
            return False
        got = (ov,) + tuple(outs) + (aligned,)
        if inner != got:
            self.bad(name, stim + " (u_u vs wrap)",
                     f"out_vld={got[0]} aligned={got[5]} "
                     f"out0..3={','.join(_hex160(x) for x in got[1:5])}",
                     f"out_vld={inner[0]} aligned={inner[5]} "
                     f"out0..3={','.join(_hex160(x) for x in inner[1:5])}",
                     HIER)
            return False
        return True

    def _sample_combo(self):
        d = self.dut
        return (
            ival(d.out_vld, -1),
            ival(d.out0, -1),
            ival(d.out1, -1),
            ival(d.out2, -1),
            ival(d.out3, -1),
        )

    def _sample_aligned(self):
        return ival(self.dut.aligned, -1)

    async def _apply(self, in_vld, ams, ins):
        """Drive on falling edge; sample combo then aligned after the posedge.

        Returns (out_vld, out0, out1, out2, out3, aligned).
        Combo outs are current inputs. aligned is saw0&..&saw3 after NBA.
        """
        d = self.dut
        sset(d.in_vld, 1 if in_vld else 0)
        for i in range(4):
            sset(getattr(d, f"am{i}"), 1 if ams[i] else 0)
            sset(getattr(d, f"in{i}"), _word160(ins[i]))
        await Timer(100, "PS")
        ov, o0, o1, o2, o3 = self._sample_combo()
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        aligned = self._sample_aligned()
        await FallingEdge(d.clk)
        return ov, o0, o1, o2, o3, aligned

    def _score_combo(self, name, stim, ov, outs, in_vld, ams, ins):
        exp_ov = exp_out_vld(in_vld, ams)
        exp = tuple(_word160(w) for w in ins)
        if ov != exp_ov:
            self.bad(name, stim,
                     f"out_vld={exp_ov}",
                     f"out_vld={ov}",
                     "u_u.out_vld")
            return False
        got = tuple(outs)
        if any(x is None for x in got) or got != exp:
            self.bad(name, stim + " (pass-through, no lane swap)",
                     f"out0..3={','.join(_hex160(x) for x in exp)}",
                     f"out0..3={','.join(_hex160(x) for x in got)}",
                     "u_u.out0")
            return False
        return True

    def _score_aligned(self, name, stim, aligned, exp):
        if aligned != exp:
            self.bad(name, stim,
                     f"aligned={exp}",
                     f"aligned={aligned}",
                     "u_u.aligned")
            return False
        return True

    def _score(self, name, stim, sample, in_vld, ams, ins, exp_al):
        ov, o0, o1, o2, o3, al = sample
        if not self._score_combo(name, stim, ov, (o0, o1, o2, o3),
                                 in_vld, ams, ins):
            return False
        return self._score_aligned(name, stim, al, exp_al)

    async def _stagger_lock(self, name, order, am_ins, data_ins, label):
        """Apply first-AMCTL on lanes in `order`; then score data, no AM."""
        for step, lane in enumerate(order):
            ams = _ams(*[i == lane for i in range(4)])
            sample = await self._apply(1, ams, am_ins)
            exp_al = 1 if step == 3 else 0
            if not self._score(
                    name, f"{label} AM lane{lane} step {step}",
                    sample, 1, ams, am_ins, exp_al):
                return False
        sample = await self._apply(1, _zeros(), data_ins)
        return self._score(
            name, f"{label} data no AM after lock",
            sample, 1, _zeros(), data_ins, 1)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_rx_deskew"

        if len(set(WIDE)) != 4 or len(set(WIDE2)) != 4:
            self.bad(name, "golden wide uniqueness",
                     "4 distinct 160b words",
                     f"WIDE={len(set(WIDE))} WIDE2={len(set(WIDE2))}",
                     "golden")
            phase.drop_objection(self)
            return
        if exp_out_vld(1, _zeros()) != 1 or exp_out_vld(1, _ams(1, 0, 0, 0)) != 0:
            self.bad(name, "golden out_vld",
                     "data=1 AM=0",
                     "mismatch",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, not aligned, no spurious out_vld.
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if ov != 0 or al != 0 or o0 != 0 or o1 != 0 or o2 != 0 or o3 != 0:
            self.bad(name, "reset then release, in_vld=0 am*=0",
                     "aligned=0 out_vld=0 out0..3=0",
                     f"aligned={al} out_vld={ov} "
                     f"out={_hex160(o0)},{_hex160(o1)},"
                     f"{_hex160(o2)},{_hex160(o3)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            sample = await self._apply(0, _zeros(), WIDE)
            if not self._score(
                    name, f"idle cycle {i} after reset (in_vld=0)",
                    sample, 0, _zeros(), WIDE, 0):
                phase.drop_objection(self)
                return

        # Hunt pass-through: data with no AM before any lock (aligned stays 0).
        sample = await self._apply(1, _zeros(), WIDE)
        if not self._score(
                name, "data no AM during hunt (factory pass-through)",
                sample, 1, _zeros(), WIDE, 0):
            phase.drop_objection(self)
            return

        # One-lane AM does not lock. Combo drops that beat.
        sample = await self._apply(1, _ams(1, 0, 0, 0), STOCK_AM)
        if not self._score(
                name, "AM lane0 only (saw0, not aligned)",
                sample, 1, _ams(1, 0, 0, 0), STOCK_AM, 0):
            phase.drop_objection(self)
            return

        # Async rst_n mid-hunt clears registered saw / aligned.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if al != 0 or ov != 0:
            self.bad(name, "async rst_n=0 mid-hunt (100ps, no posedge)",
                     "aligned=0 out_vld=0",
                     f"aligned={al} out_vld={ov}",
                     "u_u.saw0")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        if self._sample_aligned() != 0:
            self.bad(name, "after async re-reset release, idle",
                     "aligned=0",
                     f"aligned={self._sample_aligned()}",
                     "u_u.aligned")
            phase.drop_objection(self)
            return

        # 2. Lane skew absorb / lock / align (stock staggered AM 0,1,2,3).
        if not await self._stagger_lock(
                name, (0, 1, 2, 3), STOCK_AM, STOCK_DATA,
                "stock stagger 0-1-2-3"):
            phase.drop_objection(self)
            return

        # After lock, any AM beat is dropped; aligned holds.
        sample = await self._apply(1, _ams(0, 0, 1, 0), WIDE)
        if not self._score(
                name, "post-lock AM lane2 (drop, aligned holds)",
                sample, 1, _ams(0, 0, 1, 0), WIDE, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _zeros(), WIDE)
        if not self._score(
                name, "post-lock data after AM drop (wide, no swap)",
                sample, 1, _zeros(), WIDE, 1):
            phase.drop_objection(self)
            return

        # Combo hold: same pins, no drift (5 ns, clock free-runs).
        held = sample
        await Timer(5, "NS")
        later = self._sample_combo() + (self._sample_aligned(),)
        if later[0] != 1 or later[5] != 1 or later[1:5] != held[1:5]:
            self.bad(name, "hold post-lock data 5 ns (combo outs / aligned)",
                     f"out_vld=1 aligned=1 outs stay "
                     f"{','.join(_hex160(x) for x in WIDE)}",
                     f"out_vld={later[0]} aligned={later[5]} "
                     f"outs={','.join(_hex160(x) for x in later[1:5])}",
                     HIER)
            phase.drop_objection(self)
            return

        # Async rst_n after lock clears aligned without a posedge.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if self._sample_aligned() != 0:
            self.bad(name, "async rst_n=0 after lock (100ps, no posedge)",
                     "aligned=0",
                     f"aligned={self._sample_aligned()}",
                     "u_u.aligned")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        # Three-lane AM only: never aligned. Fourth lane completes lock.
        for lane in (0, 1, 2):
            ams = _ams(*[i == lane for i in range(4)])
            sample = await self._apply(1, ams, HUNT)
            if not self._score(
                    name, f"partial hunt AM lane{lane} (3 of 4)",
                    sample, 1, ams, HUNT, 0):
                phase.drop_objection(self)
                return
        sample = await self._apply(1, _zeros(), WIDE2)
        if not self._score(
                name, "data after 3-lane hunt (still not aligned)",
                sample, 1, _zeros(), WIDE2, 0):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _ams(0, 0, 0, 1), STOCK_AM)
        if not self._score(
                name, "AM lane3 completes 3+1 lock",
                sample, 1, _ams(0, 0, 0, 1), STOCK_AM, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _zeros(), WIDE2)
        if not self._score(
                name, "data after 3+1 lock (wide2, no swap)",
                sample, 1, _zeros(), WIDE2, 1):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # Simultaneous all-4 first AMCTL: one beat locks, that beat is dropped.
        sample = await self._apply(1, _ams(1, 1, 1, 1), STOCK_AM)
        if not self._score(
                name, "simultaneous AM all lanes (lock in one beat)",
                sample, 1, _ams(1, 1, 1, 1), STOCK_AM, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _zeros(), STOCK_DATA)
        if not self._score(
                name, "stock data after simultaneous lock",
                sample, 1, _zeros(), STOCK_DATA, 1):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # Reverse stagger (lane 3 first) — skew absorb is order-independent.
        if not await self._stagger_lock(
                name, (3, 1, 0, 2), WIDE, WIDE2,
                "reverse stagger 3-1-0-2"):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # Two-beat AMCTL pulse: only the rising beat latches (am && !am_r).
        sample = await self._apply(1, _ams(1, 0, 0, 0), STOCK_AM)
        if not self._score(
                name, "two-beat AM lane0 rising (first 160b)",
                sample, 1, _ams(1, 0, 0, 0), STOCK_AM, 0):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _ams(1, 0, 0, 0), WIDE)
        if not self._score(
                name, "two-beat AM lane0 second 160b (am0_r, no new lock)",
                sample, 1, _ams(1, 0, 0, 0), WIDE, 0):
            phase.drop_objection(self)
            return
        for lane in (1, 2, 3):
            ams = _ams(*[i == lane for i in range(4)])
            sample = await self._apply(1, ams, STOCK_AM)
            exp_al = 1 if lane == 3 else 0
            if not self._score(
                    name, f"two-beat then AM lane{lane}",
                    sample, 1, ams, STOCK_AM, exp_al):
                phase.drop_objection(self)
                return

        # Second AMCTL marker after lock: aligned holds, beat dropped.
        sample = await self._apply(1, _ams(1, 1, 1, 1), WIDE)
        if not self._score(
                name, "second AMCTL all-lanes after lock (drop, hold aligned)",
                sample, 1, _ams(1, 1, 1, 1), WIDE, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _ams(1, 1, 1, 1), WIDE2)
        if not self._score(
                name, "second AMCTL second 160b (am*_r, aligned holds)",
                sample, 1, _ams(1, 1, 1, 1), WIDE2, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _zeros(), WIDE2)
        if not self._score(
                name, "second data group after second AMCTL",
                sample, 1, _zeros(), WIDE2, 1):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 3. Stimulus / score: in_vld=0 does not step saw even if AM is high.
        sample = await self._apply(0, _ams(1, 1, 1, 1), STOCK_AM)
        if not self._score(
                name, "in_vld=0 with AM all lanes (no saw step)",
                sample, 0, _ams(1, 1, 1, 1), STOCK_AM, 0):
            phase.drop_objection(self)
            return
        sample = await self._apply(0, _zeros(), WIDE)
        if not self._score(
                name, "in_vld=0 stall after ignored AM",
                sample, 0, _zeros(), WIDE, 0):
            phase.drop_objection(self)
            return

        # Mid-stagger stall: lock two lanes, idle, finish the other two.
        sample = await self._apply(1, _ams(1, 0, 0, 0), HUNT)
        if not self._score(
                name, "stall-stagger AM lane0",
                sample, 1, _ams(1, 0, 0, 0), HUNT, 0):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _ams(0, 1, 0, 0), HUNT)
        if not self._score(
                name, "stall-stagger AM lane1",
                sample, 1, _ams(0, 1, 0, 0), HUNT, 0):
            phase.drop_objection(self)
            return
        for k in range(3):
            sample = await self._apply(0, _zeros(), WIDE)
            if not self._score(
                    name, f"in_vld=0 stall[{k}] mid-stagger (aligned stays 0)",
                    sample, 0, _zeros(), WIDE, 0):
                phase.drop_objection(self)
                return
        sample = await self._apply(1, _ams(0, 0, 1, 0), STOCK_AM)
        if not self._score(
                name, "resume stagger AM lane2 after stall",
                sample, 1, _ams(0, 0, 1, 0), STOCK_AM, 0):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _ams(0, 0, 0, 1), STOCK_AM)
        if not self._score(
                name, "resume stagger AM lane3 after stall (lock)",
                sample, 1, _ams(0, 0, 0, 1), STOCK_AM, 1):
            phase.drop_objection(self)
            return
        sample = await self._apply(1, _zeros(), WIDE)
        if not self._score(
                name, "data after stalled stagger lock",
                sample, 1, _zeros(), WIDE, 1):
            phase.drop_objection(self)
            return

        # Extra in_vld=0 after lock must not drop aligned.
        for i in range(3):
            sample = await self._apply(0, _zeros(), STOCK_DATA)
            if not self._score(
                    name, f"in_vld=0 after lock[{i}] (aligned holds)",
                    sample, 0, _zeros(), STOCK_DATA, 1):
                phase.drop_objection(self)
                return
        sample = await self._apply(1, _zeros(), WIDE)
        if not self._score(
                name, "data after post-lock idle (wide, no swap)",
                sample, 1, _zeros(), WIDE, 1):
            phase.drop_objection(self)
            return

        # in_vld=1 with no AM after wrap-ish many beats: still pass-through.
        for i, vec in enumerate((WIDE, WIDE2, HUNT, STOCK_DATA, WIDE)):
            sample = await self._apply(1, _zeros(), vec)
            if not self._score(
                    name, f"streaming data[{i}] after lock (wptr walks)",
                    sample, 1, _zeros(), vec, 1):
                phase.drop_objection(self)
                return

        # 4. Mid-run async rst_n clears registered saw / aligned.
        # Park the post-lock streaming state (aligned=1), then pulse
        # rst_n through dest posedge.
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if ov != 1 or al != 1:
            self.bad(name, "pre-dest-rst park (streaming after lock)",
                     "aligned=1 out_vld=1",
                     f"aligned={al} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_inner(
                name, "pre-async-rst park", ov, (o0, o1, o2, o3), al):
            phase.drop_objection(self)
            return
        u = getattr(d, "u_u", None)
        saws = [
            ival(getattr(u, f"saw{i}"), -1) if u is not None else None
            for i in range(4)
        ]
        if any(s != 1 for s in saws):
            self.bad(name, "pre-async-rst park (live saw)",
                     "u_u.saw0..3=1",
                     f"saw={saws}",
                     "u_u.saw0")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if al != 0 or ov != 0:
            self.bad(name, "mid-run rst_n=0 (100ps, no posedge)",
                     "aligned=0 out_vld=0 (async clear)",
                     f"aligned={al} out_vld={ov}",
                     "u_u.aligned")
            phase.drop_objection(self)
            return
        if not self._score_inner(
                name, "mid-run rst_n=0", ov, (o0, o1, o2, o3), al):
            phase.drop_objection(self)
            return
        saws = [ival(getattr(d.u_u, f"saw{i}"), -1) for i in range(4)]
        amrs = [ival(getattr(d.u_u, f"am{i}_r"), -1) for i in range(4)]
        wptr = ival(d.u_u.wptr, -1)
        aptrs = [ival(getattr(d.u_u, f"a{i}"), -1) for i in range(4)]
        if (any(s != 0 for s in saws) or any(r != 0 for r in amrs)
                or wptr != 0 or any(a != 0 for a in aptrs)):
            self.bad(name, "mid-run rst_n=0 (hunt async clear)",
                     "u_u.saw*=0 u_u.am*_r=0 u_u.wptr=0 u_u.a*=0",
                     f"saw={saws} am_r={amrs} wptr={wptr} a={aptrs}",
                     "u_u.saw0")
            phase.drop_objection(self)
            return
        await self._to_fall()
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if al != 0 or ov != 0:
            self.bad(name, "rst_n held 0 through dest posedge",
                     "aligned=0 out_vld=0",
                     f"aligned={al} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_inner(
                name, "rst_n held 0 through dest posedge",
                ov, (o0, o1, o2, o3), al):
            phase.drop_objection(self)
            return
        sset(d.rst_n, 1)
        await self._idle()
        await self.cycles(2)
        await FallingEdge(d.clk)
        ov, o0, o1, o2, o3 = self._sample_combo()
        al = self._sample_aligned()
        if al != 0 or ov != 0:
            self.bad(name, "after async re-release, idle",
                     "aligned=0 out_vld=0",
                     f"aligned={al} out_vld={ov}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_inner(
                name, "after async re-release, idle",
                ov, (o0, o1, o2, o3), al):
            phase.drop_objection(self)
            return
        # After mid-run rst leftover saw is gone; 4 staggered AM must lock
        # with no leftover aligned=1.
        if not await self._stagger_lock(
                name, (0, 1, 2, 3), STOCK_AM, WIDE2,
                "after dest-rst stagger 0-1-2-3"):
            phase.drop_objection(self)
            return

        # 5. Leaf pins match product SV (no ovf_l / dual-clock / leftover
        # u_dsk). Instance u_u (not leftover u_dsk / u_l).
        if not hasattr(d, "u_u"):
            self.bad(name, "leaf instance scan (u_u)",
                     "u_u present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_pcs_rx_deskew product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return
        u = d.u_u
        for need in PINS:
            if not hasattr(u, need):
                self.bad(name, f"leaf instance pin scan (u_u.{need})",
                         f"u_u.{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_rx_deskew)
