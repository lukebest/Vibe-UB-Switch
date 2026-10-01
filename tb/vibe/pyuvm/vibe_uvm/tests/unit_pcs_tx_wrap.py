"""Wrap-level uvm-python TC for Decision-I stage-47 vibe_pcs_tx.

Covers submodule wiring (u_g1 / u_fec / u_cw / u_pack / 4×
vibe_pcs_scramble u_s0..u_s3 as the product DUT instantiates them);
reset / async rst_n; light functional smoke on RTL-known pins only
(link_up ready, fec_mode bypass idle-fill / DLL beat through the
pipeline, afifo_afull backpressure). Not a full-chip consecutive-green
gate (stock Icarus tc_pcs_tx remains the official full-stack scorer).
Not 1/3, 4/3, freeze, or signoff. Does not steal make top / wrap /
port / top_wrap / mgmt_wrap / fabric_wrap. pcs_rx / lmsm stay HOLD.

Matches product rtl/pcs/vibe_pcs_tx.sv: vibe_pcs_tx_g1 u_g1,
vibe_pcs_tx_fec u_fec, vibe_pcs_tx_cw2beat u_cw, vibe_pcs_tx_pack
u_pack, vibe_pcs_scramble u_s0..u_s3. No cfg_wr_* / cfg_rd_* pin.
F1 ovf_l stays stock inside vibe_port. CFG6 R/W packing is 未知 —
do not invent. Prefer observing child-driven nets over Force.
Stock Icarus / pyuvm leaf TCs remain the official child scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK3 = 0x7
MASK160 = (1 << 160) - 1
MASK640 = (1 << 640) - 1
# RTL-known fec_mode (vibe_ub_params.vh). Do not invent CFG opcodes.
FEC_BYPASS = 0
FEC_T2 = 1
FEC_T4 = 2
# Distinct 640b = 4×160 flits. Observe-only; no FEC golden invent.
STOCK_BEAT = (
    (0xA11A << 480) | (0xB22B << 320) | (0xC33C << 160) | 0xD44D
) & MASK640
CHILDREN = ("u_g1", "u_fec", "u_cw", "u_pack",
            "u_s0", "u_s1", "u_s2", "u_s3")
HIER = ("u_ptx.u_g1 / u_ptx.u_fec / u_ptx.u_cw / u_ptx.u_pack / "
        "u_ptx.u_s0..u_s3")
PIPE_TIMEOUT = 128


class tc_vibe_pcs_tx(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=0, fec_mode=FEC_BYPASS, afifo_afull=0,
                    sdf_period=0):
        d = self.dut
        sset(d.link_up, 1 if link_up else 0)
        sset(d.sdf_period, 1 if sdf_period else 0)
        sset(d.fec_mode, int(fec_mode) & MASK3)
        sset(d.afifo_afull, 1 if afifo_afull else 0)
        sset(d.dll_pcs_vld, 0)
        sset(d.dll_pcs_data, 0)

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
            f"lu={ival(d.link_up, -1)} rdy={ival(d.dll_pcs_ready, -1)} "
            f"vld={ival(d.dll_pcs_vld, -1)} "
            f"fec={ival(d.fec_mode, -1)} afull={ival(d.afifo_afull, -1)} "
            f"sdf={ival(d.sdf_period, -1)} "
            f"lvld={ival(d.pcs_afifo_lane_vld, -1)} "
            f"win={self._inner('u_ptx.win_vld', -1)} "
            f"cw={self._inner('u_ptx.cw_vld', -1)} "
            f"beat={self._inner('u_ptx.beat_vld', -1)} "
            f"pvld={self._inner('u_ptx.p_vld', -1)} "
            f"am={self._inner('u_ptx.am_word', -1)}"
        )

    def _score_children(self, name):
        """Named children. Icarus exposes u_ptx.u_g1; Verilator 5.020
        VPI may not. Prove missing hierarchy with wrap-local packed
        nets those children drive."""
        if not self._exists("u_ptx"):
            self.bad(name, "AS-0.1 §5 wrap instance",
                     "u_ptx present", "missing", "u_ptx")
            return False
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_ptx.{inst}")]
        if missing and len(missing) != len(CHILDREN):
            self.bad(name, "AS-0.1 §5 named children present",
                     "u_g1 u_fec u_cw u_pack u_s0..u_s3",
                     f"missing={missing}", "u_ptx")
            return False
        if missing:
            for net in ("dll_pcs_ready", "pcs_afifo_lane_vld",
                        "pcs_afifo_lane0", "pcs_afifo_lane1",
                        "pcs_afifo_lane2", "pcs_afifo_lane3"):
                if ival(getattr(self.dut, net), None) is None:
                    # Wide lanes may be X on Icarus VPI; ready/vld must
                    # still resolve. Skip only the 160b lanes.
                    if net.startswith("pcs_afifo_lane") and net != \
                            "pcs_afifo_lane_vld":
                        continue
                    self.bad(name, "children via wrap nets (no child VPI)",
                             f"{net} readable", "missing", f"u_ptx.{net}")
                    return False
        return True

    def _score_combo(self, name):
        d = self.dut
        pin_rdy = ival(d.dll_pcs_ready, None)
        g1_rdy = self._inner("u_ptx.u_g1.in_ready", None)
        if (pin_rdy is not None and g1_rdy is not None
                and int(pin_rdy) != int(g1_rdy)):
            self.bad(name, "wrap dll_pcs_ready from u_g1.in_ready",
                     f"in_ready={g1_rdy}", f"dll_pcs_ready={pin_rdy}",
                     "u_ptx.u_g1.in_ready")
            return False
        pin_lu = ival(d.link_up, None)
        g1_lu = self._inner("u_ptx.u_g1.link_up", None)
        if (pin_lu is not None and g1_lu is not None
                and int(pin_lu) != int(g1_lu)):
            self.bad(name, "wrap link_up to u_g1",
                     f"link_up={pin_lu}", f"u_g1.link_up={g1_lu}",
                     "u_ptx.u_g1.link_up")
            return False
        pin_fec = ival(d.fec_mode, None)
        fec = self._inner("u_ptx.u_fec.fec_mode", None)
        if (pin_fec is not None and fec is not None
                and int(pin_fec) != int(fec)):
            self.bad(name, "wrap fec_mode to u_fec",
                     f"fec_mode={pin_fec}", f"u_fec.fec_mode={fec}",
                     "u_ptx.u_fec.fec_mode")
            return False
        pin_af = ival(d.afifo_afull, None)
        pk_af = self._inner("u_ptx.u_pack.afifo_afull", None)
        if (pin_af is not None and pk_af is not None
                and int(pin_af) != int(pk_af)):
            self.bad(name, "wrap afifo_afull to u_pack",
                     f"afifo_afull={pin_af}", f"u_pack.afifo_afull={pk_af}",
                     "u_ptx.u_pack.afifo_afull")
            return False
        pin_sdf = ival(d.sdf_period, None)
        pk_sdf = self._inner("u_ptx.u_pack.sdf_period", None)
        if (pin_sdf is not None and pk_sdf is not None
                and int(pin_sdf) != int(pk_sdf)):
            self.bad(name, "wrap sdf_period to u_pack",
                     f"sdf_period={pin_sdf}", f"u_pack.sdf_period={pk_sdf}",
                     "u_ptx.u_pack.sdf_period")
            return False
        prdy = self._inner("u_ptx.p_rdy", None)
        if prdy is not None and int(prdy) != 1:
            self.bad(name, "stock p_rdy tied 1 (AS-0.1 §5)",
                     "p_rdy=1", f"p_rdy={prdy}", "u_ptx.p_rdy")
            return False
        pin_lv = ival(d.pcs_afifo_lane_vld, None)
        s0_v = self._inner("u_ptx.u_s0.out_vld", None)
        if (pin_lv is not None and s0_v is not None
                and int(pin_lv) != int(s0_v)):
            self.bad(name, "wrap pcs_afifo_lane_vld from u_s0.out_vld",
                     f"out_vld={s0_v}", f"lane_vld={pin_lv}",
                     "u_ptx.u_s0.out_vld")
            return False
        seed = self._inner("u_ptx.u_s0.seed_load", None)
        if pin_lu is not None and seed is not None:
            exp = 0 if int(pin_lu) else 1
            if int(seed) != exp:
                self.bad(name, "u_s0.seed_load = !link_up",
                         f"seed_load={exp}", f"seed_load={seed}",
                         "u_ptx.u_s0.seed_load")
                return False
        return True

    async def _push_beat(self, beat):
        d = self.dut
        await FallingEdge(d.clk)
        for _ in range(32):
            rdy = ival(d.dll_pcs_ready, 0)
            if rdy is not None and int(rdy) == 1:
                break
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
        sset(d.dll_pcs_data, int(beat) & MASK640)
        sset(d.dll_pcs_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.dll_pcs_vld, 0)

    async def _wait_lane(self, n=PIPE_TIMEOUT):
        for _ in range(n):
            await RisingEdge(self.dut.clk)
            got = ival(self.dut.pcs_afifo_lane_vld, 0)
            if got is not None and int(got) != 0:
                return int(got)
        return 0

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset with link_up=0: G1 not ready, scramble idle.
        rdy = ival(d.dll_pcs_ready, None)
        if rdy is None or int(rdy) != 0:
            self.bad(name, "reset then release, link_up=0 dll_pcs_ready",
                     "dll_pcs_ready=0", self._fmt(), "u_ptx.u_g1.in_ready")
            phase.drop_objection(self)
            return
        lv = ival(d.pcs_afifo_lane_vld, None)
        if lv is not None and int(lv) != 0:
            self.bad(name, "reset idle pcs_afifo_lane_vld",
                     "pcs_afifo_lane_vld=0", self._fmt(),
                     "u_ptx.pcs_afifo_lane_vld")
            phase.drop_objection(self)
            return

        # 2. link_up=1: G1 combo ready (empty, win_ready from FEC).
        sset(d.link_up, 1)
        await self._settle()
        rdy = ival(d.dll_pcs_ready, None)
        if rdy is None or int(rdy) != 1:
            self.bad(name, "link_up=1 empty G1 ready",
                     "dll_pcs_ready=1", self._fmt(), "u_ptx.u_g1.in_ready")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 3. Light DLL beat + bypass pipeline (RTL-known fec_mode=0).
        # G1 idle-fills Null windows while link_up; two windows start FEC
        # bypass, then cw2beat / pack / scramble. Observe lane_vld.
        await self._push_beat(STOCK_BEAT)
        await self._push_beat(STOCK_BEAT)
        sset(d.dll_pcs_vld, 0)
        saw = await self._wait_lane(PIPE_TIMEOUT)
        if saw == 0:
            self.bad(name, "bypass pipeline pcs_afifo_lane_vld (observe)",
                     "pcs_afifo_lane_vld=1", self._fmt(),
                     "u_ptx.pcs_afifo_lane_vld")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 4. afifo_afull combo-clears pack beat_ready (no Force).
        sset(d.afifo_afull, 1)
        await self._settle()
        br = self._inner("u_ptx.u_pack.beat_ready", None)
        if br is not None and int(br) != 0:
            self.bad(name, "afifo_afull clears u_pack.beat_ready",
                     "beat_ready=0", f"beat_ready={br}",
                     "u_ptx.u_pack.beat_ready")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        sset(d.afifo_afull, 0)
        await self._settle()

        # 5. fec_mode T4 is RTL-known (vibe_port ties T4). Ready still
        # combo from G1; do not invent encode packing.
        sset(d.fec_mode, FEC_T4)
        await self._settle()
        if ival(d.fec_mode, -1) != FEC_T4:
            self.bad(name, "RTL-known fec_mode=T4 pin",
                     f"fec_mode={FEC_T4}", self._fmt(), "u_ptx.fec_mode")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        sset(d.fec_mode, FEC_BYPASS)
        await self._settle()

        # 6. Async rst_n (no posedge) clears registered scramble outs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.pcs_afifo_lane_vld, 1) != 0:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     "pcs_afifo_lane_vld=0", self._fmt(),
                     "u_ptx.u_s0.out_vld")
            phase.drop_objection(self)
            return
        unresolved = 0
        for i, net in enumerate(("pcs_afifo_lane0", "pcs_afifo_lane1",
                                 "pcs_afifo_lane2", "pcs_afifo_lane3")):
            got = ival(getattr(d, net), None)
            if got is None or (isinstance(got, int) and got < 0):
                unresolved += 1
                continue
            if int(got) != 0:
                self.bad(name, f"async rst_n clears {net}",
                         f"{net}=0", f"{net}={got:#x}",
                         f"u_ptx.u_s{i}.out_data")
                phase.drop_objection(self)
                return
        if unresolved and unresolved != 4:
            self.bad(name, "async rst_n (mixed lane X)",
                     "all lanes resolvable or all X",
                     f"unresolved={unresolved}", "u_ptx.s0")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.dll_pcs_ready, 1) != 0:
            self.bad(name, "after async re-reset, link_up=0",
                     "dll_pcs_ready=0", self._fmt(), "u_ptx.u_g1.in_ready")
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
                       "cna", "nw_fab_vld"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_pcs_tx product / wrap port",
                         f"{absent} present",
                         "vibe_pcs_tx_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n", "link_up", "sdf_period", "fec_mode",
                     "afifo_afull", "dll_pcs_data", "dll_pcs_vld",
                     "dll_pcs_ready", "pcs_afifo_lane0", "pcs_afifo_lane1",
                     "pcs_afifo_lane2", "pcs_afifo_lane3",
                     "pcs_afifo_lane_vld"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_pcs_tx_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx)
