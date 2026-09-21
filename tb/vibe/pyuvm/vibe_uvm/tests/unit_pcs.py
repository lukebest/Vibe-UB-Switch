"""PCS / PHY / gear TCs ported from tb/vibe/tests/*.sv (same stimulus/score)."""

import cocotb
from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.handle import Force, Release
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

FEC_BYPASS = 0
FEC_T2 = 1
FEC_T4 = 2

# Table 3-5 subset used by AMCTL (sel 0..30) plus default (31).
EBCH16 = [
    0x0000, 0x0A6F, 0x14DD, 0x1EB2, 0x23D6, 0x29B9, 0x370B, 0x3D64,
    0x47AC, 0x4DC3, 0x5371, 0x591E, 0x647A, 0x6E15, 0x70A7, 0x7AC8,
    0x8537, 0x8F58, 0x91EA, 0x9B85, 0xA6E1, 0xAC8E, 0xB23C, 0xB853,
    0xC29B, 0xC8F4, 0xD646, 0xDC29, 0xE14D, 0xEB22, 0xF590, 0xFFFF,
]


def _drive_rst(d, val=1):
    if hasattr(d, "txrst_n"):
        sset(d.txrst_n, val)
    if hasattr(d, "rxrst_n"):
        sset(d.rxrst_n, val)


async def _hs_monitor(vld, rdy, clk, box):
    """Count vld&&rdy once per cycle (negedge = Icarus-stable NBA window)."""
    while True:
        await RisingEdge(clk)
        await FallingEdge(clk)
        if ival(vld, 0) and ival(rdy, 0):
            box[0] += 1


async def _hi_monitor(sig, clk, box):
    """Latch a 1-cycle pulse (posedge pre-NBA or negedge post-NBA)."""
    while True:
        await RisingEdge(clk)
        if ival(sig, 0):
            box[0] = 1
        await FallingEdge(clk)
        if ival(sig, 0):
            box[0] = 1


class tc_pcs_tx_g1_window(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        fail = 0
        saw = 0
        sset(d.rst_n, 0)
        sset(d.link_up, 1)
        sset(d.in_vld, 0)
        sset(d.win_ready, 1)
        sset(d.in_data, 0x1)
        await self.cycles(3)
        sset(d.rst_n, 1)
        for _ in range(4):
            await FallingEdge(d.clk)
            if ival(d.in_ready, 0):
                sset(d.in_vld, 1)
                sset(d.in_data, 0xA)
            else:
                sset(d.in_vld, 0)
            await RisingEdge(d.clk)
            if ival(d.win_vld, 0):
                saw = 1
        sset(d.in_vld, 0)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.win_vld, 0):
                saw = 1
        # Isolated 4-flit beat then idle: nflit==4 complete with 2 Nulls (:65)
        sset(d.rst_n, 0)
        await RisingEdge(d.clk)
        sset(d.rst_n, 1)
        sset(d.in_vld, 0)
        sset(d.win_ready, 1)
        sset(d.link_up, 1)
        sset(d.in_data, 0xB)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.win_vld, 0):
                saw = 1
        # Two beats with nflit==4 between them (rem-complete :51).
        # Hold win_ready=0 after beat 1 so idle :65 cannot complete the window.
        sset(d.rst_n, 0)
        await RisingEdge(d.clk)
        sset(d.rst_n, 1)
        sset(d.in_vld, 0)
        sset(d.win_ready, 0)
        sset(d.link_up, 1)
        sset(d.in_data, 0xC)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        sset(d.in_data, 0xD)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        sset(d.win_ready, 1)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.win_vld, 0):
                saw = 1
        if not saw:
            self.bad("tc_pcs_tx_g1_window", "several 640b beats link_up=1",
                     "win_vld (6-flit / 960b window)", "no window",
                     "u_g.nflit / have")
            fail = 1
        # rem_vld → idle-null fill of next window
        sset(d.in_vld, 0)
        sset(d.win_ready, 1)
        sset(d.link_up, 1)
        await self.cycles(12)
        sset(d.link_up, 0)
        await RisingEdge(d.clk)
        if not fail:
            self.ok("tc_pcs_tx_g1_window")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_tx_g1_window)


