"""Wrap-level uvm-python TC for Decision-I stage-46 vibe_fabric.

Covers submodule wiring (4× vibe_saf_ing, u_rt / u_ps, 3× g_rt
u_rti / u_psi, u_xbar, 4× g_egr u_voq / u_rr / u_fecn as the
product DUT instantiates them); reset / async rst_n; light
functional smoke on RTL-known pins only (route write, G1 RT=10
drop, CFG6 terminate vs forward via stock vibe_cfg6_should_term,
one CFG3 beat through xbar). Not a full-chip consecutive-green
gate (stock entry_fab / make suite remains the official
fabric+mgmt scorer). Not 1/3, 4/3, freeze, or signoff. Does not
steal make top / wrap / port / top_wrap / mgmt_wrap.

Matches product rtl/fabric/vibe_fabric.sv: generate g_saf[0:3]
u_saf, vibe_route_lu u_rt, vibe_port_sel u_ps, generate g_rt[1:3]
u_rti / u_psi, vibe_xbar u_xbar, generate g_egr[0:3] u_voq /
u_rr / u_fecn. No cfg_wr_* / cfg_rd_* pin. F1 ovf_l stays stock
inside vibe_port. CFG6 R/W packing is 未知 — do not invent.
Prefer observing child-driven nets over Force. Stock Icarus /
pyuvm fabric suite remain the official fabric scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

PORT_N = 4
MASK4 = 0xF
MASK16 = 0xFFFF
MASK32 = 0xFFFFFFFF
MASK352 = (1 << 352) - 1
MASK512 = (1 << 512) - 1
STOCK_CNA = 0x1111
STOCK_MISS = 0x2222
STOCK_DEST = 0x0001
STOCK_BM = 0x2
NAMED = ("u_rt", "u_ps", "u_xbar")
GEN_SAF = tuple(f"g_saf[{i}].u_saf" for i in range(PORT_N))
GEN_RT = tuple(
    [f"g_rt[{i}].u_rti" for i in range(1, PORT_N)]
    + [f"g_rt[{i}].u_psi" for i in range(1, PORT_N)]
)
GEN_EGR = tuple(
    [f"g_egr[{i}].u_voq" for i in range(PORT_N)]
    + [f"g_egr[{i}].u_rr" for i in range(PORT_N)]
    + [f"g_egr[{i}].u_fecn" for i in range(PORT_N)]
)


def cfg3_beat(dcna, rt=0, tag=0):
    """Stock CFG3 1-beat SOP. Official LPH only."""
    flit = lph.mk_flit(3, rt, 0, 1, dcna, lph.plen_nflit(1))
    return lph.mk_beat(flit, int(tag) & MASK352)


def g1_beat(dcna=STOCK_DEST, tag=0):
    """Stock RT=10 G1 1-beat SOP. RTL drops; no Dijkstra invent."""
    flit = lph.mk_flit(3, 0b10, 0, 1, dcna, lph.plen_nflit(1))
    return lph.mk_beat(flit, int(tag) & MASK352)


def cfg6_beat(dcna, nlp=0, opc=0, tag=0):
    """Stock CFG6 flit0 + distinct payload tag. No Appendix D pack."""
    flit = lph.mk_flit(6, 0, 0, 2, dcna, lph.plen_nflit(1), 0, 0, nlp, opc)
    return lph.mk_beat(flit, int(tag) & MASK352)


class tc_vibe_fabric(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.device_rst, 0)
        sset(d.status_up, 0xF)
        sset(d.default_bm, 0)
        sset(d.rt_wr_en, 0)
        sset(d.rt_wr_idx, 0)
        sset(d.rt_wr_data, 0)
        sset(d.nw_fab_vld, 0)
        sset(d.fab_nw_ready, 0xF)
        sset(d.cna, 0)
        sset(d.cna_written, 0)
        for i in range(PORT_N):
            sset(getattr(d, f"nw_fab_data_{i}"), 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
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
            f"rdy={ival(d.nw_fab_ready, -1):#x} "
            f"evld={ival(d.fab_nw_vld, -1):#x} "
            f"g1={ival(d.drop_g1, -1)} irq={ival(d.irq_rt, -1)} "
            f"unimpl={ival(d.rt_shortest_unimpl, -1)} "
            f"ddn={ival(d.drop_down_cnt, -1)} "
            f"len={ival(d.len_err, -1):#x} "
            f"dead={ival(d.deadlock_drop, -1):#x} "
            f"hit={ival(d.fab_mgmt_cfg6_hit, -1):#x} "
            f"cna={ival(d.cna, -1):#x} wr={ival(d.cna_written, -1)}"
        )

    def _score_children(self, name):
        """u_rt / u_ps / u_xbar are named. 4× SAF / 3× g_rt / 4× g_egr
        live in generate — Icarus exposes `g_saf[i].u_saf`; Verilator
        5.020 VPI may not. Prove generate with wrap-local packed nets
        those children drive when hierarchy is missing."""
        if not self._exists("u_fab"):
            self.bad(name, "AS-0.1 §8/§9 wrap instance",
                     "u_fab present", "missing", "u_fab")
            return False
        missing_named = [inst for inst in NAMED
                         if not self._exists(f"u_fab.{inst}")]
        if missing_named:
            self.bad(name, "AS-0.1 §8 named children present",
                     "u_rt u_ps u_xbar", f"missing={missing_named}",
                     "u_fab")
            return False
        have_saf = [self._exists(f"u_fab.{p}") for p in GEN_SAF]
        have_rt = [self._exists(f"u_fab.{p}") for p in GEN_RT]
        have_egr = [self._exists(f"u_fab.{p}") for p in GEN_EGR]
        if any(have_saf) and not all(have_saf):
            self.bad(name, "AS-0.1 §8 4× vibe_saf_ing generate",
                     "all four g_saf[i].u_saf", f"have={have_saf}",
                     "u_fab.g_saf")
            return False
        if not any(have_saf):
            for net in ("nw_fab_ready", "len_err"):
                if ival(getattr(self.dut, net), None) is None:
                    self.bad(name, "4× vibe_saf_ing via wrap nets (no g_saf VPI)",
                             f"{net} readable", "missing", f"u_fab.{net}")
                    return False
        if any(have_rt) and not all(have_rt):
            self.bad(name, "AS-0.1 §8 3× g_rt u_rti/u_psi generate",
                     "all g_rt[1:3] u_rti/u_psi", f"have={have_rt}",
                     "u_fab.g_rt")
            return False
        if not any(have_rt):
            if self._inner("u_fab.u_rt.bitmap", None) is None:
                if ival(self.dut.drop_g1, None) is None:
                    self.bad(name, "g_rt via wrap nets (no g_rt VPI)",
                             "drop_g1 readable", "missing", "u_fab.drop_g1")
                    return False
        if any(have_egr) and not all(have_egr):
            self.bad(name, "AS-0.1 §8 4× g_egr voq/rr/fecn generate",
                     "all four g_egr[i] children", f"have={have_egr}",
                     "u_fab.g_egr")
            return False
        if not any(have_egr):
            for net in ("fab_nw_vld", "deadlock_drop"):
                if ival(getattr(self.dut, net), None) is None:
                    self.bad(name, "4× g_egr via wrap nets (no g_egr VPI)",
                             f"{net} readable", "missing", f"u_fab.{net}")
                    return False
        return True

    def _score_combo(self, name):
        pin_g1 = ival(self.dut.drop_g1, None)
        pin_irq = ival(self.dut.irq_rt, None)
        if (pin_g1 is not None and pin_irq is not None
                and int(pin_g1) != int(pin_irq)):
            self.bad(name, "wrap irq_rt tied to drop_g1",
                     f"irq_rt={pin_g1}", f"irq_rt={pin_irq}",
                     "u_fab.irq_rt")
            return False
        for net in ("rt_wr_en", "rt_wr_idx", "rt_wr_data", "device_rst"):
            pin = ival(getattr(self.dut, net), None)
            ch = self._inner(f"u_fab.u_rt.{net if net != 'rt_wr_en' else 'wr_en'}",
                             None)
            if net == "rt_wr_en":
                ch = self._inner("u_fab.u_rt.wr_en", None)
            elif net == "rt_wr_idx":
                ch = self._inner("u_fab.u_rt.wr_idx", None)
            elif net == "rt_wr_data":
                ch = self._inner("u_fab.u_rt.wr_data", None)
            if pin is not None and ch is not None and int(pin) != int(ch):
                self.bad(name, f"wrap {net} to u_rt",
                         f"{net}={pin}", f"u_rt={ch}", f"u_fab.u_rt.{net}")
                return False
        pin_up = ival(self.dut.status_up, None)
        ps_up = self._inner("u_fab.u_ps.status_up", None)
        if (pin_up is not None and ps_up is not None
                and int(pin_up) != int(ps_up)):
            self.bad(name, "wrap status_up to u_ps",
                     f"status_up={pin_up:#x}", f"u_ps.status_up={ps_up:#x}",
                     "u_fab.u_ps.status_up")
            return False
        pin_bm = ival(self.dut.default_bm, None)
        ps_bm = self._inner("u_fab.u_ps.default_bm", None)
        if (pin_bm is not None and ps_bm is not None
                and int(pin_bm) != int(ps_bm)):
            self.bad(name, "wrap default_bm to u_ps",
                     f"default_bm={pin_bm:#x}", f"u_ps.default_bm={ps_bm:#x}",
                     "u_fab.u_ps.default_bm")
            return False
        pin_cna = ival(self.dut.cna, None)
        fab_cna = self._inner("u_fab.cna", None)
        if (pin_cna is not None and fab_cna is not None
                and int(pin_cna) != int(fab_cna)):
            self.bad(name, "wrap cna to u_fab",
                     f"cna={pin_cna:#x}", f"u_fab.cna={fab_cna:#x}",
                     "u_fab.cna")
            return False
        return True

    async def _wr_route(self, dest, bm):
        d = self.dut
        await FallingEdge(d.clk)
        sset(d.rt_wr_idx, int(dest) & MASK16)
        sset(d.rt_wr_data, int(bm) & MASK32)
        sset(d.rt_wr_en, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        snap = {
            "en": ival(d.rt_wr_en, None),
            "idx": ival(d.rt_wr_idx, None),
            "data": ival(d.rt_wr_data, None),
            "ch_en": self._inner("u_fab.u_rt.wr_en", None),
        }
        sset(d.rt_wr_en, 0)
        return snap

    async def _inject(self, port, beat):
        d = self.dut
        await FallingEdge(d.clk)
        for _ in range(32):
            rdy = ival(d.nw_fab_ready, 0)
            if rdy is not None and ((int(rdy) >> port) & 1):
                break
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
        sset(getattr(d, f"nw_fab_data_{port}"), int(beat) & MASK512)
        sset(d.nw_fab_vld, 1 << port)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.nw_fab_vld, 0)

    async def _wait_pulse(self, sig, n=16):
        """Combo one-shots (drop_g1 / cfg6_hit) are high only while SAF
        presents; NBA consume clears them after the posedge. Sample at
        RisingEdge, not the following fall."""
        for _ in range(n):
            await RisingEdge(self.dut.clk)
            got = ival(sig, 0)
            if got is not None and int(got) != 0:
                return int(got)
        return 0

    async def _wait_hit_bit(self, port, n=16):
        for _ in range(n):
            await RisingEdge(self.dut.clk)
            hit = ival(self.dut.fab_mgmt_cfg6_hit, 0) or 0
            if (int(hit) >> port) & 1:
                return int(hit)
        return 0

    async def _drain_egr(self, n=16):
        for _ in range(n):
            ev = ival(self.dut.fab_nw_vld, 0)
            if ev is None or int(ev) == 0:
                return True
            await self._to_fall()
        return ival(self.dut.fab_nw_vld, 1) == 0

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_fabric"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset: SAF ready, egress idle, G1 counters 0.
        rdy = ival(d.nw_fab_ready, None)
        if rdy is None or int(rdy) != MASK4:
            self.bad(name, "reset then release, nw_fab_ready",
                     "nw_fab_ready=0xf", self._fmt(), "u_fab.nw_fab_ready")
            phase.drop_objection(self)
            return
        for net, exp in (("fab_nw_vld", 0), ("drop_g1", 0), ("irq_rt", 0),
                         ("rt_shortest_unimpl", 0), ("drop_down_cnt", 0),
                         ("len_err", 0), ("deadlock_drop", 0),
                         ("fab_mgmt_cfg6_hit", 0)):
            got = ival(getattr(d, net), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle wrap {net}",
                         f"{net}={exp}", self._fmt(), f"u_fab.{net}")
                phase.drop_objection(self)
                return

        # 2. RTL-known route write reaches u_rt (no CFG cmd invent).
        snap = await self._wr_route(STOCK_DEST, STOCK_BM)
        if snap["ch_en"] not in (None, 1) and int(snap["ch_en"]) != 1:
            self.bad(name, "rt_wr_en to u_rt.wr_en",
                     "wr_en=1", f"wr_en={snap['ch_en']}", "u_fab.u_rt.wr_en")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 3. Light CFG3 forward. Observe xbar offer / egress. No Force.
        # Icarus 12 VOQ wr_vl combo-feeds xbar out_ready (stock
        # vibe_fab_cocotb_top Forces wr_vl); egress may stay 0. x_in_v
        # is combo from SAF and still observable.
        await self._inject(0, cfg3_beat(STOCK_DEST, tag=0xA11A))
        saw_egr = 0
        saw_xin = 0
        saw_saf = 0
        for _ in range(32):
            await RisingEdge(d.clk)
            ev = ival(d.fab_nw_vld, 0)
            xin = self._inner("u_fab.x_in_v", 0)
            saf = self._inner("u_fab.saf_v", 0)
            if ev is not None and int(ev) != 0:
                saw_egr = int(ev)
            if xin is not None and int(xin) != 0:
                saw_xin = int(xin)
            if saf is not None and int(saf) != 0:
                saw_saf = int(saf)
            if saw_egr or saw_xin or saw_saf:
                await FallingEdge(d.clk)
                break
        if saw_egr == 0 and saw_xin == 0 and saw_saf == 0:
            self.bad(name, "CFG3 1-beat SAF/xbar offer (observe, no Force)",
                     "fab_nw_vld|x_in_v|saf_v != 0", self._fmt(),
                     "u_fab.x_in_v")
            phase.drop_objection(self)
            return
        sset(d.nw_fab_vld, 0)
        if saw_egr and not await self._drain_egr():
            self.bad(name, "CFG3 egress drained before G1",
                     "fab_nw_vld=0", self._fmt(), "u_fab.fab_nw_vld")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)

        # 4. G1 RT=10: combo drop_g1 / irq_rt, saturate counter, no egress.
        sset(d.fab_nw_ready, 0xF)
        await self._inject(0, g1_beat(tag=0xB22B))
        saw_g1 = await self._wait_pulse(d.drop_g1, 16)
        if saw_g1 == 0:
            self.bad(name, "RT=10 G1 drop_g1 pulse (stock suite)",
                     "drop_g1=1", self._fmt(), "u_fab.drop_g1")
            phase.drop_objection(self)
            return
        if ival(d.irq_rt, 0) != 1:
            self.bad(name, "irq_rt tied to drop_g1 on G1 event",
                     "irq_rt=1", self._fmt(), "u_fab.irq_rt")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        cnt = ival(d.rt_shortest_unimpl, None)
        if cnt is not None and int(cnt) < 1:
            self.bad(name, "G1 increments rt_shortest_unimpl",
                     "rt_shortest_unimpl>=1", self._fmt(),
                     "u_fab.rt_shortest_unimpl")
            phase.drop_objection(self)
            return
        leaked = False
        for _ in range(12):
            ev = ival(d.fab_nw_vld, 0)
            if ev is not None and int(ev) != 0:
                leaked = True
                break
            await self._to_fall()
        if leaked:
            self.bad(name, "G1 must not take xbar (no treat-as-RT=00)",
                     "fab_nw_vld=0", self._fmt(), "u_fab.x_in_v")
            phase.drop_objection(self)
            return

        # 5. device_rst level-clears G1 counter on posedge.
        held = ival(d.rt_shortest_unimpl, 1)
        sset(d.device_rst, 1)
        await self._to_fall()
        if ival(d.rt_shortest_unimpl, 1) != 0:
            self.bad(name, "device_rst clears rt_shortest_unimpl",
                     "rt_shortest_unimpl=0", self._fmt(),
                     "u_fab.rt_shortest_unimpl")
            phase.drop_objection(self)
            return
        if held is not None and int(held) < 1:
            self.bad(name, "G1 counter was live before device_rst",
                     "rt_shortest_unimpl>=1 before clear", self._fmt(),
                     "u_fab.rt_shortest_unimpl")
            phase.drop_objection(self)
            return
        sset(d.device_rst, 0)
        await self._to_fall()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 6. CFG6 terminate vs forward. Stock vibe_cfg6_should_term only.
        sset(d.cna, STOCK_CNA)
        sset(d.cna_written, 1)
        await self._settle()
        await self._inject(0, cfg6_beat(STOCK_CNA, tag=0xC33C))
        saw_hit = await self._wait_pulse(d.fab_mgmt_cfg6_hit, 16)
        exp_term = lph.cfg6_should_term(True, STOCK_CNA,
                                        lph.nw512_flit0(cfg6_beat(STOCK_CNA)))
        if exp_term and saw_hit == 0:
            self.bad(name, "DCNA==written CNA CFG6 terminate (no pack invent)",
                     "fab_mgmt_cfg6_hit!=0", self._fmt(),
                     "u_fab.fab_mgmt_cfg6_hit")
            phase.drop_objection(self)
            return
        leaked = False
        for _ in range(12):
            ev = ival(d.fab_nw_vld, 0)
            if ev is not None and int(ev) != 0:
                leaked = True
                break
            await self._to_fall()
        if leaked:
            self.bad(name, "terminate CFG6 must not take xbar",
                     "fab_nw_vld=0", self._fmt(), "u_fab.fab_mgmt_cfg6_hit")
            phase.drop_objection(self)
            return

        await self._inject(1, cfg6_beat(STOCK_MISS, tag=0xD44D))
        saw_miss = 1 if await self._wait_hit_bit(1, 16) else 0
        exp_miss = lph.cfg6_should_term(
            True, STOCK_CNA, lph.nw512_flit0(cfg6_beat(STOCK_MISS)))
        if exp_miss:
            if saw_miss == 0:
                self.bad(name, "NLP/opc term path (stock should_term)",
                         "hit[1]=1", self._fmt(), "u_fab.fab_mgmt_cfg6_hit")
                phase.drop_objection(self)
                return
        elif saw_miss != 0:
            self.bad(name, "miss CNA NLP=0 forward (no consume invent)",
                     "hit[1]=0", self._fmt(), "u_fab.fab_mgmt_cfg6_hit")
            phase.drop_objection(self)
            return

        # opc 0x10 without us does not invent CFG6 CSR packing.
        opc_beat = cfg6_beat(STOCK_MISS, opc=0x10, tag=0xE55E)
        await self._inject(2, opc_beat)
        saw_opc = 1 if await self._wait_hit_bit(2, 16) else 0
        exp_opc = lph.cfg6_should_term(
            True, STOCK_CNA, lph.nw512_flit0(opc_beat))
        if bool(saw_opc) != bool(exp_opc):
            self.bad(name, "opc 0x10 without us (no invented CFG6 CSR)",
                     f"term={int(exp_opc)}", f"hit[2]={saw_opc}",
                     "u_fab.fab_mgmt_cfg6_hit")
            phase.drop_objection(self)
            return
        sset(d.cna_written, 0)
        sset(d.cna, 0)
        await self._settle()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 7. Async rst_n (no posedge) clears registered wrap outputs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.drop_g1, 1) != 0 or ival(d.irq_rt, 1) != 0:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     "drop_g1=0 irq_rt=0", self._fmt(), "u_fab.drop_g1")
            phase.drop_objection(self)
            return
        if ival(d.rt_shortest_unimpl, 1) != 0:
            self.bad(name, "async rst_n clears rt_shortest_unimpl",
                     "rt_shortest_unimpl=0", self._fmt(),
                     "u_fab.rt_shortest_unimpl")
            phase.drop_objection(self)
            return
        if ival(d.fab_mgmt_cfg6_hit, 1) != 0:
            self.bad(name, "async rst_n clears CFG6 hit (SAF idle)",
                     "fab_mgmt_cfg6_hit=0", self._fmt(),
                     "u_fab.fab_mgmt_cfg6_hit")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.nw_fab_ready, 0) != MASK4:
            self.bad(name, "after async re-reset release",
                     "nw_fab_ready=0xf", self._fmt(), "u_fab.nw_fab_ready")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 8. Product wrap pins. No cfg_rd_* / Appendix D / F1 ovf_l / smoke-top.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_cmd",
                       "cfg_wr_vld", "cfg_wr_cmd", "appendix_d", "ovf_l",
                       "u_peer", "prst", "clk_fab", "pcs_pma_txdata",
                       "irq_logic", "port_rst", "lmsm_go"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_fabric product / wrap port",
                         f"{absent} present",
                         "vibe_fabric_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n", "device_rst", "status_up", "default_bm",
                     "rt_wr_en", "rt_wr_idx", "rt_wr_data",
                     "nw_fab_data_0", "nw_fab_data_1",
                     "nw_fab_data_2", "nw_fab_data_3",
                     "nw_fab_vld", "nw_fab_ready",
                     "fab_nw_data_0", "fab_nw_data_1",
                     "fab_nw_data_2", "fab_nw_data_3",
                     "fab_nw_vld", "fab_nw_ready",
                     "len_err", "drop_g1", "rt_shortest_unimpl",
                     "drop_down_cnt", "deadlock_drop", "irq_rt",
                     "cna", "cna_written", "fab_mgmt_cfg6_hit",
                     "fab_mgmt_cfg6_data_0", "fab_mgmt_cfg6_data_1",
                     "fab_mgmt_cfg6_data_2", "fab_mgmt_cfg6_data_3"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_fabric_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_fabric)
