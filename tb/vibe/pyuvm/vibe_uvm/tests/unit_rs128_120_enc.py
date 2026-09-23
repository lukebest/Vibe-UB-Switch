"""Module-level uvm-python TC for Decision-I leaf vibe_rs128_120_enc.

Covers reset/idle (in_ready=0, done=0, parity=0), systematic RS(128,120)
encode / 8-symbol parity vs a golden GF(256) LFSR, start restart,
in_vld stall without a step, and a second message after done.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_rs128_120_enc.sv: async-low rst_n, start
clears r0..r7 / cnt and sets busy, combo in_ready = busy && (cnt < 120),
step on busy && in_vld && in_ready with fb = in_sym ^ r7 and Table 3-2
G0..G7 via vibe_gf256_mul, done 1-cycle pulse on the 120th accept,
parity = {r7,r6,r5,r4,r3,r2,r1,r0}. Used by vibe_pcs_tx_fec u_enc_a /
u_enc_b. T=2 encoding produces the same 8 parity symbols.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# Table 3-2 generator coefficients (product localparam G0..G7).
G = (24, 200, 173, 239, 54, 81, 11, 255)
MSG_N = 120
MASK64 = (1 << 64) - 1
HIER = "u_enc.parity / u_enc.done"


def gf256_mul(a: int, b: int) -> int:
    """Same bit-serial GF(256) mul as vibe_ub_fn.vh (reduce 0x11D / 8'h1D)."""
    p = 0
    aa = a & 0xFF
    bb = b & 0xFF
    for _ in range(8):
        if bb & 1:
            p ^= aa
        if aa & 0x80:
            aa = ((aa << 1) & 0xFF) ^ 0x1D
        else:
            aa = (aa << 1) & 0xFF
        bb >>= 1
    return p


def pack_parity(r) -> int:
    """Product concat: {r7,r6,r5,r4,r3,r2,r1,r0}."""
    p = 0
    for i in range(7, -1, -1):
        p = (p << 8) | (r[i] & 0xFF)
    return p & MASK64


def lfsr_step(r, sym: int):
    """One product LFSR step: fb = in_sym ^ r7, then G0..G7."""
    fb = (sym ^ r[7]) & 0xFF
    nxt = [0] * 8
    nxt[0] = gf256_mul(fb, G[0])
    for i in range(1, 8):
        nxt[i] = (r[i - 1] ^ gf256_mul(fb, G[i])) & 0xFF
    return nxt


def golden_parity(msg) -> int:
    """Systematic RS(128,120) parity after len(msg) accepted symbols."""
    r = [0] * 8
    for sym in msg:
        r = lfsr_step(r, int(sym) & 0xFF)
    return pack_parity(r)


def _hex64(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:016x}"


def _msg_inc():
    return [i & 0xFF for i in range(MSG_N)]


def _msg_const(sym: int):
    return [sym & 0xFF] * MSG_N


def _msg_a5():
    return [(0xA5 if (i & 1) == 0 else 0x5A) for i in range(MSG_N)]


def _msg_walk(idx: int):
    m = [0] * MSG_N
    m[idx] = 1
    return m


class tc_vibe_rs128_120_enc(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.in_sym, 0)

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
            ival(d.in_ready, -1),
            ival(d.done, -1),
            ival(d.parity, -1),
        )

    async def _cycle(self, start=0, in_vld=0, in_sym=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.start, 1 if start else 0)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.in_sym, int(in_sym) & 0xFF)
        await self._to_fall()
        return self._sample()

    async def _start_enc(self):
        """Pulse start; leave in_vld=0 so start if/else does not share a step."""
        rd, dn, par = await self._cycle(start=1, in_vld=0, in_sym=0)
        sset(self.dut.start, 0)
        return rd, dn, par

    async def _feed(self, msg, stall_at=None, stall_n=0):
        """Accept every symbol in msg. Optional in_vld=0 stall after stall_at.

        Returns (n_accepted, last_sample, done_seen_on_last).
        """
        accepted = 0
        last = self._sample()
        done_on_last = False
        for i, sym in enumerate(msg):
            if stall_at is not None and i == stall_at:
                held = last
                for k in range(stall_n):
                    rd, dn, par = await self._cycle(0, 0, 0xFF)
                    if rd != 1 or dn != 0 or par != held[2]:
                        return accepted, (rd, dn, par), False, (
                            f"stall[{k}] after {accepted} symbols",
                            f"in_ready=1 done=0 parity={_hex64(held[2])}",
                            f"in_ready={rd} done={dn} parity={_hex64(par)}",
                        )
                    last = (rd, dn, par)
            rd, dn, par = await self._cycle(0, 1, sym)
            accepted += 1
            last = (rd, dn, par)
            if dn == 1:
                done_on_last = True
        return accepted, last, done_on_last, None

    def _score_done(self, name, stim, rd, dn, par, exp_par):
        if dn != 1:
            self.bad(name, stim,
                     f"done=1 in_ready=0 parity={_hex64(exp_par)}",
                     f"done={dn} in_ready={rd} parity={_hex64(par)}",
                     HIER)
            return False
        if rd != 0:
            self.bad(name, stim + " (in_ready after last)",
                     "in_ready=0 (busy dropped, cnt==120)",
                     f"in_ready={rd}",
                     "u_enc.in_ready")
            return False
        if par is None or par != exp_par:
            self.bad(name, stim,
                     f"parity={_hex64(exp_par)}",
                     f"parity={_hex64(par)}",
                     "u_enc.parity")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_rs128_120_enc"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, no ready, no done, zero parity.
        rd, dn, par = self._sample()
        if rd != 0 or dn != 0 or par != 0:
            self.bad(name, "reset then release, start=0 in_vld=0",
                     "in_ready=0 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            rd, dn, par = await self._cycle(0, 1, 0xA5)
            if rd != 0 or dn != 0 or par != 0:
                self.bad(name, f"idle cycle {i} after reset (in_vld=1, no start)",
                         "in_ready=0 done=0 parity=0 (not busy)",
                         f"in_ready={rd} done={dn} parity={_hex64(par)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Async rst_n mid-cycle clears registered LFSR / busy / done.
        rd, dn, par = await self._start_enc()
        if rd != 1 or dn != 0 or par != 0:
            self.bad(name, "start then idle (before async rst)",
                     "in_ready=1 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.in_ready")
            phase.drop_objection(self)
            return
        rd, dn, par = await self._cycle(0, 1, 0x11)
        if rd != 1 or dn != 0 or par == 0:
            self.bad(name, "one symbol before async rst (nonzero parity)",
                     "in_ready=1 done=0 parity!=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.parity")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        rd, dn, par = self._sample()
        if rd != 0 or dn != 0 or par != 0:
            self.bad(name, "async rst_n=0 mid-encode (100ps, no posedge)",
                     "in_ready=0 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.r0")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        rd, dn, par = self._sample()
        if rd != 0 or dn != 0 or par != 0:
            self.bad(name, "after async re-reset release, idle",
                     "in_ready=0 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Encode / parity: all-zero message → zero parity + done on 120th.
        rd, dn, par = await self._start_enc()
        if rd != 1 or dn != 0 or par != 0:
            self.bad(name, "start before all-zero encode",
                     "in_ready=1 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.in_ready")
            phase.drop_objection(self)
            return
        zeros = _msg_const(0)
        n, last, done_last, err = await self._feed(zeros)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last:
            self.bad(name, "all-zero 120-symbol encode",
                     "exactly 120 accepts, done on last",
                     f"n={n} done_on_last={done_last} "
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_done(
                name, "all-zero message (120×0x00)",
                rd, dn, par, 0):
            phase.drop_objection(self)
            return
        # done is a 1-cycle pulse; next idle cycle drops it. in_ready stays 0.
        rd, dn, par = await self._cycle(0, 0, 0)
        if dn != 0 or rd != 0 or par != 0:
            self.bad(name, "cycle after all-zero done pulse",
                     "done=0 in_ready=0 parity stays 0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.done")
            phase.drop_objection(self)
            return

        # Incrementing 0..119 vs golden LFSR.
        exp_inc = golden_parity(_msg_inc())
        rd, dn, par = await self._start_enc()
        if rd != 1:
            self.bad(name, "start before incrementing encode",
                     "in_ready=1", f"in_ready={rd}", "u_enc.in_ready")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(_msg_inc())
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "incrementing message 0..119",
                rd, dn, par, exp_inc):
            if n != MSG_N or not done_last:
                self.bad(name, "incrementing 0..119 encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last} "
                         f"parity={_hex64(par)} exp={_hex64(exp_inc)}",
                         HIER)
            phase.drop_objection(self)
            return
        if exp_inc == 0:
            self.bad(name, "incrementing golden is nonzero",
                     "parity != 0", f"parity={_hex64(exp_inc)}",
                     "u_enc.parity")
            phase.drop_objection(self)
            return

        # Alternating 0xA5/0x5A (distinct from incrementing).
        exp_a5 = golden_parity(_msg_a5())
        if exp_a5 == exp_inc:
            self.bad(name, "A5/5A golden vs incrementing uniqueness",
                     "distinct parity words",
                     f"both {_hex64(exp_a5)}",
                     "u_enc.parity")
            phase.drop_objection(self)
            return
        rd, _, _ = await self._start_enc()
        n, last, done_last, err = await self._feed(_msg_a5())
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "alternating 0xA5/0x5A message",
                rd, dn, par, exp_a5):
            if n != MSG_N or not done_last:
                self.bad(name, "A5/5A encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Walking 1 at first vs last symbol: different parity, both done.
        exp_w0 = golden_parity(_msg_walk(0))
        exp_w119 = golden_parity(_msg_walk(119))
        if exp_w0 == exp_w119 or exp_w0 == 0 or exp_w119 == 0:
            self.bad(name, "walk-1 first vs last golden",
                     "two distinct nonzero parity words",
                     f"w0={_hex64(exp_w0)} w119={_hex64(exp_w119)}",
                     "u_enc.parity")
            phase.drop_objection(self)
            return
        for label, msg, exp in (
                ("walk-1 at symbol 0", _msg_walk(0), exp_w0),
                ("walk-1 at symbol 119", _msg_walk(119), exp_w119)):
            rd, _, _ = await self._start_enc()
            n, last, done_last, err = await self._feed(msg)
            if err:
                stim, e, act = err
                self.bad(name, stim, e, act, HIER)
                phase.drop_objection(self)
                return
            rd, dn, par = last
            if n != MSG_N or not done_last or not self._score_done(
                    name, label, rd, dn, par, exp):
                if n != MSG_N or not done_last:
                    self.bad(name, f"{label} count",
                             "exactly 120 accepts, done on last",
                             f"n={n} done_on_last={done_last}",
                             HIER)
                phase.drop_objection(self)
                return

        # 3. Stimulus / score: in_vld=0 stall does not step; resume matches.
        exp_inc = golden_parity(_msg_inc())
        rd, _, _ = await self._start_enc()
        n, last, done_last, err = await self._feed(
            _msg_inc(), stall_at=40, stall_n=3)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, "u_enc.cnt")
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "incrementing with in_vld=0 stall at symbol 40",
                rd, dn, par, exp_inc):
            if n != MSG_N or not done_last:
                self.bad(name, "stalled incrementing encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start mid-stream restarts (if/else priority; leftover LFSR dropped).
        rd, _, _ = await self._start_enc()
        n, last, _, err = await self._feed(_msg_inc()[:17])
        if err or n != 17:
            self.bad(name, "partial incrementing before mid-start",
                     "17 accepts",
                     f"n={n} last={last} err={err}",
                     "u_enc.cnt")
            phase.drop_objection(self)
            return
        rd, dn, par = await self._start_enc()
        if rd != 1 or dn != 0 or par != 0:
            self.bad(name, "start mid-stream (clears LFSR)",
                     "in_ready=1 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.r0")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(_msg_a5())
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "A5/5A after mid-stream start (no leftover 0..16)",
                rd, dn, par, exp_a5):
            if n != MSG_N or not done_last:
                self.bad(name, "mid-start A5/5A encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start && in_vld same cycle: start wins, that symbol is not a step.
        # Then feed incrementing; parity must match incrementing, not
        # [0x99]+incrementing.
        rd, dn, par = await self._cycle(start=1, in_vld=1, in_sym=0x99)
        if rd != 1 or dn != 0 or par != 0:
            self.bad(name, "start&&in_vld same cycle (start wins, no step)",
                     "in_ready=1 done=0 parity=0",
                     f"in_ready={rd} done={dn} parity={_hex64(par)}",
                     "u_enc.r0")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(_msg_inc())
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "incrementing after start&&in_vld=0x99 (symbol ignored)",
                rd, dn, par, exp_inc):
            if n != MSG_N or not done_last:
                self.bad(name, "start-wins encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Second message after done (no leftover LFSR / cnt).
        rd, _, _ = await self._start_enc()
        n, last, done_last, err = await self._feed(_msg_const(0x3C))
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        exp_3c = golden_parity(_msg_const(0x3C))
        rd, dn, par = last
        if n != MSG_N or not done_last or not self._score_done(
                name, "second message after done (120×0x3C)",
                rd, dn, par, exp_3c):
            if n != MSG_N or not done_last:
                self.bad(name, "second-message encode count",
                         "exactly 120 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Extra in_vld after done must not step or re-pulse done.
        held = par
        for i in range(3):
            rd, dn, par = await self._cycle(0, 1, 0x7E)
            if rd != 0 or dn != 0 or par != held:
                self.bad(name, f"in_vld after done[{i}] (not busy)",
                         f"in_ready=0 done=0 parity stays {_hex64(held)}",
                         f"in_ready={rd} done={dn} parity={_hex64(par)}",
                         "u_enc.busy")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_rs128_120_enc)
