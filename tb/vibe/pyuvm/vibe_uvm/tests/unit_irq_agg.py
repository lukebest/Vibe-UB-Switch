"""Module-level uvm-python TC for Decision-I leaf vibe_irq_agg.

Covers reset/idle (irq_logic=0, no spurious set), SPEC §14 / AS §15
must-observe sources (rx_ovf / fc_ovf / proto_err / retry_error /
icrc_fail / len_err / deadlock_drop / drop_g1 / afifo_ovf) including
walk-1 on every 4-bit port vector, sticky hold after deassert,
irq_clr clear (wins same-cycle over any_err), async rst_n mid-sticky,
and multi-source OR still one bit. Not a full-chip consecutive-green
gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/mgmt/vibe_irq_agg.sv: async-low rst_n, irq_clr
wins the if/else over the reduction-OR set, irq_logic is the sticky
flop. No per-cause status register and no extra IRQ pins. Port Reset
is not a leaf input (wrap hold). device_rst is OR'd into irq_clr by
vibe_mgmt (held). Instantiated by vibe_mgmt u_irq. Stock Icarus
tc_irq_agg remains the official TP scorer (direct vibe_irq_agg top,
wrap-style). This is not the wrap-style tc_irq_agg / tc_mgmt.
ovf_l (F1) is not in this module.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

PORT_N = 4
MASK4 = 0xF
HIER = "u_u.sticky / u_u.irq_logic"

# 4-bit per-port vectors (SPEC §14 / AS §15).
VEC_SRCS = (
    "rx_ovf",
    "fc_ovf",
    "proto_err",
    "retry_error",
    "len_err",
    "deadlock_drop",
    "afifo_ovf",
)

# 1-bit sources (ICRC fail is receiver-side; drop_g1 is RT=10/11).
BIT_SRCS = ("icrc_fail", "drop_g1")

# Stock Icarus tc_irq_agg pulse1 mapping (one bit / one source).
STOCK_PULSE = (
    ("rx_ovf", 0x1),
    ("fc_ovf", 0x2),
    ("proto_err", 0x4),
    ("retry_error", 0x8),
    ("icrc_fail", 1),
    ("len_err", 0x1),
    ("deadlock_drop", 0x2),
    ("drop_g1", 1),
    ("afifo_ovf", 0x4),
)


def _zero_errs():
    e = {n: 0 for n in VEC_SRCS}
    e.update({n: 0 for n in BIT_SRCS})
    return e


def any_err(errs) -> int:
    """Product reduction-OR of the nine error inputs."""
    for n in VEC_SRCS:
        if int(errs.get(n, 0)) & MASK4:
            return 1
    for n in BIT_SRCS:
        if int(errs.get(n, 0)) & 1:
            return 1
    return 0


class Golden:
    """Cycle-accurate sticky vs product if / else if."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.sticky = 0

    def step(self, irq_clr=0, errs=None):
        if irq_clr:
            self.sticky = 0
        elif any_err(errs or _zero_errs()):
            self.sticky = 1


