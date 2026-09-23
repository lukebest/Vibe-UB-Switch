"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_fec.

Covers reset/idle (win_ready=1, cw_vld=0, no spurious CW), two-window
align in bypass ({w0,64'd0} then {w1,64'd0}), T=4 / T=2 encode wrap
(dual RS(128,120) vs golden GF(256) LFSR, same 8 parity symbols),
cw_ready backpressure without drop/dup, win_vld stall after the first
window without an emit, win_ready=!have1 until both CWs drain, and a
second pair after drain. Not a full-chip consecutive-green gate. Not
1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_tx_fec.sv: async-low rst_n, combo
win_ready=!have1, bypass=(fec_mode==VIBE_FEC_BYPASS), collect w0 then
w1, encode starts both vibe_rs128_120_enc on the second window,
cwa={w0,par_a} / cwb={w1,par_b}, emit cwa then cwb. Used by
vibe_pcs_tx u_fec. Sits on stage-11 enc + stage-16 pack. Stock Icarus
tc_pcs_fec_* remain the official wrap scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import hier, ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest
from vibe_uvm.tests.unit_rs128_120_enc import (
    MSG_N,
    golden_parity,
    _msg_a5,
    _msg_const,
    _msg_inc,
    _msg_walk,
)

FEC_BYPASS = 0
FEC_T2 = 1
FEC_T4 = 2
MASK64 = (1 << 64) - 1
MASK960 = (1 << 960) - 1
MASK1024 = (1 << 1024) - 1
HIER = "u_u.have1 / u_u.cw_vld / u_u.pair_done"
ENC_TIMEOUT = 200
BYP_TIMEOUT = 16


def pack_window(syms) -> int:
    """MSB-first 960b window: win[959:952] = syms[0] (product slice)."""
    if len(syms) != MSG_N:
        raise ValueError("pack_window expects 120 symbols")
    v = 0
    for s in syms:
        v = (v << 8) | (int(s) & 0xFF)
    return v & MASK960


def window_syms(win: int):
    w = int(win) & MASK960
    return [((w >> (8 * (119 - i))) & 0xFF) for i in range(MSG_N)]


def bypass_cw(win: int) -> int:
    """Bypass still 6-flit align: {win, 64'd0}."""
    return ((int(win) & MASK960) << 64) & MASK1024


def encode_cw(win: int) -> int:
    """Systematic 1024b = 960b message + p7..p0."""
    par = golden_parity(window_syms(win))
    return (((int(win) & MASK960) << 64) | par) & MASK1024


def _hex64(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:016x}"


def _cw_msg(v) -> str:
    if v is None:
        return "x"
    return f"msg=0x{(v >> 64) & MASK960:0240x} par={_hex64(v & MASK64)}"


W0 = pack_window(_msg_inc())
W1 = pack_window(_msg_a5())
W2 = pack_window(_msg_const(0x3C))
W3 = pack_window(_msg_walk(0))
W_ZERO = pack_window(_msg_const(0))


