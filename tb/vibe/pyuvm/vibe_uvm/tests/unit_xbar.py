"""Module-level uvm-python TC for Decision-I leaf vibe_xbar.

Covers reset clearing lock / locked / rr (combo in_ready=0,
out_vld=0); 1-beat sop&&eop route in0 dest=1; 2-beat locked
grant; candidate out_data independent of out_ready (accept
still needs out_ready); ingress RR on two-to-one conflict and
rr<=lock+1 after EOP; down port status_up=0 emits no data;
parallel grants to distinct dests; async rst_n mid-stream.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze,
or signoff.

Matches product rtl/fabric/vibe_xbar.sv: async-low rst_n,
combo cand_* independent of out_ready, accept
(out_vld / in_ready) requires out_ready, 4 ports, ingress RR
from rr[e], one full packet per grant. Instantiated by
vibe_fabric u_xbar. Stock Icarus tc_xbar_unit remains the
official TP scorer. Header-only vs stock; no invented
protocol. ovf_l (F1) is not in this module. Mgmt bypass is
fabric-level and does not enter this DUT.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

NPORT = 4
MASK2 = 0x3
MASK4 = 0xF
MASK512 = (1 << 512) - 1
HIER = "u_u.in_ready / out_vld / out_data / lock / locked / rr"


def beat(tag):
    """Distinct 512-bit body: tag in [31:0] and [511:352]."""
    tag = int(tag) & 0xFFFFFFFF
    return tag | ((tag & ((1 << 160) - 1)) << 352)


def bit(vec, idx):
    return (int(vec) >> int(idx)) & 1


class Golden:
    """Cycle-accurate lock / locked / rr / combo vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.lock = [0] * NPORT
        self.locked = [0] * NPORT
        self.rr = [0] * NPORT

    def combo(self, status_up=0, in_data=None, in_vld=0, in_sop=0, in_eop=0,
              in_dst=None, out_ready=0):
        status_up = int(status_up) & MASK4
        in_vld = int(in_vld) & MASK4
        in_sop = int(in_sop) & MASK4
        in_eop = int(in_eop) & MASK4
        out_ready = int(out_ready) & MASK4
        if in_data is None:
            in_data = [0] * NPORT
        if in_dst is None:
            in_dst = [0] * NPORT
        in_data = [int(x) & MASK512 for x in in_data]
        in_dst = [int(x) & MASK2 for x in in_dst]
        out_data = [0] * NPORT
        out_sop = [0] * NPORT
        out_eop = [0] * NPORT
        cand_vld = [0] * NPORT
        cand_src = [0] * NPORT
        for e in range(NPORT):
            if not bit(status_up, e):
                continue
            if self.locked[e]:
                src = self.lock[e] & MASK2
                if bit(in_vld, src) and (in_dst[src] & MASK2) == e:
                    out_data[e] = in_data[src]
                    out_sop[e] = bit(in_sop, src)
                    out_eop[e] = bit(in_eop, src)
                    cand_vld[e] = 1
                    cand_src[e] = src
            else:
                req = 0
                for i in range(NPORT):
                    if bit(in_vld, i) and (in_dst[i] & MASK2) == e:
                        req |= 1 << i
                win = self.rr[e] & MASK2
                for _ in range(NPORT):
                    if bit(req, win):
                        out_data[e] = in_data[win]
                        out_sop[e] = bit(in_sop, win)
                        out_eop[e] = bit(in_eop, win)
                        cand_vld[e] = 1
                        cand_src[e] = win
                        break
                    win = (win + 1) & MASK2
        in_ready = 0
        out_vld = 0
        for e in range(NPORT):
            if cand_vld[e] and bit(out_ready, e):
                out_vld |= 1 << e
                in_ready |= 1 << cand_src[e]
        return {
            "out_data": out_data,
            "out_sop": out_sop,
            "out_eop": out_eop,
            "out_vld": out_vld,
            "in_ready": in_ready,
            "cand_vld": cand_vld,
            "cand_src": cand_src,
        }

    def step(self, status_up=0, in_data=None, in_vld=0, in_sop=0, in_eop=0,
             in_dst=None, out_ready=0):
        if in_data is None:
            in_data = [0] * NPORT
        if in_dst is None:
            in_dst = [0] * NPORT
        in_dst = [int(x) & MASK2 for x in in_dst]
        c = self.combo(status_up, in_data, in_vld, in_sop, in_eop,
                       in_dst, out_ready)
        # Product NBA last-wins. First SOP assign lock<=in_dst[0]
        # is overwritten by hold / winner. rr<=lock+1 uses OLD lock.
        new_lock = self.lock[:]
        new_locked = self.locked[:]
        new_rr = self.rr[:]
        for e in range(NPORT):
            fire = bit(c["out_vld"], e) and bit(out_ready, e)
            if fire and c["out_sop"][e]:
                new_locked[e] = 1
                new_lock[e] = in_dst[0] & MASK2
            if fire:
                if self.locked[e]:
                    new_lock[e] = self.lock[e] & MASK2
                else:
                    new_locked[e] = 1
                    for i in range(NPORT):
                        if bit(c["in_ready"], i) and (in_dst[i] & MASK2) == e:
                            new_lock[e] = i & MASK2
                if c["out_eop"][e]:
                    new_locked[e] = 0
                    new_rr[e] = (self.lock[e] + 1) & MASK2
        self.lock = new_lock
        self.locked = new_locked
        self.rr = new_rr
        return self.combo(status_up, in_data, in_vld, in_sop, in_eop,
                          in_dst, out_ready)


