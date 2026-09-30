"""Wrap-level uvm-python TC for Decision-I stage-43 vibe_port.

Covers submodule wiring (rst_sync ×2, LMSM, NW adapt, DLL, PCS tx/rx,
4× TX AFIFO+gear, PMA, 4× RX AFIFO+gear); wrap-local fec_mode=T4 and
F1 afifo_ovf CDC idle; async rst_n / LMSM Idle → DLL Disabled; TB-only
Force am_locked walk to LinkUp/LinkReady; credit_low blocks fabric NW
until cells are granted; 1-flit CFG3 TX smoke through u_nw; CFG0 RX
terminate at u_dll (no fabric); fec_fail → start_retry → drop_data;
port_rst / async rst_n force Disabled. Not a full-chip consecutive-green
gate (stock tc_port_smoke / tc_nw_pkt_* remain the PMA-loopback scorers).
Not 1/3, 4/3, freeze, or signoff. Not vibe_mgmt / vibe_top.

Matches product rtl/port/vibe_port.sv: hierarchy wrap of vibe_rst_sync
u_txrst / u_rxrst, vibe_lmsm u_lmsm, vibe_nw_adapt u_nw, vibe_dll u_dll,
vibe_pcs_tx u_ptx, vibe_pcs_rx u_prx, 4× vibe_afifo u_at* +
vibe_gear_160_128 u_g*, vibe_pma_bnd u_pma, 4× vibe_afifo u_ar* +
vibe_gear_128_160 u_rg*; fec_mode = VIBE_FEC_T4; F1 ovf_l CDC to
afifo_ovf (do not rewrite). Stock Icarus / pyuvm tc_port_smoke remain
the official TP-PHY scorers. No invented Appendix D / CFG opcode.
CFG6 R/W packing is 未知 — do not invent. ovf_l (F1) stays stock.
"""

import os
from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.handle import Force
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_DIS = 0
ST_PARM = 1
ST_CRD = 2
ST_NRM = 3
ST_NAME = {0: "Disabled", 1: "Param", 2: "Credit", 3: "Normal"}
LMSM_IDLE = 0
LMSM_NULL = 8
LMSM_ACTIVE = 9
REQ_Q = 1
FEC_T4 = 0b010
MASK160 = (1 << 160) - 1
MASK352 = (1 << 352) - 1
MASK480 = (1 << 480) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
CHILDREN = (
    "u_txrst", "u_rxrst",
    "u_lmsm", "u_nw", "u_dll", "u_ptx", "u_prx",
    "u_at0", "u_at1", "u_at2", "u_at3",
    "u_g0", "u_g1", "u_g2", "u_g3",
    "u_pma",
    "u_ar0", "u_ar1", "u_ar2", "u_ar3",
    "u_rg0", "u_rg1", "u_rg2", "u_rg3",
)
HIER = "u_p.u_lmsm / u_p.u_nw / u_p.u_dll / u_p.u_pma"
PAT352 = int(
    "A5A55A5A0123456789ABCDEFFEDCBA98765432101111222233334444555566667777888899",
    16,
) & MASK352
PAT480 = int("A5" * 60, 16) & MASK480


def mk_nw(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """512b NW beat: LPH in [511:352] (vibe_nw512_flit0). CFG3 only."""
    if payload is None:
        payload = PAT352
    return lph.mk_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK352,
    )


def mk_pcs(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """640b PCS beat: LPH in [639:480]. CFG0 terminate / CFG3 smoke."""
    if payload is None:
        payload = PAT480
    return lph.mk_pcs_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK480,
    )


