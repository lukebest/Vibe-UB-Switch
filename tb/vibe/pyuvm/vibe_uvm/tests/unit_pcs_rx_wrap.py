"""Wrap-level uvm-python TC for Decision-I stage-48 vibe_pcs_rx.

Covers submodule wiring (4× vibe_pcs_rx_amctl_lock u_l0..u_l3,
4× vibe_pcs_scramble u_d0..u_d3, vibe_pcs_rx_deskew u_dsk,
vibe_pcs_rx_unpack u_un, vibe_pcs_rx_fec u_fec as the product DUT
instantiates them); reset / async rst_n; light functional smoke on
RTL-known pins only (link_up seed hold, fec_mode pin, non-AM lanes
do not lock, pcs_dll_ready to FEC win_ready). Not a full-chip
consecutive-green gate (stock Icarus tc_pcs_rx remains the official
full-stack scorer). Not 1/3, 4/3, freeze, or signoff. Does not steal
make top / wrap / port / top_wrap / mgmt_wrap / fabric_wrap /
pcs_tx_wrap. lmsm stays HOLD.

Matches product rtl/pcs/vibe_pcs_rx.sv: vibe_pcs_rx_amctl_lock
u_l0..u_l3, vibe_pcs_scramble u_d0..u_d3, vibe_pcs_rx_deskew u_dsk,
vibe_pcs_rx_unpack u_un, vibe_pcs_rx_fec u_fec. No cfg_wr_* /
cfg_rd_* pin. F1 ovf_l stays stock inside vibe_port. CFG6 R/W
packing is 未知 — do not invent. Prefer observing child-driven
nets over Force. Stock Icarus / pyuvm leaf TCs remain the official
child scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK3 = 0x7
MASK4 = 0xF
MASK160 = (1 << 160) - 1
# RTL-known fec_mode (vibe_ub_params.vh). Do not invent CFG opcodes.
FEC_BYPASS = 0
FEC_T2 = 1
FEC_T4 = 2
CHILDREN = ("u_l0", "u_l1", "u_l2", "u_l3",
            "u_d0", "u_d1", "u_d2", "u_d3",
            "u_dsk", "u_un", "u_fec")
HIER = ("u_prx.u_l0..u_l3 / u_prx.u_d0..u_d3 / "
        "u_prx.u_dsk / u_prx.u_un / u_prx.u_fec")
JUNK_CYCLES = 8


def junk(tag: int) -> int:
    """Non-AM 160b (same class as unit_pcs_rx_amctl_lock.junk)."""
    return ((0xA5A5A5A5A5A5A5A5 ^ (tag * 0x1111111111111111))
            & MASK160)


class tc_vibe_pcs_rx(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=0, fec_mode=FEC_BYPASS, pcs_dll_ready=1):
        d = self.dut
        sset(d.link_up, 1 if link_up else 0)
        sset(d.fec_mode, int(fec_mode) & MASK3)
        sset(d.afifo_pcs_lane_vld, 0)
        sset(d.afifo_pcs_lane0, 0)
        sset(d.afifo_pcs_lane1, 0)
        sset(d.afifo_pcs_lane2, 0)
        sset(d.afifo_pcs_lane3, 0)
        sset(d.pcs_dll_ready, 1 if pcs_dll_ready else 0)

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
            f"lu={ival(d.link_up, -1)} fec={ival(d.fec_mode, -1)} "
            f"lvld={ival(d.afifo_pcs_lane_vld, -1)} "
            f"rdy={ival(d.pcs_dll_ready, -1)} "
            f"dvld={ival(d.pcs_dll_vld, -1)} "
            f"am={ival(d.am_locked, -1)} lidb={ival(d.lid_bad, -1)} "
            f"dsk={ival(d.deskew_ok, -1)} ff={ival(d.fec_fail, -1)} "
            f"wr={self._inner('u_prx.wr', -1)} "
            f"uv={self._inner('u_prx.uv', -1)} "
            f"bv={self._inner('u_prx.bv', -1)} "
            f"wv={self._inner('u_prx.wv', -1)}"
        )

    def _score_children(self, name):
        """Named children. Icarus exposes u_prx.u_l0; Verilator 5.020
        VPI may not. Prove missing hierarchy with wrap-local packed
        nets those children drive."""
        if not self._exists("u_prx"):
            self.bad(name, "AS-0.1 §6 wrap instance",
                     "u_prx present", "missing", "u_prx")
            return False
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_prx.{inst}")]
        if missing and len(missing) != len(CHILDREN):
            self.bad(name, "AS-0.1 §6 named children present",
                     "u_l0..u_l3 u_d0..u_d3 u_dsk u_un u_fec",
                     f"missing={missing}", "u_prx")
            return False
        if missing:
            for net in ("am_locked", "lid_bad", "deskew_ok",
                        "pcs_dll_vld", "fec_fail", "pcs_dll_data"):
                if ival(getattr(self.dut, net), None) is None:
                    # Wide dll data may be X on Icarus VPI; status
                    # bits must still resolve. Skip only the 640b.
                    if net == "pcs_dll_data":
                        continue
                    self.bad(name, "children via wrap nets (no child VPI)",
                             f"{net} readable", "missing", f"u_prx.{net}")
                    return False
        return True

    def _score_combo(self, name):
        d = self.dut
        pin_fec = ival(d.fec_mode, None)
        fec = self._inner("u_prx.u_fec.fec_mode", None)
        if (pin_fec is not None and fec is not None
                and int(pin_fec) != int(fec)):
            self.bad(name, "wrap fec_mode to u_fec",
                     f"fec_mode={pin_fec}", f"u_fec.fec_mode={fec}",
                     "u_prx.u_fec.fec_mode")
            return False
        pin_lu = ival(d.link_up, None)
        seed = self._inner("u_prx.u_d0.seed_load", None)
        if pin_lu is not None and seed is not None:
            # sl0 = !link_up || (edf0 && !link_up) == !link_up
            exp = 0 if int(pin_lu) else 1
            if int(seed) != exp:
                self.bad(name, "u_d0.seed_load = !link_up",
                         f"seed_load={exp}", f"seed_load={seed}",
                         "u_prx.u_d0.seed_load")
                return False
        pin_am = ival(d.am_locked, None)
        for i in range(4):
            ch = self._inner(f"u_prx.u_l{i}.locked", None)
            if pin_am is None or ch is None:
                continue
            bit = (int(pin_am) >> i) & 1
            if bit != int(ch):
                self.bad(name, f"wrap am_locked[{i}] from u_l{i}.locked",
                         f"locked={ch}", f"am_locked[{i}]={bit}",
                         f"u_prx.u_l{i}.locked")
                return False
        pin_dsk = ival(d.deskew_ok, None)
        alg = self._inner("u_prx.u_dsk.aligned", None)
        if (pin_dsk is not None and alg is not None
                and int(pin_dsk) != int(alg)):
            self.bad(name, "wrap deskew_ok from u_dsk.aligned",
                     f"aligned={alg}", f"deskew_ok={pin_dsk}",
                     "u_prx.u_dsk.aligned")
            return False
        pin_ff = ival(d.fec_fail, None)
        ff = self._inner("u_prx.u_fec.fec_fail", None)
        if (pin_ff is not None and ff is not None
                and int(pin_ff) != int(ff)):
            self.bad(name, "wrap fec_fail from u_fec.fec_fail",
                     f"fec_fail={ff}", f"pin={pin_ff}",
                     "u_prx.u_fec.fec_fail")
            return False
        pin_lv = ival(d.afifo_pcs_lane_vld, None)
        l0v = self._inner("u_prx.u_l0.in_vld", None)
        if (pin_lv is not None and l0v is not None
                and int(pin_lv) != int(l0v)):
            self.bad(name, "wrap afifo_pcs_lane_vld to u_l0.in_vld",
                     f"lane_vld={pin_lv}", f"u_l0.in_vld={l0v}",
                     "u_prx.u_l0.in_vld")
            return False
        # wr = pcs_dll_ready && !pcs_dll_vld && !pend_vld (idle)
        pin_rdy = ival(d.pcs_dll_ready, None)
        pin_dv = ival(d.pcs_dll_vld, None)
        wr = self._inner("u_prx.wr", None)
        pv = self._inner("u_prx.pend_vld", None)
        if (pin_rdy is not None and pin_dv is not None
                and wr is not None and (pv is None or int(pv) == 0)
                and int(pin_dv) == 0):
            if int(wr) != int(pin_rdy):
                self.bad(name, "idle wr = pcs_dll_ready",
                         f"wr={pin_rdy}", f"wr={wr}", "u_prx.wr")
                return False
        fec_wr = self._inner("u_prx.u_fec.win_ready", None)
        if wr is not None and fec_wr is not None and int(wr) != int(fec_wr):
            self.bad(name, "u_fec.win_ready from wrap wr",
                     f"wr={wr}", f"win_ready={fec_wr}",
                     "u_prx.u_fec.win_ready")
            return False
        return True

    async def _drive_junk(self, n=JUNK_CYCLES):
        """Drive non-AM 160b. Product unpack/FEC still run in hunt
        (rtl/pcs/vibe_pcs_rx.sv). Return observed pipeline bits."""
        d = self.dut
        saw = {"uv": 0, "bv": 0, "dvld": 0, "am": 0}
        await FallingEdge(d.clk)
        sset(d.afifo_pcs_lane_vld, 1)
        for k in range(n):
            sset(d.afifo_pcs_lane0, junk(0x10 + k))
            sset(d.afifo_pcs_lane1, junk(0x20 + k))
            sset(d.afifo_pcs_lane2, junk(0x30 + k))
            sset(d.afifo_pcs_lane3, junk(0x40 + k))
            await RisingEdge(d.clk)
            uv = self._inner("u_prx.uv", 0)
            bv = self._inner("u_prx.bv", 0)
            dv = ival(d.pcs_dll_vld, 0)
            am = ival(d.am_locked, 0)
            if uv is not None and int(uv) != 0:
                saw["uv"] = 1
            if bv is not None and int(bv) != 0:
                saw["bv"] = 1
            if dv is not None and int(dv) != 0:
                saw["dvld"] = 1
            if am is not None and int(am) != 0:
                saw["am"] = 1
            await FallingEdge(d.clk)
        sset(d.afifo_pcs_lane_vld, 0)
        sset(d.afifo_pcs_lane0, 0)
        sset(d.afifo_pcs_lane1, 0)
        sset(d.afifo_pcs_lane2, 0)
        sset(d.afifo_pcs_lane3, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        return saw

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_rx"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset with link_up=0: hunt idle, no lock / dll.
        for net, exp in (("am_locked", 0), ("lid_bad", 0), ("deskew_ok", 0),
                         ("pcs_dll_vld", 0), ("fec_fail", 0)):
            got = ival(getattr(d, net), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle wrap {net}",
                         f"{net}={exp}", self._fmt(), f"u_prx.{net}")
                phase.drop_objection(self)
                return

        # 2. link_up=1: descramble seed_load holds 0 (UB 3.2.2.4).
        sset(d.link_up, 1)
        await self._settle()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        seed = self._inner("u_prx.u_d0.seed_load", None)
        if seed is not None and int(seed) != 0:
            self.bad(name, "link_up=1 seed_load hold",
                     "seed_load=0", self._fmt(), "u_prx.u_d0.seed_load")
            phase.drop_objection(self)
            return

        # 3. Non-AM junk on RAW 160b lanes (observe). Lock stays 0.
        # Hunt still feeds unpack/FEC (product comment: do not hold
        # empty until lock). Full-stack AMCTL lock stays Icarus
        # tc_pcs_rx. Do not invent AM packing here.
        saw = await self._drive_junk()
        if saw["am"]:
            self.bad(name, "non-AM lanes leave am_locked=0",
                     "am_locked=0", self._fmt(), "u_prx.am_locked")
            phase.drop_objection(self)
            return
        am = ival(d.am_locked, None)
        if am is not None and int(am) != 0:
            self.bad(name, "non-AM lanes leave am_locked=0",
                     "am_locked=0", self._fmt(), "u_prx.am_locked")
            phase.drop_objection(self)
            return
        dsk = ival(d.deskew_ok, None)
        if dsk is not None and int(dsk) != 0:
            self.bad(name, "non-AM lanes leave deskew_ok=0",
                     "deskew_ok=0", self._fmt(), "u_prx.deskew_ok")
            phase.drop_objection(self)
            return
        if not (saw["uv"] or saw["bv"] or saw["dvld"]):
            # Verilator 5.020 may hide uv/bv; wrap pcs_dll_vld is enough.
            if ival(d.pcs_dll_vld, 0) in (None, 0):
                self.bad(name, "hunt pipeline observe (no AM invent)",
                         "uv|bv|pcs_dll_vld != 0", self._fmt(),
                         "u_prx.pcs_dll_vld")
                phase.drop_objection(self)
                return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 4. pcs_dll_ready combo-clears wrap wr / u_fec.win_ready.
        sset(d.pcs_dll_ready, 0)
        await self._settle()
        wr = self._inner("u_prx.wr", None)
        if wr is not None and int(wr) != 0:
            self.bad(name, "pcs_dll_ready=0 clears wr",
                     "wr=0", f"wr={wr}", "u_prx.wr")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        sset(d.pcs_dll_ready, 1)
        await self._settle()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 5. fec_mode T4 is RTL-known (vibe_port ties T4). Pin only.
        sset(d.fec_mode, FEC_T4)
        await self._settle()
        if ival(d.fec_mode, -1) != FEC_T4:
            self.bad(name, "RTL-known fec_mode=T4 pin",
                     f"fec_mode={FEC_T4}", self._fmt(), "u_prx.fec_mode")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        sset(d.fec_mode, FEC_BYPASS)
        await self._settle()

        # 6. Async rst_n (no posedge) clears registered wrap outs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        for net in ("am_locked", "deskew_ok", "pcs_dll_vld", "fec_fail",
                    "lid_bad"):
            got = ival(getattr(d, net), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != 0:
                self.bad(name, f"async rst_n=0 (100ps, no posedge) {net}",
                         f"{net}=0", self._fmt(), f"u_prx.{net}")
                phase.drop_objection(self)
                return
        got = ival(d.pcs_dll_data, None)
        if got is None or (isinstance(got, int) and got < 0):
            pass
        elif int(got) != 0:
            self.bad(name, "async rst_n clears pcs_dll_data",
                     "pcs_dll_data=0", f"pcs_dll_data={got:#x}",
                     "u_prx.pcs_dll_data")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.am_locked, 1) != 0:
            self.bad(name, "after async re-reset, am_locked",
                     "am_locked=0", self._fmt(), "u_prx.am_locked")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 7. Product wrap pins. No cfg_* / Appendix D / F1 ovf_l / smoke-top.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_cmd",
                       "cfg_wr_vld", "cfg_wr_cmd", "appendix_d", "ovf_l",
                       "u_peer", "prst", "clk_fab", "pcs_pma_txdata",
                       "irq_logic", "port_rst", "lmsm_go", "device_rst",
                       "cna", "nw_fab_vld", "sdf_period", "afifo_afull",
                       "dll_pcs_data", "dll_pcs_vld"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_pcs_rx product / wrap port",
                         f"{absent} present",
                         "vibe_pcs_rx_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n", "link_up", "fec_mode",
                     "afifo_pcs_lane0", "afifo_pcs_lane1",
                     "afifo_pcs_lane2", "afifo_pcs_lane3",
                     "afifo_pcs_lane_vld", "pcs_dll_data", "pcs_dll_vld",
                     "pcs_dll_ready", "fec_fail", "am_locked", "lid_bad",
                     "deskew_ok"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_pcs_rx_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_rx)
