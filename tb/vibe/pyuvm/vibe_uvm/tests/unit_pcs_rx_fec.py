"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_rx_fec.

Covers reset/idle (beat_ready=1, win_vld=0, fec_fail=0, no spurious
window), two-beat bypass unwrap ({hi, lo[511:64]}), T=4 / T=2
syndrome-check unwrap vs golden RS(128,120) Horner, garbage CW
fec_fail=1 without forwarding a 960, win_ready backpressure
(beat_ready=!win_vld), beat_vld stall after the first half-CW,
am_gap drop of leftover have_hi, and a second CW after drain.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/pcs/vibe_pcs_rx_fec.sv: async-low rst_n, combo
beat_ready=!win_vld, bypass=(fec_mode==VIBE_FEC_BYPASS), collect hi
then lo, one-shot rs_syndromes({hi, beat_data}) (same Horner as
stage-12, inlined, not an instance), emit {hi, lo[511:64]} when
bypass or syn==0, fec_fail=|syn when !bypass, am_gap clears have_hi.
Used by vibe_pcs_rx u_fec. Pairs with stage-17 vibe_pcs_tx_fec.
Stock Icarus tc_pcs_rx_fec remains the official win_vld scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import hier, ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest
from vibe_uvm.tests.unit_rs128_120_dec import (
    codeword,
    golden_fec_fail,
    pack_data_out,
)
from vibe_uvm.tests.unit_rs128_120_enc import (
    MSG_N,
    _msg_a5,
    _msg_const,
    _msg_inc,
    _msg_walk,
)

FEC_BYPASS = 0
FEC_T2 = 1
FEC_T4 = 2
MASK64 = (1 << 64) - 1
MASK512 = (1 << 512) - 1
MASK960 = (1 << 960) - 1
MASK1024 = (1 << 1024) - 1
HIER = "u_u.have_hi / u_u.win_vld / u_u.fec_fail"


def pack_window(syms) -> int:
    """MSB-first 960b window: win[959:952] = syms[0] (product slice)."""
    if len(syms) != MSG_N:
        raise ValueError("pack_window expects 120 symbols")
    v = 0
    for s in syms:
        v = (v << 8) | (int(s) & 0xFF)
    return v & MASK960


def pack_cw(syms) -> int:
    """MSB-first 1024b CW: cw[1023:1016] = syms[0]."""
    if len(syms) != 128:
        raise ValueError("pack_cw expects 128 symbols")
    v = 0
    for s in syms:
        v = (v << 8) | (int(s) & 0xFF)
    return v & MASK1024


def encode_cw(msg) -> int:
    return pack_cw(codeword(msg))


def bypass_cw(win: int) -> int:
    """Bypass still 6-flit align: {win, 64'd0}."""
    return ((int(win) & MASK960) << 64) & MASK1024


def cw_beats(cw: int):
    """Product collect: hi = cw[1023:512], lo = cw[511:0]."""
    c = int(cw) & MASK1024
    return (c >> 512) & MASK512, c & MASK512


def unwrap_win(cw: int) -> int:
    """Product emit: {hi, lo[511:64]} = cw[1023:64]."""
    return (int(cw) >> 64) & MASK960


def _hex960(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0240x}"


def _win_msg(v) -> str:
    if v is None:
        return "x"
    return f"win={_hex960(v)}"


W0 = pack_window(_msg_inc())
W1 = pack_window(_msg_a5())
W2 = pack_window(_msg_const(0x3C))
W3 = pack_window(_msg_walk(0))
W_ZERO = pack_window(_msg_const(0))
CW0 = encode_cw(_msg_inc())
CW1 = encode_cw(_msg_a5())
CW2 = encode_cw(_msg_const(0x3C))
CW3 = encode_cw(_msg_walk(0))
CW_ZERO = encode_cw(_msg_const(0))
CW_BYP0 = bypass_cw(W0)
CW_BYP1 = bypass_cw(W1)


