"""Wrap-level uvm-python TC for Decision-I stage-50 vibe_port.

Covers DUT / CHILDREN present (from rtl/port/vibe_port.sv — named
u_txrst / u_rxrst / u_lmsm / u_nw / u_dll / u_ptx / u_prx / 4×
u_at* + u_g* / u_pma / 4× u_ar* + u_rg*; wrap-local packed nets
if Verilator 5.020 VPI hides u_p.*); reset / async rst_n /
port_rst; wrap-local fec_mode=T4 and F1 afifo_ovf CDC idle;
LMSM Idle → DLL Disabled; lmsm_go observe Idle → Disc.A (no AM
invent / no tmr / st deposit). Prefer observe over Force.
Not a full-chip consecutive-green gate (stock tc_port_smoke /
tc_nw_pkt_* remain the PMA-loopback scorers). Not 1/3, 4/3,
freeze, or signoff. Does not steal make top / wrap / port /
top_wrap / mgmt_wrap / fabric_wrap / pcs_tx_wrap / pcs_rx_wrap /
lmsm_wrap.

Matches product rtl/port/vibe_port.sv: hierarchy wrap of
vibe_rst_sync u_txrst / u_rxrst, vibe_lmsm u_lmsm, vibe_nw_adapt
u_nw, vibe_dll u_dll, vibe_pcs_tx u_ptx, vibe_pcs_rx u_prx,
4× vibe_afifo u_at* + vibe_gear_160_128 u_g*, vibe_pma_bnd u_pma,
4× vibe_afifo u_ar* + vibe_gear_128_160 u_rg*. fec_mode =
VIBE_FEC_T4; F1 ovf_l CDC to afifo_ovf (do not rewrite).
vibe_pcs_tx / vibe_pcs_rx / vibe_lmsm now have pyCircuit wraps
(stages 47–49) — listed in CHILDREN, not re-migrated. No
cfg_wr_* / cfg_rd_* pin. CFG6 R/W packing is 未知 — do not
invent. Stock Icarus / pyuvm tc_port_smoke remain the official
TP-PHY scorers. Product body / ovf_l still cd71b1d0.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_DIS = 0
ST_NAME = {0: "Disabled", 1: "Param", 2: "Credit", 3: "Normal"}
LMSM_IDLE = 0
LMSM_DISC_A = 1
FEC_T4 = 0b010
# CHILDREN from rtl/port/vibe_port.sv instance names. Do not invent.
CHILDREN = (
    "u_txrst", "u_rxrst",
    "u_lmsm", "u_nw", "u_dll", "u_ptx", "u_prx",
    "u_at0", "u_at1", "u_at2", "u_at3",
    "u_g0", "u_g1", "u_g2", "u_g3",
    "u_pma",
    "u_ar0", "u_ar1", "u_ar2", "u_ar3",
    "u_rg0", "u_rg1", "u_rg2", "u_rg3",
)
HIER = "u_p.u_lmsm / u_p.u_nw / u_p.u_dll / u_p.u_ptx / u_p.u_prx / u_p.u_pma"
WRAP = "vibe_port_wrap_cocotb_top"
WRAP_NETS = (
    "status_up", "disabled", "retry_error", "proto_err",
    "fc_ovf", "rx_ovf", "afifo_ovf", "cfg0_hit",
    "fab_nw_ready", "mgmt_nw_ready", "nw_fab_vld",
    "pcs_pma_txdata",
)


class tc_vibe_port(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk_fab

    async def _idle(self):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.device_rst, 0)
        sset(d.lmsm_go, 0)
        sset(d.pma_pcs_rxdata, 0)
        sset(d.fab_nw_vld, 0)
        sset(d.fab_nw_data, 0)
        sset(d.nw_fab_ready, 1)
        sset(d.mgmt_nw_vld, 0)
        sset(d.mgmt_nw_data, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk_fab)
        await FallingEdge(self.dut.clk_fab)

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

    def _dll_sm(self):
        st = self._inner("u_p.u_dll.sm_st", None)
        if st is None:
            st = self._inner("u_p.u_dll.u_sm.st", None)
        if st is None:
            st = self._inner("u_p.u_dll.u_sm.state", None)
        return st

    def _lmsm_st(self):
        st = self._inner("u_p.lmsm_st", None)
        if st is None:
            st = self._inner("u_p.u_lmsm.state", None)
        if st is None:
            st = self._inner("u_p.u_lmsm.st", None)
        return st

    def _fmt(self):
        d = self.dut
        st = self._dll_sm()
        name = ST_NAME.get(st, f"?{st}")
        return (
            f"dll={st} ({name}) lmsm={self._lmsm_st()} "
            f"up={ival(d.status_up, -1)} dis={ival(d.disabled, -1)} "
            f"fab_rdy={ival(d.fab_nw_ready, -1)} "
            f"mgmt_rdy={ival(d.mgmt_nw_ready, -1)} "
            f"nw_fab_vld={ival(d.nw_fab_vld, -1)} "
            f"cfg0={ival(d.cfg0_hit, -1)} "
            f"aovf={ival(d.afifo_ovf, -1)} "
            f"clow={self._inner('u_p.u_dll.credit_low', -1)} "
            f"lready={self._inner('u_p.link_ready', -1)} "
            f"lup={self._inner('u_p.link_up', -1)} "
            f"fec={self._inner('u_p.fec_mode', -1)}"
        )

    def _score_children(self, name):
        """Named CHILDREN from product SV. Icarus exposes u_p.u_lmsm;
        Verilator 5.020 VPI may not. Prove missing hierarchy with
        wrap-local packed nets those children drive."""
        if not self._exists("u_p"):
            self.bad(name, "AS-0.1 §4 wrap instance",
                     "u_p present", "missing", "u_p")
            return False
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_p.{inst}")]
        if missing and len(missing) != len(CHILDREN):
            self.bad(name, "AS-0.1 §4 named children present",
                     "u_txrst u_rxrst u_lmsm u_nw u_dll u_ptx u_prx "
                     "u_at* u_g* u_pma u_ar* u_rg*",
                     f"missing={missing}", "u_p")
            return False
        if missing:
            for net in WRAP_NETS:
                if ival(getattr(self.dut, net), None) is None:
                    if net == "pcs_pma_txdata":
                        continue
                    self.bad(name, "children via wrap nets (no child VPI)",
                             f"{net} readable", "missing", f"u_p.{net}")
                    return False
        return True

    def _score_combo(self, name):
        fec = self._inner("u_p.fec_mode", None)
        if fec is not None and int(fec) != FEC_T4:
            self.bad(name, "wrap fec_mode = VIBE_FEC_T4",
                     f"fec_mode={FEC_T4}", f"fec_mode={fec}", "u_p.fec_mode")
            return False
        pe = ival(self.dut.proto_err, None)
        dll_pe = self._inner("u_p.u_dll.proto_err", None)
        if pe is not None and dll_pe is not None and int(pe) != int(dll_pe):
            self.bad(name, "wrap proto_err from u_dll",
                     f"proto_err={dll_pe}", f"proto_err={pe}", "u_p.u_dll")
            return False
        ovf = ival(self.dut.fc_ovf, None)
        dll_ovf = self._inner("u_p.u_dll.fc_ovf", None)
        if ovf is not None and dll_ovf is not None and int(ovf) != int(dll_ovf):
            self.bad(name, "wrap fc_ovf from u_dll",
                     f"fc_ovf={dll_ovf}", f"fc_ovf={ovf}", "u_p.u_dll")
            return False
        retry = ival(self.dut.retry_error, None)
        dll_re = self._inner("u_p.u_dll.retry_error", None)
        if (retry is not None and dll_re is not None
                and int(retry) != int(dll_re)):
            self.bad(name, "wrap retry_error from u_dll",
                     f"retry_error={dll_re}", f"retry_error={retry}",
                     "u_p.u_dll")
            return False
        pin_hit = ival(self.dut.cfg0_hit, None)
        dll_hit = self._inner("u_p.u_dll.cfg0_hit", None)
        if (pin_hit is not None and dll_hit is not None
                and int(pin_hit) != int(dll_hit)):
            self.bad(name, "wrap cfg0_hit from u_dll",
                     f"cfg0_hit={dll_hit}", f"cfg0_hit={pin_hit}",
                     "u_p.u_dll.cfg0_hit")
            return False
        wrap_ff = self._inner("u_p.fec_fail", None)
        prx_ff = self._inner("u_p.u_prx.fec_fail", None)
        if (wrap_ff is not None and prx_ff is not None
                and int(wrap_ff) != int(prx_ff)):
            self.bad(name, "wrap fec_fail from u_prx",
                     f"fec_fail={prx_ff}", f"fec_fail={wrap_ff}",
                     "u_p.u_prx.fec_fail")
            return False
        pin_am = self._inner("u_p.am_locked", None)
        prx_am = self._inner("u_p.u_prx.am_locked", None)
        if (pin_am is not None and prx_am is not None
                and int(pin_am) != int(prx_am)):
            self.bad(name, "wrap am_locked from u_prx",
                     f"am_locked={prx_am}", f"am_locked={pin_am}",
                     "u_p.u_prx.am_locked")
            return False
        lready = self._inner("u_p.link_ready", None)
        nwr = self._inner("u_p.nw_dll_ready", None)
        mgmt_v = ival(self.dut.mgmt_nw_vld, 0) or 0
        fab_r = ival(self.dut.fab_nw_ready, None)
        if (lready is not None and nwr is not None and fab_r is not None
                and int(fab_r) != (int(lready) and int(nwr) and not int(mgmt_v))):
            self.bad(name, "u_nw fab_nw_ready = link_ready && nw_dll_ready && !mgmt",
                     f"ready={int(lready) and int(nwr) and not int(mgmt_v)}",
                     f"ready={fab_r} {self._fmt()}", "u_p.u_nw")
            return False
        mgmt_r = ival(self.dut.mgmt_nw_ready, None)
        if (lready is not None and nwr is not None and mgmt_r is not None
                and int(mgmt_r) != (int(lready) and int(nwr))):
            self.bad(name, "u_nw mgmt_nw_ready = link_ready && nw_dll_ready",
                     f"ready={int(lready) and int(nwr)}",
                     f"ready={mgmt_r}", "u_p.u_nw")
            return False
        dll_nw = self._inner("u_p.dll_nw_vld", None)
        fab_v = ival(self.dut.nw_fab_vld, None)
        if (dll_nw is not None and fab_v is not None
                and int(dll_nw) != int(fab_v)):
            self.bad(name, "u_nw nw_fab_vld = dll_nw_vld",
                     f"nw_fab_vld={dll_nw}", f"nw_fab_vld={fab_v}",
                     "u_p.u_nw")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_port"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk_fab)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset: LMSM Idle, DLL Disabled, wrap outputs idle.
        #    F1 afifo_ovf CDC idle. Observe; no Force.
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "reset then release, LMSM Idle → DLL Disabled",
                     "disabled=1 status_up=0", self._fmt(), "u_p.u_dll.u_sm")
            phase.drop_objection(self)
            return
        lst = self._lmsm_st()
        if lst not in (None, LMSM_IDLE) and lst != LMSM_IDLE:
            self.bad(name, "reset lmsm_st",
                     "lmsm_st=0 (Idle)", self._fmt(), "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        dst = self._dll_sm()
        if dst not in (None, ST_DIS) and dst != ST_DIS:
            self.bad(name, "reset dll sm_st",
                     "sm_st=0 (Disabled)", self._fmt(), "u_p.u_dll.sm_st")
            phase.drop_objection(self)
            return
        for pin, exp in (("nw_fab_vld", 0), ("cfg0_hit", 0),
                         ("retry_error", 0), ("proto_err", 0),
                         ("fc_ovf", 0), ("rx_ovf", 0), ("afifo_ovf", 0),
                         ("fab_nw_ready", 0), ("mgmt_nw_ready", 0)):
            got = ival(getattr(d, pin), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle {pin}",
                         f"{pin}={exp}", self._fmt(), f"u_p.{pin}")
                phase.drop_objection(self)
                return

        # 2. rst_sync dest deassert after dest clocks (u_txrst / u_rxrst).
        for _ in range(4):
            await RisingEdge(d.txclk)
        for _ in range(4):
            await RisingEdge(d.rxclk)
        txr = self._inner("u_p.txrst_n", None)
        rxr = self._inner("u_p.rxrst_n", None)
        if txr not in (None, 1) and txr != 1:
            self.bad(name, "u_txrst dest deassert",
                     "txrst_n=1", f"txrst_n={txr}", "u_p.u_txrst")
            phase.drop_objection(self)
            return
        if rxr not in (None, 1) and rxr != 1:
            self.bad(name, "u_rxrst dest deassert",
                     "rxrst_n=1", f"rxrst_n={rxr}", "u_p.u_rxrst")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk_fab)
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 3. lmsm_go observe Idle → Disc.A. am_locked stays 0 (u_prx hunt;
        #    do not invent AM / Force). DLL stays Disabled (link_up=0).
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk_fab)
        sset(d.lmsm_go, 0)
        await FallingEdge(d.clk_fab)
        lst = self._lmsm_st()
        if lst is not None and int(lst) != LMSM_DISC_A:
            self.bad(name, "lmsm_go → Disc.A (observe, no AM invent)",
                     f"lmsm_st={LMSM_DISC_A}", self._fmt(), "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        await self._to_fall()
        lst = self._lmsm_st()
        if lst is not None and int(lst) != LMSM_DISC_A:
            self.bad(name, "Disc.A holds without am_locked",
                     f"lmsm_st={LMSM_DISC_A}", self._fmt(), "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "Disc.A keeps DLL Disabled (link_up=0)",
                     "disabled=1 status_up=0", self._fmt(), "u_p.u_dll")
            phase.drop_objection(self)
            return
        am = self._inner("u_p.am_locked", None)
        if am is not None and int(am) != 0:
            self.bad(name, "non-AM hunt leaves am_locked=0",
                     "am_locked=0", self._fmt(), "u_p.u_prx.am_locked")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 4. port_rst observe → LMSM Idle + DLL Disabled.
        sset(d.port_rst, 1)
        await self._to_fall()
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "port_rst force Disabled",
                     "disabled=1 status_up=0", self._fmt(), "u_p.u_dll.u_sm")
            phase.drop_objection(self)
            return
        lst = self._lmsm_st()
        if lst not in (None, LMSM_IDLE) and lst != LMSM_IDLE:
            self.bad(name, "port_rst LMSM Idle",
                     "lmsm_st=0", self._fmt(), "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        sset(d.port_rst, 0)
        await self._to_fall()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 5. Async rst_n (no posedge) clears registered wrap outputs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     "disabled=1 status_up=0", self._fmt(), "u_p.u_dll.u_sm")
            phase.drop_objection(self)
            return
        if ival(d.nw_fab_vld, 1) != 0 or ival(d.cfg0_hit, 1) != 0:
            self.bad(name, "async rst_n clears datapath valids",
                     "nw_fab_vld=0 cfg0_hit=0", self._fmt(), "u_p")
            phase.drop_objection(self)
            return
        if ival(d.afifo_ovf, 1) != 0:
            self.bad(name, "async rst_n clears F1 afifo_ovf CDC",
                     "afifo_ovf=0", self._fmt(), "u_p.afifo_ovf")
            phase.drop_objection(self)
            return
        lst = self._lmsm_st()
        if lst not in (None, LMSM_IDLE) and int(lst) != LMSM_IDLE:
            self.bad(name, "async rst_n clears lmsm_st",
                     "lmsm_st=0", self._fmt(), "u_p.u_lmsm.st")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk_fab)
        if ival(d.disabled, 0) != 1:
            self.bad(name, "after async re-reset release, LMSM Idle",
                     "disabled=1", self._fmt(), "u_p.u_dll.u_sm")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 6. Product wrap pins. No cfg_* / Appendix D / invented children.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_wr_cmd",
                       "cfg_wr_vld", "appendix_d", "irq_logic",
                       "vibe_mgmt", "vibe_top", "vibe_ub_switch",
                       "u_peer", "prst", "cna", "device_rst_n"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_port product / wrap port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in ("clk_fab", "rst_n", "port_rst", "device_rst",
                     "lmsm_go", "txclk", "rxclk",
                     "fab_nw_ready", "nw_fab_vld", "mgmt_nw_ready",
                     "status_up", "disabled", "afifo_ovf", "cfg0_hit",
                     "pcs_pma_txdata", "pma_pcs_rxdata",
                     "retry_error", "proto_err", "fc_ovf", "rx_ovf"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_port)
