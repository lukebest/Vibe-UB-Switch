"""Module-level uvm-python TC for Decision-I leaf vibe_dll_sm.

Covers reset → Disabled; !link_up / port_rst / dll_error → Disabled;
walk Disabled → Param → Credit → Normal on param_ok / credit_ok;
status_up only in Normal; disabled only in Disabled; hold in Normal
(entity rst is not a pin). Not a full-chip consecutive-green gate.
Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/dll/vibe_dll_sm.sv: async-low rst_n, ST_DIS=0 /
ST_PARM=1 / ST_CRD=2 / ST_NRM=3, force-Disabled if/else before the
case, combo status_up=(st==ST_NRM) and disabled=(st==ST_DIS).
Instantiated by vibe_dll u_sm. Stock Icarus tc_dll_sm_states remains
the official TP-DLL-001/002/003 scorer. Header-only vs stock; no
invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_DIS = 0
ST_PARM = 1
ST_CRD = 2
ST_NRM = 3
ST_NAME = {0: "Disabled", 1: "Param", 2: "Credit", 3: "Normal"}
HIER = "u_u.st"


def decode(st: int):
    """Product combo: state, status_up, disabled."""
    st = int(st) & 3
    return st, int(st == ST_NRM), int(st == ST_DIS)


class Golden:
    """Cycle-accurate st vs product NBA (port_rst / !link_up / dll_error win)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.st = ST_DIS

    def step(self, port_rst=0, link_up=0, param_ok=0, credit_ok=0, dll_error=0):
        if port_rst or not link_up or dll_error:
            self.st = ST_DIS
        elif self.st == ST_DIS:
            self.st = ST_PARM
        elif self.st == ST_PARM:
            if param_ok:
                self.st = ST_CRD
        elif self.st == ST_CRD:
            if credit_ok:
                self.st = ST_NRM
        else:
            self.st = ST_NRM

    def combo(self):
        return decode(self.st)