class tc_vibe_xbar(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.status_up, MASK4)
        sset(d.in_vld, 0)
        sset(d.in_sop, 0)
        sset(d.in_eop, 0)
        sset(d.out_ready, MASK4)
        for i in range(NPORT):
            sset(getattr(d, f"in_data_{i}"), 0)
            sset(getattr(d, f"in_dst_{i}"), 0)
        self._stim = {
            "status_up": MASK4,
            "in_data": [0] * NPORT,
            "in_vld": 0,
            "in_sop": 0,
            "in_eop": 0,
            "in_dst": [0] * NPORT,
            "out_ready": MASK4,
        }

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

    async def _drive(self, status_up=None, in_data=None, in_vld=0, in_sop=0,
                     in_eop=0, in_dst=None, out_ready=None):
        d = self.dut
        if status_up is None:
            status_up = MASK4
        if out_ready is None:
            out_ready = MASK4
        if in_data is None:
            in_data = [0] * NPORT
        if in_dst is None:
            in_dst = [0] * NPORT
        in_data = list(in_data) + [0] * NPORT
        in_dst = list(in_dst) + [0] * NPORT
        in_data = [int(in_data[i]) & MASK512 for i in range(NPORT)]
        in_dst = [int(in_dst[i]) & MASK2 for i in range(NPORT)]
        status_up = int(status_up) & MASK4
        in_vld = int(in_vld) & MASK4
        in_sop = int(in_sop) & MASK4
        in_eop = int(in_eop) & MASK4
        out_ready = int(out_ready) & MASK4
        sset(d.status_up, status_up)
        sset(d.in_vld, in_vld)
        sset(d.in_sop, in_sop)
        sset(d.in_eop, in_eop)
        sset(d.out_ready, out_ready)
        for i in range(NPORT):
            sset(getattr(d, f"in_data_{i}"), in_data[i])
            sset(getattr(d, f"in_dst_{i}"), in_dst[i])
        self._stim = {
            "status_up": status_up,
            "in_data": in_data,
            "in_vld": in_vld,
            "in_sop": in_sop,
            "in_eop": in_eop,
            "in_dst": in_dst,
            "out_ready": out_ready,
        }
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return {
            "in_ready": ival(d.in_ready, -1),
            "out_vld": ival(d.out_vld, -1),
            "out_sop": ival(d.out_sop, -1),
            "out_eop": ival(d.out_eop, -1),
            "out_data": [ival(getattr(d, f"out_data_{i}"), -1)
                         for i in range(NPORT)],
        }

    def _fmt(self, s):
        data = " ".join(
            f"{i}={s['out_data'][i]}" if s['out_data'][i] is not None
            else f"{i}=X" for i in range(NPORT))
        return (f"in_ready=0x{s['in_ready']:x} out_vld=0x{s['out_vld']:x} "
                f"sop=0x{s['out_sop']:x} eop=0x{s['out_eop']:x} "
                f"data[{data}]")

    def _exp_combo(self):
        st = self._stim
        return self.g.combo(
            st["status_up"], st["in_data"], st["in_vld"], st["in_sop"],
            st["in_eop"], st["in_dst"], st["out_ready"])

    def _peek_state(self):
        try:
            u = self.dut.u_u
        except Exception:
            return None
        lock, locked, rr = [], [], []
        try:
            for k in range(NPORT):
                lock.append(ival(u.lock[k], None))
                locked.append(ival(u.locked[k], None))
                rr.append(ival(u.rr[k], None))
        except Exception:
            return None
        return lock, locked, rr

    def _score(self, name, stim, got, score_data=True):
        exp = self._exp_combo()
        if (got["in_ready"] != exp["in_ready"]
                or got["out_vld"] != exp["out_vld"]
                or got["out_sop"] != (self._pack_bits(exp["out_sop"]))
                or got["out_eop"] != (self._pack_bits(exp["out_eop"]))):
            self.bad(name, stim,
                     (f"in_ready=0x{exp['in_ready']:x} "
                      f"out_vld=0x{exp['out_vld']:x} "
                      f"sop=0x{self._pack_bits(exp['out_sop']):x} "
                      f"eop=0x{self._pack_bits(exp['out_eop']):x}"),
                     self._fmt(got), HIER)
            return False
        if score_data:
            for e in range(NPORT):
                gd = got["out_data"][e]
                ed = exp["out_data"][e] & MASK512
                if gd is None or gd < 0:
                    self.bad(name, stim + f" (out_data[{e}] X)",
                             f"out_data[{e}]={ed}",
                             self._fmt(got), f"u_u.out_data[{e}]")
                    return False
                if (gd & MASK512) != ed:
                    self.bad(name, stim + f" (out_data[{e}])",
                             f"out_data[{e}]={ed}",
                             self._fmt(got), f"u_u.out_data[{e}]")
                    return False
        st = self._peek_state()
        if st is not None:
            lock, locked, rr = st
            for k in range(NPORT):
                checks = (
                    ("lock", lock[k], self.g.lock[k], MASK2),
                    ("locked", locked[k], self.g.locked[k], 1),
                    ("rr", rr[k], self.g.rr[k], MASK2),
                )
                for key, got_v, exp_v, mask in checks:
                    if got_v is None:
                        continue
                    if (got_v & mask) != (exp_v & mask):
                        self.bad(name, stim + f" (u_u.{key}[{k}])",
                                 f"{key}[{k}]={exp_v}",
                                 f"u_u.{key}[{k}]={got_v}", f"u_u.{key}")
                        return False
        return True

    @staticmethod
    def _pack_bits(bits):
        v = 0
        for i, b in enumerate(bits):
            if b:
                v |= 1 << i
        return v

    async def _cycle(self, status_up=None, in_data=None, in_vld=0, in_sop=0,
                     in_eop=0, in_dst=None, out_ready=None):
        await self._drive(status_up, in_data, in_vld, in_sop, in_eop,
                          in_dst, out_ready)
        st = self._stim
        self.g.step(st["status_up"], st["in_data"], st["in_vld"],
                    st["in_sop"], st["in_eop"], st["in_dst"],
                    st["out_ready"])
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, status_up=None, in_data=None,
                      in_vld=0, in_sop=0, in_eop=0, in_dst=None,
                      out_ready=None, score_data=True):
        got = await self._cycle(status_up, in_data, in_vld, in_sop, in_eop,
                                in_dst, out_ready)
        if not self._score(name, stim, got, score_data=score_data):
            return None
        return got

    def _golden_selfcheck(self, name):
        gchk = Golden()
        idle = gchk.combo(status_up=MASK4, out_ready=MASK4)
        if idle["in_ready"] or idle["out_vld"] or any(idle["out_data"]):
            self.bad(name, "golden reset idle",
                     "in_ready=0 out_vld=0 data=0",
                     f"ir={idle['in_ready']} ov={idle['out_vld']}",
                     "golden")
            return False
        d0 = beat(0xA)
        gchk.step(status_up=MASK4, in_data=[d0, 0, 0, 0],
                  in_vld=1, in_sop=1, in_eop=1, in_dst=[1, 0, 0, 0],
                  out_ready=MASK4)
        post = gchk.combo(status_up=MASK4, in_data=[d0, 0, 0, 0],
                          in_vld=1, in_sop=1, in_eop=1, in_dst=[1, 0, 0, 0],
                          out_ready=MASK4)
        if not bit(post["out_vld"], 1) or not bit(post["in_ready"], 0):
            self.bad(name, "golden 1-beat in0 dest=1",
                     "out_vld[1]=1 in_ready[0]=1",
                     f"ov=0x{post['out_vld']:x} ir=0x{post['in_ready']:x}",
                     "golden")
            return False
        if (post["out_data"][1] & MASK512) != d0:
            self.bad(name, "golden 1-beat data",
                     f"out_data[1]={d0}",
                     f"out_data[1]={post['out_data'][1]}", "golden")
            return False
        if any(gchk.locked) or gchk.lock[1] != 0 or gchk.rr[1] != 1:
            self.bad(name, "golden 1-beat NBA",
                     "locked=0 lock[1]=0 rr[1]=1 (old lock+1)",
                     f"locked={gchk.locked} lock={gchk.lock} rr={gchk.rr}",
                     "golden")
            return False
        gchk.reset()
        d1 = beat(0xB)
        d2 = beat(0xC)
        gchk.step(status_up=MASK4, in_data=[d1, 0, 0, 0],
                  in_vld=1, in_sop=1, in_eop=0, in_dst=[2, 0, 0, 0],
                  out_ready=MASK4)
        if not gchk.locked[2] or gchk.lock[2] != 0:
            self.bad(name, "golden SOP lock",
                     "locked[2]=1 lock[2]=0",
                     f"locked={gchk.locked} lock={gchk.lock}", "golden")
            return False
        gchk.step(status_up=MASK4, in_data=[d2, 0, 0, 0],
                  in_vld=1, in_sop=0, in_eop=1, in_dst=[2, 0, 0, 0],
                  out_ready=MASK4)
        if gchk.locked[2] or gchk.rr[2] != 1:
            self.bad(name, "golden EOP unlock rr",
                     "locked[2]=0 rr[2]=1",
                     f"locked={gchk.locked} rr={gchk.rr}", "golden")
            return False
        gchk.reset()
        a = beat(0x1)
        b = beat(0x2)
        gchk.step(status_up=MASK4, in_data=[a, b, 0, 0],
                  in_vld=0b0011, in_sop=0b0011, in_eop=0b0011,
                  in_dst=[3, 3, 0, 0], out_ready=MASK4)
        post = gchk.combo(status_up=MASK4, in_data=[a, b, 0, 0],
                          in_vld=0b0011, in_sop=0b0011, in_eop=0b0011,
                          in_dst=[3, 3, 0, 0], out_ready=MASK4)
        if not bit(post["in_ready"], 0) or bit(post["in_ready"], 1):
            self.bad(name, "golden RR dest=3 rr=0 picks port 0",
                     "in_ready[0]=1 in_ready[1]=0",
                     f"ir=0x{post['in_ready']:x}", "golden")
            return False
        if (post["out_data"][3] & MASK512) != a:
            self.bad(name, "golden RR winner data",
                     f"out_data[3]={a}",
                     f"out_data[3]={post['out_data'][3]}", "golden")
            return False
        if gchk.rr[3] != 1:
            self.bad(name, "golden RR advance",
                     "rr[3]=1", f"rr={gchk.rr}", "golden")
            return False
        gchk.reset()
        down = gchk.combo(status_up=0xE, in_data=[0, 0, beat(0xD), 0],
                          in_vld=0b0100, in_sop=0b0100, in_eop=0b0100,
                          in_dst=[0, 0, 0, 0], out_ready=MASK4)
        if down["out_vld"] or down["out_data"][0]:
            self.bad(name, "golden down port 0",
                     "out_vld[0]=0 (no DLLDP)",
                     f"ov=0x{down['out_vld']:x}", "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_xbar"
        self.g = Golden()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: combo idle, lock/locked/rr cleared.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        if got["in_ready"] != 0 or got["out_vld"] != 0:
            self.bad(name, "reset idle ports",
                     "in_ready=0 out_vld=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. 1-beat sop&&eop: in0 dest=1, all ready/up.
        d0 = beat(0xA)
        got = await self._expect(
            name, "1-beat in0 dest=1",
            in_data=[d0, 0, 0, 0], in_vld=1, in_sop=1, in_eop=1,
            in_dst=[1, 0, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if not bit(got["out_vld"], 1) or not bit(got["in_ready"], 0):
            self.bad(name, "1-beat in0 dest=1",
                     "out_vld[1]=1 in_ready[0]=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if (got["out_data"][1] & MASK512) != d0:
            self.bad(name, "1-beat data",
                     f"out_data[1]={d0}",
                     self._fmt(got), "u_u.out_data")
            phase.drop_objection(self)
            return
        if not bit(got["out_sop"], 1) or not bit(got["out_eop"], 1):
            self.bad(name, "1-beat sop&&eop",
                     "out_sop[1]=1 out_eop[1]=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(name, "idle after 1-beat")
        if got is None:
            phase.drop_objection(self)
            return
        if got["out_vld"] != 0 or got["in_ready"] != 0:
            self.bad(name, "idle after 1-beat",
                     "in_ready=0 out_vld=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. 2-beat locked grant (sop then eop) dest=2.
        d_sop = beat(0xB)
        got = await self._expect(
            name, "2-beat SOP dest=2",
            in_data=[d_sop, 0, 0, 0], in_vld=1, in_sop=1, in_eop=0,
            in_dst=[2, 0, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["out_vld"], 2) or not bit(got["out_sop"], 2)
                or bit(got["out_eop"], 2)
                or (got["out_data"][2] & MASK512) != d_sop):
            self.bad(name, "2-beat SOP dest=2",
                     f"out_vld[2]/sop/eop=1/1/0 data={d_sop}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.locked[2] != 1 or self.g.lock[2] != 0:
            self.bad(name, "lock after SOP",
                     "locked[2]=1 lock[2]=0",
                     f"locked={self.g.locked} lock={self.g.lock}",
                     "u_u.locked")
            phase.drop_objection(self)
            return

        # Conflicting ingress must not steal the locked egress.
        steal = beat(0xEE)
        d_eop = beat(0xC)
        got = await self._expect(
            name, "locked grant holds vs conflicting in1",
            in_data=[d_eop, steal, 0, 0], in_vld=0b0011, in_sop=0,
            in_eop=0b0001, in_dst=[2, 2, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["out_vld"], 2) or bit(got["out_sop"], 2)
                or not bit(got["out_eop"], 2)
                or (got["out_data"][2] & MASK512) != d_eop
                or bit(got["in_ready"], 1)):
            self.bad(name, "locked grant holds vs in1",
                     f"out[2]={d_eop} eop in_ready[1]=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.locked[2] != 0:
            self.bad(name, "EOP clears locked",
                     "locked[2]=0",
                     f"locked={self.g.locked}", "u_u.locked")
            phase.drop_objection(self)
            return

        got = await self._expect(name, "idle after 2-beat")
        if got is None or got["out_vld"] != 0:
            if got is not None:
                self.bad(name, "idle after 2-beat",
                         "out_vld=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. Candidate grant independent of out_ready; accept needs it.
        d_hold = beat(0xE)
        got = await self._expect(
            name, "SOP dest=1 start lock",
            in_data=[d_hold, 0, 0, 0], in_vld=1, in_sop=1, in_eop=0,
            in_dst=[1, 0, 0, 0], out_ready=MASK4)
        if got is None:
            phase.drop_objection(self)
            return

        mid = beat(0x55)
        got = await self._expect(
            name, "locked, out_ready[1]=0 (candidate holds, no accept)",
            in_data=[mid, 0, 0, 0], in_vld=1, in_sop=0, in_eop=0,
            in_dst=[1, 0, 0, 0], out_ready=0xD)
        if got is None:
            phase.drop_objection(self)
            return
        if got["out_vld"] != 0 or got["in_ready"] != 0:
            self.bad(name, "out_ready[1]=0 must block accept",
                     "out_vld=0 in_ready=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if (got["out_data"][1] & MASK512) != mid:
            self.bad(name, "candidate out_data independent of out_ready",
                     f"out_data[1]={mid}",
                     self._fmt(got), "u_u.out_data")
            phase.drop_objection(self)
            return
        if self.g.locked[1] != 1:
            self.bad(name, "lock held while out_ready=0",
                     "locked[1]=1",
                     f"locked={self.g.locked}", "u_u.locked")
            phase.drop_objection(self)
            return

        d_fin = beat(0xF)
        got = await self._expect(
            name, "EOP after out_ready returns",
            in_data=[d_fin, 0, 0, 0], in_vld=1, in_sop=0, in_eop=1,
            in_dst=[1, 0, 0, 0], out_ready=MASK4)
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["out_vld"], 1) or not bit(got["out_eop"], 1)
                or (got["out_data"][1] & MASK512) != d_fin):
            self.bad(name, "EOP after out_ready returns",
                     f"out_vld[1]=1 eop data={d_fin}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(name, "idle after ready-stall packet")
        if got is None:
            phase.drop_objection(self)
            return

        # 5. Conflict: two ingress to dest 3. rr[3] starts at 0 → port 0.
        a = beat(0x1)
        b = beat(0x2)
        got = await self._expect(
            name, "conflict dest=3 rr starts at 0",
            in_data=[a, b, 0, 0], in_vld=0b0011, in_sop=0b0011,
            in_eop=0b0011, in_dst=[3, 3, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["in_ready"], 0) or bit(got["in_ready"], 1)
                or (got["out_data"][3] & MASK512) != a
                or not bit(got["out_vld"], 3)):
            self.bad(name, "conflict dest=3 first RR",
                     f"winner in0 data={a} in_ready[1]=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.rr[3] != 1:
            self.bad(name, "rr[3] after first conflict EOP",
                     "rr[3]=1 (old lock+1)",
                     f"rr={self.g.rr}", "u_u.rr")
            phase.drop_objection(self)
            return

        got = await self._expect(name, "idle between conflicts")
        if got is None:
            phase.drop_objection(self)
            return

        # Second conflict: rr[3]==1 → port 1.
        a2 = beat(0x11)
        b2 = beat(0x22)
        got = await self._expect(
            name, "conflict dest=3 rr starts at 1",
            in_data=[a2, b2, 0, 0], in_vld=0b0011, in_sop=0b0011,
            in_eop=0b0011, in_dst=[3, 3, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (bit(got["in_ready"], 0) or not bit(got["in_ready"], 1)
                or (got["out_data"][3] & MASK512) != b2):
            self.bad(name, "conflict dest=3 second RR",
                     f"winner in1 data={b2} in_ready[0]=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(name, "idle after second RR")
        if got is None:
            phase.drop_objection(self)
            return

        # 6. Down port: status_up[0]=0 gets no data DLLDP.
        dn = beat(0xD)
        got = await self._expect(
            name, "dest=0 status_up[0]=0",
            status_up=0xE, in_data=[0, 0, dn, 0],
            in_vld=0b0100, in_sop=0b0100, in_eop=0b0100,
            in_dst=[0, 0, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if bit(got["out_vld"], 0) or (got["out_data"][0] & MASK512) != 0:
            self.bad(name, "dest=0 status_up[0]=0",
                     "out_vld[0]=0 out_data[0]=0 (down, no DLLDP)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if bit(got["in_ready"], 2):
            self.bad(name, "down dest must not accept",
                     "in_ready[2]=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 7. Parallel grants to distinct dests (in0→1, in2→3).
        p0 = beat(0x31)
        p2 = beat(0x33)
        got = await self._expect(
            name, "parallel in0 dest=1 and in2 dest=3",
            in_data=[p0, 0, p2, 0], in_vld=0b0101, in_sop=0b0101,
            in_eop=0b0101, in_dst=[1, 0, 3, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["out_vld"], 1) or not bit(got["out_vld"], 3)
                or not bit(got["in_ready"], 0) or not bit(got["in_ready"], 2)
                or (got["out_data"][1] & MASK512) != p0
                or (got["out_data"][3] & MASK512) != p2):
            self.bad(name, "parallel distinct dests",
                     f"out[1]={p0} out[3]={p2}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 8. Async rst_n mid-stream (locked 2-beat) — no posedge.
        mid_sop = beat(0x77)
        got = await self._expect(
            name, "SOP dest=1 before async rst",
            in_data=[mid_sop, 0, 0, 0], in_vld=1, in_sop=1, in_eop=0,
            in_dst=[1, 0, 0, 0])
        if got is None or self.g.locked[1] != 1:
            if got is not None:
                self.bad(name, "pre-rst must be locked",
                         "locked[1]=1",
                         f"locked={self.g.locked}", "u_u.locked")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got["in_ready"] != 0 or got["out_vld"] != 0:
            self.bad(name, "async rst_n mid-stream",
                     "in_ready=0 out_vld=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)

        # After async rst, a 1-beat packet must route again.
        one2 = beat(0x22)
        got = await self._expect(
            name, "1-beat after async rst",
            in_data=[one2, 0, 0, 0], in_vld=1, in_sop=1, in_eop=1,
            in_dst=[1, 0, 0, 0])
        if got is None:
            phase.drop_objection(self)
            return
        if (not bit(got["out_vld"], 1) or not bit(got["in_ready"], 0)
                or (got["out_data"][1] & MASK512) != one2):
            self.bad(name, "1-beat after async rst",
                     f"out_vld[1]=1 in_ready[0]=1 data={one2}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_xbar)
