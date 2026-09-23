"""Module-level uvm-python TC for Decision-I leaf vibe_rs128_120_dec.

Covers reset/idle (in_ready=0, done=0, fec_fail=0, data_out=0),
RS(128,120) syndrome-check decode / data_out pack vs a golden Horner
recurrence, valid codeword (fec_fail=0) vs corrupted CW (fec_fail=1),
start restart, in_vld stall without a step, and a second CW after done.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_rs128_120_dec.sv: async-low rst_n, start
clears s0..s7 / cnt and sets busy, combo in_ready = busy && (cnt < 128),
step on busy && in_vld && in_ready with ns0 = s0^in_sym, ns1 = gf_mul2(s1)
^in_sym, ns2..ns7 = vibe_gf256_mul(s, α^i)^in_sym, msg[cnt] on cnt<120,
done 1-cycle pulse on the 128th accept, fec_fail = |{ns0..ns7} (last
symbol included), data_out packs msg[0] as MSB. T=2 check is
syndrome-only (no error locator / no correction). Same recurrence is
inlined in vibe_pcs_rx_fec (not an instance). Stock Icarus
tc_rs_dec_syndrome remains the official done-pulse scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest
from vibe_uvm.tests.unit_rs128_120_enc import (
    MSG_N,
    gf256_mul,
    golden_parity,
    lfsr_step,
    _msg_a5,
    _msg_const,
    _msg_inc,
    _msg_walk,
)

CW_N = 128
PAR_N = 8
MASK960 = (1 << 960) - 1
# Horner α^i = 2^i (ns0 is XOR; ns1 is gf_mul2).
ALPHA = (1, 2, 4, 8, 16, 32, 64, 128)
HIER = "u_dec.done / u_dec.fec_fail / u_dec.data_out"


def gf_mul2(a: int) -> int:
    """Same local gf_mul2 as the product decoder (α^1 / 0x11D)."""
    a = a & 0xFF
    shl = (a << 1) & 0xFF
    return shl ^ 0x1D if (a & 0x80) else shl


def syndrome_step(s, sym: int):
    """One product Horner step (last-symbol-included next syndromes)."""
    x = int(sym) & 0xFF
    ns = [0] * 8
    ns[0] = (s[0] ^ x) & 0xFF
    ns[1] = (gf_mul2(s[1]) ^ x) & 0xFF
    for i in range(2, 8):
        ns[i] = (gf256_mul(s[i], ALPHA[i]) ^ x) & 0xFF
    return ns


def golden_syndrome(cw):
    """8 syndromes after every symbol in cw (product ns0..ns7)."""
    s = [0] * 8
    for sym in cw:
        s = syndrome_step(s, sym)
    return s


def golden_fec_fail(cw) -> int:
    return 1 if any(x != 0 for x in golden_syndrome(cw)) else 0


def pack_data_out(msg) -> int:
    """Product concat: msg[0] is MSB of the 960-bit data_out."""
    p = 0
    for i in range(MSG_N):
        p = (p << 8) | (int(msg[i]) & 0xFF)
    return p & MASK960


def parity_bytes(msg):
    """8 parity symbols p7..p0 (r7 first), same concat as the encoder."""
    r = [0] * 8
    for sym in msg:
        r = lfsr_step(r, int(sym) & 0xFF)
    return [r[i] & 0xFF for i in range(7, -1, -1)]


def codeword(msg):
    """Systematic RS(128,120): 120 message symbols + p7..p0."""
    m = [int(s) & 0xFF for s in msg]
    return m + parity_bytes(m)


def _hex960(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0240x}"


class tc_vibe_rs128_120_dec(VibeUnitBaseTest):
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
            ival(d.fec_fail, -1),
            ival(d.data_out, -1),
        )

    async def _cycle(self, start=0, in_vld=0, in_sym=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.start, 1 if start else 0)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.in_sym, int(in_sym) & 0xFF)
        await self._to_fall()
        return self._sample()

    async def _start_dec(self):
        """Pulse start; leave in_vld=0 so start if/else does not share a step."""
        rd, dn, ff, dout = await self._cycle(start=1, in_vld=0, in_sym=0)
        sset(self.dut.start, 0)
        return rd, dn, ff, dout

    async def _feed(self, cw, stall_at=None, stall_n=0):
        """Accept every symbol in cw. Optional in_vld=0 stall after stall_at.

        Returns (n_accepted, last_sample, done_seen_on_last, err).
        """
        accepted = 0
        last = self._sample()
        done_on_last = False
        for i, sym in enumerate(cw):
            if stall_at is not None and i == stall_at:
                held = last
                for k in range(stall_n):
                    rd, dn, ff, dout = await self._cycle(0, 0, 0xFF)
                    if rd != 1 or dn != 0 or ff != 0 or dout != held[3]:
                        return accepted, (rd, dn, ff, dout), False, (
                            f"stall[{k}] after {accepted} symbols",
                            f"in_ready=1 done=0 fec_fail=0 "
                            f"data_out={_hex960(held[3])}",
                            f"in_ready={rd} done={dn} fec_fail={ff} "
                            f"data_out={_hex960(dout)}",
                        )
                    last = (rd, dn, ff, dout)
            rd, dn, ff, dout = await self._cycle(0, 1, sym)
            accepted += 1
            last = (rd, dn, ff, dout)
            if dn == 1:
                done_on_last = True
        return accepted, last, done_on_last, None

    def _score_done(self, name, stim, rd, dn, ff, dout, exp_ff, exp_dout):
        if dn != 1:
            self.bad(name, stim,
                     f"done=1 in_ready=0 fec_fail={exp_ff} "
                     f"data_out={_hex960(exp_dout)}",
                     f"done={dn} in_ready={rd} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     HIER)
            return False
        if rd != 0:
            self.bad(name, stim + " (in_ready after last)",
                     "in_ready=0 (busy dropped, cnt==128)",
                     f"in_ready={rd}",
                     "u_dec.in_ready")
            return False
        if ff != exp_ff:
            self.bad(name, stim,
                     f"fec_fail={exp_ff}",
                     f"fec_fail={ff}",
                     "u_dec.fec_fail")
            return False
        if dout is None or dout != exp_dout:
            self.bad(name, stim,
                     f"data_out={_hex960(exp_dout)}",
                     f"data_out={_hex960(dout)}",
                     "u_dec.data_out")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_rs128_120_dec"

        # Golden encoder/decoder consistency: valid CWs have zero syndrome.
        for label, msg in (
                ("all-zero", _msg_const(0)),
                ("incrementing", _msg_inc()),
                ("A5/5A", _msg_a5()),
                ("walk-0", _msg_walk(0)),
                ("walk-119", _msg_walk(119)),
                ("const-3C", _msg_const(0x3C))):
            cw = codeword(msg)
            if len(cw) != CW_N or golden_fec_fail(cw) != 0:
                self.bad(name, f"golden {label} codeword",
                         "128 symbols, syndrome=0 / fec_fail=0",
                         f"len={len(cw)} fec_fail={golden_fec_fail(cw)} "
                         f"syn={golden_syndrome(cw)}",
                         "golden")
                phase.drop_objection(self)
                return
            if pack_data_out(msg) != pack_data_out(cw[:MSG_N]):
                self.bad(name, f"golden {label} pack",
                         "data_out from first 120 symbols",
                         "mismatch",
                         "golden")
                phase.drop_objection(self)
                return
            # Encoder 64-bit concat must match p7..p0 bytes.
            par = golden_parity(msg)
            packed_par = 0
            for b in parity_bytes(msg):
                packed_par = (packed_par << 8) | b
            if packed_par != par:
                self.bad(name, f"golden {label} parity concat",
                         f"0x{par:016x}",
                         f"0x{packed_par:016x}",
                         "golden")
                phase.drop_objection(self)
                return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, no ready, no done, no fail, zero data_out.
        rd, dn, ff, dout = self._sample()
        if rd != 0 or dn != 0 or ff != 0 or dout != 0:
            self.bad(name, "reset then release, start=0 in_vld=0",
                     "in_ready=0 done=0 fec_fail=0 data_out=0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            rd, dn, ff, dout = await self._cycle(0, 1, 0xA5)
            if rd != 0 or dn != 0 or ff != 0 or dout != 0:
                self.bad(name, f"idle cycle {i} after reset (in_vld=1, no start)",
                         "in_ready=0 done=0 fec_fail=0 data_out=0 (not busy)",
                         f"in_ready={rd} done={dn} fec_fail={ff} "
                         f"data_out={_hex960(dout)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Async rst_n mid-cycle clears registered syndromes / busy / done.
        rd, dn, ff, dout = await self._start_dec()
        if rd != 1 or dn != 0 or ff != 0 or dout != 0:
            self.bad(name, "start then idle (before async rst)",
                     "in_ready=1 done=0 fec_fail=0 data_out=0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     "u_dec.in_ready")
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = await self._cycle(0, 1, 0x11)
        if rd != 1 or dn != 0 or ff != 0:
            self.bad(name, "one symbol before async rst",
                     "in_ready=1 done=0 fec_fail=0",
                     f"in_ready={rd} done={dn} fec_fail={ff}",
                     "u_dec.s0")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        rd, dn, ff, dout = self._sample()
        if rd != 0 or dn != 0 or ff != 0 or dout != 0:
            self.bad(name, "async rst_n=0 mid-decode (100ps, no posedge)",
                     "in_ready=0 done=0 fec_fail=0 data_out=0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     "u_dec.s0")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        rd, dn, ff, dout = self._sample()
        if rd != 0 or dn != 0 or ff != 0 or dout != 0:
            self.bad(name, "after async re-reset release, idle",
                     "in_ready=0 done=0 fec_fail=0 data_out=0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Decode / correct / err flags vs golden Horner.
        # All-zero CW (120×0 + 8×0 parity) → fec_fail=0, data_out=0.
        rd, dn, ff, dout = await self._start_dec()
        if rd != 1 or dn != 0 or ff != 0 or dout != 0:
            self.bad(name, "start before all-zero decode",
                     "in_ready=1 done=0 fec_fail=0 data_out=0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     "u_dec.in_ready")
            phase.drop_objection(self)
            return
        zeros = codeword(_msg_const(0))
        n, last, done_last, err = await self._feed(zeros)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last:
            self.bad(name, "all-zero 128-symbol decode",
                     "exactly 128 accepts, done on last",
                     f"n={n} done_on_last={done_last} "
                     f"in_ready={rd} done={dn} fec_fail={ff}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_done(
                name, "all-zero codeword (128×0x00, correct)",
                rd, dn, ff, dout, 0, 0):
            phase.drop_objection(self)
            return
        # done / fec_fail are 1-cycle pulses; data_out holds.
        rd, dn, ff, dout = await self._cycle(0, 0, 0)
        if dn != 0 or ff != 0 or rd != 0 or dout != 0:
            self.bad(name, "cycle after all-zero done pulse",
                     "done=0 fec_fail=0 in_ready=0 data_out stays 0",
                     f"in_ready={rd} done={dn} fec_fail={ff} "
                     f"data_out={_hex960(dout)}",
                     "u_dec.done")
            phase.drop_objection(self)
            return

        # Incrementing 0..119 + golden parity → correct, packed data_out.
        msg_inc = _msg_inc()
        cw_inc = codeword(msg_inc)
        exp_inc = pack_data_out(msg_inc)
        if exp_inc == 0:
            self.bad(name, "incrementing golden is nonzero",
                     "data_out != 0", f"data_out={_hex960(exp_inc)}",
                     "u_dec.data_out")
            phase.drop_objection(self)
            return
        rd, dn, ff, _ = await self._start_dec()
        if rd != 1:
            self.bad(name, "start before incrementing decode",
                     "in_ready=1", f"in_ready={rd}", "u_dec.in_ready")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(cw_inc)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "incrementing message 0..119 + golden parity (correct)",
                rd, dn, ff, dout, 0, exp_inc):
            if n != CW_N or not done_last:
                self.bad(name, "incrementing 0..119 decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last} fec_fail={ff}",
                         HIER)
            phase.drop_objection(self)
            return

        # Alternating 0xA5/0x5A (distinct from incrementing).
        msg_a5 = _msg_a5()
        cw_a5 = codeword(msg_a5)
        exp_a5 = pack_data_out(msg_a5)
        if exp_a5 == exp_inc:
            self.bad(name, "A5/5A golden vs incrementing uniqueness",
                     "distinct data_out words",
                     f"both {_hex960(exp_a5)}",
                     "u_dec.data_out")
            phase.drop_objection(self)
            return
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(cw_a5)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "alternating 0xA5/0x5A + golden parity (correct)",
                rd, dn, ff, dout, 0, exp_a5):
            if n != CW_N or not done_last:
                self.bad(name, "A5/5A decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Walking 1 at first vs last symbol: different data_out, both correct.
        exp_w0 = pack_data_out(_msg_walk(0))
        exp_w119 = pack_data_out(_msg_walk(119))
        if exp_w0 == exp_w119 or exp_w0 == 0 or exp_w119 == 0:
            self.bad(name, "walk-1 first vs last golden",
                     "two distinct nonzero data_out words",
                     f"w0={_hex960(exp_w0)} w119={_hex960(exp_w119)}",
                     "u_dec.data_out")
            phase.drop_objection(self)
            return
        for label, msg, exp in (
                ("walk-1 at symbol 0 (correct)", _msg_walk(0), exp_w0),
                ("walk-1 at symbol 119 (correct)", _msg_walk(119), exp_w119)):
            rd, _, _, _ = await self._start_dec()
            n, last, done_last, err = await self._feed(codeword(msg))
            if err:
                stim, e, act = err
                self.bad(name, stim, e, act, HIER)
                phase.drop_objection(self)
                return
            rd, dn, ff, dout = last
            if n != CW_N or not done_last or not self._score_done(
                    name, label, rd, dn, ff, dout, 0, exp):
                if n != CW_N or not done_last:
                    self.bad(name, f"{label} count",
                             "exactly 128 accepts, done on last",
                             f"n={n} done_on_last={done_last}",
                             HIER)
                phase.drop_objection(self)
                return

        # Err flags: flip one message symbol → fec_fail=1, data_out=received.
        cw_bad_msg = list(cw_inc)
        cw_bad_msg[17] ^= 0x01
        if golden_fec_fail(cw_bad_msg) != 1:
            self.bad(name, "golden flip msg[17] is detectable",
                     "fec_fail=1",
                     f"syn={golden_syndrome(cw_bad_msg)}",
                     "golden")
            phase.drop_objection(self)
            return
        exp_bad_msg = pack_data_out(cw_bad_msg[:MSG_N])
        if exp_bad_msg == exp_inc:
            self.bad(name, "flipped msg[17] changes data_out",
                     "data_out != incrementing pack",
                     f"both {_hex960(exp_inc)}",
                     "u_dec.data_out")
            phase.drop_objection(self)
            return
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(cw_bad_msg)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "incrementing CW with msg[17] flipped (err, no correct)",
                rd, dn, ff, dout, 1, exp_bad_msg):
            if n != CW_N or not done_last:
                self.bad(name, "flipped-msg decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Flip one parity symbol → fec_fail=1, data_out still the message.
        cw_bad_par = list(cw_inc)
        cw_bad_par[120] ^= 0x01
        if golden_fec_fail(cw_bad_par) != 1:
            self.bad(name, "golden flip p7 is detectable",
                     "fec_fail=1",
                     f"syn={golden_syndrome(cw_bad_par)}",
                     "golden")
            phase.drop_objection(self)
            return
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(cw_bad_par)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "incrementing CW with p7 flipped (err, data_out holds msg)",
                rd, dn, ff, dout, 1, exp_inc):
            if n != CW_N or not done_last:
                self.bad(name, "flipped-parity decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Two-symbol flip (beyond T=2 correctable if this were a locator).
        cw_bad2 = list(cw_inc)
        cw_bad2[3] ^= 0x02
        cw_bad2[80] ^= 0x04
        if golden_fec_fail(cw_bad2) != 1:
            self.bad(name, "golden two-symbol flip is detectable",
                     "fec_fail=1",
                     f"syn={golden_syndrome(cw_bad2)}",
                     "golden")
            phase.drop_objection(self)
            return
        exp_bad2 = pack_data_out(cw_bad2[:MSG_N])
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(cw_bad2)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "two-symbol flip (err flag, uncorrected data_out)",
                rd, dn, ff, dout, 1, exp_bad2):
            if n != CW_N or not done_last:
                self.bad(name, "two-symbol-flip decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # 3. Stimulus / score: in_vld=0 stall does not step; resume matches.
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(
            cw_inc, stall_at=40, stall_n=3)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, "u_dec.cnt")
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "incrementing with in_vld=0 stall at symbol 40 (correct)",
                rd, dn, ff, dout, 0, exp_inc):
            if n != CW_N or not done_last:
                self.bad(name, "stalled incrementing decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start mid-stream restarts (if/else priority; leftover syndromes dropped).
        rd, _, _, _ = await self._start_dec()
        n, last, _, err = await self._feed(cw_inc[:17])
        if err or n != 17:
            self.bad(name, "partial incrementing before mid-start",
                     "17 accepts",
                     f"n={n} last={last} err={err}",
                     "u_dec.cnt")
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = await self._start_dec()
        if rd != 1 or dn != 0 or ff != 0:
            self.bad(name, "start mid-stream (clears syndromes)",
                     "in_ready=1 done=0 fec_fail=0",
                     f"in_ready={rd} done={dn} fec_fail={ff}",
                     "u_dec.s0")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(cw_a5)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "A5/5A after mid-stream start (no leftover 0..16)",
                rd, dn, ff, dout, 0, exp_a5):
            if n != CW_N or not done_last:
                self.bad(name, "mid-start A5/5A decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start && in_vld same cycle: start wins, that symbol is not a step.
        rd, dn, ff, dout = await self._cycle(start=1, in_vld=1, in_sym=0x99)
        if rd != 1 or dn != 0 or ff != 0:
            self.bad(name, "start&&in_vld same cycle (start wins, no step)",
                     "in_ready=1 done=0 fec_fail=0",
                     f"in_ready={rd} done={dn} fec_fail={ff}",
                     "u_dec.s0")
            phase.drop_objection(self)
            return
        n, last, done_last, err = await self._feed(cw_inc)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "incrementing after start&&in_vld=0x99 (symbol ignored)",
                rd, dn, ff, dout, 0, exp_inc):
            if n != CW_N or not done_last:
                self.bad(name, "start-wins decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Second codeword after done (no leftover syndromes / cnt).
        rd, _, _, _ = await self._start_dec()
        n, last, done_last, err = await self._feed(codeword(_msg_const(0x3C)))
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        exp_3c = pack_data_out(_msg_const(0x3C))
        rd, dn, ff, dout = last
        if n != CW_N or not done_last or not self._score_done(
                name, "second codeword after done (120×0x3C, correct)",
                rd, dn, ff, dout, 0, exp_3c):
            if n != CW_N or not done_last:
                self.bad(name, "second-codeword decode count",
                         "exactly 128 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Extra in_vld after done must not step or re-pulse done / fec_fail.
        held = dout
        for i in range(3):
            rd, dn, ff, dout = await self._cycle(0, 1, 0x7E)
            if rd != 0 or dn != 0 or ff != 0 or dout != held:
                self.bad(name, f"in_vld after done[{i}] (not busy)",
                         f"in_ready=0 done=0 fec_fail=0 data_out stays "
                         f"{_hex960(held)}",
                         f"in_ready={rd} done={dn} fec_fail={ff} "
                         f"data_out={_hex960(dout)}",
                         "u_dec.busy")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_rs128_120_dec)
