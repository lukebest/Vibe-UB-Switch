"""Module-level uvm-python TC for Decision-I leaf vibe_cfg_space.

Covers reset/idle (seq outputs 0, cfg_wr_ready=1), product identity
constants already assigned in RTL (GUID Type 0x3, Class 0x0300,
PORT_BASIC/CAP), stock Icarus tc_identity_cfg_space / tc_cna_16bit
static writes (cmd 0 CNA, 1 route pulse, 2 Default bitmap, 3 Port
Reset data[0]==0 must-not / data[0]==1 W1C, 4 device_rst_pulse,
5 lmsm_go, 7 ignored still irq_clr, device_rst pin clears CNA),
walk-1 Port Reset / lmsm_go on every port, 1-cycle pulses, held
cna / default_bm / rt_wr_idx/data, cmd 6–15 ignore, hold_fall HW
clear, same-cycle W1C retrigger masks hold_fall, RSVD data bits
ignored, idx[15:2] unused for port cmds, cfg_wr_vld=0 no-op,
async rst_n mid-state. Not a full-chip consecutive-green gate.
Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/mgmt/vibe_cfg_space.sv: async-low rst_n,
device_rst sampled on posedge, cfg_wr_ready tied 1, wr_acc =
cfg_wr_vld && ready, irq_clr on any accepted write, Port Reset
RW1C per cfg_wr_idx[1:0], hold_fall HW clear when rst_ctl hold
ends (same-cycle W1C masks that bit). No cfg_rd_* pin (AS §18).
Instantiated by vibe_mgmt u_cfg. Stock Icarus
tc_identity_cfg_space remains the official TP scorer (direct
vibe_cfg_space top, wrap-style). This is not the wrap-style
tc_identity_cfg_space / tc_cna_16bit / tc_mgmt. ovf_l (F1) is
not in this module. CFG6 R/W / Appendix D packing is 未知 —
do not invent. CFG6 elsewhere is echo-only (vibe_cna_ep).
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

PORT_N = 4
MASK4 = 0xF
MASK16 = 0xFFFF
MASK32 = 0xFFFFFFFF
HIER = "u_u.cna / u_u.port_rst_rw1c / u_u.irq_clr"

# Stock Icarus tc_identity_cfg_space / tc_cna_16bit vectors.
STOCK_CNA = 0xBEEF
STOCK_CNA32 = 0x00ABCDEF
STOCK_CNA16 = 0xCDEF
STOCK_RT_IDX = 0x0003
STOCK_RT_DATA = 0x0000000F
STOCK_BM = 0x5
STOCK_PORT = 2

SEQ_FIELDS = (
    ("cna", MASK16),
    ("cna_written", 1),
    ("default_bm", MASK4),
    ("rt_wr_en", 1),
    ("rt_wr_idx", MASK16),
    ("rt_wr_data", MASK32),
    ("port_rst_pulse", MASK4),
    ("port_rst_rw1c", MASK4),
    ("device_rst_pulse", 1),
    ("lmsm_go_pulse", MASK4),
    ("irq_clr", 1),
)

CONST_EXPECT = (
    ("cfg_wr_ready", 1),
    ("guid0", 0x03),
    ("class_code", 0x0300),
    ("port_basic", lph.PORT_BASIC),
    ("port_cap", lph.PORT_CAP),
)


class Golden:
    """Cycle-accurate vs product posedge / async rst_n / device_rst."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.cna = 0
        self.cna_written = 0
        self.default_bm = 0
        self.rt_wr_en = 0
        self.rt_wr_idx = 0
        self.rt_wr_data = 0
        self.port_rst_pulse = 0
        self.device_rst_pulse = 0
        self.lmsm_go_pulse = 0
        self.irq_clr = 0
        self.port_rst_rw1c = 0
        self.port_rst_hold_d = 0

    def step(self, vld=0, cmd=0, idx=0, data=0, hold=0, device_rst=0, rst_n=1):
        if not rst_n or device_rst:
            self.reset()
            return
        cmd = int(cmd) & 0xF
        idx = int(idx) & MASK16
        data = int(data) & MASK32
        hold = int(hold) & MASK4
        wr_acc = bool(int(vld))
        wr_port = idx & 0x3
        wr_port_rst_w1c = wr_acc and cmd == 3 and (data & 1)
        hold_fall = 0
        for i in range(PORT_N):
            if ((self.port_rst_hold_d >> i) & 1) and not ((hold >> i) & 1):
                if not (wr_port_rst_w1c and wr_port == i):
                    hold_fall |= 1 << i
        self.rt_wr_en = 0
        self.port_rst_pulse = 0
        self.device_rst_pulse = 0
        self.lmsm_go_pulse = 0
        self.irq_clr = 0
        self.port_rst_hold_d = hold
        for i in range(PORT_N):
            if (hold_fall >> i) & 1:
                self.port_rst_rw1c &= ~(1 << i)
        if not wr_acc:
            return
        self.irq_clr = 1
        if cmd == 0:
            self.cna = data & MASK16
            self.cna_written = 1
        elif cmd == 1:
            self.rt_wr_en = 1
            self.rt_wr_idx = idx
            self.rt_wr_data = data
        elif cmd == 2:
            self.default_bm = data & MASK4
        elif cmd == 3:
            if data & 1:
                self.port_rst_rw1c |= 1 << wr_port
                self.port_rst_pulse |= 1 << wr_port
        elif cmd == 4:
            self.device_rst_pulse = 1
        elif cmd == 5:
            self.lmsm_go_pulse |= 1 << wr_port