class tc_pcs_fec_bypass(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        fail = 0
        ncw = 0
        sset(d.rst_n, 0)
        sset(d.fec_mode, FEC_BYPASS)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 1)
        sset(d.win_data, 0x1)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.win_vld, 1)
        sset(d.win_data, (1 << 960) - 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_data, 0xA)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_vld, 0)
        for _ in range(16):
            await RisingEdge(d.clk)
            if ival(d.cw_vld, 0):
                ncw += 1
        if ncw < 2:
            self.bad("tc_pcs_fec_bypass", "fec_mode=bypass two 960b windows",
                     "two 1024b cw beats (align, no RS)", f"{ncw} cw_vld",
                     "u_f.bypass / emit_b")
            fail = 1
        # Second pair: stall cw_ready after first emit to take bypass emit_b else
        await FallingEdge(d.clk)
        sset(d.win_vld, 1)
        sset(d.win_data, 0x3)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_data, 0x4)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 0)
        await self.cycles(4)
        sset(d.cw_ready, 1)
        await self.cycles(8)
        if not fail:
            self.ok("tc_pcs_fec_bypass")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_fec_bypass)


class tc_pcs_fec_dual_enc(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw_a = [0]
        saw_b = [0]
        sset(d.rst_n, 0)
        sset(d.fec_mode, FEC_T4)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 1)
        sset(d.win_data, 0x3)
        await self.cycles(3)
        sset(d.rst_n, 1)
        cocotb.start_soon(_hi_monitor(d.enc_a_start, d.clk, saw_a))
        cocotb.start_soon(_hi_monitor(d.enc_b_start, d.clk, saw_b))
        await FallingEdge(d.clk)
        sset(d.win_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_vld, 0)
        await self.cycles(280)
        if not saw_a[0] or not saw_b[0]:
            self.bad("tc_pcs_fec_dual_enc", "fec_mode=T4 two windows",
                     "enc_a_start and enc_b_start (dual interleave)",
                     f"a={saw_a[0]} b={saw_b[0]}", "u_f.enc_a_start / enc_b_start")
        else:
            self.ok("tc_pcs_fec_dual_enc")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_fec_dual_enc)


class tc_pcs_fec_t2(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw_a = [0]
        saw_b = [0]
        ncw = [0]
        sset(d.rst_n, 0)
        sset(d.fec_mode, FEC_T2)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 1)
        sset(d.win_data, 0x5)
        await self.cycles(3)
        sset(d.rst_n, 1)
        cocotb.start_soon(_hi_monitor(d.enc_a_start, d.clk, saw_a))
        cocotb.start_soon(_hi_monitor(d.enc_b_start, d.clk, saw_b))
        cocotb.start_soon(_hs_monitor(d.cw_vld, d.cw_ready, d.clk, ncw))
        await FallingEdge(d.clk)
        sset(d.win_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_data, 0x6)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_vld, 0)
        await self.cycles(200)
        if not saw_a[0] or not saw_b[0]:
            self.bad("tc_pcs_fec_t2", "fec_mode=T2 two 960b windows",
                     "enc_a_start and enc_b_start (not bypass)",
                     f"a={saw_a[0]} b={saw_b[0]} cw={ncw[0]}",
                     "u_f.enc_a_start / enc_b_start / bypass")
        else:
            self.ok("tc_pcs_fec_t2")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_fec_t2)


class tc_pcs_cw2beat(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        n = 0
        sset(d.rst_n, 0)
        sset(d.cw_vld, 0)
        sset(d.beat_ready, 1)
        sset(d.cw_data, (0xA << 512) | 0xB)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.cw_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cw_vld, 0)
        for _ in range(6):
            await RisingEdge(d.clk)
            if ival(d.beat_vld, 0):
                n += 1
        if n < 2:
            self.bad("tc_pcs_cw2beat", "one 1024b cw", "two 512b beats",
                     str(n), "u_c.have_hi / have_lo")
        else:
            self.ok("tc_pcs_cw2beat")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_cw2beat)


