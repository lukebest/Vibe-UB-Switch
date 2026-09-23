"""Module-level uvm-python TC for Decision-I leaf vibe_port_sel.

Covers reset clearing egr / drop / drop_down_cnt / rr / sticky;
normal select (bitmap & status_up nonempty → egr in use_bm, drop=0);
drop_g1 + sel_vld pulses drop without bumping drop_down_cnt; empty
avail + default all-0 + port0 up picks port 0, port0 down drops and
increments drop_down_cnt (no flood); RT=00 sticky keeps the slot
when still in use_bm else pick_rr + update; RT=01 (else) successive
sel_vld rotate via rr. Not a full-chip consecutive-green gate. Not
1/3, 4/3, freeze, or signoff.

Matches product rtl/fabric/vibe_port_sel.sv: async-low rst_n, combo
avail/use_bm, pick_rr walk of 4 ports from start, compact sticky
slot fidx=vl (cfg/src/dest are product ports). Instantiated by
vibe_fabric u_ps / g_rt.u_psi. Stock Icarus tc_p0_down_drop remains
the official TP scorer. Header-only vs stock; no flood.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK4 = 0xF
MASK2 = 0x3
MASK32 = 0xFFFFFFFF
NPORT = 4
NSTICKY = 16
PORT0_BM = 0b0001
HIER = "u_u.egr / drop / drop_down_cnt"


def pick_rr(bm, start):
    """Product pick_rr(bm, start): walk 4 ports from start."""
    bm = int(bm) & MASK4
    p = int(start) & MASK2
    pick = 0
    for _ in range(NPORT):
        if (bm >> p) & 1:
            return p
        p = (p + 1) & MASK2
    return pick


def use_bm(bitmap=0, status_up=0, default_bm=0, drop_g1=0):
    """Combo: avail = drop_g1 ? 0 : (bitmap & status_up); fallback Default."""
    bitmap = int(bitmap) & MASK4
    status_up = int(status_up) & MASK4
    default_bm = int(default_bm) & MASK4
    avail = 0 if drop_g1 else (bitmap & status_up)
    if avail == 0:
        fb = PORT0_BM if default_bm == 0 else default_bm
        return fb & status_up
    return avail


class Golden:
    """Cycle-accurate egr / drop / drop_down_cnt / rr / sticky vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.egr = 0
        self.drop = 0
        self.drop_down_cnt = 0
        self.rr = 0
        self.sticky = [0] * NSTICKY

    def step(self, bitmap=0, status_up=0, default_bm=0, rt=0, drop_g1=0,
             sel_vld=0, vl=0):
        self.drop = 0
        if not sel_vld:
            return
        ub = use_bm(bitmap, status_up, default_bm, drop_g1)
        if drop_g1 or ub == 0:
            self.drop = 1
            if (not drop_g1) and ub == 0:
                self.drop_down_cnt = (self.drop_down_cnt + 1) & MASK32
            return
        if (int(rt) & MASK2) == 0:
            fidx = int(vl) & MASK4
            st = self.sticky[fidx] & MASK2
            if (ub >> st) & 1:
                self.egr = st
            else:
                p = pick_rr(ub, st)
                self.egr = p
                self.sticky[fidx] = p
        else:
            p = pick_rr(ub, self.rr)
            self.egr = p
            self.rr = (p + 1) & MASK2