class tc_vibe_cfg_space(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.device_rst, 0)
        sset(d.cfg_wr_vld, 0)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        sset(d.port_rst_hold, 0)

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

    def _drive(self, vld=0, cmd=0, idx=0, data=0, hold=0, device_rst=0):
        d = self.dut
        sset(d.device_rst, 1 if device_rst else 0)
        sset(d.cfg_wr_vld, 1 if vld else 0)
        sset(d.cfg_wr_cmd, int(cmd) & 0xF)
        sset(d.cfg_wr_idx, int(idx) & MASK16)
        sset(d.cfg_wr_data, int(data) & MASK32)
        sset(d.port_rst_hold, int(hold) & MASK4)

    def _sample(self):
        d = self.dut
        snap = {}
        for name, mask in SEQ_FIELDS:
            snap[name] = ival(getattr(d, name), None)
        for name, _exp in CONST_EXPECT:
            snap[name] = ival(getattr(d, name), None)
        return snap

    def _expect(self):
        exp = {n: getattr(self.g, n) & m for n, m in SEQ_FIELDS}
        for name, val in CONST_EXPECT:
            exp[name] = val
        return exp

    def _score(self, name, stim, got):
        exp = self._expect()
        for key, eval_ in exp.items():
            gv = got.get(key)
            if gv is None:
                self.bad(name, stim,
                         f"{key}={eval_}",
                         f"{key}=X",
                         f"u_u.{key}")
                return False
            if (int(gv) & (MASK32 if key in ("rt_wr_data", "guid0",
                                             "class_code", "port_basic",
                                             "port_cap")
                           else MASK16 if key in ("cna", "rt_wr_idx")
                           else MASK4 if key in ("default_bm",
                                                 "port_rst_pulse",
                                                 "port_rst_rw1c",
                                                 "lmsm_go_pulse")
                           else 1)) != eval_:
                self.bad(name, stim,
                         f"{key}={eval_:#x}" if eval_ > 1 else f"{key}={eval_}",
                         f"{key}={int(gv):#x}" if int(gv) > 1 else f"{key}={int(gv)}",
                         f"u_u.{key}")
                return False
        return True

    async def _cycle(self, vld=0, cmd=0, idx=0, data=0, hold=0, device_rst=0):
        """Drive on this falling edge; sample NBA-stable outputs next fall."""
        self._drive(vld, cmd, idx, data, hold, device_rst)
        self.g.step(vld, cmd, idx, data, hold, device_rst, rst_n=1)
        await self._to_fall()
        return self._sample()

    async def _wr(self, name, tag, cmd, idx=0, data=0, hold=0):
        got = await self._cycle(vld=1, cmd=cmd, idx=idx, data=data, hold=hold)
        return self._score(name, tag, got)

    async def _quiet(self, name, tag, hold=0):
        got = await self._cycle(hold=hold)
        return self._score(name, tag, got)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_cfg_space"
        self.g = Golden()

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: identity constants + idle seq 0 + ready=1.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        for i in range(3):
            if not await self._quiet(name, f"idle cycle {i} after reset"):
                phase.drop_objection(self)
                return

        # 2. Stock Icarus tc_identity_cfg_space: cmd=0 CNA=BEEF.
        if not await self._wr(
                name, "stock cmd=0 data=BEEF (Icarus tc_identity_cfg_space)",
                cmd=0, data=STOCK_CNA):
            phase.drop_objection(self)
            return
        if self.g.cna != STOCK_CNA or not self.g.cna_written:
            self.bad(name, "stock cmd=0 data=BEEF",
                     "cna=BEEF cna_written=1",
                     f"cna={self.g.cna:#x} written={self.g.cna_written}",
                     "u_u.cna")
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "stock cmd=0 deassert (cna held)"):
            phase.drop_objection(self)
            return

        # 3. Stock cmd=1 route write pulse.
        if not await self._wr(
                name, "stock cmd=1 idx=3 data=F (Icarus tc_identity_cfg_space)",
                cmd=1, idx=STOCK_RT_IDX, data=STOCK_RT_DATA):
            phase.drop_objection(self)
            return
        if not self.g.rt_wr_en:
            self.bad(name, "stock cmd=1",
                     "rt_wr_en=1", f"rt_wr_en={self.g.rt_wr_en}",
                     "u_u.rt_wr_en")
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "stock cmd=1 deassert (pulse drop, idx/data held)"):
            phase.drop_objection(self)
            return

        # 4. Stock cmd=2 default bitmap.
        if not await self._wr(
                name, "stock cmd=2 data=5 (Icarus tc_identity_cfg_space)",
                cmd=2, data=STOCK_BM):
            phase.drop_objection(self)
            return
        if self.g.default_bm != STOCK_BM:
            self.bad(name, "stock cmd=2",
                     "default_bm=0101",
                     f"default_bm={self.g.default_bm:04b}",
                     "u_u.default_bm")
            phase.drop_objection(self)
            return

        # 5. Stock cmd=3 data[0]==0 must not start Port Reset.
        if not await self._wr(
                name, "stock cmd=3 idx=2 data[0]=0 (Icarus tc_identity_cfg_space)",
                cmd=3, idx=STOCK_PORT, data=0):
            phase.drop_objection(self)
            return
        if self.g.port_rst_pulse or self.g.port_rst_rw1c:
            self.bad(name, "stock cmd=3 data[0]=0",
                     "pulse=0 rw1c=0 (DUT must not reset)",
                     f"pulse={self.g.port_rst_pulse:04b} rw1c={self.g.port_rst_rw1c:04b}",
                     "u_u.port_rst_pulse")
            phase.drop_objection(self)
            return

        # 6. Stock cmd=3 data[0]==1 W1C starts that port.
        if not await self._wr(
                name, "stock cmd=3 idx=2 data[0]=1 (Icarus tc_identity_cfg_space)",
                cmd=3, idx=STOCK_PORT, data=1):
            phase.drop_objection(self)
            return
        if ((self.g.port_rst_pulse >> STOCK_PORT) & 1) != 1 or (
                (self.g.port_rst_rw1c >> STOCK_PORT) & 1) != 1:
            self.bad(name, "stock cmd=3 data[0]=1",
                     "port_rst_pulse[2]=1 rw1c[2]=1 (no cfg_rd_*)",
                     f"pulse={self.g.port_rst_pulse:04b} rw1c={self.g.port_rst_rw1c:04b}",
                     "u_u.port_rst_rw1c")
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "stock cmd=3 deassert (pulse drop, rw1c sticky)"):
            phase.drop_objection(self)
            return

        # 7. Stock cmd=4 device_rst_pulse.
        if not await self._wr(
                name, "stock cmd=4 (Icarus tc_identity_cfg_space)",
                cmd=4):
            phase.drop_objection(self)
            return
        if not self.g.device_rst_pulse:
            self.bad(name, "stock cmd=4",
                     "device_rst_pulse=1",
                     "0", "u_u.device_rst_pulse")
            phase.drop_objection(self)
            return

        # 8. Stock cmd=5 lmsm_go.
        if not await self._wr(
                name, "stock cmd=5 idx=1 (Icarus tc_identity_cfg_space)",
                cmd=5, idx=1):
            phase.drop_objection(self)
            return
        if ((self.g.lmsm_go_pulse >> 1) & 1) != 1:
            self.bad(name, "stock cmd=5 idx=1",
                     "lmsm_go_pulse[1]=1",
                     f"{self.g.lmsm_go_pulse:04b}",
                     "u_u.lmsm_go_pulse")
            phase.drop_objection(self)
            return

        # 9. Stock cmd=7 ignored opcode still irq_clr.
        if not await self._wr(
                name, "stock cmd=7 ignored opcode (Icarus tc_identity_cfg_space)",
                cmd=7):
            phase.drop_objection(self)
            return
        if not self.g.irq_clr:
            self.bad(name, "stock cmd=7",
                     "irq_clr=1 (any static write)",
                     "0", "u_u.irq_clr")
            phase.drop_objection(self)
            return

        # 10. Stock device_rst pin clears CNA (posedge sample, not async).
        got = await self._cycle(device_rst=1)
        if not self._score(name, "stock device_rst pin (Icarus tc_identity_cfg_space)",
                           got):
            phase.drop_objection(self)
            return
        if self.g.cna_written:
            self.bad(name, "stock device_rst",
                     "cna_written=0",
                     "1", "u_u.cna_written")
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "after device_rst pin drop"):
            phase.drop_objection(self)
            return

        # 11. Stock Icarus tc_cna_16bit: low 16 only.
        if not await self._wr(
                name, "stock cmd=0 data=00ABCDEF (Icarus tc_cna_16bit)",
                cmd=0, data=STOCK_CNA32):
            phase.drop_objection(self)
            return
        if self.g.cna != STOCK_CNA16:
            self.bad(name, "stock 16-bit CNA",
                     "cna=16'hCDEF (low 16 only; not 24-bit)",
                     f"cna={self.g.cna:#x}", "u_u.cna")
            phase.drop_objection(self)
            return

        # 12. Walk-1 Port Reset W1C + hold_fall HW clear on every port.
        for p in range(PORT_N):
            if not await self._wr(
                    name, f"walk-1 cmd=3 port {p} data[0]=1",
                    cmd=3, idx=p, data=1):
                phase.drop_objection(self)
                return
            if ((self.g.port_rst_rw1c >> p) & 1) != 1:
                self.bad(name, f"walk-1 cmd=3 port {p}",
                         f"rw1c[{p}]=1",
                         f"rw1c={self.g.port_rst_rw1c:04b}",
                         "u_u.port_rst_rw1c")
                phase.drop_objection(self)
                return
            if not await self._quiet(name, f"walk-1 port {p} pulse drop"):
                phase.drop_objection(self)
                return
            if not await self._quiet(name, f"walk-1 port {p} hold rise",
                                     hold=1 << p):
                phase.drop_objection(self)
                return
            if not await self._quiet(name, f"walk-1 port {p} hold_fall HW clear"):
                phase.drop_objection(self)
                return
            if self.g.port_rst_rw1c & (1 << p):
                self.bad(name, f"hold_fall port {p}",
                         f"rw1c[{p}]=0",
                         f"rw1c={self.g.port_rst_rw1c:04b}",
                         "u_u.port_rst_rw1c")
                phase.drop_objection(self)
                return

        # 13. Walk-1 cmd=5 lmsm_go.
        for p in range(PORT_N):
            if not await self._wr(
                    name, f"walk-1 cmd=5 port {p}",
                    cmd=5, idx=p):
                phase.drop_objection(self)
                return
            if self.g.lmsm_go_pulse != (1 << p):
                self.bad(name, f"walk-1 cmd=5 port {p}",
                         f"lmsm_go_pulse={1 << p:#x}",
                         f"lmsm_go_pulse={self.g.lmsm_go_pulse:#x}",
                         "u_u.lmsm_go_pulse")
                phase.drop_objection(self)
                return
            if not await self._quiet(name, f"walk-1 cmd=5 port {p} pulse drop"):
                phase.drop_objection(self)
                return

        # 14. cmd 6–15 ignore (no CNA/RT/BM/pulse change) but irq_clr.
        if not await self._wr(name, "CNA before ignore opcodes",
                              cmd=0, data=0x1111):
            phase.drop_objection(self)
            return
        held_cna = self.g.cna
        held_bm = self.g.default_bm
        held_idx = self.g.rt_wr_idx
        held_data = self.g.rt_wr_data
        for cmd in range(6, 16):
            if not await self._wr(
                    name, f"cmd={cmd} ignore (irq_clr only; no Appendix D)",
                    cmd=cmd, idx=0xFFFF, data=0xFFFFFFFF):
                phase.drop_objection(self)
                return
            if (self.g.cna != held_cna or self.g.default_bm != held_bm
                    or self.g.rt_wr_en or self.g.port_rst_pulse
                    or self.g.device_rst_pulse or self.g.lmsm_go_pulse
                    or self.g.rt_wr_idx != held_idx
                    or self.g.rt_wr_data != held_data
                    or not self.g.irq_clr):
                self.bad(name, f"cmd={cmd} ignore",
                         "irq_clr=1; CNA/RT/BM/pulses unchanged",
                         f"cna={self.g.cna:#x} irq_clr={self.g.irq_clr} "
                         f"rt_en={self.g.rt_wr_en}",
                         "u_u.irq_clr")
                phase.drop_objection(self)
                return

        # 15. Same-cycle W1C retrigger masks hold_fall (bit stays 1).
        if not await self._wr(name, "W1C port 1 before retrigger",
                              cmd=3, idx=1, data=1):
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "retrigger: pulse drop"):
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "retrigger: hold rise", hold=0x2):
            phase.drop_objection(self)
            return
        if not await self._wr(
                name, "hold fall + W1C same port (hold_fall masked)",
                cmd=3, idx=1, data=1, hold=0):
            phase.drop_objection(self)
            return
        if ((self.g.port_rst_rw1c >> 1) & 1) != 1:
            self.bad(name, "same-cycle W1C retrigger",
                     "rw1c[1]=1 (hold_fall masked)",
                     f"rw1c={self.g.port_rst_rw1c:04b}",
                     "u_u.port_rst_rw1c")
            phase.drop_objection(self)
            return

        # 16. Hold fall on port 1 while W1C port 0: clear 1, set 0.
        if not await self._quiet(name, "cross: pulse drop, rw1c[1] held"):
            phase.drop_objection(self)
            return
        if not await self._quiet(name, "cross: hold rise port 1", hold=0x2):
            phase.drop_objection(self)
            return
        if not await self._wr(
                name, "hold fall port 1 + W1C port 0",
                cmd=3, idx=0, data=1, hold=0):
            phase.drop_objection(self)
            return
        if self.g.port_rst_rw1c != 0x1:
            self.bad(name, "cross-port hold_fall + W1C",
                     "rw1c=0001",
                     f"rw1c={self.g.port_rst_rw1c:04b}",
                     "u_u.port_rst_rw1c")
            phase.drop_objection(self)
            return

        # 17. RSVD data bits ignored (RTL slices only).
        if not await self._wr(
                name, "cmd=2 RSVD data[31:4] ignored",
                cmd=2, data=0xFFFFFFF5):
            phase.drop_objection(self)
            return
        if self.g.default_bm != 0x5:
            self.bad(name, "cmd=2 RSVD",
                     "default_bm=5",
                     f"default_bm={self.g.default_bm:#x}",
                     "u_u.default_bm")
            phase.drop_objection(self)
            return
        if not await self._wr(
                name, "cmd=3 data[31:1]=1 data[0]=0 (no Port Reset)",
                cmd=3, idx=3, data=0xFFFFFFFE):
            phase.drop_objection(self)
            return
        if (self.g.port_rst_pulse >> 3) & 1:
            self.bad(name, "cmd=3 RSVD data[0]=0",
                     "pulse[3]=0",
                     f"pulse={self.g.port_rst_pulse:04b}",
                     "u_u.port_rst_pulse")
            phase.drop_objection(self)
            return
        if not await self._wr(
                name, "cmd=3 data[31:1] set data[0]=1 still W1C",
                cmd=3, idx=3, data=0xFFFFFF01):
            phase.drop_objection(self)
            return

        # 18. idx[15:2] unused for port cmds (only [1:0]).
        if not await self._wr(
                name, "cmd=5 idx=0xFFF2 (port = idx[1:0]=2)",
                cmd=5, idx=0xFFF2):
            phase.drop_objection(self)
            return
        if self.g.lmsm_go_pulse != 0x4:
            self.bad(name, "cmd=5 idx high bits unused",
                     "lmsm_go_pulse[2]=1",
                     f"{self.g.lmsm_go_pulse:04b}",
                     "u_u.lmsm_go_pulse")
            phase.drop_objection(self)
            return

        # 19. cfg_wr_vld=0 is a no-op even with cmd/data set.
        prev_cna = self.g.cna
        got = await self._cycle(vld=0, cmd=0, idx=0, data=0xDEAD)
        if not self._score(name, "cfg_wr_vld=0 no-op (cmd=0 data=DEAD)", got):
            phase.drop_objection(self)
            return
        if self.g.cna != prev_cna or self.g.irq_clr:
            self.bad(name, "cfg_wr_vld=0",
                     f"cna unchanged ({prev_cna:#x}), irq_clr=0",
                     f"cna={self.g.cna:#x} irq_clr={self.g.irq_clr}",
                     "u_u.cna")
            phase.drop_objection(self)
            return

        # 20. Async rst_n mid-state clears without a dest posedge.
        if not await self._wr(name, "CNA before async rst",
                              cmd=0, data=0xA5A5):
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-state (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got["cna"] not in (0, None) and int(got["cna"]) != 0:
            self.bad(name, "async rst_n mid-state",
                     "cna=0", f"cna={got['cna']}", "u_u.cna")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle", got):
            phase.drop_objection(self)
            return

        # 21. Leaf has no cfg_rd_* / invented CFG6 CSR / Appendix D pins.
        for absent in ("cfg_rd", "cfg_rd_vld", "cfg_rd_data", "cfg_rd_addr",
                       "appendix_d", "irq_logic", "consume", "mgmt_nw_vld"):
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_cfg_space product port",
                         f"{absent} present", "vibe_cfg_space_cocotb_top")
                phase.drop_objection(self)
                return
        for need in ("cfg_wr_ready", "cna", "cna_written", "default_bm",
                     "rt_wr_en", "port_rst_rw1c", "irq_clr", "guid0",
                     "class_code", "port_basic", "port_cap"):
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing",
                         "vibe_cfg_space_cocotb_top")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_cfg_space)
