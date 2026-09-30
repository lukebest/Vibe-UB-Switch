"""Module-level uvm-python TC for Decision-I leaf vibe_icrc.

Covers reset/idle (crc_out=0, done=0, no spurious pulse), AS §13
CRC32 encode vs golden (init all-1, per-byte bit reverse then
reverse+invert), start restart (wins over in_vld), in_vld stall
without a step, last without in_vld, and a second block after done.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/nw/vibe_icrc.sv: async-low rst_n, start reloads
32'hFFFF_FFFF and wins the if/else over in_vld, in_vld walks
vibe_rev8(in_byte) MSB-first through step8 (VIBE_ICRC_POLY), last
packs crc_out=~vibe_rev32(step8(crc, in_byte)) and pulses done one
cycle. Unit helper (TB u_icrc); intended for cna_ep (sender/receiver).
Transit has no ICRC unit. Stock Icarus tc_icrc_txrx_vs_transit remains
the official unit-responds scorer. This is not the wrap-style
tc_icrc_txrx_vs_transit (direct vibe_icrc top). ovf_l (F1) is not
in this module.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# vibe_ub_params.vh VIBE_ICRC_POLY — AS-0.1 §13
# x^32+x^26+x^23+x^22+x^16+x^12+x^11+x^10+x^8+x^7+x^5+x^4+x^2+x+1
VIBE_ICRC_POLY = 0x04C11DB7
CRC_W = 32
CRC_INIT = (1 << CRC_W) - 1
MASK8 = 0xFF
MASK32 = CRC_INIT
HIER = "u_u.crc / u_u.crc_out / u_u.done"

# Stock Icarus tc_icrc_txrx_vs_transit vectors.
STOCK_00 = 0x00
STOCK_11_22_33 = (0x11, 0x22, 0x33)
BYTE_FF = 0xFF
BYTE_01 = 0x01
BYTE_A5 = 0xA5
CLASSIC_123456789 = tuple(b"123456789")
WALK0 = 0x01
WALK7 = 0x80
WIDE16 = tuple(range(16))


def vibe_rev8(b: int) -> int:
    """Stock vibe_rev8: result[i] = x[7-i]."""
    x = int(b) & MASK8
    r = 0
    for i in range(8):
        if (x >> i) & 1:
            r |= 1 << (7 - i)
    return r


def vibe_rev32(x: int) -> int:
    """Stock vibe_rev32: result[i] = x[31-i]."""
    t = int(x) & MASK32
    r = 0
    for i in range(32):
        if (t >> i) & 1:
            r |= 1 << (31 - i)
    return r


def crc32_step(c: int, b: int) -> int:
    """One product step: {c[30:0], 1'b0} ^ ({32{c[31]^b}} & POLY)."""
    fb = ((c >> 31) & 1) ^ (b & 1)
    shl = (c << 1) & MASK32
    return shl ^ (VIBE_ICRC_POLY if fb else 0)


def step8(c: int, b: int) -> int:
    """Eat vibe_rev8(b) MSB-first (stock for k = 0; k < 8)."""
    br = vibe_rev8(b)
    t = int(c) & MASK32
    for k in range(8):
        t = crc32_step(t, (br >> (7 - k)) & 1)
    return t


def icrc_block(data) -> int:
    """CRC32 over a byte list from all-1 init. Reverse+invert on last."""
    t = CRC_INIT
    for b in data:
        t = step8(t, int(b) & MASK8)
    return (~vibe_rev32(t)) & MASK32


def _hex32(v) -> str:
    if v is None:
        return "x"
    return f"0x{int(v) & MASK32:08x}"


class tc_vibe_icrc(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.last, 0)
        sset(d.in_byte, 0)

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
            ival(d.crc_out, -1),
        )

    async def _cycle(self, start=0, in_vld=0, last=0, in_byte=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.start, 1 if start else 0)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.last, 1 if last else 0)
        sset(d.in_byte, int(in_byte) & MASK8)
        await self._to_fall()
        return self._sample()

    async def _start_crc(self):
        """Pulse start; leave in_vld=0 so start if/else does not share an eat."""
        dn, word = await self._cycle(start=1, in_vld=0)
        sset(self.dut.start, 0)
        return dn, word

    async def _feed(self, data, stall_at=None, stall_n=0):
        """Eat every byte. last=1 on the final one. Optional in_vld=0 stall.

        Returns (n_accepted, last_sample, done_seen_on_last, err_or_None).
        """
        accepted = 0
        last_s = self._sample()
        done_on_last = False
        n = len(data)
        held_word = last_s[1]
        for i, byte in enumerate(data):
            if stall_at is not None and i == stall_at:
                for k in range(stall_n):
                    dn, word = await self._cycle(0, 0, 0, 0xFF)
                    if dn != 0 or word != held_word:
                        return accepted, (dn, word), False, (
                            f"stall[{k}] after {accepted} bytes",
                            f"done=0 crc_out={_hex32(held_word)}",
                            f"done={dn} crc_out={_hex32(word)}",
                        )
                    last_s = (dn, word)
            is_last = i == n - 1
            dn, word = await self._cycle(0, 1, 1 if is_last else 0, byte)
            accepted += 1
            last_s = (dn, word)
            held_word = word
            if dn == 1:
                done_on_last = True
        return accepted, last_s, done_on_last, None

    def _score_done(self, name, stim, dn, word, data):
        exp = icrc_block(data)
        if dn != 1:
            self.bad(name, stim,
                     f"done=1 crc_out={_hex32(exp)}",
                     f"done={dn} crc_out={_hex32(word)}",
                     HIER)
            return False
        if word is None or (int(word) & MASK32) != exp:
            self.bad(name, stim + " (encode vs golden CRC32)",
                     f"crc_out={_hex32(exp)}",
                     f"crc_out={_hex32(word)}",
                     "u_u.crc_out")
            return False
        return True

    def _golden_selfcheck(self, name):
        exp00 = icrc_block([STOCK_00])
        exp_multi = icrc_block(STOCK_11_22_33)
        exp_classic = icrc_block(CLASSIC_123456789)
        exp_ff = icrc_block([BYTE_FF])
        exp_01 = icrc_block([BYTE_01])
        exp_a5 = icrc_block([BYTE_A5])
        exp_walk0 = icrc_block([WALK0])
        exp_walk7 = icrc_block([WALK7])
        exp16 = icrc_block(WIDE16)
        if exp00 == 0 or exp00 == exp_ff or exp00 == exp_01:
            self.bad(name, "golden uniqueness (0x00 / 0xFF / 0x01)",
                     "distinct nonzero CRC words",
                     f"00={_hex32(exp00)} ff={_hex32(exp_ff)} "
                     f"01={_hex32(exp_01)}",
                     "golden")
            return False
        if exp_walk0 == exp_walk7 or exp_walk0 == 0 or exp_walk7 == 0:
            self.bad(name, "golden walk-1 first vs last bit",
                     "two distinct nonzero CRC words",
                     f"b0={_hex32(exp_walk0)} b7={_hex32(exp_walk7)}",
                     "golden")
            return False
        if exp_classic != 0xCBF43926:
            self.bad(name, "golden classic 123456789 (IEEE CRC32)",
                     "0xcbf43926",
                     _hex32(exp_classic),
                     "golden")
            return False
        if exp00 != 0xD202EF8D:
            self.bad(name, "golden stock 0x00 (IEEE CRC32)",
                     "0xd202ef8d",
                     _hex32(exp00),
                     "golden")
            return False
        if exp_multi != 0xFAC73763:
            self.bad(name, "golden stock 11-22-33 (IEEE CRC32)",
                     "0xfac73763",
                     _hex32(exp_multi),
                     "golden")
            return False
        if exp_a5 == exp00 or exp16 == exp_classic:
            self.bad(name, "golden A5 / 16-byte uniqueness",
                     "distinct from stock vectors",
                     f"a5={_hex32(exp_a5)} 16={_hex32(exp16)}",
                     "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_icrc"

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        exp00 = icrc_block([STOCK_00])
        exp_multi = icrc_block(STOCK_11_22_33)
        exp_classic = icrc_block(CLASSIC_123456789)
        exp_ff = icrc_block([BYTE_FF])
        exp_01 = icrc_block([BYTE_01])
        exp_a5 = icrc_block([BYTE_A5])
        exp_walk0 = icrc_block([WALK0])
        exp_walk7 = icrc_block([WALK7])
        exp16 = icrc_block(WIDE16)

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, no done, zero crc_out.
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "reset then release, start=0 in_vld=0",
                     "done=0 crc_out=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            dn, word = await self._cycle(0, 0, 1, STOCK_00)
            if dn != 0 or word != 0:
                self.bad(name, f"idle cycle {i} after reset (last=1, no in_vld)",
                         "done=0 crc_out=0 (no eat)",
                         f"done={dn} crc_out={_hex32(word)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Async rst_n mid-block clears registered CRC / word / done.
        dn, word = await self._start_crc()
        if dn != 0:
            self.bad(name, "start then idle (before async rst)",
                     "done=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        dn, word = await self._cycle(0, 1, 0, BYTE_A5)
        if dn != 0:
            self.bad(name, "one byte before async rst (no last)",
                     "done=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "async rst_n=0 mid-encode (100ps, no posedge)",
                     "done=0 crc_out=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.crc")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        dn, word = self._sample()
        if dn != 0 or word != 0:
            self.bad(name, "after async re-reset release, idle",
                     "done=0 crc_out=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 2. Encode: stock Icarus one byte 0x00 last.
        dn, _ = await self._start_crc()
        if dn != 0:
            self.bad(name, "start before stock 0x00 encode",
                     "done=0", f"done={dn}", "u_u.done")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_00])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock 8'h00 last (Icarus tc_icrc_txrx_vs_transit)",
                dn, word, [STOCK_00]):
            if n != 1 or not done_last:
                self.bad(name, "stock 0x00 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last} "
                         f"crc_out={_hex32(word)}",
                         HIER)
            phase.drop_objection(self)
            return
        if (int(word) & MASK32) != exp00:
            self.bad(name, "stock 0x00 vs IEEE 0xd202ef8d",
                     _hex32(exp00), _hex32(word), "u_u.crc_out")
            phase.drop_objection(self)
            return
        # done is a 1-cycle pulse; crc_out holds.
        held = word
        dn, word = await self._cycle(0, 0, 0, 0)
        if dn != 0 or word != held:
            self.bad(name, "cycle after stock 0x00 done pulse",
                     f"done=0 crc_out stays {_hex32(held)}",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return

        # Stock Icarus multi-byte 0x11, 0x22, 0x33.
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed(STOCK_11_22_33)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 3 or not done_last or not self._score_done(
                name, "stock 8'h11 then 8'h22 then 8'h33 last",
                dn, word, STOCK_11_22_33):
            if n != 3 or not done_last:
                self.bad(name, "stock 11-22-33 encode count",
                         "exactly 3 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return
        if (int(word) & MASK32) != exp_multi:
            self.bad(name, "stock 11-22-33 vs IEEE",
                     _hex32(exp_multi), _hex32(word), "u_u.crc_out")
            phase.drop_objection(self)
            return

        # Single-byte walk / wide / classic IEEE vs golden.
        for label, data, exp in (
                ("8'h01", [BYTE_01], exp_01),
                ("8'hFF", [BYTE_FF], exp_ff),
                ("8'hA5", [BYTE_A5], exp_a5),
                ("walk-1 bit0", [WALK0], exp_walk0),
                ("walk-1 bit7", [WALK7], exp_walk7),
                ("classic 123456789", CLASSIC_123456789, exp_classic),
                ("16-byte 00..0F", WIDE16, exp16),
                ):
            dn, _ = await self._start_crc()
            n, last_s, done_last, err = await self._feed(data)
            if err:
                stim, e, act = err
                self.bad(name, stim, e, act, HIER)
                phase.drop_objection(self)
                return
            dn, word = last_s
            if (n != len(data) or not done_last
                    or not self._score_done(name, label, dn, word, data)
                    or (int(word) & MASK32) != exp):
                if n != len(data) or not done_last:
                    self.bad(name, f"{label} count",
                             f"exactly {len(data)} accepts, done on last",
                             f"n={n} done_on_last={done_last} "
                             f"crc_out={_hex32(word)} exp={_hex32(exp)}",
                             HIER)
                phase.drop_objection(self)
                return

        # 3. Stimulus / score: in_vld=0 stall does not eat; resume matches.
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed(
            STOCK_11_22_33, stall_at=1, stall_n=3)
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, "u_u.crc")
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 3 or not done_last or not self._score_done(
                name, "3-byte with in_vld=0 stall before byte 1",
                dn, word, STOCK_11_22_33):
            if n != 3 or not done_last:
                self.bad(name, "stalled 3-byte encode count",
                         "exactly 3 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start mid-stream restarts (if/else priority; leftover CRC dropped).
        dn, _ = await self._start_crc()
        dn, word = await self._cycle(0, 1, 0, BYTE_A5)
        if dn != 0:
            self.bad(name, "partial A5 before mid-start",
                     "done=0 (not last)",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        dn, word = await self._start_crc()
        if dn != 0:
            self.bad(name, "start mid-stream (reloads all-1)",
                     "done=0",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.crc")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_00])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock 0x00 after mid-stream start (no leftover A5)",
                dn, word, [STOCK_00]):
            if n != 1 or not done_last:
                self.bad(name, "mid-start 0x00 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # start && in_vld same cycle: start wins, that byte is not eaten.
        dn, word = await self._cycle(start=1, in_vld=1, last=1, in_byte=BYTE_A5)
        if dn != 0:
            self.bad(name, "start&&in_vld&&last same cycle (start wins, no eat)",
                     "done=0 (no last-eat)",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.done")
            phase.drop_objection(self)
            return
        n, last_s, done_last, err = await self._feed([STOCK_00])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "stock 0x00 after start&&in_vld=A5 (byte ignored)",
                dn, word, [STOCK_00]):
            if n != 1 or not done_last:
                self.bad(name, "start-wins encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Second block after done (no leftover CRC).
        dn, _ = await self._start_crc()
        n, last_s, done_last, err = await self._feed([0x00, BYTE_01])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 2 or not done_last or not self._score_done(
                name, "second block after done (0x00 then 0x01)",
                dn, word, [0x00, BYTE_01]):
            if n != 2 or not done_last:
                self.bad(name, "second-block encode count",
                         "exactly 2 accepts, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Hold: in_vld=0 after done must not re-pulse or change the word.
        held = word
        for i in range(3):
            dn, word = await self._cycle(0, 0, 1, STOCK_00)
            if dn != 0 or word != held:
                self.bad(name, f"in_vld=0 after done[{i}] (last=1 ignored)",
                         f"done=0 crc_out stays {_hex32(held)}",
                         f"done={dn} crc_out={_hex32(word)}",
                         "u_u.done")
                phase.drop_objection(self)
                return

        # start after done reloads crc but crc_out holds until next last.
        dn, word = await self._start_crc()
        if dn != 0 or word != held:
            self.bad(name, "start after done (crc_out holds)",
                     f"done=0 crc_out stays {_hex32(held)}",
                     f"done={dn} crc_out={_hex32(word)}",
                     "u_u.crc_out")
            phase.drop_objection(self)
            return

        # Re-check: encode the stock vector again; word must match first.
        n, last_s, done_last, err = await self._feed([STOCK_00])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if (n != 1 or not done_last
                or not self._score_done(
                    name, "re-encode stock 0x00 (check match)",
                    dn, word, [STOCK_00])
                or (int(word) & MASK32) != exp00):
            if n != 1 or not done_last:
                self.bad(name, "re-encode stock 0x00 count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        # Reset-init is already all-1s: in_vld+last without a start pulse
        # still encodes (product crc <= 32'hFFFF_FFFF on rst_n).
        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        n, last_s, done_last, err = await self._feed([STOCK_00])
        if err:
            stim, exp, act = err
            self.bad(name, stim, exp, act, HIER)
            phase.drop_objection(self)
            return
        dn, word = last_s
        if n != 1 or not done_last or not self._score_done(
                name, "reset-init all-1s: 0x00 last without start pulse",
                dn, word, [STOCK_00]):
            if n != 1 or not done_last:
                self.bad(name, "no-start 0x00 encode count",
                         "exactly 1 accept, done on last",
                         f"n={n} done_on_last={done_last}",
                         HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_icrc)