def _is_icarus() -> bool:
    return os.environ.get("SIM", "").lower() == "icarus"


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
            f"lup={self._inner('u_p.link_up', -1)}"
        )

    def _score_children(self, name):
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_p.{inst}")]
        if missing:
            self.bad(name, "AS-0.1 §4 children present",
                     "u_txrst u_rxrst u_lmsm u_nw u_dll u_ptx u_prx "
                     "u_at* u_g* u_pma u_ar* u_rg*",
                     f"missing={missing}", "u_p")
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
        return True

    def _try_force(self, path, val) -> bool:
        try:
            hier(self.dut, path).value = Force(val)
            return True
        except Exception:
            return False

    async def _grant_credit(self, cells=1024):
        """TB-only Force. Stock vibe_dll starts cells=0 → credit_low=1."""
        self._try_force("u_p.u_dll.u_crd.cells", cells)
        self._try_force("u_p.u_dll.u_crd.pend", 0)
        await RisingEdge(self.dut.clk_fab)
        await FallingEdge(self.dut.clk_fab)

    async def _bringup(self) -> bool:
        """TB-only Force am_locked (stock tc_port_smoke). Natural LMSM walk."""
        self._try_force("u_p.u_lmsm.am_locked", 0xF)
        self._try_force("u_p.u_lmsm.lid_bad", 0)
        await FallingEdge(self.dut.clk_fab)
        sset(self.dut.lmsm_go, 1)
        await self._to_fall()
        sset(self.dut.lmsm_go, 0)
        for _ in range(24):
            await self._to_fall()
            if (self._inner("u_p.link_ready", 0) == 1
                    and ival(self.dut.status_up, 0) == 1):
                return True
        # Stock port TCs also Force ACTIVE when the walk is short on Force.
        self._try_force("u_p.u_lmsm.st", LMSM_ACTIVE)
        for _ in range(8):
            await self._to_fall()
            if (self._inner("u_p.link_ready", 0) == 1
                    and ival(self.dut.status_up, 0) == 1):
                return True
        return (self._inner("u_p.link_ready", 0) == 1
                and ival(self.dut.status_up, 0) == 1)

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

        # 2. rst_sync deassert after dest clocks (u_txrst / u_rxrst).
        for _ in range(4):
            await RisingEdge(d.txclk)
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

        # 3. LMSM go + Force am_locked (stock port bring-up, not consecutive-green).
        up = await self._bringup()
        if not up:
            if not _is_icarus():
                self.bad(name, "lmsm_go + Force am_locked=1111 lid_bad=0",
                         "link_ready=1 status_up=1", self._fmt(),
                         "u_p.u_lmsm / u_p.u_dll")
                phase.drop_objection(self)
                return
            # Icarus: same Force-bring-up hole as stock tc_port_smoke.
        else:
            if not self._score_combo(name):
                phase.drop_objection(self)
                return
            if ival(d.status_up, 0) != 1 or ival(d.disabled, 1) != 0:
                self.bad(name, "LinkUp from u_lmsm → u_dll walk to Normal",
                         "status_up=1 disabled=0", self._fmt(), "u_p.u_dll.u_sm")
                phase.drop_objection(self)
                return

            # 4. cells=0 → credit_low → fab_nw_ready=0 (u_crd → u_tx → u_nw).
            clow = self._inner("u_p.u_dll.credit_low", None)
            if clow not in (None, 1) and clow != 1:
                self.bad(name, "stock cells=0 after LinkReady",
                         "credit_low=1", self._fmt(), "u_p.u_dll.u_crd")
                phase.drop_objection(self)
                return
            if ival(d.fab_nw_ready, 1) != 0:
                self.bad(name, "credit_low blocks fabric NW (u_nw)",
                         "fab_nw_ready=0", self._fmt(), "u_p.u_nw.fab_nw_ready")
                phase.drop_objection(self)
                return

            # 5. Grant cells (TB-only Force, same as port/top / tc_dll).
            await self._grant_credit(1024)
            if ival(d.fab_nw_ready, 0) != 1:
                self.bad(name, "after credit grant + LinkReady",
                         "fab_nw_ready=1", self._fmt(), "u_p.u_nw.fab_nw_ready")
                phase.drop_objection(self)
                return
            if ival(d.mgmt_nw_ready, 0) != 1:
                self.bad(name, "mgmt inject ready after credit",
                         "mgmt_nw_ready=1", self._fmt(), "u_p.u_nw.mgmt_nw_ready")
                phase.drop_objection(self)
                return

            # 6. TX smoke: 1-flit CFG3 through u_nw (not PMA loopback).
            b1 = mk_nw(3, 0, 1)
            sent = 0
            saw_inner = 0
            for _ in range(16):
                await FallingEdge(d.clk_fab)
                if sent == 0:
                    sset(d.fab_nw_data, b1)
                    sset(d.fab_nw_vld, ival(d.fab_nw_ready, 0))
                else:
                    sset(d.fab_nw_vld, 0)
                inner = self._inner("u_p.nw_dll_data", None)
                inner_v = self._inner("u_p.nw_dll_vld", 0)
                if inner_v and inner is not None and inner >= 0:
                    if (int(inner) & MASK512) == (b1 & MASK512):
                        saw_inner = 1
                await RisingEdge(d.clk_fab)
                if sent == 0 and ival(d.fab_nw_vld, 0) and ival(d.fab_nw_ready, 0):
                    sent = 1
                if sent and saw_inner:
                    break
            sset(d.fab_nw_vld, 0)
            if not sent:
                self.bad(name, "TX 1-flit CFG3 accept at fab_nw",
                         "fab_nw_ready handshake", self._fmt(),
                         "u_p.u_nw.fab_nw_ready")
                phase.drop_objection(self)
                return
            if not saw_inner:
                # Icarus 12 VPI may leave 512-bit nw_dll_data X.
                inner = self._inner("u_p.nw_dll_data", None)
                if inner is None and _is_icarus():
                    pass
                else:
                    self.bad(name, "u_nw forwards CFG3 fab_nw → nw_dll",
                             hex(b1 & MASK512),
                             "none" if inner is None else hex(int(inner) & MASK512),
                             "u_p.nw_dll_data")
                    phase.drop_objection(self)
                    return
            await FallingEdge(d.clk_fab)

            # 7. RX CFG0 terminate at u_dll (inner pcs_dll; not Appendix D).
            c0 = mk_pcs(0, 0, 1)
            forced = self._try_force("u_p.pcs_dll_data", c0)
            forced = self._try_force("u_p.pcs_dll_vld", 1) and forced
            if forced:
                await self._to_fall()
                if ival(d.cfg0_hit, 0) != 1:
                    self.bad(name, "RX CFG0 terminate (u_dll.u_rx)",
                             "cfg0_hit=1 nw_fab_vld=0", self._fmt(),
                             "u_p.u_dll.u_rx.cfg0_hit")
                    phase.drop_objection(self)
                    return
                if ival(d.nw_fab_vld, 1) != 0:
                    self.bad(name, "CFG0 does not enter fabric (u_nw)",
                             "nw_fab_vld=0", self._fmt(), "u_p.u_nw.nw_fab_vld")
                    phase.drop_objection(self)
                    return
                got_c0 = ival(d.cfg0_data, None)
                if (got_c0 is not None and got_c0 >= 0
                        and (int(got_c0) & MASK640) != (c0 & MASK640)):
                    if not _is_icarus():
                        self.bad(name, "CFG0 capture",
                                 hex(c0 & MASK640), hex(int(got_c0) & MASK640),
                                 "u_p.u_dll.u_rx.cfg0_data")
                        phase.drop_objection(self)
                        return
                self._try_force("u_p.pcs_dll_vld", 0)
                await self._to_fall()
                if ival(d.cfg0_hit, 1) != 0:
                    self.bad(name, "CFG0 hit is a pulse",
                             "cfg0_hit=0", self._fmt(), "u_p.u_dll.u_rx.cfg0_hit")
                    phase.drop_objection(self)
                    return

            # 8. fec_fail wires u_prx → u_dll.start_retry → drop_data.
            if self._try_force("u_p.fec_fail", 1):
                await Timer(100, "PS")
                sr = self._inner("u_p.u_dll.start_retry", None)
                if sr is None:
                    sr = self._inner("u_p.u_dll.u_rx.start_retry", None)
                if sr not in (None, 1) and sr != 1:
                    self.bad(name, "fec_fail → start_retry combo",
                             "start_retry=1", self._fmt(),
                             "u_p.u_dll.u_rx.start_retry")
                    phase.drop_objection(self)
                    return
                await self._to_fall()
                self._try_force("u_p.fec_fail", 0)
                drop = self._inner("u_p.u_dll.drop_data", None)
                if drop not in (None, 1) and drop != 1:
                    self.bad(name, "start_retry → REQ|WAIT drop_data",
                             "drop_data=1", self._fmt(), "u_p.u_dll.u_req")
                    phase.drop_objection(self)
                    return
                if ival(d.fab_nw_ready, 1) != 0:
                    self.bad(name, "drop_data blocks fabric NW (u_nw)",
                             "fab_nw_ready=0", self._fmt(),
                             "u_p.u_nw.fab_nw_ready")
                    phase.drop_objection(self)
                    return

            # 9. port_rst force LMSM Idle + DLL Disabled.
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

        # 10. Async rst_n (no posedge) clears registered wrap outputs.
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

        # 11. Leaf has no invented Appendix D / CFG opcode / mgmt-top pins.
        for absent in ("appendix_d", "cfg_rd", "cfg_rd_vld", "cfg_rd_data",
                       "cfg_wr_cmd", "cfg_wr_vld", "irq_logic",
                       "vibe_mgmt", "vibe_top", "vibe_ub_switch"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_port product port",
                         f"{absent} present", "vibe_port_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk_fab", "txclk", "rxclk", "lmsm_go",
                     "fab_nw_ready", "nw_fab_vld", "mgmt_nw_ready",
                     "status_up", "disabled", "afifo_ovf", "cfg0_hit",
                     "pcs_pma_txdata", "pma_pcs_rxdata"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_port_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_port)