class tc_vibe_pcs_tx_fec(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, fec_mode=FEC_T4, cw_ready=1):
        d = self.dut
        sset(d.fec_mode, fec_mode)
        sset(d.win_vld, 0)
        sset(d.win_data, 0)
        sset(d.cw_ready, 1 if cw_ready else 0)

    async def _hold_reset(self, n=4, fec_mode=FEC_T4, cw_ready=1):
        sset(self.dut.rst_n, 0)
        await self._idle(fec_mode=fec_mode, cw_ready=cw_ready)
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    def _sample(self):
        d = self.dut
        return (
            ival(d.win_ready, -1),
            ival(d.cw_vld, -1),
            ival(d.cw_data, -1),
        )

    def _enc_starts(self):
        try:
            return (
                ival(hier(self.dut, "u_u.enc_a_start"), 0),
                ival(hier(self.dut, "u_u.enc_b_start"), 0),
            )
        except Exception:
            return None, None

    async def _cycle(self, win_vld=0, win_data=0, cw_ready=1, fec_mode=None):
        """Drive on this falling edge; sample combo then NBA after the posedge."""
        d = self.dut
        if fec_mode is not None:
            sset(d.fec_mode, fec_mode)
        sset(d.win_vld, 1 if win_vld else 0)
        sset(d.win_data, int(win_data) & MASK960)
        sset(d.cw_ready, 1 if cw_ready else 0)
        await Timer(100, "PS")
        pre = self._sample()
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        post = self._sample()
        await FallingEdge(d.clk)
        return pre, post

    async def _take_window(self, name, label, win, fec_mode, cw_ready=1):
        """Hold win_vld until combo win_ready takes the window."""
        for spin in range(32):
            pre, post = await self._cycle(1, win, cw_ready, fec_mode)
            wr, cv, _ = pre
            if wr == 1:
                return post
            if cv == 1 and cw_ready:
                continue
            if self.fail_n:
                return None
        self.bad(name, f"{label} take window",
                 "win_ready=1 (combo !have1)",
                 "win_ready stayed 0",
                 "u_u.win_ready")
        return None

    async def _collect_cws(self, name, label, n, fec_mode, timeout,
                           cw_ready=1):
        """Consume n cw_vld&&cw_ready handshakes. Returns list or None."""
        got = []
        for i in range(timeout):
            pre, post = await self._cycle(0, 0, cw_ready, fec_mode)
            wr, cv, cd = pre
            if cv == 1 and cw_ready:
                if cd is None:
                    self.bad(name, f"{label} cw[{len(got)}] unresolved",
                             "cw_data resolved",
                             "x",
                             "u_u.cw_data")
                    return None
                got.append(int(cd) & MASK1024)
                if len(got) == n:
                    return got
            if self.fail_n:
                return None
            _ = (wr, post)
        self.bad(name, f"{label} collect {n} CWs",
                 f"{n} cw_vld&&cw_ready",
                 f"{len(got)}",
                 HIER)
        return None

    def _score_pair(self, name, stim, got, exp0, exp1):
        if got is None:
            return False
        if len(got) != 2:
            self.bad(name, stim,
                     "exactly two 1024b CWs",
                     f"n={len(got)}",
                     HIER)
            return False
        if got[0] != exp0:
            self.bad(name, stim + " (first CW / w0)",
                     _cw_msg(exp0),
                     _cw_msg(got[0]),
                     "u_u.cw_data / cwa")
            return False
        if got[1] != exp1:
            self.bad(name, stim + " (second CW / w1)",
                     _cw_msg(exp1),
                     _cw_msg(got[1]),
                     "u_u.cw_data / cwb")
            return False
        return True

    async def _pair(self, name, label, w_a, w_b, fec_mode, timeout,
                    cw_ready=1):
        post0 = await self._take_window(
            name, f"{label} w0", w_a, fec_mode, cw_ready=cw_ready)
        if post0 is None:
            return None
        wr0, cv0, _ = post0
        if wr0 != 1:
            self.bad(name, f"{label} after first window",
                     "win_ready=1 (have1 still 0)",
                     f"win_ready={wr0} cw_vld={cv0}",
                     "u_u.have1")
            return None
        if cv0 == 1:
            self.bad(name, f"{label} after first window (no emit yet)",
                     "cw_vld=0 (two-window align)",
                     f"cw_vld={cv0}",
                     "u_u.cw_vld")
            return None
        post1 = await self._take_window(
            name, f"{label} w1", w_b, fec_mode, cw_ready=cw_ready)
        if post1 is None:
            return None
        wr1, _, _ = post1
        if wr1 != 0:
            self.bad(name, f"{label} after second window",
                     "win_ready=0 (have1=1)",
                     f"win_ready={wr1}",
                     "u_u.have1")
            return None
        return await self._collect_cws(
            name, label, 2, fec_mode, timeout, cw_ready=cw_ready)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_fec"

        exp_enc_0 = encode_cw(W0)
        exp_enc_1 = encode_cw(W1)
        exp_enc_2 = encode_cw(W2)
        exp_enc_3 = encode_cw(W3)
        exp_byp_0 = bypass_cw(W0)
        exp_byp_1 = bypass_cw(W1)
        exp_zero = encode_cw(W_ZERO)
        if exp_enc_0 == exp_enc_1 or (exp_enc_0 & MASK64) == 0:
            self.bad(name, "golden W0 vs W1 uniqueness",
                     "distinct CWs, W0 parity != 0",
                     f"p0={_hex64(exp_enc_0 & MASK64)} "
                     f"p1={_hex64(exp_enc_1 & MASK64)}",
                     "golden")
            phase.drop_objection(self)
            return
        if exp_zero != bypass_cw(W_ZERO) or (exp_zero & MASK64) != 0:
            self.bad(name, "all-zero encode golden is zero parity",
                     f"par=0 cw={_cw_msg(bypass_cw(W_ZERO))}",
                     _cw_msg(exp_zero),
                     "golden")
            phase.drop_objection(self)
            return
        if window_syms(W0) != _msg_inc() or window_syms(W1) != _msg_a5():
            self.bad(name, "window pack/unpack round-trip",
                     "syms match",
                     "mismatch",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset(fec_mode=FEC_T4)
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: ready, no CW, no leftover encode.
        wr, cv, cd = self._sample()
        if wr != 1 or cv != 0 or cd != 0:
            self.bad(name, "reset then release, win_vld=0 cw_ready=1",
                     "win_ready=1 cw_vld=0 cw_data=0",
                     f"win_ready={wr} cw_vld={cv} {_cw_msg(cd)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            pre, post = await self._cycle(0, 0xA5, 1, FEC_T4)
            wr, cv, cd = post
            if wr != 1 or cv != 0 or cd != 0:
                self.bad(name, f"idle cycle {i} after reset (win_vld=0)",
                         "win_ready=1 cw_vld=0 cw_data=0",
                         f"win_ready={wr} cw_vld={cv} {_cw_msg(cd)}",
                         HIER)
                phase.drop_objection(self)
                return

        # One window is not enough to start encode / emit.
        post = await self._take_window(
            name, "lone window", W0, FEC_T4, cw_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        for i in range(6):
            pre, post = await self._cycle(0, 0, 1, FEC_T4)
            wr, cv, cd = post
            sa, sb = self._enc_starts()
            if wr != 1 or cv != 0:
                self.bad(name, f"lone window hold[{i}] (need w1)",
                         "win_ready=1 cw_vld=0",
                         f"win_ready={wr} cw_vld={cv}",
                         "u_u.have0")
                phase.drop_objection(self)
                return
            if sa == 1 or sb == 1:
                self.bad(name, f"lone window hold[{i}] (no dual start)",
                         "enc_a_start=0 enc_b_start=0",
                         f"a={sa} b={sb}",
                         "u_u.enc_a_start")
                phase.drop_objection(self)
                return

        # Async rst_n mid-hold clears have0.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        wr, cv, cd = self._sample()
        if wr != 1 or cv != 0 or cd != 0:
            self.bad(name, "async rst_n=0 after lone window (100ps, no posedge)",
                     "win_ready=1 cw_vld=0 cw_data=0",
                     f"win_ready={wr} cw_vld={cv} {_cw_msg(cd)}",
                     "u_u.w0")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        wr, cv, cd = self._sample()
        if wr != 1 or cv != 0 or cd != 0:
            self.bad(name, "after async re-reset release, idle",
                     "win_ready=1 cw_vld=0 cw_data=0",
                     f"win_ready={wr} cw_vld={cv} {_cw_msg(cd)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Bypass: two windows, 6-flit align, zero parity, emit_b.
        got = await self._pair(
            name, "bypass W0/W1", W0, W1, FEC_BYPASS, BYP_TIMEOUT)
        if not self._score_pair(
                name, "bypass two 960b windows",
                got, exp_byp_0, exp_byp_1):
            phase.drop_objection(self)
            return
        # After consume, slots free.
        pre, post = await self._cycle(0, 0, 1, FEC_BYPASS)
        wr, cv, _ = post
        if wr != 1 or cv != 0:
            self.bad(name, "bypass drain (both CWs accepted)",
                     "win_ready=1 cw_vld=0",
                     f"win_ready={wr} cw_vld={cv}",
                     "u_u.have0 / have1")
            phase.drop_objection(self)
            return

        # Bypass emit_b with cw_ready stall (first CW held, then second).
        post0 = await self._take_window(
            name, "bypass-bp w0", W2, FEC_BYPASS, cw_ready=0)
        post1 = await self._take_window(
            name, "bypass-bp w1", W3, FEC_BYPASS, cw_ready=0)
        if post0 is None or post1 is None:
            phase.drop_objection(self)
            return
        held = None
        for i in range(BYP_TIMEOUT):
            pre, post = await self._cycle(0, 0, 0, FEC_BYPASS)
            wr, cv, cd = post
            if cv == 1:
                held = int(cd) & MASK1024
                break
        if held != bypass_cw(W2):
            self.bad(name, "bypass cw_ready=0 first emit",
                     _cw_msg(bypass_cw(W2)),
                     _cw_msg(held),
                     "u_u.emit_b")
            phase.drop_objection(self)
            return
        # Accept first; hold ready=0 so second stays visible.
        await self._cycle(0, 0, 1, FEC_BYPASS)
        held2 = None
        for i in range(BYP_TIMEOUT):
            pre, post = await self._cycle(0, 0, 0, FEC_BYPASS)
            _, cv, cd = post
            if cv == 1:
                held2 = int(cd) & MASK1024
                break
        if held2 != bypass_cw(W3):
            self.bad(name, "bypass emit_b second CW (cw_ready held 0)",
                     _cw_msg(bypass_cw(W3)),
                     _cw_msg(held2),
                     "u_u.emit_b")
            phase.drop_objection(self)
            return
        await self._cycle(0, 0, 1, FEC_BYPASS)
        pre, post = await self._cycle(0, 0, 1, FEC_BYPASS)
        wr, cv, _ = post
        if wr != 1:
            self.bad(name, "bypass-bp after second accept",
                     "win_ready=1",
                     f"win_ready={wr} cw_vld={cv}",
                     "u_u.have1")
            phase.drop_objection(self)
            return

        # 3. Encode T=4: dual start + golden parity. win_vld stall after w0.
        post = await self._take_window(
            name, "T4 stall w0", W0, FEC_T4, cw_ready=1)
        if post is None:
            phase.drop_objection(self)
            return
        for i in range(3):
            pre, post = await self._cycle(0, 0xFF, 1, FEC_T4)
            wr, cv, _ = post
            if wr != 1 or cv != 0:
                self.bad(name, f"T4 win_vld=0 stall[{i}] after w0",
                         "win_ready=1 cw_vld=0 (no step / no emit)",
                         f"win_ready={wr} cw_vld={cv}",
                         "u_u.have0")
                phase.drop_objection(self)
                return
        post1 = await self._take_window(
            name, "T4 stall w1", W1, FEC_T4, cw_ready=1)
        if post1 is None:
            phase.drop_objection(self)
            return
        sa, sb = self._enc_starts()
        if sa is not None and (sa != 1 or sb != 1):
            self.bad(name, "T4 second window (dual interleave start)",
                     "enc_a_start=1 enc_b_start=1",
                     f"a={sa} b={sb}",
                     "u_u.enc_a_start / enc_b_start")
            phase.drop_objection(self)
            return
        got = await self._collect_cws(
            name, "T4 W0/W1", 2, FEC_T4, ENC_TIMEOUT)
        if not self._score_pair(
                name, "T4 encode two 960b windows (inc + A5/5A)",
                got, exp_enc_0, exp_enc_1):
            phase.drop_objection(self)
            return
        if (got[0] & MASK64) == 0 or (got[1] & MASK64) == 0:
            self.bad(name, "T4 nonzero parity on distinctive windows",
                     "both parities != 0",
                     f"p0={_hex64(got[0] & MASK64)} p1={_hex64(got[1] & MASK64)}",
                     "u_u.u_enc_a.parity")
            phase.drop_objection(self)
            return
        pre, post = await self._cycle(0, 0, 1, FEC_T4)
        wr, cv, _ = post
        if wr != 1 or cv != 0:
            self.bad(name, "T4 drain (both CWs accepted)",
                     "win_ready=1 cw_vld=0",
                     f"win_ready={wr} cw_vld={cv}",
                     "u_u.have0 / have1")
            phase.drop_objection(self)
            return

        # All-zero pair: systematic parity 0, still 1024b emit.
        got = await self._pair(
            name, "T4 zeros", W_ZERO, W_ZERO, FEC_T4, ENC_TIMEOUT)
        if not self._score_pair(
                name, "T4 all-zero windows (parity 0)",
                got, exp_zero, exp_zero):
            phase.drop_objection(self)
            return

        # Second pair after done (no leftover LFSR / have*).
        got = await self._pair(
            name, "T4 second pair", W2, W3, FEC_T4, ENC_TIMEOUT)
        if not self._score_pair(
                name, "T4 second pair after drain (0x3C + walk-1)",
                got, exp_enc_2, exp_enc_3):
            phase.drop_objection(self)
            return
        if got[0] == exp_enc_0 or got[1] == exp_enc_1:
            self.bad(name, "T4 second pair distinct from first",
                     "no leftover W0/W1 CWs",
                     _cw_msg(got[0]),
                     "u_u.w0")
            phase.drop_objection(self)
            return

        # Encode cw_ready stall: first CW held, then emit_b.
        post0 = await self._take_window(
            name, "T4-bp w0", W0, FEC_T4, cw_ready=0)
        post1 = await self._take_window(
            name, "T4-bp w1", W1, FEC_T4, cw_ready=0)
        if post0 is None or post1 is None:
            phase.drop_objection(self)
            return
        held = None
        for i in range(ENC_TIMEOUT):
            pre, post = await self._cycle(0, 0, 0, FEC_T4)
            wr, cv, cd = post
            if wr != 0:
                self.bad(name, f"T4-bp wait[{i}] (slots full)",
                         "win_ready=0",
                         f"win_ready={wr}",
                         "u_u.have1")
                phase.drop_objection(self)
                return
            if cv == 1:
                held = int(cd) & MASK1024
                break
        if held != exp_enc_0:
            self.bad(name, "T4 cw_ready=0 first encode emit",
                     _cw_msg(exp_enc_0),
                     _cw_msg(held),
                     "u_u.cwa")
            phase.drop_objection(self)
            return
        await self._cycle(0, 0, 1, FEC_T4)
        held2 = None
        for i in range(BYP_TIMEOUT):
            pre, post = await self._cycle(0, 0, 0, FEC_T4)
            _, cv, cd = post
            if cv == 1:
                held2 = int(cd) & MASK1024
                break
        if held2 != exp_enc_1:
            self.bad(name, "T4 encode emit_b second CW (cw_ready held 0)",
                     _cw_msg(exp_enc_1),
                     _cw_msg(held2),
                     "u_u.cwb")
            phase.drop_objection(self)
            return
        await self._cycle(0, 0, 1, FEC_T4)
        pre, post = await self._cycle(0, 0, 1, FEC_T4)
        wr, cv, _ = post
        if wr != 1:
            self.bad(name, "T4-bp after second accept",
                     "win_ready=1",
                     f"win_ready={wr} cw_vld={cv}",
                     "u_u.have1")
            phase.drop_objection(self)
            return

        # 4. T=2: mode pin only; same 8 parity symbols + dual start.
        post0 = await self._take_window(
            name, "T2 w0", W0, FEC_T2, cw_ready=1)
        post1 = await self._take_window(
            name, "T2 w1", W1, FEC_T2, cw_ready=1)
        if post0 is None or post1 is None:
            phase.drop_objection(self)
            return
        sa, sb = self._enc_starts()
        if sa is not None and (sa != 1 or sb != 1):
            self.bad(name, "T2 second window (not bypass)",
                     "enc_a_start=1 enc_b_start=1",
                     f"a={sa} b={sb}",
                     "u_u.enc_a_start / enc_b_start / bypass")
            phase.drop_objection(self)
            return
        got = await self._collect_cws(
            name, "T2 W0/W1", 2, FEC_T2, ENC_TIMEOUT)
        if not self._score_pair(
                name, "T2 encode (same parity as T4)",
                got, exp_enc_0, exp_enc_1):
            phase.drop_objection(self)
            return

        # Extra win_vld after drain must not recapture / emit.
        for i in range(3):
            pre, post = await self._cycle(0, 0x7E, 1, FEC_T2)
            wr, cv, _ = post
            if wr != 1 or cv != 0:
                self.bad(name, f"idle after T2[{i}]",
                         "win_ready=1 cw_vld=0",
                         f"win_ready={wr} cw_vld={cv}",
                         "u_u.have0")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_fec)
