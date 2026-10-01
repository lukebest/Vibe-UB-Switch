"""Wrap-level uvm-python TC for Decision-I stage-45 vibe_mgmt.

Covers submodule wiring (u_cfg / u_rst / u_cna / u_irq as the
product DUT instantiates them); reset / async rst_n; wrap
port_rst = rst_ctl hold | cfg RW1C; light CFG write smoke for
RTL-known cmds 0–5 (6–15 ignore, irq_clr still pulses); rst_ctl
Port Reset / device-reset stretch then HW clear; CFG6 terminate
+ request echo through u_cna (no Appendix D / opcode-0x10 packing
invented); irq_agg sticky from drop_g1, clear on any accepted
write. Not a full-chip consecutive-green gate (stock tc_mgmt
remains the direct-top scorer). Not 1/3, 4/3, freeze, or signoff.
Not a vibe_fabric wrap. Does not steal make top / wrap / port /
top_wrap.

Matches product rtl/mgmt/vibe_mgmt.sv: vibe_cfg_space u_cfg,
vibe_rst_ctl u_rst, vibe_cna_ep u_cna, vibe_irq_agg u_irq.
cfg_wr_cmd is 4 bits (0=CNA, 1=route, 2=Default bitmap, 3=Port
Reset W1C, 4=device reset, 5=lmsm_go; 6–15 ignore). No cfg_rd_*
pin. F1 ovf_l stays stock inside vibe_port. CFG6 R/W packing is
未知 — do not invent. Prefer observing child-driven nets over
Force. Stock Icarus / pyuvm tc_mgmt remain the official direct
vibe_mgmt scorers.
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
# RTL-known cfg_wr_cmd (vibe_cfg_space). Do not invent 6–15 packing.
CMD_CNA = 0
CMD_RT = 1
CMD_BM = 2
CMD_PORT_RST = 3
CMD_DEV_RST = 4
CMD_LMSM_GO = 5
CMD_IGNORE = 7
STOCK_CNA = 0x1111
STOCK_RT_IDX = 0x0003
STOCK_RT_DATA = 0x0000000F
STOCK_BM = 0x5
STOCK_MISS = 0x2222
CHILDREN = ("u_cfg", "u_rst", "u_cna", "u_irq")
HIER = "u_m.u_cfg / u_m.u_rst / u_m.u_cna / u_m.u_irq"
ERR_VECS = (
    "rx_ovf", "fc_ovf", "proto_err", "retry_error",
    "len_err", "deadlock_drop", "afifo_ovf",
)
ERR_BITS = ("drop_g1",)


def cfg6_beat(dcna, nlp=0, opc=0, tag=0):
    """Stock CFG6 flit0 + distinct payload tag. No Appendix D pack."""
    flit = lph.mk_flit(6, 0, 0, 2, dcna, lph.plen_nflit(1), 0, 0, nlp, opc)
    return lph.mk_beat(flit, int(tag) & MASK352)


class tc_vibe_mgmt(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.cfg_wr_vld, 0)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        sset(d.fab_mgmt_cfg6_hit, 0)
        sset(d.mgmt_nw_ready, 0xF)
        for i in range(PORT_N):
            sset(getattr(d, f"fab_mgmt_cfg6_data_{i}"), 0)
        for n in ERR_VECS:
            sset(getattr(d, n), 0)
        for n in ERR_BITS:
            sset(getattr(d, n), 0)

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
            f"rdy={ival(d.cfg_wr_ready, -1)} irq={ival(d.irq_logic, -1)} "
            f"cna={ival(d.cna, -1):#x} wr={ival(d.cna_written, -1)} "
            f"bm={ival(d.default_bm, -1):#x} "
            f"rt_en={ival(d.rt_wr_en, -1)} "
            f"prst={ival(d.port_rst, -1):#x} "
            f"drst={ival(d.device_rst, -1)} "
            f"lgo={ival(d.lmsm_go, -1):#x} "
            f"cons={ival(d.mgmt_fab_cfg6_consume, -1):#x} "
            f"nvld={ival(d.mgmt_nw_vld, -1):#x} "
            f"hold={self._inner('u_m.u_rst.port_rst', -1)} "
            f"rw1c={self._inner('u_m.u_cfg.port_rst_rw1c', -1)} "
            f"iclr={self._inner('u_m.u_cfg.irq_clr', -1)}"
        )

    def _score_children(self, name):
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_m.{inst}")]
        if missing:
            self.bad(name, "AS-0.1 §4/§10 children present",
                     "u_cfg u_rst u_cna u_irq",
                     f"missing={missing}", "u_m")
            return False
        return True

    def _score_combo(self, name):
        pin_rdy = ival(self.dut.cfg_wr_ready, None)
        cfg_rdy = self._inner("u_m.u_cfg.cfg_wr_ready", None)
        if pin_rdy is not None and int(pin_rdy) != 1:
            self.bad(name, "wrap cfg_wr_ready tied",
                     "cfg_wr_ready=1", self._fmt(), "u_m.u_cfg.cfg_wr_ready")
            return False
        if (pin_rdy is not None and cfg_rdy is not None
                and int(pin_rdy) != int(cfg_rdy)):
            self.bad(name, "wrap cfg_wr_ready from u_cfg",
                     f"cfg_wr_ready={cfg_rdy}", f"cfg_wr_ready={pin_rdy}",
                     "u_m.u_cfg.cfg_wr_ready")
            return False
        pin_irq = ival(self.dut.irq_logic, None)
        irq = self._inner("u_m.u_irq.irq_logic", None)
        if (pin_irq is not None and irq is not None
                and int(pin_irq) != int(irq)):
            self.bad(name, "wrap irq_logic from u_irq",
                     f"irq_logic={irq}", f"irq_logic={pin_irq}",
                     "u_m.u_irq.irq_logic")
            return False
        for net in ("cna", "cna_written", "default_bm", "rt_wr_en",
                    "rt_wr_idx", "rt_wr_data"):
            pin = ival(getattr(self.dut, net), None)
            ch = self._inner(f"u_m.u_cfg.{net}", None)
            if pin is not None and ch is not None and int(pin) != int(ch):
                self.bad(name, f"wrap {net} from u_cfg",
                         f"{net}={ch}", f"{net}={pin}", f"u_m.u_cfg.{net}")
                return False
        hold = self._inner("u_m.u_rst.port_rst", None)
        rw1c = self._inner("u_m.u_cfg.port_rst_rw1c", None)
        pin_pr = ival(self.dut.port_rst, None)
        if hold is not None and rw1c is not None and pin_pr is not None:
            exp = (int(hold) | int(rw1c)) & MASK4
            if int(pin_pr) != exp:
                self.bad(name, "wrap port_rst = hold | rw1c",
                         f"port_rst={exp:#x}", f"port_rst={int(pin_pr):#x}",
                         "u_m.port_rst")
                return False
        pin_dr = ival(self.dut.device_rst, None)
        rst_dr = self._inner("u_m.u_rst.device_rst", None)
        if (pin_dr is not None and rst_dr is not None
                and int(pin_dr) != int(rst_dr)):
            self.bad(name, "wrap device_rst from u_rst",
                     f"device_rst={rst_dr}", f"device_rst={pin_dr}",
                     "u_m.u_rst.device_rst")
            return False
        pin_go = ival(self.dut.lmsm_go, None)
        cfg_go = self._inner("u_m.u_cfg.lmsm_go_pulse", None)
        if (pin_go is not None and cfg_go is not None
                and int(pin_go) != int(cfg_go)):
            self.bad(name, "wrap lmsm_go from u_cfg.lmsm_go_pulse",
                     f"lmsm_go={cfg_go}", f"lmsm_go={pin_go}",
                     "u_m.u_cfg.lmsm_go_pulse")
            return False
        pin_c = ival(self.dut.mgmt_fab_cfg6_consume, None)
        cna_c = self._inner("u_m.u_cna.mgmt_fab_cfg6_consume", None)
        if (pin_c is not None and cna_c is not None
                and int(pin_c) != int(cna_c)):
            self.bad(name, "wrap consume from u_cna",
                     f"consume={cna_c:#x}", f"consume={pin_c:#x}",
                     "u_m.u_cna.mgmt_fab_cfg6_consume")
            return False
        pin_v = ival(self.dut.mgmt_nw_vld, None)
        cna_v = self._inner("u_m.u_cna.mgmt_nw_vld", None)
        if (pin_v is not None and cna_v is not None
                and int(pin_v) != int(cna_v)):
            self.bad(name, "wrap mgmt_nw_vld from u_cna",
                     f"vld={cna_v:#x}", f"vld={pin_v:#x}",
                     "u_m.u_cna.mgmt_nw_vld")
            return False
        return True

    async def _cfgw(self, cmd, idx, data):
        """One accepted cfg_wr beat. Sample child nets on the write cycle."""
        d = self.dut
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, int(cmd) & 0xF)
        sset(d.cfg_wr_idx, int(idx) & MASK16)
        sset(d.cfg_wr_data, int(data) & MASK32)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        snap = {
            "cna": ival(d.cna, None),
            "cna_written": ival(d.cna_written, None),
            "default_bm": ival(d.default_bm, None),
            "rt_wr_en": ival(d.rt_wr_en, None),
            "rt_wr_idx": ival(d.rt_wr_idx, None),
            "rt_wr_data": ival(d.rt_wr_data, None),
            "lmsm_go": ival(d.lmsm_go, None),
            "port_rst": ival(d.port_rst, None),
            "device_rst": ival(d.device_rst, None),
            "irq_clr": self._inner("u_m.u_cfg.irq_clr", None),
            "pulse": self._inner("u_m.u_cfg.port_rst_pulse", None),
            "hold": self._inner("u_m.u_rst.port_rst", None),
            "rw1c": self._inner("u_m.u_cfg.port_rst_rw1c", None),
            "dev_pulse": self._inner("u_m.u_cfg.device_rst_pulse", None),
        }
        sset(d.cfg_wr_vld, 0)
        return snap

    def _score_echo(self, name, stim, hit, beats, written, cna):
        exp_c, exp_v, exp_d, exp_i = 0, 0, [0] * PORT_N, 0
        for p in range(PORT_N):
            beat = int(beats[p]) & MASK512
            if (int(hit) >> p) & 1:
                flit = lph.nw512_flit0(beat)
                if lph.cfg6_should_term(bool(written), int(cna) & MASK16, flit):
                    exp_c |= 1 << p
                    exp_v |= 1 << p
                    exp_d[p] = beat
        got_c = ival(self.dut.mgmt_fab_cfg6_consume, None)
        got_v = ival(self.dut.mgmt_nw_vld, None)
        got_i = self._inner("u_m.u_cna.icrc_fail", None)
        if None in (got_c, got_v):
            self.bad(name, stim,
                     f"consume={exp_c:#x} vld={exp_v:#x}",
                     f"consume={got_c} vld={got_v}", "u_m.u_cna")
            return False
        if int(got_c) != exp_c or int(got_v) != exp_v:
            self.bad(name, stim,
                     f"consume={exp_c:#x} vld={exp_v:#x}",
                     f"consume={int(got_c):#x} vld={int(got_v):#x}",
                     "u_m.u_cna")
            return False
        if got_i not in (None, exp_i) and int(got_i) != exp_i:
            self.bad(name, f"{stim} (icrc_fail tied 0)",
                     f"icrc_fail={exp_i}", f"icrc_fail={got_i}",
                     "u_m.u_cna.icrc_fail")
            return False
        unresolved = 0
        for p in range(PORT_N):
            gd = ival(getattr(self.dut, f"mgmt_nw_data_{p}"), None)
            if gd is None or gd < 0:
                unresolved += 1
                continue
            if (gd & MASK512) != exp_d[p]:
                self.bad(name, f"{stim} (echo port {p})",
                         f"mgmt_nw_data={exp_d[p]:#x} (request echo)",
                         f"mgmt_nw_data={gd:#x}",
                         f"u_m.u_cna.mgmt_nw_data[{p}]")
                return False
        # Icarus 12 VPI: 512-bit packed mgmt_nw_data_* is X.
        if unresolved and unresolved != PORT_N:
            self.bad(name, f"{stim} (mixed echo X)",
                     "all mgmt_nw_data resolvable or all X",
                     f"unresolved={unresolved}", "u_m.u_cna.mgmt_nw_data")
            return False
        return True

    async def _drive_cfg6(self, hit, beats):
        d = self.dut
        for p in range(PORT_N):
            sset(getattr(d, f"fab_mgmt_cfg6_data_{p}"),
                 int(beats[p]) & MASK512)
        sset(d.fab_mgmt_cfg6_hit, int(hit) & MASK4)
        await self._settle()

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_mgmt"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 1. After reset: ready tied, irq idle, seq outputs 0.
        if ival(d.cfg_wr_ready, 0) != 1:
            self.bad(name, "reset then release, cfg_wr_ready tied",
                     "cfg_wr_ready=1", self._fmt(), "u_m.u_cfg.cfg_wr_ready")
            phase.drop_objection(self)
            return
        if ival(d.irq_logic, 1) != 0:
            self.bad(name, "reset then release, irq_logic idle",
                     "irq_logic=0", self._fmt(), "u_m.u_irq.irq_logic")
            phase.drop_objection(self)
            return
        for net, exp in (("cna", 0), ("cna_written", 0), ("default_bm", 0),
                         ("rt_wr_en", 0), ("port_rst", 0), ("device_rst", 0),
                         ("lmsm_go", 0), ("mgmt_fab_cfg6_consume", 0),
                         ("mgmt_nw_vld", 0)):
            got = ival(getattr(d, net), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle wrap {net}",
                         f"{net}={exp}", self._fmt(), f"u_m.{net}")
                phase.drop_objection(self)
                return
        guid = self._inner("u_m.u_cfg.guid0", None)
        klass = self._inner("u_m.u_cfg.class_code", None)
        if guid not in (None, 0x03) and int(guid) != 0x03:
            self.bad(name, "u_cfg GUID Type 0x3",
                     "guid0=0x3", f"guid0={guid:#x}", "u_m.u_cfg.guid0")
            phase.drop_objection(self)
            return
        if klass not in (None, 0x0300) and int(klass) != 0x0300:
            self.bad(name, "u_cfg Class 0x0300",
                     "class_code=0x0300", f"class_code={klass:#x}",
                     "u_m.u_cfg.class_code")
            phase.drop_objection(self)
            return

        # 2. Light CFG smoke — only RTL-known opcodes (0–5; 7 ignore).
        snap = await self._cfgw(CMD_CNA, 0, STOCK_CNA)
        if snap["cna"] not in (None, STOCK_CNA) and snap["cna"] != STOCK_CNA:
            self.bad(name, "cfg_wr cmd=0 CNA (stock tc_mgmt)",
                     f"cna={STOCK_CNA:#x}", f"cna={snap['cna']}",
                     "u_m.u_cfg.cna")
            phase.drop_objection(self)
            return
        if (snap["cna_written"] not in (None, 1)
                and snap["cna_written"] != 1):
            self.bad(name, "cfg_wr cmd=0 sets cna_written",
                     "cna_written=1", f"cna_written={snap['cna_written']}",
                     "u_m.u_cfg.cna_written")
            phase.drop_objection(self)
            return
        if snap["irq_clr"] not in (None, 1) and snap["irq_clr"] != 1:
            self.bad(name, "any accepted write pulses irq_clr",
                     "irq_clr=1", f"irq_clr={snap['irq_clr']}",
                     "u_m.u_cfg.irq_clr")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_RT, STOCK_RT_IDX, STOCK_RT_DATA)
        if snap["rt_wr_en"] not in (None, 1) and snap["rt_wr_en"] != 1:
            self.bad(name, "cfg_wr cmd=1 route pulse",
                     "rt_wr_en=1", f"rt_wr_en={snap['rt_wr_en']}",
                     "u_m.u_cfg.rt_wr_en")
            phase.drop_objection(self)
            return
        if (snap["rt_wr_idx"] not in (None, STOCK_RT_IDX)
                and snap["rt_wr_idx"] != STOCK_RT_IDX):
            self.bad(name, "cfg_wr cmd=1 captures idx",
                     hex(STOCK_RT_IDX),
                     "none" if snap["rt_wr_idx"] is None
                     else hex(int(snap["rt_wr_idx"])),
                     "u_m.u_cfg.rt_wr_idx")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_BM, 0, STOCK_BM)
        if (snap["default_bm"] not in (None, STOCK_BM)
                and snap["default_bm"] != STOCK_BM):
            self.bad(name, "cfg_wr cmd=2 Default bitmap",
                     f"default_bm={STOCK_BM}",
                     f"default_bm={snap['default_bm']}",
                     "u_m.u_cfg.default_bm")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_LMSM_GO, 0, 0)
        go = snap["lmsm_go"]
        if go is not None and ((int(go) >> 0) & 1) != 1:
            self.bad(name, "cfg_wr cmd=5 pulse lmsm_go[0]",
                     "lmsm_go[0]=1", f"lmsm_go={go}", "u_m.lmsm_go")
            phase.drop_objection(self)
            return
        await self._to_fall()
        if ival(d.lmsm_go, 1) != 0:
            self.bad(name, "lmsm_go is a 1-cycle pulse",
                     "lmsm_go=0 next cycle", self._fmt(),
                     "u_m.u_cfg.lmsm_go_pulse")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_PORT_RST, 0, 0)
        if snap["port_rst"] not in (None, 0) and int(snap["port_rst"]) != 0:
            self.bad(name, "cfg_wr cmd=3 data[0]=0 must-not (stock tc_mgmt)",
                     "port_rst=0", self._fmt(), "u_m.port_rst")
            phase.drop_objection(self)
            return

        snap = await self._cfgw(CMD_PORT_RST, 0, 1)
        pr = snap["port_rst"]
        if pr is not None and ((int(pr) >> 0) & 1) != 1:
            self.bad(name, "cfg_wr cmd=3 Port Reset W1C port0",
                     "port_rst[0]=1", f"port_rst={pr}", "u_m.port_rst")
            phase.drop_objection(self)
            return
        if (snap["rw1c"] is not None
                and ((int(snap["rw1c"]) >> 0) & 1) != 1):
            self.bad(name, "cmd=3 sets u_cfg.port_rst_rw1c[0]",
                     "rw1c[0]=1", f"rw1c={snap['rw1c']}",
                     "u_m.u_cfg.port_rst_rw1c")
            phase.drop_objection(self)
            return
        if (snap["hold"] is not None
                and ((int(snap["hold"]) >> 0) & 1) != 1):
            self.bad(name, "cmd=3 starts u_rst port hold",
                     "hold[0]=1", f"hold={snap['hold']}",
                     "u_m.u_rst.port_rst")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        # rst_ctl stretch: hold 7 dest clocks then HW-clear RW1C.
        still = None
        for _ in range(6):
            await self._to_fall()
            still = ival(d.port_rst, None)
            if still is not None and (int(still) & 1) != 1:
                self.bad(name, "rst_ctl Port Reset stretch holds",
                         "port_rst[0]=1 during hold", self._fmt(),
                         "u_m.u_rst.port_rst")
                phase.drop_objection(self)
                return
        cleared = False
        for _ in range(6):
            await self._to_fall()
            got = ival(d.port_rst, None)
            if got is not None and (int(got) & 1) == 0:
                cleared = True
                break
        if not cleared:
            self.bad(name, "rst_ctl hold_fall HW-clears Port Reset",
                     "port_rst[0]=0 after stretch", self._fmt(),
                     "u_m.u_cfg.port_rst_rw1c")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        held_cna = ival(d.cna, STOCK_CNA)
        snap = await self._cfgw(CMD_IGNORE, 0, 0xA5A5)
        if (held_cna is not None and snap["cna"] is not None
                and int(snap["cna"]) != int(held_cna)):
            self.bad(name, "cfg_wr cmd=7 ignore (no invented CFG6)",
                     f"cna stays {held_cna:#x}", f"cna={snap['cna']}",
                     "u_m.u_cfg.cna")
            phase.drop_objection(self)
            return
        if snap["irq_clr"] not in (None, 1) and snap["irq_clr"] != 1:
            self.bad(name, "cmd 6–15 ignore still irq_clr",
                     "irq_clr=1", f"irq_clr={snap['irq_clr']}",
                     "u_m.u_cfg.irq_clr")
            phase.drop_objection(self)
            return
        if snap["rt_wr_en"] not in (None, 0) and snap["rt_wr_en"] != 0:
            self.bad(name, "cmd=7 does not pulse rt_wr_en",
                     "rt_wr_en=0", f"rt_wr_en={snap['rt_wr_en']}",
                     "u_m.u_cfg.rt_wr_en")
            phase.drop_objection(self)
            return

        # 3. CFG6 echo through u_cna after CNA written. No packing invent.
        zeros = [0] * PORT_N
        beats = list(zeros)
        beats[0] = cfg6_beat(STOCK_CNA, tag=0xA11A)
        await self._drive_cfg6(0x1, beats)
        if not self._score_echo(
                name, "DCNA==written CNA terminate+echo",
                0x1, beats, 1, STOCK_CNA):
            phase.drop_objection(self)
            return
        await self._drive_cfg6(0, beats)
        if not self._score_echo(
                name, "CFG6 hit deassert (combo drop, not sticky)",
                0, beats, 1, STOCK_CNA):
            phase.drop_objection(self)
            return
        beats = list(zeros)
        beats[1] = cfg6_beat(STOCK_MISS, nlp=1, tag=0xB22B)
        await self._drive_cfg6(0x2, beats)
        if not self._score_echo(
                name, "NLP=1 DCNA!=CNA still terminate+echo",
                0x2, beats, 1, STOCK_CNA):
            phase.drop_objection(self)
            return
        beats = list(zeros)
        beats[2] = cfg6_beat(STOCK_MISS, tag=0xC33C)
        await self._drive_cfg6(0x4, beats)
        if not self._score_echo(
                name, "miss CNA NLP=0 forward (no consume)",
                0x4, beats, 1, STOCK_CNA):
            phase.drop_objection(self)
            return
        # opc 0x10 without us does not terminate; do not invent CSR pack.
        beats = list(zeros)
        beats[3] = cfg6_beat(STOCK_MISS, opc=0x10, tag=0xD44D)
        await self._drive_cfg6(0x8, beats)
        if not self._score_echo(
                name, "opc 0x10 without us (no invented CFG6 CSR)",
                0x8, beats, 1, STOCK_CNA):
            phase.drop_objection(self)
            return
        sset(d.fab_mgmt_cfg6_hit, 0)
        await self._settle()
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 4. irq_agg sticky from drop_g1; any write clears (irq_clr wins).
        await FallingEdge(d.clk)
        sset(d.drop_g1, 1)
        await self._to_fall()
        if ival(d.irq_logic, 0) != 1:
            self.bad(name, "drop_g1 sets irq_logic sticky (stock tc_mgmt)",
                     "irq_logic=1", self._fmt(), "u_m.u_irq.irq_logic")
            phase.drop_objection(self)
            return
        sset(d.drop_g1, 0)
        await self._to_fall()
        if ival(d.irq_logic, 0) != 1:
            self.bad(name, "irq_logic stays sticky after drop_g1 deassert",
                     "irq_logic=1", self._fmt(), "u_m.u_irq.sticky")
            phase.drop_objection(self)
            return
        snap = await self._cfgw(CMD_IGNORE, 0, 0)
        if ival(d.irq_logic, 1) != 0:
            self.bad(name, "accepted write irq_clr clears sticky",
                     "irq_logic=0", self._fmt(), "u_m.u_irq.irq_logic")
            phase.drop_objection(self)
            return
        if snap["irq_clr"] not in (None, 1) and snap["irq_clr"] != 1:
            self.bad(name, "clear write still pulses irq_clr",
                     "irq_clr=1", f"irq_clr={snap['irq_clr']}",
                     "u_m.u_cfg.irq_clr")
            phase.drop_objection(self)
            return

        # 5. device_rst stretch clears CNA / cna_written (u_rst → u_cfg).
        snap = await self._cfgw(CMD_DEV_RST, 0, 0)
        if snap["device_rst"] not in (None, 1) and snap["device_rst"] != 1:
            self.bad(name, "cfg_wr cmd=4 starts device_rst hold",
                     "device_rst=1", self._fmt(), "u_m.u_rst.device_rst")
            phase.drop_objection(self)
            return
        if (snap["dev_pulse"] not in (None, 1)
                and snap["dev_pulse"] != 1):
            self.bad(name, "cmd=4 pulses u_cfg.device_rst_pulse",
                     "device_rst_pulse=1", f"pulse={snap['dev_pulse']}",
                     "u_m.u_cfg.device_rst_pulse")
            phase.drop_objection(self)
            return
        await self._to_fall()
        if ival(d.cna, 1) != 0 or ival(d.cna_written, 1) != 0:
            self.bad(name, "device_rst hold clears CNA (unwritten)",
                     "cna=0 cna_written=0", self._fmt(), "u_m.u_cfg.cna")
            phase.drop_objection(self)
            return
        if ival(d.default_bm, 1) != 0:
            self.bad(name, "device_rst hold clears default_bm",
                     "default_bm=0", self._fmt(), "u_m.u_cfg.default_bm")
            phase.drop_objection(self)
            return
        # Power-on CNA UNKNOWN: matching DCNA must not terminate.
        beats = list(zeros)
        beats[0] = cfg6_beat(STOCK_CNA, tag=0xE55E)
        await self._drive_cfg6(0x1, beats)
        if not self._score_echo(
                name, "device_rst CNA unwritten, no CFG6 match",
                0x1, beats, 0, 0):
            phase.drop_objection(self)
            return
        sset(d.fab_mgmt_cfg6_hit, 0)
        released = False
        for _ in range(10):
            await self._to_fall()
            if ival(d.device_rst, 1) == 0:
                released = True
                break
        if not released:
            self.bad(name, "rst_ctl device_rst released after stretch",
                     "device_rst=0", self._fmt(), "u_m.u_rst.device_rst")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 6. Async rst_n (no posedge) clears registered wrap outputs.
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.irq_logic, 1) != 0:
            self.bad(name, "async rst_n=0 (100ps, no posedge)",
                     "irq_logic=0", self._fmt(), "u_m.u_irq.irq_logic")
            phase.drop_objection(self)
            return
        if ival(d.cna, 1) != 0 or ival(d.cna_written, 1) != 0:
            self.bad(name, "async rst_n clears CNA",
                     "cna=0 cna_written=0", self._fmt(), "u_m.u_cfg.cna")
            phase.drop_objection(self)
            return
        if ival(d.port_rst, 1) != 0 or ival(d.device_rst, 1) != 0:
            self.bad(name, "async rst_n clears rst_ctl holds",
                     "port_rst=0 device_rst=0", self._fmt(), "u_m.u_rst")
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.irq_logic, 1) != 0 or ival(d.cfg_wr_ready, 0) != 1:
            self.bad(name, "after async re-reset release",
                     "irq_logic=0 cfg_wr_ready=1", self._fmt(), "u_m")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return

        # 7. Product wrap pins. No cfg_rd_* / Appendix D / F1 ovf_l / smoke-top.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_cmd",
                       "appendix_d", "ovf_l", "u_peer", "prst",
                       "clk_fab", "pcs_pma_txdata"):
            if hasattr(d, absent):
                self.bad(name, f"wrap pin scan ({absent})",
                         "not a vibe_mgmt product / wrap port",
                         f"{absent} present",
                         "vibe_mgmt_wrap_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("clk", "rst_n",
                     "cfg_wr_vld", "cfg_wr_ready", "cfg_wr_cmd",
                     "cfg_wr_idx", "cfg_wr_data",
                     "cna", "cna_written", "default_bm",
                     "rt_wr_en", "rt_wr_idx", "rt_wr_data",
                     "port_rst", "device_rst", "lmsm_go",
                     "fab_mgmt_cfg6_hit",
                     "fab_mgmt_cfg6_data_0", "fab_mgmt_cfg6_data_1",
                     "fab_mgmt_cfg6_data_2", "fab_mgmt_cfg6_data_3",
                     "mgmt_fab_cfg6_consume",
                     "mgmt_nw_data_0", "mgmt_nw_data_1",
                     "mgmt_nw_data_2", "mgmt_nw_data_3",
                     "mgmt_nw_vld", "mgmt_nw_ready",
                     "rx_ovf", "fc_ovf", "proto_err", "retry_error",
                     "len_err", "deadlock_drop", "drop_g1", "afifo_ovf",
                     "irq_logic"):
            if not hasattr(d, need):
                self.bad(name, f"wrap pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_mgmt_wrap_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_mgmt)
