"""Module-level uvm-python TC for Decision-I leaf vibe_dll_retry_ack_sm.

Covers reset / port_rst clears to NORMAL; start_ack → 1 Idle then 32 Ack;
replay RdPtr from RcvPtr until WrPtr; return to NORMAL; start_ack ignored
in ACK / PLAY; rcv_ptr==wr_ptr one-cycle PLAY; 8-bit rd_ptr wrap (DUT +1).
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/dll/vibe_dll_retry_ack_sm.sv: async-low rst_n,
ST_N=0 / ST_A=1 / ST_P=2, combo send_idle=(st==ST_A)&&(burst==0),
send_ack=(st==ST_A)&&(burst!=0), replay=(st==ST_P), rd_ptr=rp.
At burst==32 enter PLAY with rp:=rcv_ptr; increment until rp==wr_ptr.
Instantiated by vibe_dll u_ack. Stock Icarus tc_retry_ack_replay remains
the official TP scorer. Header-only vs stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_N = 0
ST_A = 1
ST_P = 2
ACK_BURST = 32
MASK8 = 0xFF
MASK6 = 0x3F
ST_NAME = {0: "NORMAL", 1: "ACK", 2: "PLAY"}
HIER = "u_u.st / u_u.burst / u_u.rp"


def decode(st: int, burst: int, rp: int):
    """Product combo: state, send_idle, send_ack, replay, rd_ptr."""
    st = int(st) & 7
    burst = int(burst) & MASK6
    rp = int(rp) & MASK8
    send_idle = int(st == ST_A and burst == 0)
    send_ack = int(st == ST_A and burst != 0)
    replay = int(st == ST_P)
    return st, send_idle, send_ack, replay, rp


class Golden:
    """Cycle-accurate st / burst / rp vs product NBA (port_rst wins)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.st = ST_N
        self.burst = 0
        self.rp = 0

    def step(self, port_rst=0, start_ack=0, wr_ptr=0, rcv_ptr=0):
        if port_rst:
            self.st = ST_N
            self.burst = 0
            self.rp = 0
            return
        if self.st == ST_N:
            if start_ack:
                self.st = ST_A
                self.burst = 0
        elif self.st == ST_A:
            if self.burst == ACK_BURST:
                self.st = ST_P
                self.rp = int(rcv_ptr) & MASK8
            else:
                self.burst = (self.burst + 1) & MASK6
        elif self.st == ST_P:
            if self.rp == (int(wr_ptr) & MASK8):
                self.st = ST_N
            else:
                self.rp = (self.rp + 1) & MASK8
        else:
            self.st = ST_N

    def combo(self):
        return decode(self.st, self.burst, self.rp)


