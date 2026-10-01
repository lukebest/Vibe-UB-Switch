"""Wrap-level uvm-python TC for Decision-I stage-44 vibe_ub_switch.

Covers submodule wiring (4× vibe_port, vibe_fabric, vibe_mgmt,
4× vibe_mgmt_byp as the product DUT instantiates them); reset /
async rst_n; LMSM Idle → DLL Disabled on every port without Force
over PCS-driven nets; credit_low / !link_ready blocks fabric NW;
light CFG write smoke for RTL-known cmds 0–5 (6–15 ignore). CFG6
R/W packing is 未知 — do not invent. Not a full-chip consecutive-
green gate (stock tc_top_smoke / make top remains the official
product-pin PMA+peer scorer). Not 1/3, 4/3, freeze, or signoff.
Not a vibe_mgmt / vibe_fabric wrap migration (those stay HOLD).

Matches product rtl/top/vibe_ub_switch.sv: generate g_port[0:3]
u_port, u_fab, u_mgmt, generate g_byp[0:3] u_byp. cfg_wr_cmd is
4 bits (0=CNA, 1=route, 2=Default bitmap, 3=Port Reset, 4=device
reset, 5=lmsm_go; 6–15 ignore). No cfg_rd_* pin. F1 ovf_l stays
stock inside vibe_port. Prefer observing child-driven nets over
Force. Stock Icarus / pyuvm tc_top_smoke remain the official
top scorers. No invented Appendix D / CFG opcode.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_DIS = 0
ST_NAME = {0: "Disabled", 1: "Param", 2: "Credit", 3: "Normal"}
LMSM_IDLE = 0
PORT_N = 4
# RTL-known cfg_wr_cmd (vibe_cfg_space). Do not invent 6–15 packing.
CMD_CNA = 0
CMD_RT = 1
CMD_BM = 2
CMD_PORT_RST = 3
CMD_LMSM_GO = 5
CMD_IGNORE = 7
STOCK_CNA = 0x0001
STOCK_RT_IDX = 0x0003
STOCK_RT_DATA = 0x0000000F
STOCK_BM = 0x5
CHILDREN = tuple(
    [f"g_port[{i}].u_port" for i in range(PORT_N)]
    + ["u_fab", "u_mgmt"]
    + [f"g_byp[{i}].u_byp" for i in range(PORT_N)]
)
HIER = "u_sw.g_port[*].u_port / u_sw.u_fab / u_sw.u_mgmt / u_sw.g_byp[*].u_byp"


class tc_vibe_ub_switch(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk_fab

    async def _idle(self):
        d = self.dut
        sset(d.cfg_wr_vld, 0)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        for i in range(PORT_N):
            sset(getattr(d, f"pma_pcs_rxdata_{i}"), 0)

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

    def _port(self, i, tail=""):
        base = f"u_sw.g_port[{i}].u_port"
        return f"{base}.{tail}" if tail else base

    def _dll_sm(self, i):
        st = self._inner(self._port(i, "u_dll.sm_st"), None)
        if st is None:
            st = self._inner(self._port(i, "u_dll.u_sm.st"), None)
        if st is None:
            st = self._inner(self._port(i, "u_dll.u_sm.state"), None)
        return st

    def _lmsm_st(self, i):
        st = self._inner(self._port(i, "lmsm_st"), None)
        if st is None:
            st = self._inner(self._port(i, "u_lmsm.state"), None)
        if st is None:
            st = self._inner(self._port(i, "u_lmsm.st"), None)
        return st

    def _fmt(self):
        d = self.dut
        bits = []
        for i in range(PORT_N):
            st = self._dll_sm(i)
            bits.append(
                f"p{i}:dll={st}({ST_NAME.get(st, f'?{st}')})"
                f"/lmsm={self._lmsm_st(i)}"
                f"/up={self._inner(self._port(i, 'status_up'), -1)}"
                f"/dis={self._inner(self._port(i, 'disabled'), -1)}"
                f"/frdy={self._inner(self._port(i, 'fab_nw_ready'), -1)}"
                f"/clow={self._inner(self._port(i, 'u_dll.credit_low'), -1)}"
            )
        return (
            f"irq={ival(d.irq_logic, -1)} rdy={ival(d.cfg_wr_ready, -1)} "
            f"wdis={self._inner('u_sw.disabled', -1)} "
            f"wup={self._inner('u_sw.status_up', -1)} "
            f"frdy={self._inner('u_sw.fab_nw_ready', -1)} "
            + " ".join(bits)
        )

    def _score_children(self, name):
        """u_fab / u_mgmt are named instances. 4× port / 4× byp live in
        generate — Icarus exposes `g_port[i].u_port`; Verilator 5.020 VPI
        does not map those scopes. Prove the generate with wrap-local
        packed nets the DUT drives from those children."""
        if not self._exists("u_sw.u_fab") or not self._exists("u_sw.u_mgmt"):
            self.bad(name, "AS-0.1 §4/§17 children present",
                     "u_fab and u_mgmt instances",
                     f"fab={self._exists('u_sw.u_fab')} "
                     f"mgmt={self._exists('u_sw.u_mgmt')}", "u_sw")
            return False
        have_port = [self._exists(self._port(i)) for i in range(PORT_N)]
        have_byp = [self._exists(f"u_sw.g_byp[{i}].u_byp")
                    for i in range(PORT_N)]
        if any(have_port) and not all(have_port):
            self.bad(name, "AS-0.1 §4 4× vibe_port generate",
                     "all four g_port[i].u_port",
                     f"have={have_port}", "u_sw.g_port")
            return False
        if not any(have_port):
            for net in ("status_up", "disabled", "port_rst", "lmsm_go",
                        "fab_nw_ready", "nw_fab_vld"):
                if self._inner(f"u_sw.{net}", None) is None:
                    self.bad(name, "4× vibe_port via wrap nets (no g_port VPI)",
                             f"u_sw.{net} readable", "missing", f"u_sw.{net}")
                    return False
        if any(have_byp) and not all(have_byp):
            self.bad(name, "AS-0.1 §4 4× vibe_mgmt_byp generate",
                     "all four g_byp[i].u_byp",
                     f"have={have_byp}", "u_sw.g_byp")
            return False
        if not any(have_byp):
            if self._inner("u_sw.mgmt_nw_vld", None) is None:
                self.bad(name, "4× vibe_mgmt_byp via wrap nets (no g_byp VPI)",
                         "u_sw.mgmt_nw_vld readable", "missing",
                         "u_sw.mgmt_nw_vld")
                return False
        return True

    def _score_combo(self, name):
        pin_irq = ival(self.dut.irq_logic, None)
        mgmt_irq = self._inner("u_sw.u_mgmt.irq_logic", None)
        if (pin_irq is not None and mgmt_irq is not None
                and int(pin_irq) != int(mgmt_irq)):
            self.bad(name, "wrap irq_logic from u_mgmt",
                     f"irq_logic={mgmt_irq}", f"irq_logic={pin_irq}",
                     "u_sw.u_mgmt.irq_logic")
            return False
        pin_rdy = ival(self.dut.cfg_wr_ready, None)
        mgmt_rdy = self._inner("u_sw.u_mgmt.cfg_wr_ready", None)
        if (pin_rdy is not None and mgmt_rdy is not None
                and int(pin_rdy) != int(mgmt_rdy)):
            self.bad(name, "wrap cfg_wr_ready from u_mgmt",
                     f"cfg_wr_ready={mgmt_rdy}", f"cfg_wr_ready={pin_rdy}",
                     "u_sw.u_mgmt.cfg_wr_ready")
            return False
        for net in ("cna", "cna_written", "default_bm", "rt_wr_en",
                    "rt_wr_idx", "rt_wr_data"):
            mg = self._inner(f"u_sw.u_mgmt.{net}", None)
            fb = self._inner(f"u_sw.u_fab.{net}", None)
            if mg is not None and fb is not None and int(mg) != int(fb):
                self.bad(name, f"u_mgmt.{net} wired to u_fab",
                         f"{net}={mg}", f"{net}={fb}", f"u_sw.{net}")
                return False
        for i in range(PORT_N):
            pup = self._inner(self._port(i, "status_up"), None)
            pdis = self._inner(self._port(i, "disabled"), None)
            wup = self._inner("u_sw.status_up", None)
            wdis = self._inner("u_sw.disabled", None)
            if (pup is not None and wup is not None
                    and int(pup) != ((int(wup) >> i) & 1)):
                self.bad(name, f"wrap status_up[{i}] from u_port",
                         f"status_up[{i}]={pup}",
                         f"status_up={wup}", self._port(i, "status_up"))
                return False
            if (pdis is not None and wdis is not None
                    and int(pdis) != ((int(wdis) >> i) & 1)):
                self.bad(name, f"wrap disabled[{i}] from u_port",
                         f"disabled[{i}]={pdis}",
                         f"disabled={wdis}", self._port(i, "disabled"))
                return False
        return True

    async def _cfgw(self, cmd, idx, data):
        """One accepted cfg_wr beat. Sample child nets on the write cycle."""
        d = self.dut
        await FallingEdge(d.clk_fab)
        sset(d.cfg_wr_cmd, cmd)
        sset(d.cfg_wr_idx, idx)
        sset(d.cfg_wr_data, data)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk_fab)
        await FallingEdge(d.clk_fab)
        snap = {
            "cna": self._inner("u_sw.u_mgmt.cna", None),
            "cna_written": self._inner("u_sw.u_mgmt.cna_written", None),
            "default_bm": self._inner("u_sw.u_mgmt.default_bm", None),
            "lmsm_go": self._inner("u_sw.lmsm_go", None),
            "port_rst": self._inner("u_sw.port_rst", None),
            "device_rst": self._inner("u_sw.device_rst", None),
            "irq_clr": self._inner("u_sw.u_mgmt.u_cfg.irq_clr", None),
            "rt_wr_en": self._inner("u_sw.u_mgmt.rt_wr_en", None),
            "rt_wr_idx": self._inner("u_sw.u_mgmt.rt_wr_idx", None),
            "rt_wr_data": self._inner("u_sw.u_mgmt.rt_wr_data", None),
            "fab_cna": self._inner("u_sw.u_fab.cna", None),
            "fab_bm": self._inner("u_sw.u_fab.default_bm", None),
            "fab_rt_en": self._inner("u_sw.u_fab.rt_wr_en", None),
        }
        sset(d.cfg_wr_vld, 0)
        return snap

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_ub_switch"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk_fab)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset: every port LMSM Idle → DLL Disabled; mgmt idle.
        if ival(d.cfg_wr_ready, 0) != 1:
            self.bad(name, "reset then release, cfg_wr_ready tied",
                     "cfg_wr_ready=1", self._fmt(), "u_sw.u_mgmt.cfg_wr_ready")
            phase.drop_objection(self)
            return
        if ival(d.irq_logic, 1) != 0:
            self.bad(name, "reset then release, irq_logic idle",
                     "irq_logic=0", self._fmt(), "u_sw.u_mgmt.irq_logic")
            phase.drop_objection(self)
            return
        wdis = self._inner("u_sw.disabled", None)
        wup = self._inner("u_sw.status_up", None)
        if wdis not in (None, 0xF) and int(wdis) != 0xF:
            self.bad(name, "reset 4× port Disabled (wrap packed)",
                     "disabled=4'b1111", self._fmt(), "u_sw.disabled")
            phase.drop_objection(self)
            return
        if wup not in (None, 0) and int(wup) != 0:
            self.bad(name, "reset 4× port not LinkUp (wrap packed)",
                     "status_up=4'b0000", self._fmt(), "u_sw.status_up")
            phase.drop_objection(self)
            return
        for net, exp in (("fab_nw_ready", 0), ("nw_fab_vld", 0),
                         ("mgmt_nw_vld", 0), ("lmsm_go", 0),
                         ("port_rst", 0)):
            got = self._inner(f"u_sw.{net}", None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle wrap {net}",
                         f"{net}={exp}", self._fmt(), f"u_sw.{net}")
                phase.drop_objection(self)
                return
        for i in range(PORT_N):
            dis = self._inner(self._port(i, "disabled"), None)
            up = self._inner(self._port(i, "status_up"), None)
            if dis not in (None, 1) and dis != 1:
                self.bad(name, f"reset port{i} Disabled",
                         "disabled=1", self._fmt(), self._port(i, "disabled"))
                phase.drop_objection(self)
                return
            if up not in (None, 0) and up != 0:
                self.bad(name, f"reset port{i} not LinkUp",
                         "status_up=0", self._fmt(), self._port(i, "status_up"))
                phase.drop_objection(self)
                return
            lst = self._lmsm_st(i)
            if lst not in (None, LMSM_IDLE) and lst != LMSM_IDLE:
                self.bad(name, f"reset port{i} lmsm_st Idle",
                         "lmsm_st=0", self._fmt(), self._port(i, "u_lmsm"))
                phase.drop_objection(self)
                return
            dst = self._dll_sm(i)
            if dst not in (None, ST_DIS) and dst != ST_DIS:
                self.bad(name, f"reset port{i} dll Disabled",
                         "sm_st=0", self._fmt(), self._port(i, "u_dll.sm_st"))
                phase.drop_objection(self)
                return
            for pin, exp in (("nw_fab_vld", 0), ("fab_nw_ready", 0),
                             ("mgmt_nw_vld", 0), ("afifo_ovf", 0)):
                got = self._inner(self._port(i, pin), None)
                if got is None or (isinstance(got, int) and got < 0):
                    continue
                if int(got) != exp:
                    self.bad(name, f"reset idle port{i}.{pin}",
                             f"{pin}={exp}", self._fmt(),
                             self._port(i, pin))
                    phase.drop_objection(self)
                    return
            byp_v = self._inner(f"u_sw.g_byp[{i}].u_byp.out_vld", None)
            if byp_v not in (None, 0) and byp_v != 0:
                self.bad(name, f"reset g_byp[{i}] idle",
                         "out_vld=0", f"out_vld={byp_v}",
                         f"u_sw.g_byp[{i}].u_byp")
                phase.drop_objection(self)
                return

        # 2. rst_sync dest deassert after dest clocks (observe, no Force).
        for _ in range(4):
            await RisingEdge(d.txclk_0)
        for i in range(PORT_N):
            txr = self._inner(self._port(i, "txrst_n"), None)
            rxr = self._inner(self._port(i, "rxrst_n"), None)
            if txr not in (None, 1) and txr != 1:
                self.bad(name, f"port{i} u_txrst dest deassert",
                         "txrst_n=1", f"txrst_n={txr}",
                         self._port(i, "u_txrst"))
                phase.drop_objection(self)
                return
            if rxr not in (None, 1) and rxr != 1:
                self.bad(name, f"port{i} u_rxrst dest deassert",
                         "rxrst_n=1", f"rxrst_n={rxr}",
                         self._port(i, "u_rxrst"))
                phase.drop_objection(self)
                return
        await FallingEdge(d.clk_fab)
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 3. credit / path block: cells=0 + !link_ready → fab_nw_ready=0.
        # Observe child-driven wrap nets — no Force over PCS-driven am_locked.
        frw = self._inner("u_sw.fab_nw_ready", None)
        if frw not in (None, 0) and int(frw) != 0:
            self.bad(name, "credit/path blocks fabric NW (wrap packed)",
                     "fab_nw_ready=4'b0000", self._fmt(),
                     "u_sw.fab_nw_ready")
            phase.drop_objection(self)
            return
        for i in range(PORT_N):
            clow = self._inner(self._port(i, "u_dll.credit_low"), None)
            if clow not in (None, 1) and clow != 1:
                self.bad(name, f"stock cells=0 after reset port{i}",
                         "credit_low=1", self._fmt(),
                         self._port(i, "u_dll.u_crd"))
                phase.drop_objection(self)
                return
            lready = self._inner(self._port(i, "link_ready"), None)
            if lready not in (None, 0) and lready != 0:
                self.bad(name, f"LMSM Idle, port{i} not LinkReady",
                         "link_ready=0", self._fmt(),
                         self._port(i, "link_ready"))
                phase.drop_objection(self)
                return
            fr = self._inner(self._port(i, "fab_nw_ready"), None)
            if fr not in (None, 0) and fr != 0:
                self.bad(name, f"credit/path blocks fabric NW port{i}",
                         "fab_nw_ready=0", self._fmt(),
                         self._port(i, "fab_nw_ready"))
                phase.drop_objection(self)
                return

        # 4. Light CFG smoke — only RTL-known opcodes (0–5; 7 ignore).
        snap = await self._cfgw(CMD_CNA, 0, STOCK_CNA)
        if snap["cna"] not in (None, STOCK_CNA) and snap["cna"] != STOCK_CNA:
            self.bad(name, "cfg_wr cmd=0 CNA",
                     f"u_mgmt.cna={STOCK_CNA}", f"cna={snap['cna']}",
                     "u_sw.u_mgmt.cna")
            phase.drop_objection(self)
            return
        if (snap["cna_written"] not in (None, 1)
                and snap["cna_written"] != 1):
            self.bad(name, "cfg_wr cmd=0 sets cna_written",
                     "cna_written=1", f"cna_written={snap['cna_written']}",
                     "u_sw.u_mgmt.cna_written")
            phase.drop_objection(self)
            return
        if (snap["fab_cna"] is not None and snap["cna"] is not None
                and int(snap["fab_cna"]) != int(snap["cna"])):
            self.bad(name, "CNA wire u_mgmt → u_fab",
                     f"cna={snap['cna']}", f"cna={snap['fab_cna']}",
                     "u_sw.u_fab.cna")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_RT, STOCK_RT_IDX, STOCK_RT_DATA)
        if snap["rt_wr_en"] not in (None, 1) and snap["rt_wr_en"] != 1:
            self.bad(name, "cfg_wr cmd=1 route pulse",
                     "rt_wr_en=1", f"rt_wr_en={snap['rt_wr_en']}",
                     "u_sw.u_mgmt.rt_wr_en")
            phase.drop_objection(self)
            return
        if (snap["fab_rt_en"] is not None and snap["rt_wr_en"] is not None
                and int(snap["fab_rt_en"]) != int(snap["rt_wr_en"])):
            self.bad(name, "rt_wr_en wire u_mgmt → u_fab",
                     f"rt_wr_en={snap['rt_wr_en']}",
                     f"rt_wr_en={snap['fab_rt_en']}", "u_sw.u_fab.rt_wr_en")
            phase.drop_objection(self)
            return
        if (snap["rt_wr_idx"] not in (None, STOCK_RT_IDX)
                and snap["rt_wr_idx"] != STOCK_RT_IDX):
            self.bad(name, "cfg_wr cmd=1 captures idx",
                     hex(STOCK_RT_IDX),
                     "none" if snap["rt_wr_idx"] is None
                     else hex(int(snap["rt_wr_idx"])),
                     "u_sw.u_mgmt.rt_wr_idx")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_BM, 0, STOCK_BM)
        if snap["default_bm"] not in (None, STOCK_BM) and snap["default_bm"] != STOCK_BM:
            self.bad(name, "cfg_wr cmd=2 Default bitmap",
                     f"default_bm={STOCK_BM}",
                     f"default_bm={snap['default_bm']}",
                     "u_sw.u_mgmt.default_bm")
            phase.drop_objection(self)
            return
        if (snap["fab_bm"] is not None and snap["default_bm"] is not None
                and int(snap["fab_bm"]) != int(snap["default_bm"])):
            self.bad(name, "default_bm wire u_mgmt → u_fab",
                     f"default_bm={snap['default_bm']}",
                     f"default_bm={snap['fab_bm']}",
                     "u_sw.u_fab.default_bm")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_LMSM_GO, 0, 0)
        go = snap["lmsm_go"]
        if go is not None and ((int(go) >> 0) & 1) != 1:
            self.bad(name, "cfg_wr cmd=5 pulse lmsm_go[0]",
                     "lmsm_go[0]=1", f"lmsm_go={go}", "u_sw.lmsm_go")
            phase.drop_objection(self)
            return
        await self._to_fall()
        # No Force am_locked: LMSM stays Idle / ports stay Disabled.
        wdis = self._inner("u_sw.disabled", None)
        if wdis is not None and int(wdis) != 0xF:
            self.bad(name, "lmsm_go without am_locked stays Disabled",
                     "disabled=4'b1111 (no Force over PCS)", self._fmt(),
                     "u_sw.disabled")
            phase.drop_objection(self)
            return
        if self._inner(self._port(0, "disabled"), 1) == 0:
            self.bad(name, "lmsm_go without am_locked stays Disabled",
                     "disabled=1 (no Force over PCS)", self._fmt(),
                     self._port(0, "u_lmsm"))
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_PORT_RST, 0, 1)
        pr = snap["port_rst"]
        if pr is not None and ((int(pr) >> 0) & 1) != 1:
            self.bad(name, "cfg_wr cmd=3 Port Reset W1C port0",
                     "port_rst[0]=1", f"port_rst={pr}", "u_sw.port_rst")
            phase.drop_objection(self)
            return
        wdis = self._inner("u_sw.disabled", None)
        if wdis is not None and (int(wdis) & 1) != 1:
            self.bad(name, "port_rst keeps port0 Disabled (wrap packed)",
                     "disabled[0]=1", self._fmt(), "u_sw.disabled")
            phase.drop_objection(self)
            return
        if self._inner(self._port(0, "disabled"), 1) == 0:
            self.bad(name, "port_rst keeps port0 Disabled",
                     "disabled=1", self._fmt(), self._port(0, "disabled"))
            phase.drop_objection(self)
            return

        held_cna = self._inner("u_sw.u_mgmt.cna", STOCK_CNA)
        snap = await self._cfgw(CMD_IGNORE, 0, 0xA5A5)
        if (held_cna is not None and snap["cna"] is not None
                and int(snap["cna"]) != int(held_cna)):
            self.bad(name, "cfg_wr cmd=7 ignore (no invented CFG6)",
                     f"cna stays {held_cna}", f"cna={snap['cna']}",
                     "u_sw.u_mgmt.cna")
            phase.drop_objection(self)
            return
        if snap["irq_clr"] not in (None, 1) and snap["irq_clr"] != 1:
            self.bad(name, "cmd 6–15 ignore still irq_clr",
                     "irq_clr=1", f"irq_clr={snap['irq_clr']}",
                     "u_sw.u_mgmt.u_cfg.irq_clr")
            phase.drop_objection(self)
            return
        # CFG6 packing is 未知 — do not drive invented Appendix D / 0x10.
        if self._inner("u_sw.u_fab.fab_mgmt_cfg6_hit", 0) not in (None, 0):
            hit = self._inner("u_sw.u_fab.fab_mgmt_cfg6_hit", 0)
            if hit not in (None, 0) and int(hit) != 0:
                self.bad(name, "no invented CFG6 beat on wrap CFG writes",
                         "fab_mgmt_cfg6_hit=0", f"hit={hit}",
                         "u_sw.u_fab.fab_mgmt_cfg6_hit")
                phase.drop_objection(self)
                return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 5. Async rst_n (no posedge) clears registered wrap outputs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.irq_logic, 1) != 0:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     "irq_logic=0", self._fmt(), "u_sw.u_mgmt.irq_logic")
            phase.drop_objection(self)
            return
        wdis = self._inner("u_sw.disabled", None)
        wup = self._inner("u_sw.status_up", None)
        wnv = self._inner("u_sw.nw_fab_vld", None)
        if wdis not in (None, 0xF) and int(wdis) != 0xF:
            self.bad(name, "async rst_n 4× Disabled (wrap packed)",
                     "disabled=4'b1111", self._fmt(), "u_sw.disabled")
            phase.drop_objection(self)
            return
        if wup not in (None, 0) and int(wup) != 0:
            self.bad(name, "async rst_n clears status_up",
                     "status_up=0", self._fmt(), "u_sw.status_up")
            phase.drop_objection(self)
            return
        if wnv not in (None, 0) and int(wnv) != 0:
            self.bad(name, "async rst_n clears nw_fab_vld",
                     "nw_fab_vld=0", self._fmt(), "u_sw.nw_fab_vld")
            phase.drop_objection(self)
            return
        for i in range(PORT_N):
            dis = self._inner(self._port(i, "disabled"), None)
            if dis not in (None, 1) and dis != 1:
                self.bad(name, f"async rst_n port{i} Disabled",
                         "disabled=1", self._fmt(),
                         self._port(i, "u_dll.u_sm"))
                phase.drop_objection(self)
                return
            nv = self._inner(self._port(i, "nw_fab_vld"), None)
            if nv not in (None, 0) and nv != 0:
                self.bad(name, f"async rst_n clears port{i} nw_fab_vld",
                         "nw_fab_vld=0", self._fmt(),
                         self._port(i, "nw_fab_vld"))
                phase.drop_objection(self)
                return
        cna = self._inner("u_sw.u_mgmt.cna", None)
        if cna not in (None, 0) and cna != 0:
            self.bad(name, "async rst_n clears CNA",
                     "cna=0", f"cna={cna}", "u_sw.u_mgmt.cna")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk_fab)
        if ival(d.irq_logic, 1) != 0 or ival(d.cfg_wr_ready, 0) != 1:
            self.bad(name, "after async re-reset release",
                     "irq_logic=0 cfg_wr_ready=1", self._fmt(), "u_sw")
            phase.drop_objection(self)
            return
        wdis = self._inner("u_sw.disabled", None)
        if wdis is not None and int(wdis) != 0xF:
            self.bad(name, "after async re-reset, LMSM Idle",
                     "disabled=4'b1111", self._fmt(), "u_sw.disabled")
            phase.drop_objection(self)
            return
        if self._inner(self._port(0, "disabled"), 1) == 0:
            self.bad(name, "after async re-reset, LMSM Idle",
                     "disabled=1", self._fmt(),
                     self._port(0, "u_dll.u_sm"))
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 6. Product wrap pins. No cfg_rd_* / Appendix D / smoke-top peer.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_cmd",
                       "appendix_d", "u_peer", "prst", "p_ftv", "p_fab_tx"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_ub_switch product port",
                         f"{absent} present",
                         "vibe_ub_switch_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk_fab", "rst_n",
                     "txclk_0", "txclk_1", "txclk_2", "txclk_3",
                     "rxclk_0", "rxclk_1", "rxclk_2", "rxclk_3",
                     "pcs_pma_txdata_0", "pcs_pma_txdata_1",
                     "pcs_pma_txdata_2", "pcs_pma_txdata_3",
                     "pma_pcs_rxdata_0", "pma_pcs_rxdata_1",
                     "pma_pcs_rxdata_2", "pma_pcs_rxdata_3",
                     "cfg_wr_vld", "cfg_wr_ready", "cfg_wr_cmd",
                     "cfg_wr_idx", "cfg_wr_data", "irq_logic"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_ub_switch_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_ub_switch)
