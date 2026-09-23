"""Module-level uvm-python TC for Decision-I leaf vibe_dll_retry_req_sm.

Covers reset / port_rst / device_rst clears to NORMAL; start_retry →
1 Idle then 32 Req; REQ → WAIT (or RETRAIN at NUM_RETRY / phy_retrain);
wait_done_ack → NORMAL; WAIT timeout → REQ; RETRAIN 1-cycle then
NORMAL or ERROR at NUM_PHY_REINIT; ERROR waits Port/device reset.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/dll/vibe_dll_retry_req_sm.sv: async-low rst_n,
ST_N=0 / ST_Q=1 / ST_W=2 / ST_R=3 / ST_E=4, combo drop_data=REQ|WAIT,
retrain_req=(st==ST_R), retry_error=(st==ST_E),
send_idle=(st==ST_Q)&&(burst==0), send_req=(st==ST_Q)&&(burst!=0),
send_cnt=burst[4:0]. VIBE_NUM_RETRY=15 / VIBE_NUM_PHY_REINIT=4.
Product RETRY_WAIT_CYC default 12500. Instantiated by vibe_dll u_req.
Stock Icarus tc_retry_req_gbn / tc_retry_wait_retrain remain the
official TP scorers. Header-only vs stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_N = 0
ST_Q = 1
ST_W = 2
ST_R = 3
ST_E = 4
REQ_BURST = 32
VIBE_NUM_RETRY = 15
VIBE_NUM_PHY_REINIT = 4
RETRY_WAIT_CYC = 12500
MASK3 = 0x7
MASK4 = 0xF
MASK5 = 0x1F
MASK6 = 0x3F
MASK24 = 0xFFFFFF
ST_NAME = {0: "NORMAL", 1: "REQ", 2: "WAIT", 3: "RETRAIN", 4: "ERROR"}
HIER = "u_u.st / u_u.burst / u_u.num_retry / u_u.num_phy / u_u.wtmr"


def decode(st: int, burst: int):
    """Product combo: state + drop / retrain / error / idle / req / cnt."""
    st = int(st) & MASK3
    burst = int(burst) & MASK6
    drop_data = int(st == ST_Q or st == ST_W)
    retrain_req = int(st == ST_R)
    retry_error = int(st == ST_E)
    send_idle = int(st == ST_Q and burst == 0)
    send_req = int(st == ST_Q and burst != 0)
    send_cnt = burst & MASK5
    return (st, drop_data, retrain_req, retry_error, send_idle, send_req,
            send_cnt)


class Golden:
    """Cycle-accurate st / burst / counters vs product NBA (rst wins)."""

    def __init__(self):
        self.hard_reset()

    def hard_reset(self):
        self.st = ST_N
        self.num_retry = 0
        self.num_phy = 0
        self.wtmr = 0
        self.burst = 0

    def port_clear(self):
        self.st = ST_N
        self.num_retry = 0
        self.num_phy = 0
        self.burst = 0

    def step(self, rst_n=1, port_rst=0, device_rst=0, start_retry=0,
             phy_retrain=0, wait_done_ack=0):
        if not rst_n:
            self.hard_reset()
            return
        if port_rst or device_rst:
            self.port_clear()
            return
        if self.st == ST_N:
            if start_retry:
                self.st = ST_Q
                self.burst = 0
        elif self.st == ST_Q:
            if self.burst == REQ_BURST:
                self.num_retry = (self.num_retry + 1) & MASK4
                if self.num_retry == VIBE_NUM_RETRY or phy_retrain:
                    self.st = ST_R
                else:
                    self.st = ST_W
                    self.wtmr = RETRY_WAIT_CYC
            else:
                self.burst = (self.burst + 1) & MASK6
        elif self.st == ST_W:
            if wait_done_ack:
                self.st = ST_N
            elif self.wtmr == 0:
                self.st = ST_Q
                self.burst = 0
            else:
                self.wtmr = (self.wtmr - 1) & MASK24
        elif self.st == ST_R:
            self.num_phy = (self.num_phy + 1) & MASK3
            if self.num_phy == VIBE_NUM_PHY_REINIT:
                self.st = ST_E
            else:
                self.st = ST_N
        elif self.st == ST_E:
            pass
        else:
            self.st = ST_N

    def combo(self):
        return decode(self.st, self.burst)


class tc_vibe_dll_retry_req_sm(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.device_rst, 0)
        sset(d.start_retry, 0)
        sset(d.phy_retrain, 0)
        sset(d.wait_done_ack, 0)

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

    def _sample(self):
        d = self.dut
        return (
            ival(d.state, -1),
            ival(d.drop_data, -1),
            ival(d.retrain_req, -1),
            ival(d.retry_error, -1),
            ival(d.send_idle, -1),
            ival(d.send_req, -1),
            ival(d.send_cnt, -1) & MASK5,
        )

    def _fmt(self, s):
        st, drop, retrain, err, idle, req, cnt = s
        name = ST_NAME.get(st, f"?{st}")
        return (
            f"state={st} ({name}) drop_data={drop} retrain_req={retrain} "
            f"retry_error={err} send_idle={idle} send_req={req} "
            f"send_cnt={cnt}"
        )

    async def _cycle(self, port_rst=0, device_rst=0, start_retry=0,
                     phy_retrain=0, wait_done_ack=0, rst_n=1):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.device_rst, 1 if device_rst else 0)
        sset(d.start_retry, 1 if start_retry else 0)
        sset(d.phy_retrain, 1 if phy_retrain else 0)
        sset(d.wait_done_ack, 1 if wait_done_ack else 0)
        sset(d.rst_n, 1 if rst_n else 0)
        self.g.step(
            rst_n=rst_n, port_rst=port_rst, device_rst=device_rst,
            start_retry=start_retry, phy_retrain=phy_retrain,
            wait_done_ack=wait_done_ack,
        )
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got):
        exp = self.g.combo()
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        st, drop, retrain, err, idle, req, cnt = got
        dec = decode(st, self.g.burst)
        if (drop, retrain, err, idle, req, cnt) != dec[1:]:
            self.bad(name, stim + " (combo decode)",
                     self._fmt(dec), self._fmt(got),
                     "u_u.drop_data / u_u.send_idle / u_u.send_req")
            return False
        if idle and req:
            self.bad(name, stim + " (Idle vs Req exclusive)",
                     "send_idle and send_req not both 1",
                     self._fmt(got), "u_u.send_idle / u_u.send_req")
            return False
        if st == ST_N and (drop or retrain or err or idle or req):
            self.bad(name, stim + " (NORMAL flags)",
                     "all combo outs 0", self._fmt(got), HIER)
            return False
        if st == ST_Q and (not drop or retrain or err or idle == req):
            self.bad(name, stim + " (REQ flags)",
                     "drop_data=1 retrain=0 error=0 Idle xor Req",
                     self._fmt(got), HIER)
            return False
        if st == ST_W and (not drop or retrain or err or idle or req):
            self.bad(name, stim + " (WAIT flags)",
                     "drop_data=1 send_idle=0 send_req=0",
                     self._fmt(got), HIER)
            return False
        if st == ST_R and (drop or not retrain or err or idle or req):
            self.bad(name, stim + " (RETRAIN flags)",
                     "retrain_req=1 drop_data=0 retry_error=0",
                     self._fmt(got), HIER)
            return False
        if st == ST_E and (drop or retrain or not err or idle or req):
            self.bad(name, stim + " (ERROR flags)",
                     "retry_error=1 drop_data=0 retrain_req=0",
                     self._fmt(got), HIER)
            return False
        if cnt != (self.g.burst & MASK5):
            self.bad(name, stim + " (send_cnt vs burst[4:0])",
                     f"send_cnt={self.g.burst & MASK5}",
                     self._fmt(got), "u_u.send_cnt")
            return False
        try:
            inner = ival(self.dut.u_u.st, None)
            inner_burst = ival(self.dut.u_u.burst, None)
        except Exception:
            inner = None
            inner_burst = None
        if inner is not None and inner != st:
            self.bad(name, stim + " (port vs u_u.st)",
                     f"st={st}", f"u_u.st={inner} state={st}", HIER)
            return False
        if inner_burst is not None and (inner_burst & MASK6) != self.g.burst:
            self.bad(name, stim + " (port vs u_u.burst)",
                     f"burst={self.g.burst}",
                     f"u_u.burst={inner_burst}", HIER)
            return False
        return True

    async def _expect(self, name, stim, **kw):
        got = await self._cycle(**kw)
        if not self._score(name, stim, got):
            return None
        return got

    async def _walk_req(self, name, tag, phy_retrain=0):
        """start_retry → 1 Idle + 32 Req. Leaves DUT on last REQ (burst=32)."""
        got = await self._expect(
            name, f"{tag} start_retry → REQ Idle",
            start_retry=1, phy_retrain=phy_retrain)
        if got is None:
            return None
        if got[0] != ST_Q or got[4] != 1 or got[5] != 0 or got[1] != 1:
            self.bad(name, f"{tag} first REQ cycle is Idle",
                     "state=1 send_idle=1 send_req=0 drop_data=1",
                     self._fmt(got), HIER)
            return None
        for i in range(REQ_BURST):
            got = await self._expect(
                name, f"{tag} Req[{i + 1}/32]",
                phy_retrain=phy_retrain)
            if got is None:
                return None
            if got[0] != ST_Q or got[5] != 1 or got[4] != 0:
                self.bad(name, f"{tag} Req[{i + 1}/32]",
                         "state=1 send_req=1 send_idle=0",
                         self._fmt(got), HIER)
                return None
            exp_cnt = (i + 1) & MASK5
            if got[6] != exp_cnt:
                self.bad(name, f"{tag} Req[{i + 1}/32] send_cnt",
                         f"send_cnt={exp_cnt} (burst[4:0])",
                         self._fmt(got), "u_u.send_cnt")
                return None
        return got

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_retry_req_sm"
        self.g = Golden()

        if decode(ST_N, 0)[1:] != (0, 0, 0, 0, 0, 0):
            self.bad(name, "golden NORMAL flags",
                     "all combo outs 0",
                     str(decode(ST_N, 0)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_Q, 0) != (ST_Q, 1, 0, 0, 1, 0, 0):
            self.bad(name, "golden REQ burst=0 is Idle",
                     "state=1 drop=1 send_idle=1 send_req=0 send_cnt=0",
                     str(decode(ST_Q, 0)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_Q, 1) != (ST_Q, 1, 0, 0, 0, 1, 1):
            self.bad(name, "golden REQ burst=1 is Req",
                     "state=1 drop=1 send_idle=0 send_req=1 send_cnt=1",
                     str(decode(ST_Q, 1)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_Q, REQ_BURST) != (ST_Q, 1, 0, 0, 0, 1, 0):
            self.bad(name, "golden REQ burst=32 send_cnt wrap",
                     "state=1 send_req=1 send_cnt=0 (burst[4:0])",
                     str(decode(ST_Q, REQ_BURST)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_W, 9) != (ST_W, 1, 0, 0, 0, 0, 9):
            self.bad(name, "golden WAIT flags",
                     "state=2 drop=1 send_idle=0 send_req=0",
                     str(decode(ST_W, 9)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_R, 0) != (ST_R, 0, 1, 0, 0, 0, 0):
            self.bad(name, "golden RETRAIN flags",
                     "state=3 retrain_req=1 drop=0 error=0",
                     str(decode(ST_R, 0)), "golden")
            phase.drop_objection(self)
            return
        if decode(ST_E, 0) != (ST_E, 0, 0, 1, 0, 0, 0):
            self.bad(name, "golden ERROR flags",
                     "state=4 retry_error=1 drop=0 retrain=0",
                     str(decode(ST_E, 0)), "golden")
            phase.drop_objection(self)
            return
        g0 = Golden()
        g0.step(start_retry=1)
        if g0.st != ST_Q or g0.burst != 0:
            self.bad(name, "golden start_retry",
                     "ST_Q burst=0",
                     f"st={g0.st} burst={g0.burst}", "golden")
            phase.drop_objection(self)
            return
        for _ in range(REQ_BURST):
            g0.step()
        g0.step()
        if g0.st != ST_W or g0.num_retry != 1 or g0.wtmr != RETRY_WAIT_CYC:
            self.bad(name, "golden first burst → WAIT",
                     f"ST_W num_retry=1 wtmr={RETRY_WAIT_CYC}",
                     f"st={g0.st} nr={g0.num_retry} wtmr={g0.wtmr}",
                     "golden")
            phase.drop_objection(self)
            return
        g0.step(wait_done_ack=1)
        if g0.st != ST_N:
            self.bad(name, "golden wait_done_ack",
                     "ST_N", f"st={g0.st}", "golden")
            phase.drop_objection(self)
            return
        g1 = Golden()
        g1.step(start_retry=1)
        for _ in range(REQ_BURST):
            g1.step(phy_retrain=1)
        g1.step(phy_retrain=1)
        if g1.st != ST_R or g1.num_retry != 1:
            self.bad(name, "golden phy_retrain at burst done",
                     "ST_R num_retry=1",
                     f"st={g1.st} nr={g1.num_retry}", "golden")
            phase.drop_objection(self)
            return
        g1.step()
        if g1.st != ST_N or g1.num_phy != 1:
            self.bad(name, "golden RETRAIN 1-cycle → NORMAL",
                     "ST_N num_phy=1",
                     f"st={g1.st} np={g1.num_phy}", "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: NORMAL, no drop/retrain/error/idle/req (stock).
        got = self._sample()
        if not self._score(name, "reset then release, start_retry=0", got):
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0, 0, 0):
            self.bad(name, "reset idle ports",
                     "state=0 (NORMAL) all combo outs 0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._expect(
                name, f"idle cycle {i} after reset (start_retry=0)",
                start_retry=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_N:
                self.bad(name, f"hold NORMAL while !start_retry [{i}]",
                         "state=0 (NORMAL)", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # Walk into REQ Idle, then async rst_n mid-REQ (no posedge).
        got = await self._expect(name, "start_retry from NORMAL → REQ Idle",
                                 start_retry=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_Q or got[4] != 1 or got[1] != 1:
            self.bad(name, "start_retry GBN",
                     "REQ Idle (state=1 send_idle=1 drop_data=1)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.hard_reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-REQ (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0, 0, 0):
            self.bad(name, "async rst_n mid-REQ",
                     "state=0", self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle NORMAL",
                           got):
            phase.drop_objection(self)
            return

        # 2. Stock: start_retry → 1 Idle + 32 Req → WAIT (num_retry=1).
        got = await self._walk_req(name, "stock first burst")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "stock first burst → WAIT")
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_W or got[1] != 1 or got[4] != 0 or got[5] != 0:
            self.bad(name, "REQ burst done → WAIT",
                     "state=2 drop_data=1 send_idle=0 send_req=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.num_retry != 1 or self.g.wtmr != RETRY_WAIT_CYC:
            self.bad(name, "WAIT loads wtmr / increments num_retry",
                     f"num_retry=1 wtmr={RETRY_WAIT_CYC}",
                     f"nr={self.g.num_retry} wtmr={self.g.wtmr}",
                     "u_u.num_retry / u_u.wtmr")
            phase.drop_objection(self)
            return

        # start_retry ignored in WAIT (no invented hop).
        got = await self._expect(
            name, "start_retry held in WAIT (still WAIT, no re-REQ)",
            start_retry=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_W:
            self.bad(name, "start_retry in WAIT ignored",
                     "state=2 (WAIT)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. Stock: wait_done_ack → NORMAL. num_retry stays (not a rst).
        got = await self._expect(name, "wait_done_ack → NORMAL (stock)",
                                 wait_done_ack=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_N:
            self.bad(name, "wait_done_ack",
                     "state=0 (NORMAL)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.num_retry != 1:
            self.bad(name, "wait_done_ack does not clear num_retry",
                     "num_retry=1", f"nr={self.g.num_retry}",
                     "u_u.num_retry")
            phase.drop_objection(self)
            return
        for i in range(3):
            got = await self._expect(
                name, f"hold NORMAL after wait_done_ack [{i}]")
            if got is None or got[0] != ST_N:
                if got is not None:
                    self.bad(name, "NORMAL holds after ack",
                             "state=0", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # 4. Second burst → WAIT, then WAIT timeout (wtmr 12500 → 0) → REQ.
        got = await self._walk_req(name, "second burst")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "second burst → WAIT")
        if got is None or got[0] != ST_W:
            if got is not None:
                self.bad(name, "second burst → WAIT",
                         "state=2", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        # Decrement 12500 times, then the wtmr==0 cycle re-enters REQ Idle.
        for i in range(RETRY_WAIT_CYC):
            got = await self._expect(name, f"WAIT decrement [{i}]")
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_W:
                self.bad(name, f"WAIT decrement [{i}] still WAIT",
                         "state=2", self._fmt(got), HIER)
                phase.drop_objection(self)
                return
        got = await self._expect(name, "WAIT timeout → REQ Idle (stock)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_Q or got[4] != 1 or got[5] != 0:
            self.bad(name, "WAIT timeout",
                     "state=1 send_idle=1 send_req=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Finish this REQ burst so num_retry becomes 3 (was 2 at WAIT entry).
        for i in range(REQ_BURST):
            got = await self._expect(name, f"timeout-REQ Req[{i + 1}/32]")
            if got is None:
                phase.drop_objection(self)
                return
        got = await self._expect(name, "timeout-REQ burst → WAIT")
        if got is None or got[0] != ST_W:
            if got is not None:
                self.bad(name, "timeout-REQ → WAIT",
                         "state=2", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 5. port_rst during WAIT clears to NORMAL (num_retry/burst, not wtmr).
        wtmr_hold = self.g.wtmr
        got = await self._expect(name, "port_rst during WAIT (stock)",
                                 port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0, 0, 0):
            self.bad(name, "port_rst during WAIT",
                     "state=0 (clears burst / num_retry / num_phy)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.num_retry != 0 or self.g.burst != 0 or self.g.num_phy != 0:
            self.bad(name, "port_rst clears counters (not wtmr)",
                     "num_retry=0 burst=0 num_phy=0",
                     f"nr={self.g.num_retry} burst={self.g.burst} "
                     f"np={self.g.num_phy}", HIER)
            phase.drop_objection(self)
            return
        if self.g.wtmr != wtmr_hold:
            self.bad(name, "port_rst does not clear wtmr (stock)",
                     f"wtmr stays {wtmr_hold}",
                     f"wtmr={self.g.wtmr}", "u_u.wtmr")
            phase.drop_objection(self)
            return

        # device_rst from REQ (same clear as port_rst).
        got = await self._expect(name, "start_retry after port_rst",
                                 start_retry=1)
        if got is None or got[0] != ST_Q:
            if got is not None:
                self.bad(name, "start_retry after port_rst",
                         "REQ Idle", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "start_retry held in REQ (no skip)",
                                 start_retry=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_Q or got[5] != 1:
            self.bad(name, "start_retry in REQ does not skip burst",
                     "state=1 send_req=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "device_rst during REQ (stock)",
                                 device_rst=1, start_retry=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0, 0, 0):
            self.bad(name, "device_rst during REQ",
                     "state=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 6. Stock: phy_retrain at burst done → RETRAIN (1-cycle) then NORMAL.
        got = await self._walk_req(name, "phy_retrain", phy_retrain=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "phy_retrain at burst done → RETRAIN",
                                 phy_retrain=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_R or got[2] != 1 or got[1] != 0 or got[3] != 0:
            self.bad(name, "phy_retrain → RETRAIN",
                     "state=3 retrain_req=1 drop_data=0 retry_error=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "RETRAIN 1-cycle → NORMAL (phy 1/4)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_N or self.g.num_phy != 1:
            self.bad(name, "RETRAIN → NORMAL",
                     "state=0 num_phy=1",
                     f"{self._fmt(got)} np={self.g.num_phy}", HIER)
            phase.drop_objection(self)
            return

        # 7. Three more phy_retrain visits → ERROR at NUM_PHY_REINIT=4.
        for k in range(3):
            got = await self._walk_req(
                name, f"phy_retrain[{k + 2}/4]", phy_retrain=1)
            if got is None:
                phase.drop_objection(self)
                return
            got = await self._expect(
                name, f"phy_retrain[{k + 2}/4] → RETRAIN",
                phy_retrain=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_R:
                self.bad(name, f"phy_retrain[{k + 2}/4]",
                         "state=3 (RETRAIN)", self._fmt(got), HIER)
                phase.drop_objection(self)
                return
            got = await self._expect(
                name, f"RETRAIN exit [{k + 2}/4]")
            if got is None:
                phase.drop_objection(self)
                return
            if k < 2:
                if got[0] != ST_N:
                    self.bad(name, f"RETRAIN [{k + 2}/4] → NORMAL",
                             "state=0", self._fmt(got), HIER)
                    phase.drop_objection(self)
                    return
            else:
                if got[0] != ST_E or got[3] != 1:
                    self.bad(name, "4 phy reinits → ERROR (stock)",
                             "state=4 retry_error=1",
                             self._fmt(got), "u_u.num_phy / u_u.st")
                    phase.drop_objection(self)
                    return

        # ERROR holds; start_retry / wait_done_ack / phy_retrain ignored.
        for i, kw in enumerate((
                {},
                {"start_retry": 1},
                {"wait_done_ack": 1},
                {"phy_retrain": 1},
        )):
            got = await self._expect(
                name, f"ERROR holds [{i}]", **kw)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_E or got[3] != 1:
                self.bad(name, f"ERROR holds [{i}]",
                         "state=4 retry_error=1", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # 8. Stock: port_rst in ERROR → NORMAL.
        got = await self._expect(name, "port_rst in ERROR (stock)",
                                 port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_N, 0, 0, 0, 0, 0, 0):
            self.bad(name, "port_rst in ERROR",
                     "state=0 (NORMAL)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.num_retry != 0 or self.g.num_phy != 0:
            self.bad(name, "port_rst in ERROR clears counters",
                     "num_retry=0 num_phy=0",
                     f"nr={self.g.num_retry} np={self.g.num_phy}", HIER)
            phase.drop_objection(self)
            return

        # device_rst from ERROR (re-enter via phy_retrain x4).
        for k in range(4):
            got = await self._walk_req(
                name, f"reenter-phy[{k + 1}/4]", phy_retrain=1)
            if got is None:
                phase.drop_objection(self)
                return
            got = await self._expect(
                name, f"reenter-phy[{k + 1}/4] RETRAIN",
                phy_retrain=1)
            if got is None:
                phase.drop_objection(self)
                return
            got = await self._expect(name, f"reenter-phy[{k + 1}/4] exit")
            if got is None:
                phase.drop_objection(self)
                return
        if got[0] != ST_E:
            self.bad(name, "reenter ERROR for device_rst",
                     "state=4", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "device_rst in ERROR (stock)",
                                 device_rst=1)
        if got is None or got[0] != ST_N:
            if got is not None:
                self.bad(name, "device_rst in ERROR",
                         "state=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 9. NUM_RETRY=15: 14× (burst→WAIT→ack) then 15th burst → RETRAIN.
        for k in range(VIBE_NUM_RETRY - 1):
            got = await self._walk_req(name, f"retry[{k + 1}/15]")
            if got is None:
                phase.drop_objection(self)
                return
            got = await self._expect(name, f"retry[{k + 1}/15] → WAIT")
            if got is None or got[0] != ST_W:
                if got is not None:
                    self.bad(name, f"retry[{k + 1}/15] WAIT",
                             "state=2", self._fmt(got), HIER)
                phase.drop_objection(self)
                return
            if self.g.num_retry != k + 1:
                self.bad(name, f"retry[{k + 1}/15] num_retry",
                         f"num_retry={k + 1}",
                         f"nr={self.g.num_retry}", "u_u.num_retry")
                phase.drop_objection(self)
                return
            got = await self._expect(
                name, f"retry[{k + 1}/15] wait_done_ack",
                wait_done_ack=1)
            if got is None or got[0] != ST_N:
                if got is not None:
                    self.bad(name, f"retry[{k + 1}/15] ack",
                             "state=0", self._fmt(got), HIER)
                phase.drop_objection(self)
                return
        got = await self._walk_req(name, "retry[15/15]")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "15th burst → RETRAIN (NUM_RETRY, no phy_retrain)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_R or got[2] != 1:
            self.bad(name, "NUM_RETRY=15 → RETRAIN",
                     "state=3 retrain_req=1",
                     self._fmt(got), "u_u.num_retry / u_u.st")
            phase.drop_objection(self)
            return
        if self.g.num_retry != VIBE_NUM_RETRY:
            self.bad(name, "NUM_RETRY increment at cap",
                     f"num_retry={VIBE_NUM_RETRY}",
                     f"nr={self.g.num_retry}", "u_u.num_retry")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "NUM_RETRY RETRAIN → NORMAL (phy 1/4)")
        if got is None or got[0] != ST_N:
            if got is not None:
                self.bad(name, "NUM_RETRY RETRAIN exit",
                         "state=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Async rst_n from WAIT (after one more burst).
        got = await self._walk_req(name, "async-from-WAIT")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "enter WAIT before async rst")
        if got is None or got[0] != ST_W:
            if got is not None:
                self.bad(name, "reach WAIT before async rst",
                         "WAIT", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.hard_reset()
        got = self._sample()
        if got[0] != ST_N or got[1] != 0 or got[3] != 0:
            self.bad(name, "async rst_n from WAIT (100ps, no posedge)",
                     "state=0 drop_data=0 retry_error=0",
                     self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_retry_req_sm)