class tc_vibe_dll_retry_ack_sm(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, wr_ptr=0, rcv_ptr=0):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.start_ack, 0)
        sset(d.wr_ptr, int(wr_ptr) & MASK8)
        sset(d.rcv_ptr, int(rcv_ptr) & MASK8)

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
            ival(d.state, -1),
            ival(d.send_idle, -1),
            ival(d.send_ack, -1),
            ival(d.replay, -1),
            ival(d.rd_ptr, -1) & MASK8,
        )

    def _fmt(self, s):
        st, idle, ack, replay, rd = s
        name = ST_NAME.get(st, f"?{st}")
        return (
            f"state={st} ({name}) send_idle={idle} send_ack={ack} "
            f"replay={replay} rd_ptr={rd}"
        )

    async def _cycle(self, port_rst=0, start_ack=0, wr_ptr=0, rcv_ptr=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.start_ack, 1 if start_ack else 0)
        sset(d.wr_ptr, int(wr_ptr) & MASK8)
        sset(d.rcv_ptr, int(rcv_ptr) & MASK8)
        self.g.step(
            port_rst=port_rst, start_ack=start_ack,
            wr_ptr=wr_ptr, rcv_ptr=rcv_ptr,
        )
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got):
        exp = self.g.combo()
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        st, idle, ack, replay, rd = got
        dec = decode(st, self.g.burst, self.g.rp)
        if (idle, ack, replay, rd) != dec[1:]:
            self.bad(name, stim + " (combo decode)",
                     self._fmt(dec), self._fmt(got),
                     "u_u.send_idle / u_u.send_ack / u_u.replay")
            return False
        if idle and ack:
            self.bad(name, stim + " (Idle vs Ack exclusive)",
                     "send_idle and send_ack not both 1",
                     self._fmt(got), "u_u.send_idle / u_u.send_ack")
            return False
        if replay and (idle or ack):
            self.bad(name, stim + " (PLAY vs Idle/Ack exclusive)",
                     "replay=1 implies send_idle=0 send_ack=0",
                     self._fmt(got), "u_u.replay")
            return False
        if st == ST_N and (idle or ack or replay):
            self.bad(name, stim + " (NORMAL flags)",
                     "send_idle=0 send_ack=0 replay=0",
                     self._fmt(got), HIER)
            return False
        if st == ST_A and replay:
            self.bad(name, stim + " (ACK flags)",
                     "replay=0", self._fmt(got), HIER)
            return False
        if st == ST_P and (not replay or idle or ack):
            self.bad(name, stim + " (PLAY flags)",
                     "replay=1 send_idle=0 send_ack=0",
                     self._fmt(got), HIER)
            return False
        try:
            inner = ival(self.dut.u_u.st, None)
            inner_rp = ival(self.dut.u_u.rp, None)
        except Exception:
            inner = None
            inner_rp = None
        if inner is not None and inner != st:
            self.bad(name, stim + " (port vs u_u.st)",
                     f"st={st}", f"u_u.st={inner} state={st}", HIER)
            return False
        if inner_rp is not None and inner_rp != rd:
            self.bad(name, stim + " (port vs u_u.rp)",
                     f"rd_ptr={rd}", f"u_u.rp={inner_rp} rd_ptr={rd}", HIER)
            return False
        return True

    async def _expect(self, name, stim, **kw):
        got = await self._cycle(**kw)
        if not self._score(name, stim, got):
            return None
        return got

    async def _walk_ack_replay(self, name, tag, wr_ptr, rcv_ptr):
        """start_ack → 1 Idle + 32 Ack → PLAY from rcv until wr → NORMAL."""
        wr_ptr = int(wr_ptr) & MASK8
        rcv_ptr = int(rcv_ptr) & MASK8
        got = await self._expect(
            name, f"{tag} start_ack → ACK Idle",
            start_ack=1, wr_ptr=wr_ptr, rcv_ptr=rcv_ptr)
        if got is None:
            return None
        if got[0] != ST_A or got[1] != 1 or got[2] != 0 or got[3] != 0:
            self.bad(name, f"{tag} first ACK cycle is Idle",
                     "state=1 send_idle=1 send_ack=0 replay=0",
                     self._fmt(got), HIER)
            return None
        for i in range(ACK_BURST):
            got = await self._expect(
                name, f"{tag} Ack[{i + 1}/32]",
                wr_ptr=wr_ptr, rcv_ptr=rcv_ptr)
            if got is None:
                return None
            if got[0] != ST_A or got[2] != 1 or got[1] != 0:
                self.bad(name, f"{tag} Ack[{i + 1}/32]",
                         "state=1 send_ack=1 send_idle=0",
                         self._fmt(got), HIER)
                return None
        got = await self._expect(
            name, f"{tag} enter PLAY rd_ptr=rcv_ptr",
            wr_ptr=wr_ptr, rcv_ptr=rcv_ptr)
        if got is None:
            return None
        if got[0] != ST_P or got[3] != 1 or got[4] != rcv_ptr:
            self.bad(name, f"{tag} ACK done → PLAY",
                     f"state=2 replay=1 rd_ptr={rcv_ptr}",
                     self._fmt(got), HIER)
            return None
        for i in range(260):
            got = await self._expect(
                name, f"{tag} replay[{i}]",
                wr_ptr=wr_ptr, rcv_ptr=rcv_ptr)
            if got is None:
                return None
            if got[0] == ST_N:
                if got[4] != wr_ptr:
                    self.bad(name, f"{tag} back to NORMAL",
                             f"state=0 rd_ptr={wr_ptr} (stopped at WrPtr)",
                             self._fmt(got), HIER)
                    return None
                return got
        self.bad(name, f"{tag} replay until rd_ptr==wr_ptr",
                 f"NORMAL with rd_ptr={wr_ptr}",
                 self._fmt(got), HIER)
        return None

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_retry_ack_sm"
        self.g = Golden()

        if decode(ST_N, 0, 0)[1:] != (0, 0, 0, 0):
            self.bad(name, "golden NORMAL flags",
                     "send_idle=0 send_ack=0 replay=0 rd=0",
                     str(decode(ST_N, 0, 0)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_A, 0, 3) != (ST_A, 1, 0, 0, 3):
            self.bad(name, "golden ACK burst=0 is Idle",
                     "state=1 send_idle=1 send_ack=0 replay=0 rd=3",
                     str(decode(ST_A, 0, 3)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_A, 1, 0) != (ST_A, 0, 1, 0, 0):
            self.bad(name, "golden ACK burst=1 is Ack",
                     "state=1 send_idle=0 send_ack=1",
                     str(decode(ST_A, 1, 0)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_A, ACK_BURST, 5) != (ST_A, 0, 1, 0, 5):
            self.bad(name, "golden ACK burst=32 is still Ack",
                     "state=1 send_ack=1",
                     str(decode(ST_A, ACK_BURST, 5)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_P, 99, 7) != (ST_P, 0, 0, 1, 7):
            self.bad(name, "golden PLAY flags",
                     "state=2 send_idle=0 send_ack=0 replay=1 rd=7",
                     str(decode(ST_P, 99, 7)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_A, 0, 0)[1] == decode(ST_A, 0, 0)[2]:
            self.bad(name, "golden Idle vs Ack exclusive",
                     "burst=0 send_idle != send_ack",
                     str(decode(ST_A, 0, 0)), "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: NORMAL, no Idle/Ack/replay, rd_ptr=0 (stock).
        got = self._sample()
        if not self._score(name, "reset then release, start_ack=0", got):
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0):
            self.bad(name, "reset idle ports",
                     "state=0 (NORMAL) send_idle=0 send_ack=0 replay=0 rd_ptr=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._expect(
                name, f"idle cycle {i} after reset (start_ack=0, junk ptrs)",
                start_ack=0, wr_ptr=4, rcv_ptr=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_N:
                self.bad(name, f"hold NORMAL while !start_ack [{i}]",
                         "state=0 (NORMAL)", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # Walk into ACK Idle, then async rst_n mid-ACK (no posedge).
        got = await self._expect(name, "start_ack from NORMAL → ACK Idle",
                                 start_ack=1, wr_ptr=4, rcv_ptr=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_A or got[1] != 1:
            self.bad(name, "start_ack", "ACK Idle (state=1 send_idle=1)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle(wr_ptr=4, rcv_ptr=0)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-ACK (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0):
            self.bad(name, "async rst_n mid-ACK",
                     "state=0 rd_ptr=0", self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle NORMAL",
                           got):
            phase.drop_objection(self)
            return

        # 2. Stock vector: wr_ptr=4 rcv_ptr=0 (tc_retry_ack_replay).
        got = await self._walk_ack_replay(name, "stock wr=4 rcv=0", 4, 0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 4):
            self.bad(name, "stock replay until rd_ptr==wr_ptr=4",
                     "state=0 (NORMAL) rd_ptr=4",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # start_ack=0 holds NORMAL after return (rd_ptr stays at WrPtr).
        for i in range(3):
            got = await self._expect(
                name, f"hold NORMAL after stock replay [{i}]",
                wr_ptr=4, rcv_ptr=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_N or got[4] != 4:
                self.bad(name, "NORMAL holds; rd_ptr not cleared without rst",
                         "state=0 rd_ptr=4", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # 3. start_ack ignored in ACK / PLAY (no invented hop).
        got = await self._expect(name, "second start_ack → ACK Idle",
                                 start_ack=1, wr_ptr=4, rcv_ptr=0)
        if got is None or got[0] != ST_A:
            if got is not None:
                self.bad(name, "second start_ack",
                         "ACK Idle", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "start_ack held in ACK (still Ack[1], no skip)",
            start_ack=1, wr_ptr=4, rcv_ptr=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_A or got[2] != 1:
            self.bad(name, "start_ack in ACK does not skip burst",
                     "state=1 send_ack=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "port_rst during ACK (stock)",
                                 port_rst=1, start_ack=1, wr_ptr=4, rcv_ptr=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0):
            self.bad(name, "port_rst during ACK",
                     "state=0 rd_ptr=0 (clears burst / rp)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. rcv_ptr == wr_ptr: one PLAY cycle then NORMAL (DUT equality).
        got = await self._walk_ack_replay(name, "rcv==wr=7", 7, 7)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 7):
            self.bad(name, "rcv_ptr==wr_ptr replay",
                     "state=0 rd_ptr=7", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 5. 8-bit increment wrap (DUT rp + 1), rcv=254 wr=1.
        got = await self._walk_ack_replay(name, "wrap rcv=254 wr=1", 1, 254)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 1):
            self.bad(name, "8-bit wrap replay",
                     "state=0 rd_ptr=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # start_ack ignored in PLAY (walk until PLAY, then pulse).
        got = await self._expect(name, "start_ack before PLAY-ignore",
                                 start_ack=1, wr_ptr=3, rcv_ptr=1)
        if got is None:
            phase.drop_objection(self)
            return
        for i in range(ACK_BURST):
            got = await self._expect(
                name, f"ACK to PLAY for ignore [{i}]",
                wr_ptr=3, rcv_ptr=1)
            if got is None:
                phase.drop_objection(self)
                return
        got = await self._expect(name, "enter PLAY before start_ack-ignore",
                                 wr_ptr=3, rcv_ptr=1)
        if got is None or got[0] != ST_P or got[4] != 1:
            if got is not None:
                self.bad(name, "reach PLAY before start_ack-ignore",
                         "state=2 rd_ptr=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "start_ack=1 in PLAY (still increment, no re-ACK)",
            start_ack=1, wr_ptr=3, rcv_ptr=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_P or got[4] != 2:
            self.bad(name, "start_ack in PLAY ignored",
                     "state=2 rd_ptr=2", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # port_rst during PLAY clears rd_ptr (unlike return-to-NORMAL).
        got = await self._expect(
            name, "port_rst during PLAY",
            port_rst=1, start_ack=1, wr_ptr=3, rcv_ptr=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0):
            self.bad(name, "port_rst during PLAY",
                     "state=0 rd_ptr=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 6. Second packet after first complete (stock recovery).
        got = await self._walk_ack_replay(name, "second-ack wr=2 rcv=0", 2, 0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_N or got[4] != 2:
            self.bad(name, "second start_ack after first NORMAL",
                     "state=0 rd_ptr=2", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Async rst_n from PLAY (after re-enter).
        got = await self._expect(name, "start_ack before async-from-PLAY",
                                 start_ack=1, wr_ptr=2, rcv_ptr=0)
        if got is None:
            phase.drop_objection(self)
            return
        for i in range(ACK_BURST):
            got = await self._expect(
                name, f"ACK to PLAY for async rst [{i}]",
                wr_ptr=2, rcv_ptr=0)
            if got is None:
                phase.drop_objection(self)
                return
        got = await self._expect(name, "enter PLAY before async rst",
                                 wr_ptr=2, rcv_ptr=0)
        if got is None or got[0] != ST_P:
            if got is not None:
                self.bad(name, "reach PLAY before async rst",
                         "PLAY", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle(wr_ptr=2, rcv_ptr=0)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got[0] != ST_N or got[3] != 0 or got[4] != 0:
            self.bad(name, "async rst_n from PLAY (100ps, no posedge)",
                     "state=0 replay=0 rd_ptr=0",
                     self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_retry_ack_sm)
