"""Module-level uvm-python TC for Decision-I leaf vibe_dll_credit.

Covers reset/idle (pending=0, credit_low=1, no bp / proto_err / fc_ovf),
credit_ret grant (already cells, no ×n / no /n), consume ceil(flits/n)
vs golden, CFG0 skip, grain_n=0 → 0, consume_vld stall without a step,
same-cycle credit_ret && consume_vld, 1023 vs 1024 cell thresh (bp_nw +
force Crd_Ack), second consume after the first, port_rst / !link_up
clear, 1us timeout → proto_err, mid-run async rst_n through dest
posedge, and a pin scan with instance u_u.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/dll/vibe_dll_credit.sv: async-low rst_n, pending is
a cell count, VIBE_CREDIT_THRESH=1024, VIBE_US_CYC=1250, CFG0 does not
consume, credit_ret_n is already cells, no underflow subtract.
Instantiated by vibe_dll u_crd. This is not vibe_dll / vibe_dll_tx /
vibe_bcrc / vibe_dll_sm / vibe_dll_rx / vibe_icrc / vibe_pcs_tx /
vibe_pcs_rx / vibe_pcs_scramble / vibe_ebch16 / vibe_pcs_tx_cw2beat /
vibe_pcs_tx_amctl / vibe_pcs_tx_g1 / vibe_pcs_tx_fec /
vibe_rs128_120_enc / vibe_rs128_120_dec / vibe_pcs_rx_deskew /
vibe_pcs_rx_amctl_lock / vibe_pcs_rx_unpack / vibe_pcs_tx_pack /
gear / vibe_afifo / vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module.
CHILDREN: none.
Stock Icarus tc_credit_1024_flit_bp / tc_credit_grain_n /
tc_cfg0_no_credit / tc_credit_timeout_1us remain the official scorers.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# vibe_ub_params.vh — FS-0.2.6 / AS-0.1 §12
VIBE_CREDIT_THRESH = 1024
VIBE_US_CYC = 1250
MASK16 = 0xFFFF
MASK10 = 0x3FF
MASK8 = 0xFF
HIER = "u_u.pend / u_u.cells / u_u.bp_nw"
WRAP = "vibe_dll_credit_cocotb_top"
PINS = (
    "clk", "rst_n", "port_rst", "link_up",
    "grain_n", "consume_vld", "consume_flits", "is_cfg0",
    "credit_ret", "credit_ret_n",
    "pending", "credit_low", "force_crd_ack",
    "bp_nw", "proto_err", "fc_ovf",
)
ABSENT = (
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld",
    "u_crd", "u_bcrc", "u_b", "u_l", "u_dsk", "u_un", "u_fec",
    "u_sm", "u_rbuf", "u_dll", "u_tx", "u_rx",
    "lane_id", "seed_load", "en", "cw_sel", "cw", "u_cw", "u_a",
    "cw_data", "cw_vld", "cw_ready", "beat_data", "beat_vld", "beat_ready",
    "amctl_40B", "sdf_period", "fec_fail", "data_out",
    "u_g", "u_g1", "u_enc", "u_enc_a", "u_enc_b", "u_pack", "u_dec",
    "start", "in_vld", "in_flit", "last", "error_flag", "crc_word", "done",
    "in_sym", "parity", "in_ready",
    "win_data", "win_vld", "win_ready",
    "locked", "lid", "lid_bad", "is_amctl", "sdf", "edf",
    "bcrc_fail", "start_retry", "rx_ovf", "cfg0_hit",
    "status_up", "disabled",
)


def ceil_div(flits: int, n: int) -> int:
    """Product ceil_div: n==0 → 0; else (flits + n - 1) / n."""
    flits = int(flits) & MASK16
    n = int(n) & MASK8
    if n == 0:
        return 0
    return (flits + n - 1) // n


class Golden:
    """Cycle-accurate cells / pend / to / proto_err / fc_ovf vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.cells = 0
        self.pend = 0
        self.to = 0
        self.proto_err = 0
        self.fc_ovf = 0

    def combo(self, consume_vld=0):
        pending = self.pend & MASK16
        credit_low = int(self.cells == 0)
        force_crd_ack = int(
            (self.pend >= VIBE_CREDIT_THRESH)
            or ((not consume_vld) and self.pend != 0)
        )
        bp_nw = int(self.pend >= VIBE_CREDIT_THRESH)
        return (
            pending,
            credit_low,
            force_crd_ack,
            bp_nw,
            int(self.proto_err),
            int(self.fc_ovf),
            self.cells & MASK16,
        )

    def step(self, port_rst=0, link_up=1, grain_n=8, consume_vld=0,
             consume_flits=0, is_cfg0=0, credit_ret=0, credit_ret_n=0):
        consume_cells = ceil_div(int(consume_flits) & MASK10, int(grain_n) & MASK8)
        do_consume = bool(consume_vld) and not bool(is_cfg0)
        if port_rst or not link_up:
            self.cells = 0
            self.pend = 0
            self.to = 0
            return
        old_pend = self.pend
        old_to = self.to
        if do_consume:
            cells_sum = self.cells + consume_cells
            if cells_sum > 65535:
                self.fc_ovf = 1
                self.cells = 65535
            else:
                self.cells = cells_sum
        pend_sum = old_pend
        if credit_ret:
            pend_sum += int(credit_ret_n) & MASK16
        if do_consume:
            pend_sum += consume_cells
        self.pend = pend_sum & MASK16
        if credit_ret or (do_consume and consume_cells != 0):
            self.to = VIBE_US_CYC
        elif old_pend != 0:
            if old_to == 0:
                self.proto_err = 1
            else:
                self.to = old_to - 1