class tc_pcs_amctl(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.link_up, 1)
        sset(d.sdf_period, 1)
        sset(d.lane_id, 0)
        sset(d.req, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        sset(d.req, 1)
        await self.cycles(4)
        if ival(d.amctl_40B, 0) == 0:
            self.bad("tc_pcs_amctl", "link_up sdf_period lane0 req",
                     "nonzero 40-symbol AMCTL (eBCH-16)", "0",
                     "u_a.amctl_40B / u_a.cw21")
        sset(d.lane_id, 1)
        await Timer(1, "NS")
        sset(d.lane_id, 2)
        await Timer(1, "NS")
        sset(d.lane_id, 3)
        await Timer(1, "NS")
        if ival(d.amctl_40B, 0) == 0:
            self.bad("tc_pcs_amctl", "lane_id=3", "nonzero AMCTL", "0",
                     "amctl_40B")
        sset(d.link_up, 0)
        await Timer(1, "NS")
        if ival(d.ack, 0):
            self.bad("tc_pcs_amctl", "req=1 link_up=0", "ack=0", "1", "ack")
        self.finish_ok("tc_pcs_amctl")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_amctl)


class tc_pcs_scramble(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.lane_id, 0)
        sset(d.seed_load, 0)
        sset(d.en, 0)
        sset(d.in_vld, 0)
        sset(d.in_data, 0x55)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        sset(d.en, 0)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        if ival(d.out_data, -1) != 0x55:
            self.bad("tc_pcs_scramble", "en=0 in=55",
                     "pass-through (AMCTL/EEIB)",
                     f"{ival(d.out_data, 0):x}", "out_data")
            phase.drop_objection(self)
            return
        sset(d.seed_load, 1)
        await RisingEdge(d.clk)
        sset(d.seed_load, 0)
        sset(d.en, 1)
        sset(d.in_data, 0)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        if ival(d.out_data, 0) == 0:
            self.bad("tc_pcs_scramble", "en=1 in=0 after seed",
                     "scrambled nonzero mask", "0", "out_data")
        else:
            self.ok("tc_pcs_scramble")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_scramble)


class tc_ebch16_lut(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        # Combo LUT: no clock. #1 settle after each sel.
        for i, exp in enumerate(EBCH16):
            sset(d.cw_sel, i)
            await Timer(1, "NS")
            act = ival(d.cw, -1)
            if act != exp:
                self.bad("tc_ebch16_lut", f"cw_sel={i}", f"{exp:x}",
                         f"{0 if act is None else act:x}", "cw")
                break
        else:
            self.ok("tc_ebch16_lut")
        phase.drop_objection(self)


uvm_component_utils(tc_ebch16_lut)


class tc_pcs_fec_emitb(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        fail = 0
        saw1 = 0
        saw2 = 0
        sset(d.rst_n, 0)
        sset(d.fec_mode, FEC_BYPASS)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 0)
        sset(d.win_data, 0x1)
        await self.cycles(4)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.win_vld, 1)
        sset(d.win_data, 0xAA)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_data, 0xBB)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.win_vld, 0)
        sset(d.cw_ready, 0)
        n = 0
        while not ival(d.cw_vld, 0) and n < 20:
            await RisingEdge(d.clk)
            n += 1
        if not ival(d.cw_vld, 0):
            self.bad("tc_pcs_fec_emitb", "two bypass windows, cw_ready=0",
                     "first cw_vld",
                     f"0 emit_b={ival(d.emit_b, 0)}", "u_f.emit_b")
            fail = 1
        else:
            saw1 = 1
        await FallingEdge(d.clk)
        sset(d.cw_ready, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cw_ready, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.cw_vld, 0):
            saw2 = 1
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.cw_vld, 0):
            saw2 = 1
        if not saw2:
            self.bad("tc_pcs_fec_emitb", "ack first CW, emit_b held",
                     "second cw_vld (line 96 else)",
                     f"0 emit_b={ival(d.emit_b, 0)} have0={ival(d.have0, 0)} "
                     f"have1={ival(d.have1, 0)}",
                     "u_f.emit_b / have0 / have1")
            fail = 1
        if not fail and saw1:
            self.ok("tc_pcs_fec_emitb")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_fec_emitb)