class tc_vibe_irq_agg(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.irq_clr, 0)
        for n in VEC_SRCS:
            sset(getattr(d, n), 0)
        for n in BIT_SRCS:
            sset(getattr(d, n), 0)

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
        return ival(self.dut.irq_logic, -1)

    def _drive(self, irq_clr=0, errs=None):
        d = self.dut
        e = _zero_errs()
        if errs:
            e.update(errs)
        sset(d.irq_clr, 1 if irq_clr else 0)
        for n in VEC_SRCS:
            sset(getattr(d, n), int(e[n]) & MASK4)
        for n in BIT_SRCS:
            sset(getattr(d, n), 1 if e[n] else 0)
        return e

    async def _cycle(self, irq_clr=0, errs=None):
        """Drive on this falling edge; sample NBA-stable irq_logic next fall."""
        e = self._drive(irq_clr, errs)
        self.g.step(irq_clr, e)
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got):
        exp = self.g.sticky
        if got != exp:
            self.bad(name, stim,
                     f"irq_logic={exp}",
                     f"irq_logic={got}",
                     HIER)
            return False
        return True

    async def _clr(self, name, tag):
        got = await self._cycle(irq_clr=1)
        if not self._score(name, f"{tag}: irq_clr", got):
            return False
        if got != 0:
            self.bad(name, f"{tag}: irq_clr",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            return False
        got = await self._cycle(0)
        return self._score(name, f"{tag}: cycle after irq_clr (quiet)", got)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_irq_agg"
        self.g = Golden()

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, irq_logic=0. Quiet / last-without-err stay 0.
        got = self._sample()
        if got != 0:
            self.bad(name, "reset then release, all sources 0",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._cycle(0)
            if not self._score(name, f"idle cycle {i} after reset", got):
                phase.drop_objection(self)
                return

        # 2. Stock Icarus pulse1 sources: set, deassert, still sticky.
        for src, val in STOCK_PULSE:
            if not await self._clr(name, f"stock {src}"):
                phase.drop_objection(self)
                return
            got = await self._cycle(0, {src: val})
            if not self._score(
                    name, f"stock pulse {src}={val:#x} (Icarus tc_irq_agg)",
                    got):
                phase.drop_objection(self)
                return
            if got != 1:
                self.bad(name, f"stock pulse {src}={val:#x}",
                         "irq_logic=1 (sticky set)",
                         f"irq_logic={got}", src)
                phase.drop_objection(self)
                return
            got = await self._cycle(0)
            if not self._score(
                    name, f"stock {src} deasserted (still sticky)", got):
                phase.drop_objection(self)
                return
            if got != 1:
                self.bad(name, f"stock {src} deasserted",
                         "irq_logic=1 (sticky hold)",
                         f"irq_logic={got}", HIER)
                phase.drop_objection(self)
                return

        # 3. Walk-1 on every 4-bit port vector (SPEC §14 per-port OR).
        for src in VEC_SRCS:
            for bit in range(PORT_N):
                val = 1 << bit
                if not await self._clr(name, f"walk {src}[{bit}]"):
                    phase.drop_objection(self)
                    return
                got = await self._cycle(0, {src: val})
                if not self._score(
                        name, f"walk-1 {src}[{bit}]={val:#x}", got):
                    phase.drop_objection(self)
                    return
                if got != 1:
                    self.bad(name, f"walk-1 {src}[{bit}]",
                             "irq_logic=1", f"irq_logic={got}", src)
                    phase.drop_objection(self)
                    return
                got = await self._cycle(0)
                if not self._score(
                        name, f"walk-1 {src}[{bit}] deasserted", got):
                    phase.drop_objection(self)
                    return

        # 4. irq_clr wins same-cycle over any_err (stock if / else if).
        if not await self._clr(name, "before clr-wins"):
            phase.drop_objection(self)
            return
        got = await self._cycle(irq_clr=1, errs={"afifo_ovf": 0x8,
                                                "rx_ovf": 0x1,
                                                "drop_g1": 1})
        if not self._score(
                name, "irq_clr && afifo_ovf/rx_ovf/drop_g1 same cycle (clr wins)",
                got):
            phase.drop_objection(self)
            return
        if got != 0:
            self.bad(name, "irq_clr wins over any_err same cycle",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return
        # Error still held, clr gone → next posedge sets.
        got = await self._cycle(0, {"afifo_ovf": 0x8, "rx_ovf": 0x1,
                                    "drop_g1": 1})
        if not self._score(
                name, "held any_err after clr-wins cycle (set)", got):
            phase.drop_objection(self)
            return
        if got != 1:
            self.bad(name, "any_err held after irq_clr dropped",
                     "irq_logic=1", f"irq_logic={got}", "u_u.sticky")
            phase.drop_objection(self)
            return

        # 5. Multi-source OR is still one irq_logic bit (no vector).
        if not await self._clr(name, "before multi-OR"):
            phase.drop_objection(self)
            return
        got = await self._cycle(0, {
            "rx_ovf": 0xF, "fc_ovf": 0xF, "proto_err": 0xF,
            "retry_error": 0xF, "icrc_fail": 1, "len_err": 0xF,
            "deadlock_drop": 0xF, "drop_g1": 1, "afifo_ovf": 0xF,
        })
        if not self._score(name, "all nine sources asserted (OR, 1-bit)", got):
            phase.drop_objection(self)
            return
        if got != 1:
            self.bad(name, "all SPEC §14 sources asserted",
                     "irq_logic=1 (single sticky bit)",
                     f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return
        got = await self._cycle(0)
        if not self._score(name, "all sources deasserted (still sticky)", got):
            phase.drop_objection(self)
            return

        # 6. Async rst_n mid-sticky clears without a dest posedge.
        got = self._sample()
        if got != 1:
            self.bad(name, "pre-async-rst (expect sticky 1)",
                     "irq_logic=1", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got != 0:
            self.bad(name, "async rst_n=0 mid-sticky (100ps, no posedge)",
                     "irq_logic=0", f"irq_logic={got}", "u_u.sticky")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if got != 0:
            self.bad(name, "after async re-reset release, idle",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return

        # 7. Sync rst after a fresh sticky set (posedge path).
        got = await self._cycle(0, {"afifo_ovf": 0x1})
        if not self._score(name, "afifo_ovf[0] before sync rst", got):
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await self._idle()
        self.g.reset()
        await self._to_fall()
        got = self._sample()
        if got != 0:
            self.bad(name, "sync rst_n held 0 through posedge",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 1)
        await self._to_fall()
        got = self._sample()
        if got != 0:
            self.bad(name, "after sync rst release, idle",
                     "irq_logic=0", f"irq_logic={got}", HIER)
            phase.drop_objection(self)
            return

        # 8. Leaf has no port_rst / device_rst / extra IRQ pins.
        for absent in ("port_rst", "device_rst", "irq_vec", "irq_n",
                       "irq_status"):
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_irq_agg product port",
                         f"{absent} present", "vibe_irq_agg_cocotb_top")
                phase.drop_objection(self)
                return
        if not hasattr(d, "irq_logic"):
            self.bad(name, "leaf pin scan (irq_logic)",
                     "irq_logic present (1-bit sticky OR)",
                     "missing", "u_u.irq_logic")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_irq_agg)