class tc_vibe_pcs_rx_fec(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, fec_mode=FEC_T4, win_ready=1):
        d = self.dut
        sset(d.fec_mode, fec_mode)
        sset(d.beat_vld, 0)
        sset(d.beat_data, 0)
        sset(d.win_ready, 1 if win_ready else 0)
        sset(d.am_gap, 0)

    async def _hold_reset(self, n=4, fec_mode=FEC_T4, win_ready=1):
        sset(self.dut.rst_n, 0)
        await self._idle(fec_mode=fec_mode, win_ready=win_ready)
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    def _sample(self):
        d = self.dut
        return (
            ival(d.beat_ready, -1),
            ival(d.win_vld, -1),
            ival(d.win_data, -1),
            ival(d.fec_fail, -1),
        )

    def _have_hi(self):
        try:
            return ival(hier(self.dut, "u_u.have_hi"), -1)
        except Exception:
            return None

    async def _cycle(self, beat_vld=0, beat_data=0, win_ready=1,
                     fec_mode=None, am_gap=0):
        """Drive on this falling edge; sample combo then NBA after the posedge."""
        d = self.dut
        if fec_mode is not None:
            sset(d.fec_mode, fec_mode)
        sset(d.beat_vld, 1 if beat_vld else 0)
        sset(d.beat_data, int(beat_data) & MASK512)
        sset(d.win_ready, 1 if win_ready else 0)
        sset(d.am_gap, 1 if am_gap else 0)
        await Timer(100, "PS")
        pre = self._sample()
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        post = self._sample()
        await FallingEdge(d.clk)
        return pre, post

    async def _take_beat(self, name, label, beat, fec_mode, win_ready=1):
        """Hold beat_vld until combo beat_ready takes the beat."""
        for _ in range(32):
            pre, post = await self._cycle(1, beat, win_ready, fec_mode)
            br, wv, _, _ = pre
            if br == 1:
                return post
            if wv == 1 and win_ready:
                continue
            if self.fail_n:
                return None
        self.bad(name, f"{label} take beat",
                 "beat_ready=1 (combo !win_vld)",
                 "beat_ready stayed 0",
                 "u_u.beat_ready")
        return None

    async def _feed_cw(self, name, label, cw, fec_mode, win_ready=1):
        """Push both 512b halves. Returns post of the second take or None."""
        hi, lo = cw_beats(cw)
        post0 = await self._take_beat(
            name, f"{label} hi", hi, fec_mode, win_ready=win_ready)
        if post0 is None:
            return None
        br0, wv0, _, ff0 = post0
        if wv0 == 1:
            self.bad(name, f"{label} after first beat (need lo)",
                     "win_vld=0 fec_fail=0",
                     f"win_vld={wv0} fec_fail={ff0}",
                     "u_u.have_hi")
            return None
        if br0 != 1:
            self.bad(name, f"{label} after first beat (slot free)",
                     "beat_ready=1",
                     f"beat_ready={br0}",
                     "u_u.win_vld")
            return None
        return await self._take_beat(
            name, f"{label} lo", lo, fec_mode, win_ready=win_ready)

    def _score_win(self, name, stim, br, wv, wd, ff, exp_win, exp_ff):
        if wv != 1:
            self.bad(name, stim,
                     f"win_vld=1 fec_fail={exp_ff} {_win_msg(exp_win)}",
                     f"win_vld={wv} fec_fail={ff} {_win_msg(wd)}",
                     HIER)
            return False
        if ff != exp_ff:
            self.bad(name, stim,
                     f"fec_fail={exp_ff}",
                     f"fec_fail={ff}",
                     "u_u.fec_fail")
            return False
        if wd is None or (int(wd) & MASK960) != (int(exp_win) & MASK960):
            self.bad(name, stim,
                     _win_msg(exp_win),
                     _win_msg(wd),
                     "u_u.win_data")
            return False
        if br != 0:
            self.bad(name, stim + " (beat_ready while window pending)",
                     "beat_ready=0 (combo !win_vld)",
                     f"beat_ready={br}",
                     "u_u.beat_ready")
            return False
        return True

    async def _ack_win(self, name, label, fec_mode):
        """Consume a pending window (win_ready=1)."""
        pre, post = await self._cycle(0, 0, 1, fec_mode)
        br, wv, _, ff = post
        if wv != 0 or br != 1:
            self.bad(name, f"{label} ack window",
                     "win_vld=0 beat_ready=1",
                     f"win_vld={wv} beat_ready={br} fec_fail={ff}",
                     "u_u.win_vld")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_rx_fec"

        if unwrap_win(CW0) != W0 or unwrap_win(CW1) != W1:
            self.bad(name, "golden encode unwrap is the 960b message",
                     f"{_win_msg(W0)} / {_win_msg(W1)}",
                     f"{_win_msg(unwrap_win(CW0))} / {_win_msg(unwrap_win(CW1))}",
                     "golden")
            phase.drop_objection(self)
            return
        if unwrap_win(CW_BYP0) != W0 or unwrap_win(CW_ZERO) != 0:
            self.bad(name, "golden bypass / zero unwrap",
                     f"{_win_msg(W0)} / win=0",
                     f"{_win_msg(unwrap_win(CW_BYP0))} / "
                     f"{_win_msg(unwrap_win(CW_ZERO))}",
                     "golden")
            phase.drop_objection(self)
            return
        if (golden_fec_fail(codeword(_msg_inc())) != 0
                or golden_fec_fail(codeword(_msg_const(0))) != 0):
            self.bad(name, "golden valid CWs have zero syndrome",
                     "fec_fail=0",
                     "nonzero",
                     "golden")
            phase.drop_objection(self)
            return
        if pack_data_out(_msg_inc()) != W0:
            self.bad(name, "window pack matches decoder data_out pack",
                     _win_msg(W0),
                     _win_msg(pack_data_out(_msg_inc())),
                     "golden")
            phase.drop_objection(self)
            return
        if W0 == W1 or W0 == 0 or (CW0 & MASK64) == 0:
            self.bad(name, "golden W0 vs W1 uniqueness",
                     "distinct nonzero windows, W0 parity != 0",
                     f"w0={_win_msg(W0)} p0=0x{CW0 & MASK64:016x}",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset(fec_mode=FEC_T4)
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: ready, no window, no leftover fail / have_hi.
        br, wv, wd, ff = self._sample()
        hh = self._have_hi()
        if br != 1 or wv != 0 or wd != 0 or ff != 0 or hh == 1:
            self.bad(name, "reset then release, beat_vld=0 win_ready=1",
                     "beat_ready=1 win_vld=0 win_data=0 fec_fail=0 have_hi=0",
                     f"beat_ready={br} win_vld={wv} {_win_msg(wd)} "
                     f"fec_fail={ff} have_hi={hh}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            pre, post = await self._cycle(0, 0xA5, 1, FEC_T4)
            br, wv, wd, ff = post
            if br != 1 or wv != 0 or wd != 0 or ff != 0:
                self.bad(name, f"idle cycle {i} after reset (beat_vld=0)",
                         "beat_ready=1 win_vld=0 win_data=0 fec_fail=0",
                         f"beat_ready={br} win_vld={wv} {_win_msg(wd)} "
                         f"fec_fail={ff}",
                         HIER)
                phase.drop_objection(self)
                return

        # One 512b beat is not enough to unwrap / fail.
        hi0, _ = cw_beats(CW0)
        post = await self._take_beat(
            name, "lone beat", hi0, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        for i in range(6):
            pre, post = await self._cycle(0, 0, 1, FEC_T4)
            br, wv, wd, ff = post
            hh = self._have_hi()
            if br != 1 or wv != 0 or ff != 0:
                self.bad(name, f"lone beat hold[{i}] (need lo)",
                         "beat_ready=1 win_vld=0 fec_fail=0",
                         f"beat_ready={br} win_vld={wv} fec_fail={ff}",
                         "u_u.have_hi")
                phase.drop_objection(self)
                return
            if hh == 0:
                self.bad(name, f"lone beat hold[{i}] (half-CW parked)",
                         "have_hi=1",
                         f"have_hi={hh}",
                         "u_u.have_hi")
                phase.drop_objection(self)
                return

        # Async rst_n mid-hold clears have_hi.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        br, wv, wd, ff = self._sample()
        hh = self._have_hi()
        if br != 1 or wv != 0 or wd != 0 or ff != 0 or hh == 1:
            self.bad(name, "async rst_n=0 after lone beat (100ps, no posedge)",
                     "beat_ready=1 win_vld=0 win_data=0 fec_fail=0 have_hi=0",
                     f"beat_ready={br} win_vld={wv} {_win_msg(wd)} "
                     f"fec_fail={ff} have_hi={hh}",
                     "u_u.hi")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        br, wv, wd, ff = self._sample()
        if br != 1 or wv != 0 or wd != 0 or ff != 0:
            self.bad(name, "after async re-reset release, idle",
                     "beat_ready=1 win_vld=0 win_data=0 fec_fail=0",
                     f"beat_ready={br} win_vld={wv} {_win_msg(wd)} "
                     f"fec_fail={ff}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Bypass: two 512b beats, 6-flit unwrap, no fail.
        post = await self._feed_cw(
            name, "bypass W0", CW_BYP0, FEC_BYPASS, win_ready=0)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "bypass two 512b beats (inc window, zero pad)",
                br, wv, wd, ff, W0, 0):
            phase.drop_objection(self)
            return
        # win_ready=0 holds the window; no more beats accepted.
        for i in range(3):
            pre, post = await self._cycle(1, 0xFF, 0, FEC_BYPASS)
            br, wv, wd, ff = post
            if br != 0 or wv != 1 or (int(wd) & MASK960) != W0 or ff != 0:
                self.bad(name, f"bypass win_ready=0 hold[{i}]",
                         f"beat_ready=0 win_vld=1 fec_fail=0 {_win_msg(W0)}",
                         f"beat_ready={br} win_vld={wv} fec_fail={ff} "
                         f"{_win_msg(wd)}",
                         "u_u.win_vld")
                phase.drop_objection(self)
                return
        if not await self._ack_win(name, "bypass W0", FEC_BYPASS):
            phase.drop_objection(self)
            return

        # Bypass of a "garbage" lo still unwraps (no syndrome).
        post = await self._feed_cw(
            name, "bypass W1", CW_BYP1, FEC_BYPASS, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "bypass two 512b beats (A5/5A window, zero pad)",
                br, wv, wd, ff, W1, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "bypass W1", FEC_BYPASS):
            phase.drop_objection(self)
            return

        # 3. T=4: valid encode unwrap vs golden; beat_vld stall after hi.
        hi, lo = cw_beats(CW0)
        post = await self._take_beat(
            name, "T4 stall hi", hi, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        for i in range(3):
            pre, post = await self._cycle(0, 0xFF, 1, FEC_T4)
            br, wv, _, ff = post
            if br != 1 or wv != 0 or ff != 0:
                self.bad(name, f"T4 beat_vld=0 stall[{i}] after hi",
                         "beat_ready=1 win_vld=0 fec_fail=0 (no unwrap)",
                         f"beat_ready={br} win_vld={wv} fec_fail={ff}",
                         "u_u.have_hi")
                phase.drop_objection(self)
                return
        post = await self._take_beat(
            name, "T4 stall lo", lo, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T4 valid CW (inc + golden parity)",
                br, wv, wd, ff, W0, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "T4 W0", FEC_T4):
            phase.drop_objection(self)
            return

        # All-zero valid CW: systematic parity 0, window 0.
        post = await self._feed_cw(
            name, "T4 zeros", CW_ZERO, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T4 all-zero CW (parity 0)",
                br, wv, wd, ff, 0, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "T4 zeros", FEC_T4):
            phase.drop_objection(self)
            return

        # Second valid CW after drain (no leftover hi / fail).
        post = await self._feed_cw(
            name, "T4 second", CW1, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T4 second CW after drain (A5/5A)",
                br, wv, wd, ff, W1, 0):
            phase.drop_objection(self)
            return
        if (int(wd) & MASK960) == W0:
            self.bad(name, "T4 second CW distinct from first",
                     "no leftover W0 window",
                     _win_msg(wd),
                     "u_u.hi")
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "T4 second", FEC_T4):
            phase.drop_objection(self)
            return

        # Garbage CW: fec_fail pulse, no 960 forwarded (pairing stays on grid).
        bad_syms = list(codeword(_msg_inc()))
        bad_syms[17] ^= 0x01
        if golden_fec_fail(bad_syms) != 1:
            self.bad(name, "golden flip msg[17] is detectable",
                     "fec_fail=1",
                     "0",
                     "golden")
            phase.drop_objection(self)
            return
        cw_bad = pack_cw(bad_syms)
        post = await self._feed_cw(
            name, "T4 bad", cw_bad, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if ff != 1:
            self.bad(name, "T4 flipped msg[17] (err, no forward)",
                     "fec_fail=1 win_vld=0",
                     f"fec_fail={ff} win_vld={wv}",
                     "u_u.fec_fail")
            phase.drop_objection(self)
            return
        if wv == 1:
            self.bad(name, "T4 flipped msg[17] must not become a 960",
                     "win_vld=0",
                     f"win_vld=1 {_win_msg(wd)}",
                     "u_u.win_vld")
            phase.drop_objection(self)
            return
        if br != 1:
            self.bad(name, "T4 bad CW leaves ingress free",
                     "beat_ready=1 (no parked window)",
                     f"beat_ready={br}",
                     "u_u.beat_ready")
            phase.drop_objection(self)
            return
        # fec_fail is a 1-cycle pulse.
        pre, post = await self._cycle(0, 0, 1, FEC_T4)
        br, wv, _, ff = post
        if ff != 0 or wv != 0 or br != 1:
            self.bad(name, "cycle after T4 fec_fail pulse",
                     "fec_fail=0 win_vld=0 beat_ready=1",
                     f"fec_fail={ff} win_vld={wv} beat_ready={br}",
                     "u_u.fec_fail")
            phase.drop_objection(self)
            return

        # After a failed CW, a good CW still unwraps (no leftover syndromes).
        post = await self._feed_cw(
            name, "T4 after fail", CW2, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T4 valid CW after garbage (0x3C)",
                br, wv, wd, ff, W2, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "T4 after fail", FEC_T4):
            phase.drop_objection(self)
            return

        # Flip parity only: fail, still no window (data would have been W0).
        bad_par = list(codeword(_msg_inc()))
        bad_par[120] ^= 0x01
        post = await self._feed_cw(
            name, "T4 bad par", pack_cw(bad_par), FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if ff != 1 or wv != 0:
            self.bad(name, "T4 flipped p7 (err, no forward)",
                     "fec_fail=1 win_vld=0",
                     f"fec_fail={ff} win_vld={wv} {_win_msg(wd)}",
                     "u_u.fec_fail")
            phase.drop_objection(self)
            return
        pre, post = await self._cycle(0, 0, 1, FEC_T4)

        # 4. T=2: mode pin only; same unwrap + fail as T=4.
        post = await self._feed_cw(
            name, "T2 W0", CW0, FEC_T2, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T2 valid CW (same unwrap as T4)",
                br, wv, wd, ff, W0, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "T2 W0", FEC_T2):
            phase.drop_objection(self)
            return
        post = await self._feed_cw(
            name, "T2 bad", cw_bad, FEC_T2, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, _, ff = post
        if ff != 1 or wv != 0:
            self.bad(name, "T2 flipped msg[17] (not bypass)",
                     "fec_fail=1 win_vld=0",
                     f"fec_fail={ff} win_vld={wv}",
                     "u_u.fec_fail / bypass")
            phase.drop_objection(self)
            return

        # 5. am_gap drops leftover have_hi so pairing does not straddle AMCTL.
        hi3, lo3 = cw_beats(CW3)
        post = await self._take_beat(
            name, "am_gap hi", hi3, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        if self._have_hi() == 0:
            self.bad(name, "am_gap setup (half-CW parked)",
                     "have_hi=1",
                     f"have_hi={self._have_hi()}",
                     "u_u.have_hi")
            phase.drop_objection(self)
            return
        pre, post = await self._cycle(0, 0, 1, FEC_T4, am_gap=1)
        hh = self._have_hi()
        br, wv, _, ff = post
        if hh == 1 or wv != 0 or ff != 0:
            self.bad(name, "am_gap pulse drops leftover have_hi",
                     "have_hi=0 win_vld=0 fec_fail=0",
                     f"have_hi={hh} win_vld={wv} fec_fail={ff}",
                     "u_u.have_hi")
            phase.drop_objection(self)
            return
        # Next beat is a new hi, not paired with the dropped leftover.
        post = await self._take_beat(
            name, "am_gap new hi", lo3, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, _, ff = post
        if wv == 1 or ff != 0:
            self.bad(name, "am_gap next beat is a new hi (not a lo)",
                     "win_vld=0 fec_fail=0",
                     f"win_vld={wv} fec_fail={ff}",
                     "u_u.have_hi")
            phase.drop_objection(self)
            return
        pre, post = await self._cycle(0, 0, 1, FEC_T4, am_gap=1)
        if self._have_hi() == 1:
            self.bad(name, "am_gap clears the post-gap parked hi",
                     "have_hi=0",
                     f"have_hi={self._have_hi()}",
                     "u_u.have_hi")
            phase.drop_objection(self)
            return
        # Complete a fresh valid CW after the gap.
        post = await self._feed_cw(
            name, "after am_gap", CW3, FEC_T4, win_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        br, wv, wd, ff = post
        if not self._score_win(
                name, "T4 valid CW after am_gap (walk-1)",
                br, wv, wd, ff, W3, 0):
            phase.drop_objection(self)
            return
        if not await self._ack_win(name, "after am_gap", FEC_T4):
            phase.drop_objection(self)
            return

        # Extra beat_vld after drain must not recapture / emit.
        for i in range(3):
            pre, post = await self._cycle(0, 0x7E, 1, FEC_T4)
            br, wv, _, ff = post
            if br != 1 or wv != 0 or ff != 0:
                self.bad(name, f"idle after drain[{i}]",
                         "beat_ready=1 win_vld=0 fec_fail=0",
                         f"beat_ready={br} win_vld={wv} fec_fail={ff}",
                         "u_u.have_hi")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_rx_fec)