class tc_vibe_port_sel(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.bitmap, 0)
        sset(d.status_up, 0)
        sset(d.default_bm, 0)
        sset(d.rt, 0)
        sset(d.drop_g1, 0)
        sset(d.sel_vld, 0)
        sset(d.cfg, 0)
        sset(d.src, 0)
        sset(d.dest, 0)
        sset(d.vl, 0)

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

    async def _drive(self, bitmap=0, status_up=0, default_bm=0, rt=0,
                     drop_g1=0, sel_vld=0, cfg=0, src=0, dest=0, vl=0):
        d = self.dut
        sset(d.bitmap, int(bitmap) & MASK4)
        sset(d.status_up, int(status_up) & MASK4)
        sset(d.default_bm, int(default_bm) & MASK4)
        sset(d.rt, int(rt) & MASK2)
        sset(d.drop_g1, 1 if drop_g1 else 0)
        sset(d.sel_vld, 1 if sel_vld else 0)
        sset(d.cfg, int(cfg) & MASK4)
        sset(d.src, int(src) & 0xFFFF)
        sset(d.dest, int(dest) & 0xFFFF)
        sset(d.vl, int(vl) & MASK4)
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return (ival(d.egr, -1), ival(d.drop, -1), ival(d.drop_down_cnt, -1))

    def _fmt(self, s, rr=None):
        egr, drop, cnt = s
        extra = f" rr={rr}" if rr is not None else ""
        return f"egr={egr} drop={drop} drop_down_cnt={cnt}{extra}"

    def _peek_inner(self):
        try:
            u = self.dut.u_u
            rr = ival(u.rr, None)
            egr = ival(u.egr, None)
            drop = ival(u.drop, None)
            cnt = ival(u.drop_down_cnt, None)
            sticky = []
            try:
                arr = u.sticky
                for k in range(NSTICKY):
                    sticky.append(ival(arr[k], None))
            except Exception:
                sticky = None
            return rr, egr, drop, cnt, sticky
        except Exception:
            return None, None, None, None, None

    def _score(self, name, stim, got, expect_in_bm=None):
        exp = (self.g.egr & MASK2, self.g.drop, self.g.drop_down_cnt & MASK32)
        if got != exp:
            self.bad(name, stim, self._fmt(exp, self.g.rr),
                     self._fmt(got), HIER)
            return False
        egr, drop, _cnt = got
        if drop not in (0, 1):
            self.bad(name, stim + " (drop 0/1)",
                     "drop=0 or 1", self._fmt(got), "u_u.drop")
            return False
        if expect_in_bm is not None and not drop:
            if egr < 0 or not ((int(expect_in_bm) >> (egr & MASK2)) & 1):
                self.bad(name, stim + " (egr must be in use_bm)",
                         f"use_bm=0x{int(expect_in_bm) & MASK4:x} bit {egr}",
                         self._fmt(got), "u_u.egr")
                return False
        irr, iegr, idrop, icnt, isticky = self._peek_inner()
        if irr is not None and (irr & MASK2) != (self.g.rr & MASK2):
            self.bad(name, stim + " (port vs u_u.rr)",
                     f"rr={self.g.rr}", f"u_u.rr={irr}", "u_u.rr")
            return False
        if iegr is not None and (iegr & MASK2) != (egr & MASK2):
            self.bad(name, stim + " (port vs u_u.egr)",
                     f"egr={egr}", f"u_u.egr={iegr}", "u_u.egr")
            return False
        if idrop is not None and idrop != drop:
            self.bad(name, stim + " (port vs u_u.drop)",
                     f"drop={drop}", f"u_u.drop={idrop}", "u_u.drop")
            return False
        if icnt is not None and (icnt & MASK32) != (self.g.drop_down_cnt & MASK32):
            self.bad(name, stim + " (port vs u_u.drop_down_cnt)",
                     f"drop_down_cnt={self.g.drop_down_cnt}",
                     f"u_u.drop_down_cnt={icnt}", "u_u.drop_down_cnt")
            return False
        if isticky is not None:
            for k, got_st in enumerate(isticky):
                if got_st is None:
                    continue
                if (got_st & MASK2) != (self.g.sticky[k] & MASK2):
                    self.bad(name, stim + f" (u_u.sticky[{k}])",
                             f"sticky[{k}]={self.g.sticky[k]}",
                             f"u_u.sticky[{k}]={got_st}", "u_u.sticky")
                    return False
        return True

    async def _cycle(self, bitmap=0, status_up=0, default_bm=0, rt=0,
                     drop_g1=0, sel_vld=0, cfg=0, src=0, dest=0, vl=0):
        await self._drive(bitmap, status_up, default_bm, rt, drop_g1,
                          sel_vld, cfg, src, dest, vl)
        self.g.step(bitmap, status_up, default_bm, rt, drop_g1, sel_vld, vl)
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, bitmap=0, status_up=0, default_bm=0,
                      rt=0, drop_g1=0, sel_vld=0, cfg=0, src=0, dest=0, vl=0,
                      expect_in_bm=None):
        got = await self._cycle(bitmap, status_up, default_bm, rt, drop_g1,
                                sel_vld, cfg, src, dest, vl)
        if not self._score(name, stim, got, expect_in_bm):
            return None
        return got

    def _golden_selfcheck(self, name):
        if pick_rr(0b0110, 0) != 1:
            self.bad(name, "golden pick_rr(0110, 0)",
                     "1", str(pick_rr(0b0110, 0)), "golden")
            return False
        if pick_rr(0b1000, 0) != 3:
            self.bad(name, "golden pick_rr(1000, 0)",
                     "3", str(pick_rr(0b1000, 0)), "golden")
            return False
        if pick_rr(0b0001, 2) != 0:
            self.bad(name, "golden pick_rr wrap to port 0",
                     "0", str(pick_rr(0b0001, 2)), "golden")
            return False
        if use_bm(0b0110, 0b1111, 0, 0) != 0b0110:
            self.bad(name, "golden nonempty avail",
                     "use_bm=6", f"use_bm={use_bm(0b0110, 0b1111, 0, 0)}",
                     "golden")
            return False
        if use_bm(0, 0b1111, 0, 0) != PORT0_BM:
            self.bad(name, "golden default all-0 → port 0",
                     "use_bm=1", f"use_bm={use_bm(0, 0b1111, 0, 0)}",
                     "golden")
            return False
        if use_bm(0, 0b1110, 0, 0) != 0:
            self.bad(name, "golden port0 down empty",
                     "use_bm=0", f"use_bm={use_bm(0, 0b1110, 0, 0)}",
                     "golden")
            return False
        # drop_g1 forces avail=0; Default all-0 then yields port0 if up.
        if use_bm(0b1111, 0b1111, 0, 1) != PORT0_BM:
            self.bad(name, "golden drop_g1 zeros avail then Default port0",
                     "use_bm=1", f"use_bm={use_bm(0b1111, 0b1111, 0, 1)}",
                     "golden")
            return False
        if use_bm(0b1111, 0b1110, 0, 1) != 0:
            self.bad(name, "golden drop_g1 + port0 down → use_bm empty",
                     "use_bm=0", f"use_bm={use_bm(0b1111, 0b1110, 0, 1)}",
                     "golden")
            return False
        gchk = Golden()
        gchk.step(bitmap=0b1111, status_up=0b1111, rt=0b01, sel_vld=1)
        if gchk.egr != 0 or gchk.drop or gchk.rr != 1:
            self.bad(name, "golden RT=01 first pick",
                     "egr=0 drop=0 rr=1",
                     f"egr={gchk.egr} drop={gchk.drop} rr={gchk.rr}",
                     "golden")
            return False
        gchk.step(bitmap=0b1111, status_up=0b1111, rt=0b01, sel_vld=1)
        if gchk.egr != 1 or gchk.rr != 2:
            self.bad(name, "golden RT=01 rotate",
                     "egr=1 rr=2", f"egr={gchk.egr} rr={gchk.rr}", "golden")
            return False
        gchk.reset()
        if (gchk.egr or gchk.drop or gchk.drop_down_cnt or gchk.rr
                or any(gchk.sticky)):
            self.bad(name, "golden reset",
                     "egr/drop/cnt/rr/sticky=0",
                     f"egr={gchk.egr} rr={gchk.rr}", "golden")
            return False
        gchk.step(bitmap=0, status_up=0b1111, default_bm=0, rt=0, sel_vld=1)
        if gchk.egr != 0 or gchk.drop:
            self.bad(name, "golden default port 0",
                     "egr=0 drop=0",
                     f"egr={gchk.egr} drop={gchk.drop}", "golden")
            return False
        gchk.step(bitmap=0, status_up=0b1110, default_bm=0, rt=0, sel_vld=1)
        if gchk.drop != 1 or gchk.drop_down_cnt != 1:
            self.bad(name, "golden port0 down drop+count",
                     "drop=1 cnt=1",
                     f"drop={gchk.drop} cnt={gchk.drop_down_cnt}", "golden")
            return False
        gchk.step(bitmap=0b1111, status_up=0b1111, drop_g1=1, sel_vld=1)
        if gchk.drop != 1 or gchk.drop_down_cnt != 1:
            self.bad(name, "golden drop_g1 no cnt bump",
                     "drop=1 cnt=1",
                     f"drop={gchk.drop} cnt={gchk.drop_down_cnt}", "golden")
            return False
        gchk.reset()
        gchk.step(bitmap=0b1111, status_up=0b1111, rt=0, vl=3, sel_vld=1)
        if gchk.egr != 0 or gchk.sticky[3] != 0:
            self.bad(name, "golden RT=00 keep sticky 0",
                     "egr=0 sticky[3]=0",
                     f"egr={gchk.egr} sticky[3]={gchk.sticky[3]}", "golden")
            return False
        gchk.step(bitmap=0b1110, status_up=0b1111, rt=0, vl=3, sel_vld=1)
        if gchk.egr != 1 or gchk.sticky[3] != 1:
            self.bad(name, "golden RT=00 pick_rr when sticky out",
                     "egr=1 sticky[3]=1",
                     f"egr={gchk.egr} sticky[3]={gchk.sticky[3]}", "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_port_sel"
        self.g = Golden()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: outs / rr / sticky are 0.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        if got != (0, 0, 0):
            self.bad(name, "reset idle ports",
                     "egr=0 drop=0 drop_down_cnt=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        irr, _ie, _id, _ic, isticky = self._peek_inner()
        if irr is not None and (irr & MASK2) != 0:
            self.bad(name, "reset rr", "rr=0", f"u_u.rr={irr}", "u_u.rr")
            phase.drop_objection(self)
            return
        if isticky is not None and any((s or 0) & MASK2 for s in isticky):
            self.bad(name, "reset sticky[0:15]",
                     "all 0", f"sticky={isticky}", "u_u.sticky")
            phase.drop_objection(self)
            return

        # 2. Normal select: bitmap & status_up nonempty → egr in use_bm, drop=0.
        got = await self._expect(
            name, "normal select bitmap=0110 status_up=1111 RT=01",
            bitmap=0b0110, status_up=0b1111, default_bm=0, rt=0b01,
            sel_vld=1, expect_in_bm=0b0110)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[1] != 0:
            self.bad(name, "normal select pick from rr=0",
                     "egr=1 drop=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        held = got
        got = await self._expect(
            name, "!sel_vld holds egr / no drop pulse",
            bitmap=0b0110, status_up=0b1111, rt=0b01, sel_vld=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (held[0], 0, held[2]):
            self.bad(name, "!sel_vld must hold egr and clear drop",
                     self._fmt((held[0], 0, held[2])), self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. drop_g1 + sel_vld → drop pulse, drop_down_cnt unchanged.
        cnt_before = self.g.drop_down_cnt
        got = await self._expect(
            name, "drop_g1 + sel_vld (no flood, no cnt)",
            bitmap=0b1111, status_up=0b1111, default_bm=0, rt=0b01,
            drop_g1=1, sel_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 1 or got[2] != cnt_before:
            self.bad(name, "drop_g1 pulse must not bump drop_down_cnt",
                     f"drop=1 drop_down_cnt={cnt_before}",
                     self._fmt(got), "u_u.drop_down_cnt")
            phase.drop_objection(self)
            return
        if got[0] != held[0]:
            self.bad(name, "drop_g1 must not rewrite egr",
                     f"egr={held[0]}", self._fmt(got), "u_u.egr")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "drop is a 1-cycle pulse (next cycle !sel_vld)",
            bitmap=0b1111, status_up=0b1111, drop_g1=1, sel_vld=0)
        if got is None or got[1] != 0 or got[2] != cnt_before:
            if got is not None:
                self.bad(name, "drop_g1 pulse width",
                         f"drop=0 drop_down_cnt={cnt_before}",
                         self._fmt(got), "u_u.drop")
            phase.drop_objection(self)
            return

        # 4. Empty avail + default all-0 + port0 up → pick 0;
        #    port0 down → drop + drop_down_cnt++ (no flood).
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        got = await self._expect(
            name, "empty bitmap + default all-0 + port0 up → egr=0",
            bitmap=0, status_up=0b1111, default_bm=0, rt=0,
            sel_vld=1, expect_in_bm=PORT0_BM)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0, 0):
            self.bad(name, "default all-0 → port 0",
                     "egr=0 drop=0 drop_down_cnt=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        cnt_before = self.g.drop_down_cnt
        got = await self._expect(
            name, "empty bitmap + default all-0 + port0 down → drop+count",
            bitmap=0, status_up=0b1110, default_bm=0, rt=0, sel_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 1 or got[2] != cnt_before + 1:
            self.bad(name, "port0 Down after empty filter (no flood)",
                     f"drop=1 drop_down_cnt={cnt_before + 1}",
                     self._fmt(got), "u_u.drop_down_cnt")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "second port0-down sel_vld increments again",
            bitmap=0, status_up=0b1110, default_bm=0, rt=0, sel_vld=1)
        if got is None or got[1] != 1 or got[2] != cnt_before + 2:
            if got is not None:
                self.bad(name, "drop_down_cnt second bump",
                         f"drop=1 drop_down_cnt={cnt_before + 2}",
                         self._fmt(got), "u_u.drop_down_cnt")
            phase.drop_objection(self)
            return

        # 5. RT=00 sticky: same vl keeps sticky port while in use_bm;
        #    when sticky port leaves use_bm, pick_rr and update sticky.
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        got = await self._expect(
            name, "RT=00 first sel vl=3 (sticky[3]=0, port0 in use_bm)",
            bitmap=0b1111, status_up=0b1111, rt=0, vl=3, sel_vld=1,
            cfg=0xA, src=0x1111, dest=0x2222, expect_in_bm=0b1111)
        if got is None or got != (0, 0, 0):
            if got is not None:
                self.bad(name, "RT=00 first pick sticky 0",
                         "egr=0 drop=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.sticky[3] != 0:
            self.bad(name, "RT=00 keep sticky when still in use_bm",
                     "sticky[3]=0", f"sticky[3]={self.g.sticky[3]}",
                     "u_u.sticky")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=00 same vl keeps sticky port 0 (cfg/src/dest ignored)",
            bitmap=0b1111, status_up=0b1111, rt=0, vl=3, sel_vld=1,
            cfg=0x5, src=0xAAAA, dest=0xBBBB, expect_in_bm=0b1111)
        if got is None or got[0] != 0 or got[1] != 0:
            if got is not None:
                self.bad(name, "RT=00 sticky hold",
                         "egr=0 drop=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=00 sticky port not in use_bm → pick_rr + update",
            bitmap=0b1110, status_up=0b1111, rt=0, vl=3, sel_vld=1,
            expect_in_bm=0b1110)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != 1 or got[1] != 0 or self.g.sticky[3] != 1:
            self.bad(name, "RT=00 pick_rr from sticky=0 on 1110",
                     "egr=1 drop=0 sticky[3]=1",
                     f"{self._fmt(got)} sticky[3]={self.g.sticky[3]}",
                     HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=00 same vl keeps updated sticky port 1",
            bitmap=0b1110, status_up=0b1111, rt=0, vl=3, sel_vld=1,
            expect_in_bm=0b1110)
        if got is None or got[0] != 1:
            if got is not None:
                self.bad(name, "RT=00 sticky hold after update",
                         "egr=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=00 different vl uses its own sticky slot (0)",
            bitmap=0b1111, status_up=0b1111, rt=0, vl=5, sel_vld=1,
            expect_in_bm=0b1111)
        if got is None or got[0] != 0:
            if got is not None:
                self.bad(name, "RT=00 independent sticky[5]",
                         "egr=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if self.g.sticky[3] != 1 or self.g.sticky[5] != 0:
            self.bad(name, "RT=00 slots stay independent",
                     "sticky[3]=1 sticky[5]=0",
                     f"sticky[3]={self.g.sticky[3]} sticky[5]={self.g.sticky[5]}",
                     "u_u.sticky")
            phase.drop_objection(self)
            return

        # 6. RT=01 (else): successive sel_vld rotate via rr.
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)

        picks = []
        for i in range(5):
            got = await self._expect(
                name, f"RT=01 rotate sel_vld [{i}]",
                bitmap=0b1111, status_up=0b1111, rt=0b01, sel_vld=1,
                expect_in_bm=0b1111)
            if got is None:
                phase.drop_objection(self)
                return
            if got[1] != 0:
                self.bad(name, f"RT=01 rotate drop [{i}]",
                         "drop=0", self._fmt(got), "u_u.drop")
                phase.drop_objection(self)
                return
            picks.append(got[0])
        if picks != [0, 1, 2, 3, 0]:
            self.bad(name, "RT=01 successive sel_vld rotate via rr",
                     "egr 0,1,2,3,0", f"picks={picks}", HIER)
            phase.drop_objection(self)
            return

        # Sparse RT=01: bitmap=0110 from rr after wrap (rr=1) → 1 then 2.
        await self._idle()
        sset(d.rst_n, 0)
        self.g.reset()
        await Timer(100, "PS")
        await self._release_reset()
        await FallingEdge(d.clk)
        sparse = []
        for i in range(3):
            got = await self._expect(
                name, f"RT=01 sparse 0110 [{i}]",
                bitmap=0b0110, status_up=0b1111, rt=0b01, sel_vld=1,
                expect_in_bm=0b0110)
            if got is None:
                phase.drop_objection(self)
                return
            sparse.append(got[0])
        if sparse != [1, 2, 1]:
            self.bad(name, "RT=01 sparse rotate ports 1,2",
                     "egr 1,2,1", f"picks={sparse}", HIER)
            phase.drop_objection(self)
            return

        # 7. Async rst_n mid-stream clears outs / rr / sticky (no posedge).
        if self.g.rr == 0 and all(s == 0 for s in self.g.sticky):
            # Leave rr nonzero first (already true after sparse walk).
            pass
        if self.g.rr == 0:
            self.bad(name, "precondition: rr nonzero before async rst",
                     "rr!=0", f"rr={self.g.rr}", "u_u.rr")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.bitmap, 0b1111)
        sset(d.status_up, 0b1111)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got != (0, 0, 0) or self.g.rr != 0 or any(self.g.sticky):
            self.bad(name, "async rst_n mid-stream",
                     "egr=0 drop=0 cnt=0 rr=0 sticky=0",
                     self._fmt(got, self.g.rr), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        got = await self._expect(
            name, "after async rst, RT=01 first pick still from rr=0",
            bitmap=0b1111, status_up=0b1111, rt=0b01, sel_vld=1,
            expect_in_bm=0b1111)
        if got is None or got != (0, 0, 0):
            if got is not None:
                self.bad(name, "post-async-rst first pick from 0",
                         "egr=0 drop=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_port_sel)