class tc_vibe_dll_sm(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 0)
        sset(d.param_ok, 0)
        sset(d.credit_ok, 0)
        sset(d.dll_error, 0)

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
            ival(d.status_up, -1),
            ival(d.disabled, -1),
        )

    def _fmt(self, s):
        st, up, dis = s
        name = ST_NAME.get(st, f"?{st}")
        return f"state={st} ({name}) status_up={up} disabled={dis}"

    async def _cycle(self, port_rst=0, link_up=0, param_ok=0, credit_ok=0,
                     dll_error=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.param_ok, 1 if param_ok else 0)
        sset(d.credit_ok, 1 if credit_ok else 0)
        sset(d.dll_error, 1 if dll_error else 0)
        self.g.step(
            port_rst=port_rst, link_up=link_up, param_ok=param_ok,
            credit_ok=credit_ok, dll_error=dll_error,
        )
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got):
        exp = self.g.combo()
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        st, up, dis = got
        if up != int(st == ST_NRM) or dis != int(st == ST_DIS):
            self.bad(name, stim + " (combo decode)",
                     f"status_up only in Normal, disabled only in Disabled "
                     f"({self._fmt(decode(st))})",
                     self._fmt(got), "u_u.status_up / u_u.disabled")
            return False
        if st == ST_NRM and (up != 1 or dis != 0):
            self.bad(name, stim + " (Normal flags)",
                     "status_up=1 disabled=0", self._fmt(got), HIER)
            return False
        if st == ST_DIS and (up != 0 or dis != 1):
            self.bad(name, stim + " (Disabled flags)",
                     "status_up=0 disabled=1", self._fmt(got), HIER)
            return False
        if st in (ST_PARM, ST_CRD) and (up != 0 or dis != 0):
            self.bad(name, stim + " (Param/Credit flags)",
                     "status_up=0 disabled=0", self._fmt(got), HIER)
            return False
        try:
            inner = ival(self.dut.u_u.st, None)
        except Exception:
            inner = None
        if inner is not None and inner != st:
            self.bad(name, stim + " (port vs u_u.st)",
                     f"st={st}", f"u_u.st={inner} state={st}", HIER)
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
        name = "tc_vibe_dll_sm"
        self.g = Golden()

        if decode(ST_DIS) == decode(ST_NRM) or decode(ST_PARM) == decode(ST_CRD):
            self.bad(name, "golden uniqueness (DIS vs NRM / PARM vs CRD)",
                     "distinct (state, status_up, disabled)",
                     f"dis={decode(ST_DIS)} nrm={decode(ST_NRM)} "
                     f"parm={decode(ST_PARM)} crd={decode(ST_CRD)}",
                     "golden")
            phase.drop_objection(self)
            return
        if decode(ST_DIS)[2] != 1 or decode(ST_NRM)[1] != 1:
            self.bad(name, "golden decode (disabled only DIS, status_up only NRM)",
                     "DIS disabled=1; NRM status_up=1",
                     f"dis={decode(ST_DIS)} nrm={decode(ST_NRM)}",
                     "golden")
            phase.drop_objection(self)
            return
        if decode(ST_PARM)[1] or decode(ST_PARM)[2] or decode(ST_CRD)[1] or decode(ST_CRD)[2]:
            self.bad(name, "golden Param/Credit flags",
                     "status_up=0 disabled=0",
                     f"parm={decode(ST_PARM)} crd={decode(ST_CRD)}",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: Disabled (stock: reset LinkUp=0).
        got = self._sample()
        if not self._score(name, "reset then release, link_up=0", got):
            phase.drop_objection(self)
            return
        if got != (ST_DIS, 0, 1):
            self.bad(name, "reset idle ports",
                     "state=0 (Disabled) status_up=0 disabled=1",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._expect(
                name, f"idle cycle {i} after reset (link_up=0, param_ok=1 junk)",
                link_up=0, param_ok=1, credit_ok=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_DIS:
                self.bad(name, f"hold Disabled while !link_up [{i}]",
                         "state=0 (Disabled)", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # Walk to Param, then async rst_n mid-walk (no posedge).
        got = await self._expect(name, "link_up=1 from Disabled → Param",
                                 link_up=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_PARM:
            self.bad(name, "LinkUp=1", "Param_Init (1)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-Param (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got != (ST_DIS, 0, 1):
            self.bad(name, "async rst_n mid-Param",
                     "state=0 disabled=1", self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle Disabled",
                           got):
            phase.drop_objection(self)
            return

        # 2. Walk Disabled → Param → Credit → Normal (stock + hold).
        # param_ok/credit_ok in Disabled do not skip Param (no invented hop).
        got = await self._expect(
            name, "link_up=1 param_ok=1 credit_ok=1 from Disabled (still Param)",
            link_up=1, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_PARM:
            self.bad(name, "DIS + oks does not skip Param",
                     "Param_Init (1)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Drop oks and hold Param (stock: stay Param while !param_ok).
        for i in range(3):
            got = await self._expect(
                name, f"hold Param while !param_ok [{i}]",
                link_up=1, param_ok=0, credit_ok=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_PARM:
                self.bad(name, f"stay Param_Init [{i}]",
                         "state=1", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        got = await self._expect(name, "param_ok → Credit_Init",
                                 link_up=1, param_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_CRD:
            self.bad(name, "param_ok", "Credit_Init (2)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        for i in range(3):
            got = await self._expect(
                name, f"hold Credit while !credit_ok [{i}]",
                link_up=1, param_ok=1, credit_ok=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_CRD:
                self.bad(name, f"stay Credit_Init [{i}]",
                         "state=2", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        got = await self._expect(name, "credit_ok → Normal status_up=1",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (ST_NRM, 1, 0):
            self.bad(name, "credit_ok",
                     "state=3 (Normal) status_up=1 disabled=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Hold Normal: entity rst is not a pin (stock).
        for i in range(4):
            got = await self._expect(
                name, f"hold Normal (no port_rst) [{i}]",
                link_up=1, param_ok=1, credit_ok=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got[0] != ST_NRM:
                self.bad(name, "remain Normal (entity rst must not force Disabled)",
                         "state=3", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # param_ok / credit_ok drop must not leave Normal.
        got = await self._expect(
            name, "hold Normal with param_ok=0 credit_ok=0",
            link_up=1, param_ok=0, credit_ok=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_NRM:
            self.bad(name, "Normal ignores param_ok/credit_ok",
                     "state=3", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. !link_up → Disabled from Normal (stock TP-DLL-002).
        got = await self._expect(name, "LinkUp=0 from Normal → Disabled",
                                 link_up=0, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_DIS:
            self.bad(name, "LinkUp=0", "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Walk back to Normal with both oks (stock 3-cycle DIS→PARM→CRD→NRM).
        got = await self._expect(name, "re-walk DIS→Param",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None or got[0] != ST_PARM:
            if got is not None:
                self.bad(name, "re-walk after !link_up",
                         "Param_Init (1)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "re-walk Param→Credit",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None or got[0] != ST_CRD:
            if got is not None:
                self.bad(name, "re-walk param_ok",
                         "Credit_Init (2)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "re-walk Credit→Normal",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None or got != (ST_NRM, 1, 0):
            if got is not None:
                self.bad(name, "re-walk credit_ok",
                         "Normal status_up=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # port_rst → Disabled even if LinkUp=1 (stock; sample while held).
        got = await self._expect(
            name, "port_rst while LinkUp=1 (sample while held)",
            port_rst=1, link_up=1, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_DIS:
            self.bad(name, "port_rst while LinkUp=1",
                     "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. dll_error → Disabled from Normal (stock).
        for stim, exp in (
                ("after port_rst: DIS→Param", ST_PARM),
                ("after port_rst: Param→Credit", ST_CRD),
                ("after port_rst: Credit→Normal", ST_NRM),
                ):
            got = await self._expect(
                name, stim, link_up=1, param_ok=1, credit_ok=1)
            if got is None or got[0] != exp:
                if got is not None:
                    self.bad(name, stim, ST_NAME[exp], self._fmt(got), HIER)
                phase.drop_objection(self)
                return
        got = await self._expect(name, "dll_error in Normal → Disabled",
                                 link_up=1, param_ok=1, credit_ok=1,
                                 dll_error=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[0] != ST_DIS:
            self.bad(name, "dll_error in Normal",
                     "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # dll_error from Param / Credit (RTL if/else; not invented states).
        got = await self._expect(name, "DIS→Param before dll_error-from-Param",
                                 link_up=1)
        if got is None or got[0] != ST_PARM:
            if got is not None:
                self.bad(name, "reach Param before dll_error",
                         "Param_Init (1)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "dll_error in Param → Disabled",
                                 link_up=1, param_ok=1, dll_error=1)
        if got is None or got[0] != ST_DIS:
            if got is not None:
                self.bad(name, "dll_error in Param",
                         "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(name, "DIS→Param before dll_error-from-Credit",
                                 link_up=1, param_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "Param→Credit before dll_error-from-Credit",
                                 link_up=1, param_ok=1)
        if got is None or got[0] != ST_CRD:
            if got is not None:
                self.bad(name, "reach Credit before dll_error",
                         "Credit_Init (2)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(name, "dll_error in Credit → Disabled",
                                 link_up=1, param_ok=1, credit_ok=1,
                                 dll_error=1)
        if got is None or got[0] != ST_DIS:
            if got is not None:
                self.bad(name, "dll_error in Credit",
                         "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # !link_up from Param; port_rst from Credit.
        got = await self._expect(name, "DIS→Param before !link_up-from-Param",
                                 link_up=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "LinkUp=0 from Param → Disabled",
                                 link_up=0, param_ok=1)
        if got is None or got[0] != ST_DIS:
            if got is not None:
                self.bad(name, "LinkUp=0 from Param",
                         "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(name, "DIS→Param before port_rst-from-Credit",
                                 link_up=1, param_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "Param→Credit before port_rst-from-Credit",
                                 link_up=1, param_ok=1)
        if got is None or got[0] != ST_CRD:
            if got is not None:
                self.bad(name, "reach Credit before port_rst",
                         "Credit_Init (2)", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "port_rst from Credit while LinkUp=1",
            port_rst=1, link_up=1, param_ok=1, credit_ok=1)
        if got is None or got[0] != ST_DIS:
            if got is not None:
                self.bad(name, "port_rst from Credit",
                         "Disabled", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Recovery: dll_error pulse then re-walk to Normal (stock recovery).
        got = await self._expect(name, "recovery DIS→Param",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "recovery Param→Credit",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "recovery Credit→Normal",
                                 link_up=1, param_ok=1, credit_ok=1)
        if got is None or got != (ST_NRM, 1, 0):
            if got is not None:
                self.bad(name, "recovery to Normal",
                         "state=3 status_up=1 disabled=0",
                         self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Async rst_n from Normal.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got[0] != ST_DIS or got[2] != 1:
            self.bad(name, "async rst_n from Normal (100ps, no posedge)",
                     "state=0 disabled=1", self._fmt(got), "u_u.st")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_sm)
