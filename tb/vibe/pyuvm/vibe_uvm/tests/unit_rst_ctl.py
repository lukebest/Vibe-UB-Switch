"""Module-level uvm-python TC for Decision-I leaf vibe_rst_ctl.

Covers reset/idle (device_rst=0, port_rst=0), stock Icarus
tc_rst_port_device (port_rst_pulse[2] isolate, device_rst
hold then release), walk-1 on every port bit, 7-dest-clock
stretch vs product dct/pct, retrigger while holding, device
and port holds independent, multi-port same-cycle pulse,
async rst_n mid-hold (no dest posedge), wrap-vs-DUT instance
score (cocotb instance u_u), and a pin scan with instance
u_u. Not a full-chip consecutive-green gate. Not 1/3, 4/3,
freeze, or signoff.

Matches product rtl/mgmt/vibe_rst_ctl.sv: async-low rst_n,
pulse loads hold=1 and cnt=7, else cnt decrements and hold
clears when cnt==1. Instantiated by vibe_mgmt u_rst. Stock
Icarus tc_rst_port_device remains the official TP scorer
(direct vibe_rst_ctl top, instance u_r). Decision-I wrap
uses instance u_u (not leftover u_r / u_rst). This is not
vibe_rst_sync / vibe_irq_agg / vibe_cna_ep / vibe_cfg_space
/ vibe_mgmt. ovf_l (F1) is not in this module; do not ECO
F1. CHILDREN: none. Fourth mgmt leaf after stage-40
vibe_irq_agg, stage-41 vibe_cna_ep, and stage-42
vibe_cfg_space. Tip-align leaf wave is done; do not invent
further tip-align leaves.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

PORT_N = 4
MASK4 = 0xF
HIER = "u_u.device_rst / u_u.port_rst / u_u.dhold / u_u.phold"
WRAP = "vibe_rst_ctl_cocotb_top"
INST = "u_u"
PINS = (
    "clk", "rst_n",
    "device_rst_pulse", "port_rst_pulse",
    "device_rst", "port_rst",
)
DUT_PINS = PINS
# Leftover leaf / F1 / sibling pins must not appear on the wrap
# top. Instance is u_u (Decision-I leaf wrappers), not leftover
# product instantiator u_rst or stock Icarus u_r.
ABSENT = (
    "ovf_l", "almost_full",
    "irq_logic", "irq_clr", "irq_vec", "irq_n", "irq_status",
    "cfg_wr_vld", "cfg_wr_ready", "cfg_wr_cmd", "cfg_rd",
    "cfg_rd_vld", "cfg_rd_data", "appendix_d",
    "cna", "cna_written", "guid0", "class_code",
    "dll_disabled", "lmsm_go", "lmsm_go_pulse",
    "rst_n_in", "rst_n_out", "r1",
    "u_r", "u_rst", "u_cfg", "u_cna", "u_irq", "u_m",
    "clk_fab", "wclk", "rclk",
)


class Golden:
    """Cycle-accurate stretch vs product if / else if (NBA)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.dhold = 0
        self.phold = 0
        self.dct = 0
        self.pct = [0] * PORT_N

    def step(self, device_rst_pulse=0, port_rst_pulse=0):
        if device_rst_pulse:
            self.dhold = 1
            self.dct = 7
        elif self.dct != 0:
            if self.dct == 1:
                self.dhold = 0
            self.dct -= 1
        pulse = int(port_rst_pulse) & MASK4
        for i in range(PORT_N):
            if (pulse >> i) & 1:
                self.phold |= 1 << i
                self.pct[i] = 7
            elif self.pct[i] != 0:
                if self.pct[i] == 1:
                    self.phold &= ~(1 << i)
                self.pct[i] -= 1


