"""Wrap-level uvm-python TC for Decision-I stage-49 vibe_lmsm.

Covers DUT presence (stock vibe_lmsm u_lmsm; CHILDREN empty — no
child-instance asserts); reset / async rst_n / port_rst; light FSM
smoke on RTL-known pins only (Idle → Disc.A → Disc.C → CFG → NULL →
ACTIVE, lid_bad back to Idle, retrain_req to RTR_A). Prefer observe
over Force (no tmr / st deposit). Not a full-chip consecutive-green
gate (stock Icarus / pyuvm tc_lmsm_walk remains the official FSM
scorer). Not 1/3, 4/3, freeze, or signoff. Does not steal make top /
wrap / port / top_wrap / mgmt_wrap / fabric_wrap / pcs_tx_wrap /
pcs_rx_wrap.

Matches product rtl/lmsm/vibe_lmsm.sv: leaf FSM, no child instances.
No cfg_wr_* / cfg_rd_* pin. F1 ovf_l stays stock inside vibe_port.
CFG6 R/W packing is 未知 — do not invent. Do not invent Probe /
RXEQ_Optimize / Change_Speed / QDLWS. Stock Icarus / pyuvm leaf TCs
remain the official FSM scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# RTL-known states (vibe_lmsm.sv). Do not invent CFG opcodes.
ST_IDLE = 0
ST_DISC_A = 1
ST_DISC_C = 2
ST_CFG_A = 3
ST_CFG_K = 4
ST_CFG_C = 5
ST_EQ_P = 6
ST_EQ_A = 7
ST_NULL = 8
ST_ACTIVE = 9
ST_RTR_A = 10
ST_RTR_C = 11
CHILDREN = ()
HIER = "u_lmsm (CHILDREN empty)"
ACTIVE_WAIT = 16
WRAP = "vibe_lmsm_wrap_cocotb_top"


class tc_vibe_lmsm(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, lmsm_go=0, am_locked=0, lid_bad=0, lane0_fail=0,
                    eq_negotiated=0, retrain_req=0, port_rst=0):
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.lmsm_go, 1 if lmsm_go else 0)
        sset(d.am_locked, int(am_locked) & 0xF)
        sset(d.lid_bad, 1 if lid_bad else 0)
        sset(d.lane0_fail, 1 if lane0_fail else 0)
        sset(d.eq_negotiated, 1 if eq_negotiated else 0)
        sset(d.retrain_req, 1 if retrain_req else 0)

    async def _hold_reset(self, n=4, **kw):
        sset(self.dut.rst_n, 0)
        await self._idle(**kw)
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def _settle(self):
        await Timer(1, "NS")

    def _inner(self, path, default=None):
        try:
            return ival(hier(self.dut, path), default)
        except Exception:
            return default

    def _exists(self, path) -> bool:
        try:
            hier(self.dut, path)
            return True
        except Exception:
            return False

    def _fmt(self):
        d = self.dut
        return (
            f"st={ival(d.state, -1)} go={ival(d.lmsm_go, -1)} "
            f"am={ival(d.am_locked, -1)} lidb={ival(d.lid_bad, -1)} "
            f"l0f={ival(d.lane0_fail, -1)} eq={ival(d.eq_negotiated, -1)} "
            f"rtr={ival(d.retrain_req, -1)} prst={ival(d.port_rst, -1)} "
            f"lu={ival(d.link_up, -1)} rdy={ival(d.link_ready, -1)} "
            f"sdf={ival(d.sdf_period, -1)} wf={ival(d.width_fail, -1)} "
            f"inner_st={self._inner('u_lmsm.st', -1)}"
        )

    def _score_presence(self, name):
        """DUT present. CHILDREN is empty — no child-instance asserts.
        Icarus exposes u_lmsm; Verilator 5.020 VPI may not. Prove
        missing hierarchy with wrap-local packed nets the FSM drives."""
        if self._exists("u_lmsm"):
            return True
        for net in ("state", "link_up", "link_ready", "sdf_period",
                    "width_fail"):
            if ival(getattr(self.dut, net), None) is None:
                self.bad(name, "DUT via wrap nets (no u_lmsm VPI)",
                         f"{net} readable", "missing", f"u_lmsm.{net}")
                return False
        return True

    def _score_combo(self, name):
        d = self.dut
        st = ival(d.state, None)
        if st is None or (isinstance(st, int) and st < 0):
            self.bad(name, "wrap state readable",
                     "state resolvable", self._fmt(), "u_lmsm.state")
            return False
        st = int(st)
        inner = self._inner("u_lmsm.st", None)
        if inner is not None and int(inner) != st:
            self.bad(name, "wrap state from u_lmsm.st",
                     f"st={inner}", f"state={st}", "u_lmsm.st")
            return False
        exp_up = 1 if st in (ST_NULL, ST_ACTIVE) else 0
        exp_rdy = 1 if st == ST_ACTIVE else 0
        exp_sdf = 1 if st in (ST_NULL, ST_ACTIVE) else 0
        lu = ival(d.link_up, None)
        if lu is None or int(lu) != exp_up:
            self.bad(name, "link_up = (NULL|ACTIVE)",
                     f"link_up={exp_up}", self._fmt(), "u_lmsm.link_up")
            return False
        rdy = ival(d.link_ready, None)
        if rdy is None or int(rdy) != exp_rdy:
            self.bad(name, "link_ready = ACTIVE",
                     f"link_ready={exp_rdy}", self._fmt(),
                     "u_lmsm.link_ready")
            return False
        sdf = ival(d.sdf_period, None)
        if sdf is None or int(sdf) != exp_sdf:
            self.bad(name, "sdf_period = (NULL|ACTIVE)",
                     f"sdf_period={exp_sdf}", self._fmt(),
                     "u_lmsm.sdf_period")
            return False
        wf = ival(d.width_fail, None)
        if wf is None or int(wf) != 0:
            self.bad(name, "width_fail tied 0 (x4-only; no Probe)",
                     "width_fail=0", self._fmt(), "u_lmsm.width_fail")
            return False
        return True

    async def _expect(self, name, exp, stim):
        got = ival(self.dut.state, None)
        if got is None or int(got) != int(exp):
            self.bad(name, stim, f"state={exp}", self._fmt(),
                     "u_lmsm.state")
            return False
        if not self._score_combo(name):
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_lmsm"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_presence(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset: Idle, outs clear, width_fail=0. Stay Idle
        #    while lmsm_go=0 (observe; no Force).
        if not await self._expect(name, ST_IDLE, "reset then release Idle"):
            phase.drop_objection(self)
            return
        await self.cycles(3)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_IDLE, "lmsm_go=0 stays Idle"):
            phase.drop_objection(self)
            return

        # 2. lmsm_go → Disc.A. No lock: stay Disc.A (tmr loaded).
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_DISC_A, "lmsm_go → Disc.A"):
            phase.drop_objection(self)
            return
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_DISC_A,
                                  "Disc.A holds without am_locked"):
            phase.drop_objection(self)
            return

        # 3. am_locked=1111, lid_bad=0: Disc.C then lid_bad → Idle
        #    (U24 observe). No tmr Force.
        sset(d.am_locked, 0xF)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_DISC_C, "all_lock → Disc.C"):
            phase.drop_objection(self)
            return
        sset(d.lid_bad, 1)
        await RisingEdge(d.clk)
        sset(d.lid_bad, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_IDLE, "Disc.C lid_bad → Idle"):
            phase.drop_objection(self)
            return

        # 4. Happy walk (observe): Idle → Disc.A → Disc.C → CFG_A/K/C
        #    → NULL (no EQ) → ACTIVE. Timers stay loaded; transitions
        #    are condition-driven while tmr != 0.
        sset(d.am_locked, 0)
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_DISC_A, "re-go → Disc.A"):
            phase.drop_objection(self)
            return
        sset(d.am_locked, 0xF)
        walk = (
            (ST_DISC_C, "x4_ok → Disc.C"),
            (ST_CFG_A, "x4_ok → CFG_A"),
            (ST_CFG_K, "CFG_A → CFG_K"),
            (ST_CFG_C, "x4_ok → CFG_C"),
            (ST_NULL, "CFG_C !eq_negotiated → NULL"),
        )
        for exp, stim in walk:
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            if not await self._expect(name, exp, stim):
                phase.drop_objection(self)
                return
        saw_active = False
        for _ in range(ACTIVE_WAIT):
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            if ival(d.state, -1) == ST_ACTIVE:
                saw_active = True
                break
        if not saw_active:
            self.bad(name, "NULL 8-count → ACTIVE (observe)",
                     f"state={ST_ACTIVE}", self._fmt(), "u_lmsm.state")
            phase.drop_objection(self)
            return
        if not await self._expect(name, ST_ACTIVE, "NULL → ACTIVE"):
            phase.drop_objection(self)
            return

        # 5. retrain_req → RTR_A (observe). Then port_rst → Idle.
        sset(d.retrain_req, 1)
        await RisingEdge(d.clk)
        sset(d.retrain_req, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_RTR_A, "ACTIVE retrain_req → RTR_A"):
            phase.drop_objection(self)
            return
        sset(d.port_rst, 1)
        await RisingEdge(d.clk)
        sset(d.port_rst, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_IDLE, "port_rst → Idle"):
            phase.drop_objection(self)
            return

        # 6. Async rst_n (no posedge) clears registered st.
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_DISC_A, "pre-async Disc.A"):
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.state, 1) != ST_IDLE:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     f"state={ST_IDLE}", self._fmt(), "u_lmsm.st")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        if not await self._expect(name, ST_IDLE, "after async re-reset Idle"):
            phase.drop_objection(self)
            return

        # 7. Product wrap pins. No cfg_* / Appendix D / F1 ovf_l /
        #    smoke-top / Probe / invented children.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_cmd",
                       "cfg_wr_vld", "cfg_wr_cmd", "appendix_d", "ovf_l",
                       "u_peer", "prst", "clk_fab", "pcs_pma_txdata",
                       "irq_logic", "device_rst", "cna", "nw_fab_vld",
                       "fec_mode", "afifo_afull", "dll_pcs_data",
                       "dll_pcs_vld", "pcs_dll_data", "pcs_dll_vld",
                       "deskew_ok", "probe", "rxeq_optimize",
                       "change_speed", "qdlws"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_lmsm product / wrap port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n", "port_rst", "lmsm_go", "am_locked",
                     "lid_bad", "lane0_fail", "eq_negotiated",
                     "retrain_req", "link_up", "link_ready", "sdf_period",
                     "state", "width_fail"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_lmsm)