async def _amctl_send_pair(d, body, lidw, endw):
    w0 = (body & 0xFFFF) << 144
    w1 = ((endw & 0xFFFF) << 112) | ((lidw & 0xFFFF) << 64)
    await FallingEdge(d.clk)
    sset(d.in_data, w0)
    sset(d.in_vld, 1)
    await RisingEdge(d.clk)
    await FallingEdge(d.clk)
    sset(d.in_data, w1)
    await RisingEdge(d.clk)
    await FallingEdge(d.clk)
    sset(d.in_vld, 0)


class tc_pcs_rx_amctl(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        cw21, cw22, cw28 = EBCH16[21], EBCH16[22], EBCH16[28]
        cw3, cw8, cw9, cw10 = EBCH16[3], EBCH16[8], EBCH16[9], EBCH16[10]
        sset(d.rst_n, 0)
        sset(d.in_vld, 0)
        sset(d.in_data, 0)
        await Timer(1, "NS")
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        for _ in range(4):
            await _amctl_send_pair(d, cw21, cw3, cw22)
        if not ival(d.locked, 0) or ival(d.lid, -1) != 0:
            self.bad("tc_pcs_rx_amctl", "4× AMCTL LID0", "locked lid=0",
                     f"lock={ival(d.locked, 0)} lid={ival(d.lid, -1)}",
                     "locked / lid")
            phase.drop_objection(self)
            return
        await _amctl_send_pair(d, cw28, cw8, cw22)
        if ival(d.lid, -1) != 1:
            self.bad("tc_pcs_rx_amctl", "LID cw8", "lid=1",
                     str(ival(d.lid, -1)), "lid")
            phase.drop_objection(self)
            return
        await _amctl_send_pair(d, cw21, cw9, cw22)
        await _amctl_send_pair(d, cw21, cw10, cw22)
        if ival(d.lid, -1) != 3:
            self.bad("tc_pcs_rx_amctl", "LID cw10", "lid=3",
                     str(ival(d.lid, -1)), "lid")
            phase.drop_objection(self)
            return
        for _ in range(4):
            await _amctl_send_pair(d, 0, 0, 0)
        if ival(d.locked, 0):
            self.bad("tc_pcs_rx_amctl", "4 non-AM while locked", "unlock",
                     "still locked", "locked")
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await RisingEdge(d.clk)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        await _amctl_send_pair(d, cw21, 0xFFFF, cw22)
        if not ival(d.lid_bad, 0):
            self.bad("tc_pcs_rx_amctl", "AMCTL LID not {0,1,2,3}",
                     "lid_bad (U24 no swap)", "0", "lid_bad")
        else:
            self.ok("tc_pcs_rx_amctl")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_rx_amctl)


class tc_pcs_rx_deskew(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.in_vld, 0)
        sset(d.am0, 0)
        sset(d.am1, 0)
        sset(d.am2, 0)
        sset(d.am3, 0)
        sset(d.in0, 0)
        sset(d.in1, 0)
        sset(d.in2, 0)
        sset(d.in3, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        sset(d.am0, 1)
        sset(d.in0, 0xA)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am0, 0)
        sset(d.am1, 1)
        sset(d.in1, 0xB)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am1, 0)
        sset(d.am2, 1)
        sset(d.in2, 0xC)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am2, 0)
        sset(d.am3, 1)
        sset(d.in3, 0xD)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am3, 0)
        await RisingEdge(d.clk)
        if not ival(d.aligned, 0):
            self.bad("tc_pcs_rx_deskew", "AM on each lane staggered",
                     "aligned", "0", "aligned")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.in0, 0x1)
        sset(d.in1, 0x2)
        sset(d.in2, 0x3)
        sset(d.in3, 0x4)
        sset(d.in_vld, 1)
        await Timer(1, "NS")
        if not ival(d.out_vld, 0):
            self.bad("tc_pcs_rx_deskew", "aligned + data no AM", "out_vld",
                     "0", "out_vld")
        else:
            await RisingEdge(d.clk)
            sset(d.in_vld, 0)
            self.ok("tc_pcs_rx_deskew")
            phase.drop_objection(self)
            return
        await RisingEdge(d.clk)
        sset(d.in_vld, 0)
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_rx_deskew)