class tc_vibe_rst_ctl(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        sset(self.dut.device_rst_pulse, 0)
        sset(self.dut.port_rst_pulse, 0)

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
        return {
            "device_rst": ival(self.dut.device_rst, -1),
            "port_rst": ival(self.dut.port_rst, -1),
        }

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        try:
            return {
                "device_rst": ival(u.device_rst, -1),
                "port_rst": ival(u.port_rst, -1),
            }
        except Exception:
            return None

    def _drive(self, device_rst_pulse=0, port_rst_pulse=0):
        sset(self.dut.device_rst_pulse, 1 if device_rst_pulse else 0)
        sset(self.dut.port_rst_pulse, int(port_rst_pulse) & MASK4)

    def _score_combo(self, name, stim, got):
        exp_d = self.g.dhold
        exp_p = self.g.phold & MASK4
        gd = got["device_rst"]
        gp = got["port_rst"]
        if gd is None or gd < 0 or gp is None or gp < 0:
            self.bad(name, stim,
                     f"device_rst={exp_d} port_rst={exp_p:#x}",
                     f"device_rst={gd} port_rst={gp}",
                     HIER)
            return False
        if (int(gd) & 1) != exp_d or (int(gp) & MASK4) != exp_p:
            self.bad(name, stim,
                     f"device_rst={exp_d} port_rst={exp_p:#x}",
                     f"device_rst={int(gd) & 1} port_rst={int(gp) & MASK4:#x}",
                     HIER)
            return False
        return True

    def _score_inner(self, name, stim, got, inner=None):
        if inner is None:
            inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        for pname in ("device_rst", "port_rst"):
            outer = got[pname]
            inner_v = inner[pname]
            if outer is None or inner_v is None:
                if outer != inner_v:
                    self.bad(name, stim + f" ({INST} vs wrap)",
                             f"{pname}={outer}",
                             f"{INST}.{pname}={inner_v}",
                             f"{INST}.{pname}")
                    return False
                continue
            if outer < 0 or inner_v < 0:
                continue
            mask = 1 if pname == "device_rst" else MASK4
            if (int(inner_v) & mask) != (int(outer) & mask):
                self.bad(name, stim + f" ({INST} vs wrap)",
                         f"{pname}={outer}",
                         f"{INST}.{pname}={inner_v}",
                         f"{INST}.{pname}")
                return False
        return True

    def _score(self, name, stim, got, inner=None):
        if not self._score_combo(name, stim, got):
            return False
        return self._score_inner(name, stim, got, inner=inner)

    async def _cycle(self, device_rst_pulse=0, port_rst_pulse=0):
        """Drive on this falling edge; sample NBA-stable next fall."""
        self._drive(device_rst_pulse, port_rst_pulse)
        self.g.step(device_rst_pulse, port_rst_pulse)
        await self._to_fall()
        return self._sample(), self._inner_sample()

    async def _expect(self, name, stim, device_rst_pulse=0, port_rst_pulse=0):
        got, inner = await self._cycle(device_rst_pulse, port_rst_pulse)
        return self._score(name, stim, got, inner=inner)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_rst_ctl"
        self.g = Golden()

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, both holds 0. Quiet stay 0.
        got = self._sample()
        if not self._score(name, "reset then release, pulses 0", got):
            phase.drop_objection(self)
            return
        if got["device_rst"] != 0 or (got["port_rst"] & MASK4) != 0:
            self.bad(name, "reset then release, pulses 0",
                     "device_rst=0 port_rst=0",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(3):
            if not await self._expect(name, f"idle cycle {i} after reset"):
                phase.drop_objection(self)
                return

        # 2. Stock Icarus tc_rst_port_device: port_rst_pulse[2].
        if not await self._expect(
                name, "stock port_rst_pulse[2] (Icarus tc_rst_port_device)",
                port_rst_pulse=0x4):
            phase.drop_objection(self)
            return
        got = self._sample()
        if (int(got["port_rst"]) & MASK4) != 0x4 or int(got["device_rst"]) != 0:
            self.bad(name, "stock port_rst_pulse[2]",
                     "port_rst[2]=1 others 0, device_rst=0",
                     f"port_rst={got['port_rst']:#x} device_rst={got['device_rst']}",
                     "u_u.port_rst")
            phase.drop_objection(self)
            return
        if not await self._expect(
                name, "stock port pulse deasserted (still holding)"):
            phase.drop_objection(self)
            return

        # 3. Stock device_rst_pulse hold (port[2] still stretching).
        if not await self._expect(
                name, "stock device_rst_pulse (Icarus tc_rst_port_device)",
                device_rst_pulse=1):
            phase.drop_objection(self)
            return
        got = self._sample()
        if int(got["device_rst"]) != 1:
            self.bad(name, "stock device_rst_pulse",
                     "device_rst=1 (hold)",
                     f"device_rst={got['device_rst']}",
                     "u_u.device_rst")
            phase.drop_objection(self)
            return
        if not await self._expect(
                name, "stock device pulse deasserted (still holding)"):
            phase.drop_objection(self)
            return

        # Stretch: hold 7 dest clocks from the load, then clear.
        # Device was loaded two cycles ago (pulse + deassert). Drain.
        released = False
        for i in range(10):
            if not await self._expect(
                    name, f"stock device stretch drain cycle {i}"):
                phase.drop_objection(self)
                return
            if self.g.dhold == 0:
                released = True
                break
        if not released or int(self._sample()["device_rst"]) != 0:
            self.bad(name, "stock 10 cyc after device_rst_pulse",
                     "device_rst released",
                     f"device_rst={self._sample()['device_rst']}",
                     "u_u.device_rst")
            phase.drop_objection(self)
            return
        for i in range(8):
            if not await self._expect(
                    name, f"stock port[2] drain cycle {i}"):
                phase.drop_objection(self)
                return
            if (self.g.phold & 0x4) == 0:
                break
        got = self._sample()
        if (int(got["port_rst"]) & 0x4) != 0:
            self.bad(name, "stock wait after port_rst_pulse[2]",
                     "port_rst[2]=0",
                     f"port_rst={got['port_rst']:#x}",
                     "u_u.port_rst")
            phase.drop_objection(self)
            return

        # 4. Walk-1 on every port bit: isolate, 7-clock stretch, clear.
        for bit in range(PORT_N):
            val = 1 << bit
            if not await self._expect(
                    name, f"walk-1 port_rst_pulse[{bit}]",
                    port_rst_pulse=val):
                phase.drop_objection(self)
                return
            got = self._sample()
            if (int(got["port_rst"]) & MASK4) != val:
                self.bad(name, f"walk-1 port_rst_pulse[{bit}]",
                         f"port_rst={val:#x}",
                         f"port_rst={got['port_rst']:#x}",
                         "u_u.port_rst")
                phase.drop_objection(self)
                return
            if int(got["device_rst"]) != 0:
                self.bad(name, f"walk-1 port[{bit}] must not set device_rst",
                         "device_rst=0",
                         f"device_rst={got['device_rst']}",
                         "u_u.device_rst")
                phase.drop_objection(self)
                return
            # Pulse cycle is clock 1 of the 7-clock hold. Six more.
            for i in range(6):
                if not await self._expect(
                        name, f"walk-1 port[{bit}] hold cycle {i + 1}"):
                    phase.drop_objection(self)
                    return
                if (self.g.phold & val) == 0:
                    self.bad(name, f"walk-1 port[{bit}] stretch holds",
                             f"port_rst[{bit}]=1 during 7 dest clocks",
                             f"phold={self.g.phold:#x} cycle {i + 1}",
                             "u_u.port_rst")
                    phase.drop_objection(self)
                    return
            if not await self._expect(
                    name, f"walk-1 port[{bit}] hold_fall (7th dest clock)"):
                phase.drop_objection(self)
                return
            if (self.g.phold & val) != 0 or (int(self._sample()["port_rst"]) & val):
                self.bad(name, f"walk-1 port[{bit}] hold_fall",
                         f"port_rst[{bit}]=0 after 7 dest clocks",
                         f"port_rst={self._sample()['port_rst']:#x}",
                         "u_u.port_rst")
                phase.drop_objection(self)
                return

        # 5. Device stretch is also exactly 7 dest clocks.
        if not await self._expect(
                name, "device_rst_pulse starts 7-clock hold",
                device_rst_pulse=1):
            phase.drop_objection(self)
            return
        for i in range(6):
            if not await self._expect(name, f"device hold cycle {i + 1}"):
                phase.drop_objection(self)
                return
            if self.g.dhold != 1:
                self.bad(name, f"device stretch holds cycle {i + 1}",
                         "device_rst=1 during 7 dest clocks",
                         f"dhold={self.g.dhold}",
                         "u_u.device_rst")
                phase.drop_objection(self)
                return
        if not await self._expect(name, "device hold_fall (7th dest clock)"):
            phase.drop_objection(self)
            return
        if self.g.dhold != 0 or int(self._sample()["device_rst"]) != 0:
            self.bad(name, "device hold_fall",
                     "device_rst=0 after 7 dest clocks",
                     f"device_rst={self._sample()['device_rst']}",
                     "u_u.device_rst")
            phase.drop_objection(self)
            return

        # 6. Retrigger while holding reloads cnt=7 (does not early-clear).
        if not await self._expect(
                name, "retrigger setup pulse", port_rst_pulse=0x1):
            phase.drop_objection(self)
            return
        for _ in range(3):
            if not await self._expect(name, "pre-retrigger hold"):
                phase.drop_objection(self)
                return
        if not await self._expect(
                name, "retrigger port_rst_pulse[0] mid-hold",
                port_rst_pulse=0x1):
            phase.drop_objection(self)
            return
        for i in range(6):
            if not await self._expect(name, f"retrigger hold cycle {i + 1}"):
                phase.drop_objection(self)
                return
            if (self.g.phold & 1) == 0:
                self.bad(name, "retrigger must not early-clear",
                         "port_rst[0]=1 for 7 clocks after retrigger",
                         f"phold={self.g.phold:#x} cycle {i + 1}",
                         "u_u.port_rst")
                phase.drop_objection(self)
                return
        if not await self._expect(name, "retrigger hold_fall"):
            phase.drop_objection(self)
            return
        if (self.g.phold & 1) != 0:
            self.bad(name, "retrigger hold_fall",
                     "port_rst[0]=0 after reloaded stretch",
                     f"port_rst={self._sample()['port_rst']:#x}",
                     "u_u.port_rst")
            phase.drop_objection(self)
            return

        # 7. Device and port holds are independent.
        if not await self._expect(
                name, "independent: port[1] then device",
                port_rst_pulse=0x2):
            phase.drop_objection(self)
            return
        if not await self._expect(
                name, "independent: device pulse while port[1] holds",
                device_rst_pulse=1):
            phase.drop_objection(self)
            return
        got = self._sample()
        if int(got["device_rst"]) != 1 or (int(got["port_rst"]) & 0x2) != 0x2:
            self.bad(name, "independent device+port holds",
                     "device_rst=1 port_rst[1]=1",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']:#x}",
                     HIER)
            phase.drop_objection(self)
            return
        # Drain both (device loaded one cycle later).
        for i in range(8):
            if not await self._expect(name, f"independent drain {i}"):
                phase.drop_objection(self)
                return
        got = self._sample()
        if int(got["device_rst"]) != 0 or (int(got["port_rst"]) & MASK4) != 0:
            self.bad(name, "independent drain complete",
                     "device_rst=0 port_rst=0",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']:#x}",
                     HIER)
            phase.drop_objection(self)
            return

        # 8. Multi-port same-cycle pulse (all four).
        if not await self._expect(
                name, "port_rst_pulse=0xF same cycle",
                port_rst_pulse=0xF):
            phase.drop_objection(self)
            return
        got = self._sample()
        if (int(got["port_rst"]) & MASK4) != 0xF:
            self.bad(name, "multi-port pulse 0xF",
                     "port_rst=0xf",
                     f"port_rst={got['port_rst']:#x}",
                     "u_u.port_rst")
            phase.drop_objection(self)
            return
        for i in range(7):
            if not await self._expect(name, f"multi-port drain {i}"):
                phase.drop_objection(self)
                return
        if (int(self._sample()["port_rst"]) & MASK4) != 0:
            self.bad(name, "multi-port hold_fall",
                     "port_rst=0",
                     f"port_rst={self._sample()['port_rst']:#x}",
                     "u_u.port_rst")
            phase.drop_objection(self)
            return

        # 9. Async rst_n mid-hold clears without a dest posedge.
        if not await self._expect(
                name, "pre-async-rst device+port[3]",
                device_rst_pulse=1, port_rst_pulse=0x8):
            phase.drop_objection(self)
            return
        got = self._sample()
        if int(got["device_rst"]) != 1 or (int(got["port_rst"]) & 0x8) != 0x8:
            self.bad(name, "pre-async-rst (expect holds 1)",
                     "device_rst=1 port_rst[3]=1",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']:#x}",
                     HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if int(got["device_rst"] or 0) != 0 or (int(got["port_rst"] or 0) & MASK4) != 0:
            self.bad(name, "async rst_n=0 mid-hold (100ps, no posedge)",
                     "device_rst=0 port_rst=0",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']}",
                     "u_u.dhold")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "async rst_n=0 mid-hold", got):
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle", got):
            phase.drop_objection(self)
            return

        # 10. Sync rst after a fresh hold (posedge path).
        if not await self._expect(
                name, "port[0] before sync rst", port_rst_pulse=0x1):
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await self._idle()
        self.g.reset()
        await self._to_fall()
        got = self._sample()
        if int(got["device_rst"] or 0) != 0 or (int(got["port_rst"] or 0) & MASK4) != 0:
            self.bad(name, "sync rst_n held 0 through posedge",
                     "device_rst=0 port_rst=0",
                     f"device_rst={got['device_rst']} port_rst={got['port_rst']}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 1)
        await self._to_fall()
        got = self._sample()
        if not self._score(name, "after sync rst release, idle", got):
            phase.drop_objection(self)
            return

        # 11. Leaf pins + instance u_u (no ovf_l / leftover u_r).
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_rst_ctl product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return
        u = getattr(d, INST)
        for need in DUT_PINS:
            if not hasattr(u, need):
                self.bad(name, f"leaf instance pin scan ({INST}.{need})",
                         f"{INST}.{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_rst_ctl)