class tc_vibe_dll_credit(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)

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
        d = self.dut
        return (
            ival(d.pending, -1),
            ival(d.credit_low, -1),
            ival(d.force_crd_ack, -1),
            ival(d.bp_nw, -1),
            ival(d.proto_err, -1),
            ival(d.fc_ovf, -1),
            ival(d.u_u.cells, -1),
        )

    def _inner_sample(self):
        u = getattr(self.dut, "u_u", None)
        if u is None:
            return None
        return (
            ival(u.pending, -1),
            ival(u.credit_low, -1),
            ival(u.force_crd_ack, -1),
            ival(u.bp_nw, -1),
            ival(u.proto_err, -1),
            ival(u.fc_ovf, -1),
            ival(u.cells, -1),
        )

    def _score_inner(self, name, stim, got):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + " (u_u)",
                     "u_u present", "missing", WRAP)
            return False
        if inner != got:
            self.bad(name, stim + " (port vs u_u)",
                     self._fmt(got), self._fmt(inner), WRAP)
            return False
        return True

    def _fmt(self, s):
        pend, cl, ack, bp, pe, ovf, cells = s
        return (
            f"pending={pend} cells={cells} credit_low={cl} "
            f"ack={ack} bp={bp} proto_err={pe} fc_ovf={ovf}"
        )

    async def _cycle(self, port_rst=0, link_up=1, grain_n=8, consume_vld=0,
                     consume_flits=0, is_cfg0=0, credit_ret=0, credit_ret_n=0):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.grain_n, int(grain_n) & MASK8)
        sset(d.consume_vld, 1 if consume_vld else 0)
        sset(d.consume_flits, int(consume_flits) & MASK10)
        sset(d.is_cfg0, 1 if is_cfg0 else 0)
        sset(d.credit_ret, 1 if credit_ret else 0)
        sset(d.credit_ret_n, int(credit_ret_n) & MASK16)
        self.g.step(
            port_rst=port_rst, link_up=link_up, grain_n=grain_n,
            consume_vld=consume_vld, consume_flits=consume_flits,
            is_cfg0=is_cfg0, credit_ret=credit_ret, credit_ret_n=credit_ret_n,
        )
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got, consume_vld=0):
        exp = self.g.combo(consume_vld)
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        return self._score_inner(name, stim, got)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_credit"
        self.g = Golden()

        if ceil_div(8, 8) != 1 or ceil_div(7, 8) != 1 or ceil_div(9, 8) != 2:
            self.bad(name, "golden ceil(flits/n) n=8",
                     "8→1 7→1 9→2",
                     f"8→{ceil_div(8, 8)} 7→{ceil_div(7, 8)} 9→{ceil_div(9, 8)}",
                     "golden")
            phase.drop_objection(self)
            return
        if ceil_div(8, 1) != 8 or ceil_div(16, 0) != 0 or ceil_div(0, 8) != 0:
            self.bad(name, "golden ceil(flits/n) n=1 / n=0 / 0 flits",
                     "8/1→8 16/0→0 0/8→0",
                     f"{ceil_div(8, 1)} {ceil_div(16, 0)} {ceil_div(0, 8)}",
                     "golden")
            phase.drop_objection(self)
            return
        if ceil_div(1, 8) != 1 or ceil_div(1023, 1) != 1023:
            self.bad(name, "golden ceil uniqueness (1/8 vs 1023/1)",
                     "1 and 1023",
                     f"{ceil_div(1, 8)} {ceil_div(1023, 1)}",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, credit_low, no bp / proto_err / fc_ovf.
        got = self._sample()
        if not self._score(name, "reset then release, consume_vld=0 credit_ret=0",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        pend, cl, ack, bp, pe, ovf, cells = got
        if pend != 0 or cells != 0 or cl != 1 or ack != 0 or bp != 0 or pe or ovf:
            self.bad(name, "reset idle ports",
                     "pending=0 cells=0 credit_low=1 ack=0 bp=0 proto_err=0 fc_ovf=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._cycle(consume_vld=0, consume_flits=32, is_cfg0=0)
            if not self._score(name, f"idle cycle {i} after reset (no consume_vld)",
                               got, consume_vld=0):
                phase.drop_objection(self)
                return

        # Async rst_n mid-consume clears registered cells / pend / flags.
        got = await self._cycle(consume_vld=1, consume_flits=8, grain_n=8)
        if not self._score(name, "one consume before async rst (8 flits grain=8)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != 1 or got[0] != 1:
            self.bad(name, "one consume before async rst",
                     "cells=1 pending=1", self._fmt(got), "u_u.cells")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-credit (100ps, no posedge)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return

        # 2. Consume vs golden ceil (stock grain_n vectors).
        for label, flits, grain, _exp_add in (
                ("8 flits grain=8 → +1 cell", 8, 8, 1),
                ("7 flits grain=8 → +1 cell (ceil)", 7, 8, 1),
                ("9 flits grain=8 → +2 cells", 9, 8, 2),
                ("8 flits grain=1 → +8 cells", 8, 1, 8),
                ):
            got = await self._cycle(consume_vld=1, consume_flits=flits, grain_n=grain)
            if not self._score(name, label, got, consume_vld=1):
                phase.drop_objection(self)
                return
            got = await self._cycle(grain_n=grain)
            if not self._score(name, f"{label} then stall", got, consume_vld=0):
                phase.drop_objection(self)
                return

        # CFG0 does not consume (stock tc_cfg0_no_credit).
        held_cells = self.g.cells
        held_pend = self.g.pend
        got = await self._cycle(consume_vld=1, consume_flits=32, is_cfg0=1, grain_n=8)
        if not self._score(name, "consume_vld=1 is_cfg0=1 consume_flits=32",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != held_cells or got[0] != held_pend:
            self.bad(name, "CFG0 skip (cells / pending hold)",
                     f"cells={held_cells} pending={held_pend}",
                     self._fmt(got), "u_u.cells / is_cfg0")
            phase.drop_objection(self)
            return

        # grain_n=0 → ceil_div=0 (stock tc_credit_1024_flit_bp).
        got = await self._cycle(consume_vld=1, consume_flits=16, grain_n=0)
        if not self._score(name, "grain_n=0 consume 16 flits (ceil_div=0)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != held_cells:
            self.bad(name, "grain_n=0 consume",
                     f"cells unchanged ({held_cells})",
                     self._fmt(got), "u_u.cells / ceil_div")
            phase.drop_objection(self)
            return

        # 3. consume_vld=0 stall does not eat; junk flits ignored.
        held = (self.g.cells, self.g.pend)
        for k in range(3):
            got = await self._cycle(consume_vld=0, consume_flits=0x3FF, grain_n=8)
            if not self._score(name, f"stall[{k}] consume_vld=0 flits=0x3FF",
                               got, consume_vld=0):
                phase.drop_objection(self)
                return
            if (self.g.cells, self.g.pend) != held:
                self.bad(name, f"stall[{k}] cells/pend hold",
                         f"cells={held[0]} pending={held[1]}",
                         self._fmt(got), "u_u.cells")
                phase.drop_objection(self)
                return

        # Same-cycle credit_ret && consume_vld: both add (no start pin; analog of start&&valid).
        before_cells = self.g.cells
        before_pend = self.g.pend
        got = await self._cycle(
            consume_vld=1, consume_flits=8, grain_n=8,
            credit_ret=1, credit_ret_n=3)
        if not self._score(
                name, "credit_ret&&consume_vld same cycle (ret 3 cells + ceil(8/8))",
                got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != before_cells + 1 or got[0] != ((before_pend + 3 + 1) & MASK16):
            self.bad(name, "same-cycle ret+consume adds both",
                     f"cells={before_cells + 1} pending={before_pend + 4}",
                     self._fmt(got), "u_u.pend / u_u.cells")
            phase.drop_objection(self)
            return
        # After drop of consume_vld, force_crd_ack follows pend!=0.
        got = await self._cycle()
        if not self._score(name, "cycle after same-cycle ret+consume (consume_vld=0)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[2] != 1:
            self.bad(name, "force_crd_ack when pend!=0 and !consume_vld",
                     "force_crd_ack=1", self._fmt(got), "u_u.force_crd_ack")
            phase.drop_objection(self)
            return

        # credit_ret is already cells (stock: no ×n / no /n).
        before_pend = self.g.pend
        got = await self._cycle(credit_ret=1, credit_ret_n=8, grain_n=8)
        if not self._score(name, "credit_ret_n=8 cell (already cells, no ×n / no /n)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != ((before_pend + 8) & MASK16):
            self.bad(name, "credit_ret_n=8 is cells not ceil_div",
                     f"pending={before_pend + 8}",
                     self._fmt(got), "u_u.pend")
            phase.drop_objection(self)
            return

        # port_rst clears cells / pend / to (not a full async rst).
        got = await self._cycle(port_rst=1)
        if not self._score(name, "port_rst", got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != 0 or got[6] != 0 or got[1] != 1:
            self.bad(name, "port_rst clears pending/cells",
                     "pending=0 cells=0 credit_low=1",
                     self._fmt(got), "u_u.pend")
            phase.drop_objection(self)
            return

        # 4. Stock 1023 → 1024 cell thresh (tc_credit_1024_flit_bp / hole).
        got = await self._cycle(credit_ret=1, credit_ret_n=1023)
        if not self._score(name, "credit_ret_n=1023 cell (already cells)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != 1023 or got[3] != 0:
            self.bad(name, "pending=1023 cell",
                     "pending=1023 bp_nw=0 (threshold is 1024 cell)",
                     self._fmt(got), "u_u.pend / bp_nw")
            phase.drop_objection(self)
            return
        got = await self._cycle()
        if not self._score(name, "hold after 1023 (credit_ret=0)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        got = await self._cycle(credit_ret=1, credit_ret_n=1)
        if not self._score(name, "pending reaches 1024 cell via credit_ret_n",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != 1024 or got[3] != 1 or got[2] != 1:
            self.bad(name, "pending=1024 cell",
                     "pending=1024 bp_nw=1 force_crd_ack=1",
                     self._fmt(got), "u_u.pend / bp_nw / force_crd_ack")
            phase.drop_objection(self)
            return

        # During consume below a *new* add that stays >=1024, bp stays.
        # force_crd_ack stays 1 at thresh even while consume_vld=1.
        got = await self._cycle(consume_vld=1, consume_flits=8, grain_n=8)
        if not self._score(name, "consume at pending>=1024 (bp holds)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[3] != 1 or got[2] != 1:
            self.bad(name, "bp_nw / force_crd_ack at thresh during consume",
                     "bp_nw=1 force_crd_ack=1",
                     self._fmt(got), "u_u.bp_nw")
            phase.drop_objection(self)
            return

        # Second consume after the first (no leftover grain).
        got = await self._cycle(consume_vld=1, consume_flits=8, grain_n=8)
        if not self._score(name, "second consume after first (8 flits grain=8)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        got = await self._cycle()
        if not self._score(name, "idle after second consume",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return

        # !link_up clears pending / cells (stock).
        got = await self._cycle(link_up=0)
        if not self._score(name, "link_up=0", got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != 0 or got[6] != 0:
            self.bad(name, "link_up=0 clears pending/cells",
                     "pending=0 cells=0", self._fmt(got), "u_u.pend")
            phase.drop_objection(self)
            return
        got = await self._cycle(link_up=1)
        if not self._score(name, "link_up=1 after clear", got, consume_vld=0):
            phase.drop_objection(self)
            return

        # force_crd_ack drops while consume_vld=1 and pend < 1024.
        got = await self._cycle(credit_ret=1, credit_ret_n=5)
        if not self._score(name, "credit_ret_n=5 (below thresh)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[2] != 1 or got[3] != 0:
            self.bad(name, "pend=5 consume_vld=0",
                     "force_crd_ack=1 bp_nw=0",
                     self._fmt(got), "u_u.force_crd_ack")
            phase.drop_objection(self)
            return
        got = await self._cycle(consume_vld=1, consume_flits=8, grain_n=8)
        if not self._score(name, "consume_vld=1 while pend<1024 (ack drops)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[2] != 0 or got[3] != 0:
            self.bad(name, "force_crd_ack combo during consume below thresh",
                     "force_crd_ack=0 bp_nw=0",
                     self._fmt(got), "u_u.force_crd_ack")
            phase.drop_objection(self)
            return

        # port_rst again so timeout starts from a clean pend=1.
        got = await self._cycle(port_rst=1)
        if not self._score(name, "port_rst before timeout", got, consume_vld=0):
            phase.drop_objection(self)
            return

        # 5. Timeout 1us = 1250 clk (stock tc_credit_timeout_1us).
        got = await self._cycle(credit_ret=1, credit_ret_n=1)
        if not self._score(name, "credit_ret_n=1 load timeout",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        to = ival(d.u_u.to, -1)
        if to != VIBE_US_CYC:
            self.bad(name, "to reload on credit_ret",
                     f"to={VIBE_US_CYC}", f"to={to}", "u_u.to")
            phase.drop_objection(self)
            return
        for i in range(VIBE_US_CYC - 2):
            got = await self._cycle()
            if got[4] != 0:
                self.bad(name, f"pending=1 wait <1250 (cycle {i})",
                         "proto_err still 0",
                         self._fmt(got), "u_u.to / proto_err")
                phase.drop_objection(self)
                return
            if not self._score(name, f"timeout countdown {i}",
                               got, consume_vld=0):
                phase.drop_objection(self)
                return
        saw = False
        for i in range(8):
            got = await self._cycle()
            if not self._score(name, f"timeout expire wait[{i}]",
                               got, consume_vld=0):
                phase.drop_objection(self)
                return
            if got[4] == 1:
                saw = True
                break
        if not saw:
            self.bad(name, "pending held without return for >=1us",
                     "proto_err=1 (credit timeout, not deadlock)",
                     self._fmt(got), "u_u.to / proto_err")
            phase.drop_objection(self)
            return

        # port_rst does not clear proto_err (stock: only cells/pend/to).
        got = await self._cycle(port_rst=1)
        if not self._score(name, "port_rst after proto_err (flag sticky)",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[4] != 1:
            self.bad(name, "port_rst after timeout",
                     "proto_err stays 1",
                     self._fmt(got), "u_u.proto_err")
            phase.drop_objection(self)
            return

        # Async rst_n does clear proto_err.
        sset(d.rst_n, 0)
        await self._idle()
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got[4] != 0 or got[5] != 0:
            self.bad(name, "async rst_n clears proto_err / fc_ovf",
                     "proto_err=0 fc_ovf=0",
                     self._fmt(got), "u_u.proto_err")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        # 6. fc_ovf: 17-bit cells_sum > 65535 (stock grain_n / 1024_flit_bp).
        # 64 × 1023 (grain=1) → 65472; +63 → 65535 no ovf; +1 → ovf sat.
        for k in range(64):
            got = await self._cycle(consume_vld=1, consume_flits=1023, grain_n=1)
            if not self._score(name, f"climb 1023-flit grain=1 [{k}]",
                               got, consume_vld=1):
                phase.drop_objection(self)
                return
        got = await self._cycle(consume_vld=1, consume_flits=63, grain_n=1)
        if not self._score(name, "cells=65472 + 63 flits n=1 → 65535 no ovf",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != 65535 or got[5] != 0:
            self.bad(name, "cells reach 65535 without ovf",
                     "cells=65535 fc_ovf=0",
                     self._fmt(got), "u_u.cells")
            phase.drop_objection(self)
            return
        got = await self._cycle(consume_vld=1, consume_flits=1, grain_n=1)
        if not self._score(name, "cells=65535 + 1 flit n=1 → fc_ovf",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[5] != 1 or got[6] != 65535:
            self.bad(name, "17-bit cells_sum > 65535",
                     "fc_ovf=1 cells=65535",
                     self._fmt(got), "u_u.cells_sum / fc_ovf")
            phase.drop_objection(self)
            return

        # 7. Mid-run async rst_n clears registered cells / pend / to /
        # proto_err / fc_ovf. Park live leftover (cells=65535 fc_ovf=1),
        # then pulse rst_n through dest posedge.
        if not self._score_inner(name, "pre-async-rst park (live cells/fc_ovf)",
                                 got):
            phase.drop_objection(self)
            return
        if got[6] != 65535 or got[5] != 1:
            self.bad(name, "pre-async-rst park (live leftover)",
                     "cells=65535 fc_ovf=1",
                     self._fmt(got), "u_u.cells")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got[0] != 0 or got[6] != 0 or got[4] != 0 or got[5] != 0:
            self.bad(name, "mid-run rst_n=0 (100ps, no posedge)",
                     "pending=0 cells=0 proto_err=0 fc_ovf=0 (async clear)",
                     self._fmt(got), "u_u.pend / u_u.cells")
            phase.drop_objection(self)
            return
        if not self._score(name, "mid-run rst_n=0", got, consume_vld=0):
            phase.drop_objection(self)
            return
        rst_to = ival(d.u_u.to, -1)
        if rst_to != 0:
            self.bad(name, "mid-run rst_n=0 (to async clear)",
                     "u_u.to=0", f"to={rst_to}", "u_u.to")
            phase.drop_objection(self)
            return
        await self._to_fall()
        got = self._sample()
        if got[0] != 0 or got[6] != 0 or got[4] != 0 or got[5] != 0:
            self.bad(name, "rst_n held 0 through dest posedge",
                     "pending=0 cells=0 proto_err=0 fc_ovf=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if not self._score(name, "rst_n held 0 through dest posedge",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        hold_to = ival(d.u_u.to, -1)
        if hold_to != 0:
            self.bad(name, "rst_n held 0 through dest posedge (to)",
                     "u_u.to=0", f"to={hold_to}", "u_u.to")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-release, idle",
                           got, consume_vld=0):
            phase.drop_objection(self)
            return
        if got[0] != 0 or got[6] != 0 or got[5] != 0:
            self.bad(name, "after async re-release, no leftover cells/fc_ovf",
                     "pending=0 cells=0 fc_ovf=0",
                     self._fmt(got), "u_u.cells")
            phase.drop_objection(self)
            return
        # After mid-run rst leftover cells / fc_ovf are gone; a new
        # consume must add 1 cell with no leftover 65535.
        got = await self._cycle(consume_vld=1, consume_flits=8, grain_n=8)
        if not self._score(name, "8 flits grain=8 after mid-run rst (no leftover)",
                           got, consume_vld=1):
            phase.drop_objection(self)
            return
        if got[6] != 1 or got[0] != 1 or got[5] != 0:
            self.bad(name, "after mid-run rst consume (no leftover 65535)",
                     "cells=1 pending=1 fc_ovf=0",
                     self._fmt(got), "u_u.cells")
            phase.drop_objection(self)
            return

        # 8. Leaf pins match product SV (no ovf_l / dual-clock / leftover
        # u_crd). Instance u_u (not leftover u_crd / u_bcrc / u_sm).
        if not hasattr(d, "u_u"):
            self.bad(name, "leaf instance scan (u_u)",
                     "u_u present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_dll_credit product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return
        u = d.u_u
        for need in PINS:
            if not hasattr(u, need):
                self.bad(name, f"leaf instance pin scan (u_u.{need})",
                         f"u_u.{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_credit)