class tc_pcs_rx_unpack(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw = 0
        sset(d.rst_n, 0)
        sset(d.lane_vld, 0)
        sset(d.am0, 0)
        sset(d.am1, 0)
        sset(d.am2, 0)
        sset(d.am3, 0)
        sset(d.am_gap, 0)
        sset(d.beat_ready, 1)
        sset(d.lane0, 0)
        sset(d.lane1, 0)
        sset(d.lane2, 0)
        sset(d.lane3, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.am0, 1)
        sset(d.lane_vld, 1)
        sset(d.lane0, 0xAA)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am0, 0)
        for n in range(5):
            sset(d.lane0, n)
            sset(d.lane1, n + 16)
            sset(d.lane2, n + 32)
            sset(d.lane3, n + 48)
            sset(d.lane_vld, 1)
            await RisingEdge(d.clk)
            if ival(d.beat_vld, 0):
                saw = 1
        await FallingEdge(d.clk)
        sset(d.lane_vld, 0)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.beat_vld, 0):
                saw = 1
        if not saw:
            self.bad("tc_pcs_rx_unpack", "4+ lane groups", "beat_vld", "0",
                     "have / n")
            phase.drop_objection(self)
            return
        sset(d.beat_ready, 0)
        await RisingEdge(d.clk)
        sset(d.beat_ready, 1)
        await self.cycles(6)
        await FallingEdge(d.clk)
        sset(d.am_gap, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am_gap, 0)
        sset(d.beat_ready, 1)
        for n in range(8):
            sset(d.lane0, n)
            sset(d.lane1, n + 16)
            sset(d.lane2, n + 32)
            sset(d.lane3, n + 48)
            sset(d.lane_vld, 1)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.lane_vld, 0)
        await self.cycles(10)
        # n==0 && have drain else (coverage; NOTE if force ignored)
        inst = getattr(d, "u_u", d)
        try:
            inst.n.value = Force(0)
            inst.have.value = Force(1)
        except Exception:
            pass
        sset(d.beat_ready, 1)
        await RisingEdge(d.clk)
        try:
            inst.n.value = Release()
            inst.have.value = Release()
        except Exception:
            pass
        await RisingEdge(d.clk)
        self.ok("tc_pcs_rx_unpack")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_rx_unpack)


class tc_pcs_rx_fec(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw = 0
        sset(d.rst_n, 0)
        sset(d.fec_mode, FEC_BYPASS)
        sset(d.beat_vld, 0)
        sset(d.win_ready, 1)
        sset(d.am_gap, 0)
        sset(d.beat_data, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.beat_data, (1 << 512) - 1)
        sset(d.beat_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.beat_data, 0xA)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.beat_vld, 0)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.win_vld, 0):
                saw = 1
        if not saw:
            self.bad("tc_pcs_rx_fec", "bypass two 512b beats", "win_vld", "0",
                     "win_vld")
            phase.drop_objection(self)
            return
        sset(d.win_ready, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.am_gap, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.am_gap, 0)
        sset(d.fec_mode, FEC_T4)
        await FallingEdge(d.clk)
        sset(d.beat_data, 0x1)
        sset(d.beat_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.beat_data, 0x2)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.beat_vld, 0)
        await self.cycles(200)
        self.ok("tc_pcs_rx_fec")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_rx_fec)


