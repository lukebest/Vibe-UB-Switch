"""Module-level uvm-python TC for Decision-I leaf vibe_bcrc.

Covers reset/idle (crc_word=0, done=0, no spurious pulse), AS §12
CRC30 encode vs golden (init all-1, no invert, LSB-first 160b eat),
ERROR_FLAG / reserved packing, check (DUT word vs golden residue),
start restart (wins over in_vld), in_vld stall without a step, last
without in_vld, and a second block after done.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/dll/vibe_bcrc.sv: async-low rst_n, start reloads
{30{1'b1}} and wins the if/else over in_vld, in_vld walks 160 bits
LSB-first through crc30_step (VIBE_BCRC_POLY), last packs
crc_word={1'b0, error_flag, t} and pulses done one cycle. Unit helper
(TB u_bcrc); vibe_dll_tx inlines the same CRC30. Stock Icarus
tc_bcrc_crc30 remains the official bit31/bit30 scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# vibe_ub_params.vh VIBE_BCRC_POLY — AS-0.1 §12
# x^30+x^28+x^26+x^24+x^23+x^21+x^19+x^16+x^14+x^11+x^9+x^7+x^6+x^4+x^2+1
VIBE_BCRC_POLY = 0x15A94AD5
CRC_W = 30
CRC_INIT = (1 << CRC_W) - 1
MASK30 = CRC_INIT
MASK32 = (1 << 32) - 1
MASK160 = (1 << 160) - 1
HIER = "u_u.crc / u_u.crc_word / u_u.done"

# Stock Icarus tc_bcrc_crc30 one-flit vector (high 80b are 0).
STOCK_A5 = 0xA5A5A5A5A5A5A5A5A5A5
FLIT_ZERO = 0
FLIT_ONE = 1
FLIT_WALK0 = 1
FLIT_WALK159 = 1 << 159
FLIT_WIDE = 0x0123456789ABCDEF0123456789ABCDEF01234567


def crc30_step(c: int, b: int) -> int:
    """One product step: {c[28:0], 1'b0} ^ ({30{c[29]^b}} & POLY)."""
    fb = ((c >> 29) & 1) ^ (b & 1)
    shl = (c << 1) & MASK30
    return shl ^ (VIBE_BCRC_POLY if fb else 0)


def crc30_flit(c: int, flit: int) -> int:
    """Eat 160 flit bits LSB-first (stock for i = 0; i < 160)."""
    t = int(c) & MASK30
    f = int(flit) & MASK160
    for i in range(160):
        t = crc30_step(t, (f >> i) & 1)
    return t


def crc30_block(flits) -> int:
    """CRC30 over a flit list from all-1 init. No invert."""
    t = CRC_INIT
    for flit in flits:
        t = crc30_flit(t, flit)
    return t


def pack_crc_word(crc30: int, error_flag: int) -> int:
    """Product concat: {1'b0, error_flag, crc[29:0]}."""
    return ((int(error_flag) & 1) << 30) | (int(crc30) & MASK30)


def check_crc_word(word: int, flits, error_flag: int) -> bool:
    """RX-style check: reserved / ERROR_FLAG / CRC30 vs golden."""
    exp = pack_crc_word(crc30_block(flits), error_flag)
    return (int(word) & MASK32) == exp


def _hex32(v) -> str:
    if v is None:
        return "x"
    return f"0x{int(v) & MASK32:08x}"


def _hex160(v) -> str:
    if v is None:
        return "x"
    return f"0x{int(v) & MASK160:040x}"


class tc_vibe_bcrc(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.last, 0)
        sset(d.error_flag, 0)
        sset(d.in_flit, 0)

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
            ival(d.done, -1),
            ival(d.crc_word, -1),
        )

    async def _cycle(self, start=0, in_vld=0, last=0, error_flag=0, in_flit=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.start, 1 if start else 0)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.last, 1 if last else 0)
        sset(d.error_flag, 1 if error_flag else 0)
        sset(d.in_flit, int(in_flit) & MASK160)
        await self._to_fall()
        return self._sample()

    async def _start_crc(self):
        """Pulse start; leave in_vld=0 so start if/else does not share an eat."""
        dn, word = await self._cycle(start=1, in_vld=0)
        sset(self.dut.start, 0)
        return dn, word

    async def _feed(self, flits, error_flag=0, stall_at=None, stall_n=0):
        """Eat every flit. last=1 on the final one. Optional in_vld=0 stall.

        Returns (n_accepted, last_sample, done_seen_on_last, err_or_None).
        """
        accepted = 0
        last_s = self._sample()
        done_on_last = False
        n = len(flits)
        held_word = last_s[1]
        for i, flit in enumerate(flits):
            if stall_at is not None and i == stall_at:
                for k in range(stall_n):
                    dn, word = await self._cycle(0, 0, 0, error_flag, 0xFF)
                    if dn != 0 or word != held_word:
                        return accepted, (dn, word), False, (
                            f"stall[{k}] after {accepted} flits",
                            f"done=0 crc_word={_hex32(held_word)}",
                            f"done={dn} crc_word={_hex32(word)}",
                        )
                    last_s = (dn, word)
            is_last = i == n - 1
            dn, word = await self._cycle(
                0, 1, 1 if is_last else 0, error_flag, flit)
            accepted += 1
            last_s = (dn, word)
            held_word = word
            if dn == 1:
                done_on_last = True
        return accepted, last_s, done_on_last, None

    def _score_done(self, name, stim, dn, word, flits, error_flag):
        exp = pack_crc_word(crc30_block(flits), error_flag)
        if dn != 1:
            self.bad(name, stim,
                     f"done=1 crc_word={_hex32(exp)}",
                     f"done={dn} crc_word={_hex32(word)}",
                     HIER)
            return False
        if word is None or (int(word) & MASK32) != exp:
            self.bad(name, stim + " (encode vs golden CRC30)",
                     f"crc_word={_hex32(exp)}",
                     f"crc_word={_hex32(word)}",
                     "u_u.crc_word")
            return False
        if not check_crc_word(word, flits, error_flag):
            self.bad(name, stim + " (check vs golden residue)",
                     f"bit31=0 bit30={error_flag} crc30={crc30_block(flits):08x}",
                     _hex32(word),
                     "u_u.crc_word")
            return False
        if ((int(word) >> 31) & 1) != 0:
            self.bad(name, stim + " (bit31 reserved)",
                     "bit31=0",
                     _hex32(word),
                     "u_u.crc_word")
            return False
        if ((int(word) >> 30) & 1) != (int(error_flag) & 1):
            self.bad(name, stim + " (bit30 ERROR_FLAG)",
                     f"bit30={int(error_flag) & 1}",
                     _hex32(word),
                     "u_u.crc_word")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_bcrc"

        exp_a5_ef1 = pack_crc_word(crc30_block([STOCK_A5]), 1)
        exp_a5_ef0 = pack_crc_word(crc30_block([STOCK_A5]), 0)
        exp_one = pack_crc_word(crc30_block([FLIT_ONE]), 0)
        exp_wide = pack_crc_word(crc30_block([FLIT_WIDE]), 0)
        exp_multi = pack_crc_word(crc30_block([FLIT_WIDE, STOCK_A5, FLIT_ONE]), 1)
        exp_walk0 = pack_crc_word(crc30_block([FLIT_WALK0]), 0)
        exp_walk159 = pack_crc_word(crc30_block([FLIT_WALK159]), 0)
        if exp_a5_ef1 == exp_a5_ef0:
            self.bad(name, "golden ERROR_FLAG uniqueness (same CRC30)",
                     "bit30 differs",
                     f"ef1={_hex32(exp_a5_ef1)} ef0={_hex32(exp_a5_ef0)}",
                     "golden")
            phase.drop_objection(self)
            return
        if (exp_a5_ef1 & MASK30) != (exp_a5_ef0 & MASK30):
            self.bad(name, "golden CRC30 independent of ERROR_FLAG",
                     "low 30 bits match",
                     f"ef1={_hex32(exp_a5_ef1)} ef0={_hex32(exp_a5_ef0)}",
                     "golden")
            phase.drop_objection(self)
            return
        if exp_a5_ef0 == 0 or exp_one == exp_a5_ef0 or exp_wide == exp_one:
            self.bad(name, "golden uniqueness (A5 / 1 / wide)",
                     "distinct nonzero CRC words",
                     f"a5={_hex32(exp_a5_ef0)} one={_hex32(exp_one)} "
                     f"wide={_hex32(exp_wide)}",
                     "golden")
            phase.drop_objection(self)
            return
        if exp_walk0 == exp_walk159 or exp_walk0 == 0 or exp_walk159 == 0:
            self.bad(name, "golden walk-1 first vs last bit",
                     "two distinct nonzero CRC words",
                     f"b0={_hex32(exp_walk0)} b159={_hex32(exp_walk159)}",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, no done, zero crc_word.
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "reset then release, start=0 in_vld=0",
                     "done=0 crc_word=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            dn, word = await self._cycle(0, 0, 1, 1, STOCK_A5)
            if dn != 0 or word != 0:
                self.bad(name, f"idle cycle {i} after reset (last=1, no in_vld)",
                         "done=0 crc_word=0 (no eat)",
                         f"done={dn} crc_word={_hex32(word)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Async rst_n mid-block clears registered CRC / word / done.
        dn, word = await self._start_crc()
        if dn != 0:
            self.bad(name, "start then idle (before async rst)",
                     "done=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        dn, word = await self._cycle(0, 1, 0, 0, FLIT_WIDE)
        if dn != 0:
            self.bad(name, "one flit before async rst (no last)",
                     "done=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "async rst_n=0 mid-encode (100ps, no posedge)",
                     "done=0 crc_word=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.crc")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "after async re-reset release, idle",
                     "done=0 crc_word=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Encode / check: stock A5 + error_flag=1 (Icarus vector).
        dn, _ = await self._start_crc()
        if dn != 0:
            self.bad(name, "start before stock A5 encode",
                     "done=0", f"done={dn}", "u_u.done")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_A5], error_flag=1)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock 160'hA5A5… last error_flag=1",
                dn, word, [STOCK_A5], 1):
            if n != 1 or not done_last:
                self.bad(name, "stock A5 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last} "
                         f"crc_word={_hex32(word)}",
                         HIER)
            phase.drop_objection(self)
            return
        # done is a 1-cycle pulse; crc_word holds.
        held = word
        dn, word = await self._cycle(0, 0, 0, 0, 0)
        if dn != 0 or word != held:
            self.bad(name, "cycle after stock A5 done pulse",
                     f"done=0 crc_word stays {_hex32(held)}",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return

        # Same CRC30, error_flag=0: only bit30 clears.
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed([STOCK_A5], error_flag=0)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock A5 last error_flag=0",
                dn, word, [STOCK_A5], 0):
            if n != 1 or not done_last:
                self.bad(name, "stock A5 ef0 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return
        if (int(word) ^ int(held)) != (1 << 30):
            self.bad(name, "ERROR_FLAG toggle vs prior A5 word",
                     f"xor == bit30 ({_hex32(1 << 30)})",
                     f"ef1={_hex32(held)} ef0={_hex32(word)} "
                     f"xor={_hex32(int(word) ^ int(held))}",
                     "u_u.crc_word")
            phase.drop_objection(self)
            return

        # Single-flit walk / wide / 160'h1 vs golden.
        for label, flits, eflag, exp in (
                ("160'h1 error_flag=0", [FLIT_ONE], 0, exp_one),
                ("wide flit error_flag=0", [FLIT_WIDE], 0, exp_wide),
                ("walk-1 bit0", [FLIT_WALK0], 0, exp_walk0),
                ("walk-1 bit159", [FLIT_WALK159], 0, exp_walk159),
                ("3-flit last error_flag=1",
                 [FLIT_WIDE, STOCK_A5, FLIT_ONE], 1, exp_multi),
                ):
            dn, _ = await self._start_crc()
            n, last_s, done_last, err = await self._feed(flits, error_flag=eflag)
            if err:
                stim, e, act = err
                self.bad(name, stim, e, act, HIER)
                phase.drop_objection(self)
                return
            dn, word = last_s
            if (n != len(flits) or not done_last
                    or not self._score_done(name, label, dn, word, flits, eflag)
                    or (int(word) & MASK32) != exp):
                if n != len(flits) or not done_last:
                    self.bad(name, f"{label} count",
                             f"exactly {len(flits)} accepts, done on last",
                             f"n={n} done_on_last={done_last} "
                             f"crc_word={_hex32(word)} exp={_hex32(exp)}",
                             HIER)
                phase.drop_objection(self)
                return

        # 3. Stimulus / score: in_vld=0 stall does not eat; resume matches.
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed(
            [FLIT_WIDE, STOCK_A5, FLIT_ONE], error_flag=1,
            stall_at=1, stall_n=3)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, "u_u.crc")
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 3 or not done_last or not self._score_done(
                name, "3-flit with in_vld=0 stall before flit 1",
                dn, word, [FLIT_WIDE, STOCK_A5, FLIT_ONE], 1):
            if n != 3 or not done_last:
                self.bad(name, "stalled 3-flit encode count",
                         "exactly 3 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start mid-stream restarts (if/else priority; leftover CRC dropped).
        dn, _ = await self._start_crc()
        dn, word = await self._cycle(0, 1, 0, 0, FLIT_WIDE)
        if dn != 0:
            self.bad(name, "partial wide before mid-start",
                     "done=0 (not last)",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        dn, word = await self._start_crc()
        if dn != 0:
            self.bad(name, "start mid-stream (reloads all-1)",
                     "done=0",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.crc")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_A5], error_flag=1)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock A5 after mid-stream start (no leftover wide)",
                dn, word, [STOCK_A5], 1):
            if n != 1 or not done_last:
                self.bad(name, "mid-start A5 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start && in_vld same cycle: start wins, that flit is not eaten.
        dn, word = await self._cycle(start=1, in_vld=1, last=1,
                                     error_flag=1, in_flit=FLIT_WIDE)
        if dn != 0:
            self.bad(name, "start&&in_vld&&last same cycle (start wins, no eat)",
                     "done=0 (no last-eat)",
                     f"done={dn} crc_word={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_A5], error_flag=1)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock A5 after start&&in_vld=wide (flit ignored)",
                dn, word, [STOCK_A5], 1):
            if n != 1 or not done_last:
                self.bad(name, "start-wins encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Second block after done (no leftover CRC).
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed(
            [FLIT_ZERO, FLIT_ONE], error_flag=0)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 2 or not done_last or not self._score_done(
                name, "second block after done (0 then 160'h1)",
                dn, word, [FLIT_ZERO, FLIT_ONE], 0):
            if n != 2 or not done_last:
                self.bad(name, "second-block encode count",
                         "exactly 2 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Extra in_vld after done still eats (no busy). Must start first.
        # Hold: in_vld=0 after done must not re-pulse or change the word.
        held = word
        for i in range(3):
            dn, word = await self._cycle(0, 0, 1, 1, STOCK_A5)
            if dn != 0 or word != held:
                self.bad(name, f"in_vld=0 after done[{i}] (last=1 ignored)",
                         f"done=0 crc_word stays {_hex32(held)}",
                         f"done={dn} crc_word={_hex32(word)}",
                         "u_u.done")
                phase.drop_objection(self)
                return

        # Re-check: encode the stock vector again; word must match first.
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed([STOCK_A5], error_flag=1)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if (n != 1 or not done_last
                or not self._score_done(
                    name, "re-encode stock A5 error_flag=1 (check match)",
                    dn, word, [STOCK_A5], 1)
                or (int(word) & MASK32) != exp_a5_ef1):
            if n != 1 or not done_last:
                self.bad(name, "re-encode stock A5 count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_bcrc)
