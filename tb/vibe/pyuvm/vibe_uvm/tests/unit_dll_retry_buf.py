"""Module-level uvm-python TC for Decision-I leaf vibe_dll_retry_buf.

Covers reset / port_rst / !link_up pointers+free; proto_err cleared
only on hard rst_n; normal write advances wr_ptr and decrements free;
can_send tracks free vs send_size; Null and Retry writes do not enter;
ack release advances tail/rcv and restores free; overflow
free+rel_size>256 asserts proto_err; rd_ptr_i returns stored flit.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff. Not TP-DLL-004 / full vibe_dll.

Matches product rtl/dll/vibe_dll_retry_buf.sv: async-low rst_n,
depth 256 FS-must, write when wr_en && !is_null && !is_retry &&
can_send, can_send=(freeb>={1'b0,send_size}), ack_rel overflow
sticky proto_err, port_rst/!link_up clear ptrs/free not proto_err,
mem not cleared, last NBA to freeb wins on same-cycle write+release.
Instantiated by vibe_dll u_rbuf. Stock Icarus tc_retry_buf_256
remains the official TP scorer. Header-only vs stock; no invented
protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

DEPTH = 256
MASK8 = 0xFF
MASK9 = 0x1FF
MASK160 = (1 << 160) - 1
HIER = "u_u.wrp / u_u.tail / u_u.rcv / u_u.freeb / u_u.proto_err"


class Golden:
    """Cycle-accurate ptrs / free / proto_err / mem vs product NBA."""

    def __init__(self):
        self.mem = {}
        self.hard_reset()

    def hard_reset(self):
        self.wrp = 0
        self.tail = 0
        self.rcv = 0
        self.freeb = DEPTH
        self.proto_err = 0

    def port_clear(self):
        self.wrp = 0
        self.tail = 0
        self.rcv = 0
        self.freeb = DEPTH

    def can_send(self, send_size):
        return int(self.freeb >= (int(send_size) & MASK8))

    def rd_flit(self, rd_ptr_i):
        return self.mem.get(int(rd_ptr_i) & MASK8)

    def step(self, rst_n=1, port_rst=0, link_up=1, wr_en=0, is_null=0,
             is_retry=0, wr_flit=0, send_size=1, ack_rel=0, rel_size=0):
        if not rst_n:
            self.hard_reset()
            return
        if port_rst or not link_up:
            self.port_clear()
            return
        old_free = self.freeb
        do_wr = (bool(wr_en) and not bool(is_null) and not bool(is_retry)
                 and bool(self.can_send(send_size)))
        if do_wr:
            self.mem[self.wrp] = int(wr_flit) & MASK160
            self.wrp = (self.wrp + 1) & MASK8
            self.freeb = (old_free - 1) & MASK9
        if ack_rel:
            rel = int(rel_size) & MASK8
            if old_free + rel > DEPTH:
                self.proto_err = 1
            else:
                self.freeb = (old_free + rel) & MASK9
                self.tail = (self.tail + rel) & MASK8
                self.rcv = (self.rcv + rel) & MASK8

    def combo(self, send_size=1, rd_ptr_i=0):
        return (
            self.wrp & MASK8,
            self.tail & MASK8,
            self.rcv & MASK8,
            self.freeb & MASK9,
            int(self.proto_err),
            self.can_send(send_size),
            self.rd_flit(rd_ptr_i),
        )


class tc_vibe_dll_retry_buf(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, send_size=1, rd_ptr_i=0):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.wr_en, 0)
        sset(d.is_null, 0)
        sset(d.is_retry, 0)
        sset(d.wr_flit, 0)
        sset(d.send_size, int(send_size) & MASK8)
        sset(d.ack_rel, 0)
        sset(d.rel_size, 0)
        sset(d.rd_ptr_i, int(rd_ptr_i) & MASK8)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        self.g.hard_reset()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    def _sample(self, send_size=1, rd_ptr_i=0):
        d = self.dut
        return (
            ival(d.wr_ptr, -1) & MASK8,
            ival(d.tail_ptr, -1) & MASK8,
            ival(d.rcv_ptr, -1) & MASK8,
            ival(d.num_free, -1) & MASK9,
            ival(d.proto_err, -1),
            ival(d.can_send, -1),
            ival(d.rd_flit, None),
            int(send_size) & MASK8,
            int(rd_ptr_i) & MASK8,
        )

    def _fmt(self, s):
        wr, tail, rcv, free, err, cs, rd, send_size, rd_ptr = s
        rd_s = "X" if rd is None else hex(rd)
        return (
            f"wr={wr} tail={tail} rcv={rcv} free={free} proto_err={err} "
            f"can_send={cs} rd_flit={rd_s} send_size={send_size} "
            f"rd_ptr_i={rd_ptr}"
        )

    async def _cycle(self, port_rst=0, link_up=1, wr_en=0, is_null=0,
                     is_retry=0, wr_flit=0, send_size=1, ack_rel=0,
                     rel_size=0, rd_ptr_i=0, rst_n=1):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.wr_en, 1 if wr_en else 0)
        sset(d.is_null, 1 if is_null else 0)
        sset(d.is_retry, 1 if is_retry else 0)
        sset(d.wr_flit, int(wr_flit) & MASK160)
        sset(d.send_size, int(send_size) & MASK8)
        sset(d.ack_rel, 1 if ack_rel else 0)
        sset(d.rel_size, int(rel_size) & MASK8)
        sset(d.rd_ptr_i, int(rd_ptr_i) & MASK8)
        sset(d.rst_n, 1 if rst_n else 0)
        self.g.step(
            rst_n=rst_n, port_rst=port_rst, link_up=link_up,
            wr_en=wr_en, is_null=is_null, is_retry=is_retry,
            wr_flit=wr_flit, send_size=send_size,
            ack_rel=ack_rel, rel_size=rel_size,
        )
        await self._to_fall()
        return self._sample(send_size=send_size, rd_ptr_i=rd_ptr_i)

    def _score(self, name, stim, got):
        send_size = got[7]
        rd_ptr = got[8]
        exp = self.g.combo(send_size=send_size, rd_ptr_i=rd_ptr)
        got_core = got[:6]
        exp_core = exp[:6]
        if got_core != exp_core:
            self.bad(name, stim, self._fmt(exp + (send_size, rd_ptr)),
                     self._fmt(got), HIER)
            return False
        exp_rd = exp[6]
        got_rd = got[6]
        if exp_rd is not None:
            if got_rd is None or (got_rd & MASK160) != (exp_rd & MASK160):
                self.bad(name, stim + " (rd_flit)",
                         hex(exp_rd),
                         "X" if got_rd is None else hex(got_rd),
                         "u_u.mem / u_u.rd_flit")
                return False
        wr, tail, rcv, free, err, cs = got_core
        if cs != int(free >= send_size):
            self.bad(name, stim + " (can_send combo)",
                     f"can_send=({free}>={send_size})={int(free >= send_size)}",
                     self._fmt(got), "u_u.can_send")
            return False
        if free > DEPTH:
            self.bad(name, stim + " (free vs depth)",
                     f"num_free<={DEPTH}", self._fmt(got), "u_u.freeb")
            return False
        try:
            inner_wr = ival(self.dut.u_u.wrp, None)
            inner_free = ival(self.dut.u_u.freeb, None)
            inner_err = ival(self.dut.u_u.proto_err, None)
        except Exception:
            inner_wr = inner_free = inner_err = None
        if inner_wr is not None and (inner_wr & MASK8) != wr:
            self.bad(name, stim + " (port vs u_u.wrp)",
                     f"wr_ptr={wr}", f"u_u.wrp={inner_wr}", HIER)
            return False
        if inner_free is not None and (inner_free & MASK9) != free:
            self.bad(name, stim + " (port vs u_u.freeb)",
                     f"num_free={free}", f"u_u.freeb={inner_free}", HIER)
            return False
        if inner_err is not None and inner_err != err:
            self.bad(name, stim + " (port vs u_u.proto_err)",
                     f"proto_err={err}", f"u_u.proto_err={inner_err}", HIER)
            return False
        return True

    async def _expect(self, name, stim, **kw):
        got = await self._cycle(**kw)
        if not self._score(name, stim, got):
            return None
        return got

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_retry_buf"
        self.g = Golden()

        g0 = Golden()
        if g0.combo(send_size=1)[:6] != (0, 0, 0, DEPTH, 0, 1):
            self.bad(name, "golden reset combo",
                     "wr=0 tail=0 rcv=0 free=256 proto_err=0 can_send=1",
                     str(g0.combo(send_size=1)[:6]), "golden")
            phase.drop_objection(self)
            return
        g0.step(wr_en=1, wr_flit=0x55, send_size=1)
        if g0.combo(send_size=1, rd_ptr_i=0)[:7] != (1, 0, 0, 255, 0, 1, 0x55):
            self.bad(name, "golden one data flit",
                     "wr=1 free=255 rd=0x55",
                     str(g0.combo(send_size=1, rd_ptr_i=0)), "golden")
            phase.drop_objection(self)
            return
        g0.step(wr_en=1, is_null=1, wr_flit=0x1)
        if g0.wrp != 1 or g0.freeb != 255:
            self.bad(name, "golden Null skip",
                     "wr=1 free=255",
                     f"wr={g0.wrp} free={g0.freeb}", "golden")
            phase.drop_objection(self)
            return
        g0.step(ack_rel=1, rel_size=8)
        if not g0.proto_err or g0.freeb != 255 or g0.tail != 0:
            self.bad(name, "golden overflow 255+8",
                     "proto_err=1 free=255 tail=0",
                     f"err={g0.proto_err} free={g0.freeb} tail={g0.tail}",
                     "golden")
            phase.drop_objection(self)
            return
        if g0.can_send(255) != 1 or g0.can_send(0) != 1:
            self.bad(name, "golden can_send vs send_size",
                     "free=255 → send_size 255/0 can_send=1",
                     f"cs255={g0.can_send(255)} cs0={g0.can_send(0)}",
                     "golden")
            phase.drop_objection(self)
            return
        g0.freeb = 1
        if g0.can_send(2) != 0 or g0.can_send(1) != 1:
            self.bad(name, "golden can_send free=1",
                     "send_size=2 → 0; send_size=1 → 1",
                     f"cs2={g0.can_send(2)} cs1={g0.can_send(1)}",
                     "golden")
            phase.drop_objection(self)
            return
        wr_hold, free_hold = g0.wrp, g0.freeb
        g0.step(wr_en=1, wr_flit=0x66, send_size=2)
        if g0.wrp != wr_hold or g0.freeb != free_hold:
            self.bad(name, "golden !can_send blocks write",
                     f"wr stays {wr_hold} free={free_hold} when send_size>free",
                     f"wr={g0.wrp} free={g0.freeb}", "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. Reset: pointers 0, free=256, proto_err=0 (stock).
        got = self._sample(send_size=1, rd_ptr_i=0)
        if not self._score(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        if got[:6] != (0, 0, 0, DEPTH, 0, 1):
            self.bad(name, "reset idle ports",
                     "wr=0 tail=0 rcv=0 free=256 proto_err=0 can_send=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(3):
            got = await self._expect(name, f"idle after reset [{i}]")
            if got is None:
                phase.drop_objection(self)
                return
            if got[:6] != (0, 0, 0, DEPTH, 0, 1):
                self.bad(name, f"hold reset idle [{i}]",
                         "wr=0 free=256 proto_err=0",
                         self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # can_send tracks free vs send_size (combo, no write).
        got = await self._expect(name, "can_send send_size=255 at free=256",
                                 send_size=255)
        if got is None or got[5] != 1:
            if got is not None:
                self.bad(name, "can_send at full free",
                         "can_send=1", self._fmt(got), "u_u.can_send")
            phase.drop_objection(self)
            return

        # 2. Stock: Null does not consume.
        got = await self._expect(
            name, "wr_en is_null (stock)",
            wr_en=1, is_null=1, wr_flit=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 0 or got[3] != DEPTH:
            self.bad(name, "wr_en is_null",
                     "free stays 256 wr=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. Stock: Retry does not enter.
        got = await self._expect(
            name, "is_retry write (stock)",
            wr_en=1, is_retry=1, wr_flit=2)
        if got is None or got[3] != DEPTH or got[0] != 0:
            if got is not None:
                self.bad(name, "is_retry write",
                         "not entered (free=256 wr=0)",
                         self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # both marks still skip
        got = await self._expect(
            name, "is_null && is_retry skip",
            wr_en=1, is_null=1, is_retry=1, wr_flit=3)
        if got is None or got[0] != 0 or got[3] != DEPTH:
            if got is not None:
                self.bad(name, "both marks skip",
                         "free=256 wr=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. Stock: one data flit → free=255; read back via rd_ptr_i.
        got = await self._expect(
            name, "one data flit (stock)",
            wr_en=1, wr_flit=0x55, rd_ptr_i=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[3] != 255 or got[6] != 0x55:
            self.bad(name, "one data flit",
                     "wr=1 free=255 rd_flit=0x55",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "hold after data write; rd_ptr_i=0",
                                 rd_ptr_i=0)
        if got is None or got[6] != 0x55:
            if got is not None:
                self.bad(name, "rd_ptr_i returns stored flit",
                         "rd_flit=0x55", self._fmt(got), "u_u.rd_flit")
            phase.drop_objection(self)
            return

        # can_send: free=255 vs send_size=255 (yes). send_size is 8-bit
        # so it cannot exceed 255; block-write is scored later at free=252.
        got = await self._expect(
            name, "can_send=1 at free=255 send_size=255 (no write)",
            send_size=255, rd_ptr_i=0)
        if got is None or got[5] != 1 or got[0] != 1 or got[3] != 255:
            if got is not None:
                self.bad(name, "can_send at free=255 send_size=255",
                         "can_send=1 wr stays 1 free=255", self._fmt(got),
                         "u_u.can_send")
            phase.drop_objection(self)
            return

        # Async rst_n mid-buffer (no posedge) clears proto_err + ptrs.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.hard_reset()
        got = self._sample(send_size=1, rd_ptr_i=0)
        if got[:6] != (0, 0, 0, DEPTH, 0, 1):
            self.bad(name, "async rst_n after first writes (100ps, no posedge)",
                     "wr=0 free=256 proto_err=0",
                     self._fmt(got), "u_u.wrp")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = await self._expect(
            name, "rewrite one data flit after async rst",
            wr_en=1, wr_flit=0x55, rd_ptr_i=0)
        if got is None or got[3] != 255:
            if got is not None:
                self.bad(name, "rewrite after async rst",
                         "free=255", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 5. Stock overflow: ack_rel 8 with free=255 → 263>256 proto_err.
        got = await self._expect(
            name, "ack_rel 8 with free=255 → 263>256 (stock)",
            ack_rel=1, rel_size=8)
        if got is None:
            phase.drop_objection(self)
            return
        if got[4] != 1 or got[3] != 255 or got[1] != 0 or got[2] != 0:
            self.bad(name, "ack_rel overflow",
                     "proto_err=1 free=255 tail=0 rcv=0 (no release)",
                     self._fmt(got), "u_u.freeb")
            phase.drop_objection(self)
            return

        # port_rst / !link_up clear ptrs+free, not proto_err.
        got = await self._expect(name, "port_rst after overflow (sticky err)",
                                 port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != DEPTH or got[0] != 0 or got[4] != 1:
            self.bad(name, "port_rst clears ptrs/free, not proto_err",
                     "wr=0 free=256 proto_err=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "!link_up after port_rst (err still sticky)",
            link_up=0)
        if got is None or got[3] != DEPTH or got[4] != 1:
            if got is not None:
                self.bad(name, "!link_up sticky proto_err",
                         "free=256 proto_err=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "relink after !link_up")
        if got is None or got[4] != 1:
            if got is not None:
                self.bad(name, "relink keeps proto_err",
                         "proto_err=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Hard reset clears proto_err (RTL !rst_n arm).
        sset(d.rst_n, 0)
        await self._idle()
        await Timer(100, "PS")
        self.g.hard_reset()
        got = self._sample(send_size=1, rd_ptr_i=0)
        if got[4] != 0 or got[3] != DEPTH:
            self.bad(name, "hard rst_n clears proto_err",
                     "proto_err=0 free=256",
                     self._fmt(got), "u_u.proto_err")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        # 6. Stock: write 1 then ack_rel 1 → free=256 proto_err=0.
        got = await self._expect(
            name, "write 1 then (next) ack_rel 1 setup",
            wr_en=1, wr_flit=0x11, rd_ptr_i=0)
        if got is None or got[3] != 255:
            if got is not None:
                self.bad(name, "write before legal release",
                         "free=255", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "write 1 then ack_rel 1 (stock)",
            ack_rel=1, rel_size=1, rd_ptr_i=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != DEPTH or got[4] != 0 or got[1] != 1 or got[2] != 1:
            self.bad(name, "legal ack_rel 1",
                     "free=256 proto_err=0 tail=1 rcv=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if got[6] != 0x11:
            self.bad(name, "rd after legal release (mem not cleared)",
                     "rd_flit=0x11", self._fmt(got), "u_u.rd_flit")
            phase.drop_objection(self)
            return

        # 7. Stock: write then port_rst → free=256 (ptrs 0).
        got = await self._expect(name, "write before port_rst (stock)",
                                 wr_en=1, wr_flit=0x22)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "port_rst (stock)", port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != DEPTH or got[0] != 0 or got[1] != 0 or got[2] != 0:
            self.bad(name, "port_rst",
                     "free=256 wr=tail=rcv=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 8. Normal writes + can_send + blocked write + read.
        flits = [0xA500 + i for i in range(4)]
        for i, flit in enumerate(flits):
            got = await self._expect(
                name, f"write flit[{i}]",
                wr_en=1, wr_flit=flit, rd_ptr_i=i)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != i + 1 or got[3] != DEPTH - (i + 1) or got[6] != flit:
                self.bad(name, f"write flit[{i}]",
                         f"wr={i + 1} free={DEPTH - (i + 1)} rd={hex(flit)}",
                         self._fmt(got), HIER)
                phase.drop_objection(self)
                return
        # free=252; send_size=253 blocks write
        got = await self._expect(
            name, "can_send=0 blocks write send_size=253 free=252",
            wr_en=1, wr_flit=0xDEAD, send_size=253, rd_ptr_i=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 4 or got[3] != 252 or got[5] != 0:
            self.bad(name, "blocked write when !can_send",
                     "wr=4 free=252 can_send=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i, flit in enumerate(flits):
            got = await self._expect(
                name, f"read back flit[{i}]",
                rd_ptr_i=i)
            if got is None or got[6] != flit:
                if got is not None:
                    self.bad(name, f"rd_ptr_i={i}",
                             hex(flit), self._fmt(got), "u_u.rd_flit")
                phase.drop_objection(self)
                return

        # legal release of 4 restores free; tail/rcv advance
        got = await self._expect(
            name, "ack_rel 4 restores free",
            ack_rel=1, rel_size=4, rd_ptr_i=0)
        if got is None or got[3] != DEPTH or got[1] != 4 or got[2] != 4:
            if got is not None:
                self.bad(name, "ack_rel 4",
                         "free=256 tail=4 rcv=4",
                         self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 9. Same-cycle write + legal release: last NBA to freeb wins (release).
        # From free=256 a same-cycle rel_size=1 overflows (256+1>256).
        # First consume one, then same-cycle write + rel_size=1.
        got = await self._expect(name, "pre-write for same-cycle NBA",
                                 wr_en=1, wr_flit=0x77, rd_ptr_i=got[0] - 1
                                 if got[0] else 4)
        if got is None:
            phase.drop_objection(self)
            return
        wr_before = got[0]
        got = await self._expect(
            name, "same-cycle write + legal ack_rel 1 (release wins freeb)",
            wr_en=1, wr_flit=0x88, ack_rel=1, rel_size=1,
            rd_ptr_i=wr_before)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != DEPTH or got[4] != 0 or got[0] != ((wr_before + 1) & MASK8):
            self.bad(name, "same-cycle write+release",
                     f"wr={((wr_before + 1) & MASK8)} free=256 proto_err=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if got[6] != 0x88:
            self.bad(name, "same-cycle write stored flit",
                     "rd_flit=0x88", self._fmt(got), "u_u.rd_flit")
            phase.drop_objection(self)
            return

        # 10. Depth 256: fill, wrap wr_ptr, can_send=0, read all, overflow.
        await self._idle()
        sset(d.rst_n, 0)
        await self.cycles(2)
        self.g.hard_reset()
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        for i in range(DEPTH):
            flit = (0x10000 + i) & MASK160
            got = await self._expect(
                name, f"fill[{i}]",
                wr_en=1, wr_flit=flit, rd_ptr_i=i)
            if got is None:
                phase.drop_objection(self)
                return
        if got[0] != 0 or got[3] != 0 or got[5] != 0:
            self.bad(name, "fill 256",
                     "wr=0 (wrap) free=0 can_send=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "write when full send_size=1 blocked",
            wr_en=1, wr_flit=0x999, send_size=1, rd_ptr_i=0)
        if got is None or got[0] != 0 or got[3] != 0:
            if got is not None:
                self.bad(name, "full write blocked",
                         "wr=0 free=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(0, DEPTH, 17):
            exp_flit = (0x10000 + i) & MASK160
            got = await self._expect(
                name, f"read filled [{i}]",
                rd_ptr_i=i)
            if got is None or got[6] != exp_flit:
                if got is not None:
                    self.bad(name, f"depth read rd_ptr_i={i}",
                             hex(exp_flit), self._fmt(got), "u_u.rd_flit")
                phase.drop_objection(self)
                return
        # rel_size max 255; 0+255=255 legal
        got = await self._expect(
            name, "ack_rel 255 from free=0",
            ack_rel=1, rel_size=255)
        if got is None or got[3] != 255 or got[4] != 0:
            if got is not None:
                self.bad(name, "ack_rel 255",
                         "free=255 proto_err=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if got[1] != 255 or got[2] != 255:
            self.bad(name, "tail/rcv after rel 255",
                     "tail=255 rcv=255", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "ack_rel 2 with free=255 → 257>256",
            ack_rel=1, rel_size=2)
        if got is None or got[4] != 1 or got[3] != 255 or got[1] != 255:
            if got is not None:
                self.bad(name, "second overflow",
                         "proto_err=1 free=255 tail=255",
                         self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # empty-buffer overflow: free=256 + rel_size=1
        sset(d.rst_n, 0)
        await self.cycles(2)
        self.g.hard_reset()
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        got = await self._expect(
            name, "ack_rel 1 at free=256 overflows",
            ack_rel=1, rel_size=1)
        if got is None or got[4] != 1 or got[3] != DEPTH:
            if got is not None:
                self.bad(name, "release on empty",
                         "proto_err=1 free=256", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_retry_buf)