class tc_pcs_tx_pack(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw = 0
        sset(d.rst_n, 0)
        sset(d.sdf_period, 0)
        sset(d.afifo_afull, 0)
        sset(d.beat_vld, 0)
        sset(d.lane_ready, 1)
        sset(d.beat_data, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        for i in range(8):
            await FallingEdge(d.clk)
            if ival(d.beat_ready, 0):
                sset(d.beat_vld, 1)
                sset(d.beat_data, (i & 0xFF) << 504)
            else:
                sset(d.beat_vld, 0)
            await RisingEdge(d.clk)
            if ival(d.lane_vld, 0):
                saw = 1
        await FallingEdge(d.clk)
        sset(d.beat_vld, 0)
        for _ in range(16):
            await RisingEdge(d.clk)
            if ival(d.lane_vld, 0):
                saw = 1
        try:
            d.sym_cnt.value = Force(512)
        except Exception:
            pass
        await FallingEdge(d.clk)
        sset(d.beat_vld, 1)
        sset(d.beat_data, 0x55)
        await self.cycles(3)
        try:
            d.sym_cnt.value = Release()
        except Exception:
            pass
        await FallingEdge(d.clk)
        sset(d.beat_vld, 0)
        await self.cycles(8)
        sset(d.afifo_afull, 1)
        await RisingEdge(d.clk)
        sset(d.afifo_afull, 0)
        sset(d.sdf_period, 1)
        await RisingEdge(d.clk)
        if not saw:
            self.bad("tc_pcs_tx_pack", "8 beats", "lane_vld", "0", "pack_vld")
        else:
            self.ok("tc_pcs_tx_pack")
        phase.drop_objection(self)


uvm_component_utils(tc_pcs_tx_pack)


class tc_rs_dec_syndrome(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        saw_done = 0
        sset(d.rst_n, 0)
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.in_sym, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await FallingEdge(d.clk)
        sset(d.start, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.start, 0)
        for _ in range(128):
            await FallingEdge(d.clk)
            while not ival(d.in_ready, 0):
                await RisingEdge(d.clk)
                if ival(d.done, 0):
                    saw_done = 1
            sset(d.in_sym, 0)
            sset(d.in_vld, 1)
            await RisingEdge(d.clk)
            if ival(d.done, 0):
                saw_done = 1
            await FallingEdge(d.clk)
            if ival(d.done, 0):
                saw_done = 1
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.done, 0):
                saw_done = 1
            await FallingEdge(d.clk)
            if ival(d.done, 0):
                saw_done = 1
        if not saw_done:
            self.bad("tc_rs_dec_syndrome", "start + 128 zero symbols",
                     "done pulse",
                     f"no done fail={ival(d.fec_fail, 0)}",
                     "u_d.busy / cnt / s0")
        else:
            self.ok("tc_rs_dec_syndrome")
        phase.drop_objection(self)


uvm_component_utils(tc_rs_dec_syndrome)


class tc_gear_160_128(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        nout = [0]
        sent = 0
        sset(d.rst_n, 0)
        sset(d.in_vld, 0)
        sset(d.out_ready, 1)
        sset(d.in_data, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        cocotb.start_soon(_hs_monitor(d.out_vld, d.out_ready, d.clk, nout))
        while sent < 4:
            await FallingEdge(d.clk)
            if ival(d.in_ready, 0):
                sset(d.in_data, (0xA << 120) | 0x1)
                sset(d.in_vld, 1)
                sent += 1
            else:
                sset(d.in_vld, 0)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await self.cycles(16)
        if nout[0] < 5:
            self.bad("tc_gear_160_128", "4×160b in, out_ready=1",
                     "5×128b out beats (U26)", f"{nout[0]} beats",
                     "u_g.rbits / hold_vld")
        else:
            self.ok("tc_gear_160_128")
        phase.drop_objection(self)


uvm_component_utils(tc_gear_160_128)


class tc_gear_128_160(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        nout = [0]
        sent = 0
        sset(d.rst_n, 0)
        sset(d.in_vld, 0)
        sset(d.out_ready, 1)
        sset(d.in_data, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        cocotb.start_soon(_hs_monitor(d.out_vld, d.out_ready, d.clk, nout))
        while sent < 5:
            await FallingEdge(d.clk)
            if ival(d.in_ready, 0):
                sset(d.in_data, 0x55)
                sset(d.in_vld, 1)
                sent += 1
            else:
                sset(d.in_vld, 0)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await self.cycles(16)
        if nout[0] < 4:
            self.bad("tc_gear_128_160", "5×128b in", "4×160b out",
                     str(nout[0]), "u_g.phase / hold_vld")
        else:
            self.ok("tc_gear_128_160")
        phase.drop_objection(self)


uvm_component_utils(tc_gear_128_160)


class tc_pma_922mhz(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        _drive_rst(d, 1)
        sset(d.afifo_pma_lane0, 0xA0)
        sset(d.afifo_pma_lane1, 0xA1)
        sset(d.afifo_pma_lane2, 0xA2)
        sset(d.afifo_pma_lane3, 0xA3)
        sset(d.afifo_pma_lane_vld, 1)
        sset(d.pma_pcs_rxdata, 0)
        edges = 0
        for _ in range(8):
            await RisingEdge(d.txclk)
            edges += 1
        tx = ival(d.pcs_pma_txdata, 0)
        lo = tx & ((1 << 128) - 1)
        hi = (tx >> 384) & ((1 << 128) - 1)
        if lo != 0xA0 or hi != 0xA3:
            self.bad("tc_pma_922mhz",
                     "512b PMA at T=1085ps (~922 MHz), lanes A0..A3",
                     "packed {A3,A2,A1,A0}", f"{tx:x}",
                     "u_p.pcs_pma_txdata")
            phase.drop_objection(self)
            return
        if edges < 8:
            self.bad("tc_pma_922mhz", "8 posedges at 922 MHz period",
                     "clocks advance", f"edges={edges}", "txclk")
        else:
            self.ok("tc_pma_922mhz")
        phase.drop_objection(self)


uvm_component_utils(tc_pma_922mhz)


class tc_phy_u26_chain(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        n128 = [0]
        n160 = [0]
        sent = 0
        sset(d.rst_n, 0)
        sset(d.g1_iv, 0)
        sset(d.g1_or, 1)
        sset(d.g1_id, 0)
        sset(d.g2_iv, 0)
        sset(d.g2_or, 1)
        sset(d.g2_id, 0)
        sset(d.t0, 0)
        sset(d.t1, 0)
        sset(d.t2, 0)
        sset(d.t3, 0)
        sset(d.tvl, 0)
        sset(d.pma_pcs_rxdata, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        cocotb.start_soon(_hs_monitor(d.g1_ov, d.g1_or, d.clk, n128))
        cocotb.start_soon(_hs_monitor(d.g2_ov, d.g2_or, d.clk, n160))
        while sent < 4:
            await FallingEdge(d.clk)
            if ival(d.g1_ir, 0):
                sset(d.g1_id, (0xA << 120) | 0x1)
                sset(d.g1_iv, 1)
                sent += 1
            else:
                sset(d.g1_iv, 0)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.g1_iv, 0)
        await self.cycles(16)
        sset(d.t0, 0x11)
        sset(d.t1, 0x22)
        sset(d.t2, 0x33)
        sset(d.t3, 0x44)
        sset(d.tvl, 1)
        await RisingEdge(d.txclk)
        await RisingEdge(d.txclk)
        sset(d.pma_pcs_rxdata, ival(d.pcs_pma_txdata, 0))
        await RisingEdge(d.rxclk)
        await RisingEdge(d.rxclk)
        tx = ival(d.pcs_pma_txdata, 0)
        r0 = ival(d.r0, -1)
        if n128[0] < 5:
            self.bad("tc_phy_u26_chain", "4x160 into TX gear",
                     ">=5 x128 beats (U26 4*160=5*128)", str(n128[0]),
                     "u_txg.rbits / hold_vld")
            phase.drop_objection(self)
            return
        if (tx & ((1 << 128) - 1)) != 0x11 or r0 != 0x11:
            self.bad("tc_phy_u26_chain",
                     "PMA lanes 11/22/33/44 looped pma_pcs_rxdata=pcs_pma_txdata",
                     "[127:0]=lane0=11 both TX pack and RX slice",
                     f"pcs_pma_txdata[127:0]={tx & ((1 << 128) - 1):x} r0="
                     f"{0 if r0 is None else r0:x}",
                     "u_p.pcs_pma_txdata / u_p.pma_afifo_lane0")
            phase.drop_objection(self)
            return
        sent = 0
        while sent < 5:
            await FallingEdge(d.clk)
            if ival(d.g2_ir, 0):
                sset(d.g2_id, 0x55)
                sset(d.g2_iv, 1)
                sent += 1
            else:
                sset(d.g2_iv, 0)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.g2_iv, 0)
        await self.cycles(16)
        if n160[0] < 4:
            self.bad("tc_phy_u26_chain", "5x128 into RX gear",
                     ">=4 x160 beats", str(n160[0]), "u_rxg.phase / hold_vld")
        else:
            self.ok("tc_phy_u26_chain")
        phase.drop_objection(self)


uvm_component_utils(tc_phy_u26_chain)
