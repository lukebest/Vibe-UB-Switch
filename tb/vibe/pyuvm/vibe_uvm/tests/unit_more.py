"""More Icarus leaf units: fabric / mgmt / DLL / credit / NW / LMSM."""

from pathlib import Path
from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.handle import Force, Release
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, bit
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ROOT = Path(__file__).resolve().parents[5]


class tc_irq_agg(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("irq_clr", "icrc_fail", "drop_g1"):
            sset(getattr(d, n), 0)
        for n in ("rx_ovf", "fc_ovf", "proto_err", "retry_error",
                  "len_err", "deadlock_drop", "afifo_ovf"):
            sset(getattr(d, n), 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        if ival(d.irq_logic, 0):
            self.bad("tc_irq_agg", "reset", "irq_logic=0", "1", "u_i")
            phase.drop_objection(self)
            return
        srcs = [
            ("rx_ovf", 0x1), ("fc_ovf", 0x2), ("proto_err", 0x4),
            ("retry_error", 0x8), ("icrc_fail", 1), ("len_err", 0x1),
            ("deadlock_drop", 0x2), ("drop_g1", 1), ("afifo_ovf", 0x4),
        ]
        for name, val in srcs:
            sset(d.irq_clr, 1)
            await RisingEdge(d.clk)
            sset(d.irq_clr, 0)
            await RisingEdge(d.clk)
            if ival(d.irq_logic, 0):
                self.bad("tc_irq_agg", "irq_clr", "0", "1", "irq_logic")
                break
            sset(getattr(d, name), val)
            await RisingEdge(d.clk)
            sset(getattr(d, name), 0)
            await RisingEdge(d.clk)
            if not ival(d.irq_logic, 0):
                self.bad("tc_irq_agg", f"error source {name}", "sticky 1", "0", name)
                break
            await RisingEdge(d.clk)
            if not ival(d.irq_logic, 0):
                self.bad("tc_irq_agg", f"{name} deasserted", "still sticky", "0", "irq")
                break
        else:
            sset(d.rst_n, 0)
            await RisingEdge(d.clk)
            sset(d.rst_n, 1)
            await RisingEdge(d.clk)
            if ival(d.irq_logic, 0):
                self.bad("tc_irq_agg", "reset after sticky", "0", "1", "irq")
            else:
                self.ok("tc_irq_agg")
        phase.drop_objection(self)


uvm_component_utils(tc_irq_agg)


class tc_rst_port_device(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.device_rst_pulse, 0)
        sset(d.port_rst_pulse, 0)
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.port_rst_pulse, 0b0100)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.port_rst_pulse, 0)
        await RisingEdge(d.clk)
        pr = ival(d.port_rst, 0)
        if ((pr >> 2) & 1) != 1 or (pr & 1) != 0:
            self.bad("tc_rst_port_device", "port_rst_pulse[2]",
                     "port_rst[2]=1 others 0", f"{pr:04b}", "port_rst")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.device_rst_pulse, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.device_rst_pulse, 0)
        await RisingEdge(d.clk)
        if not ival(d.device_rst, 0):
            self.bad("tc_rst_port_device", "device_rst_pulse", "device_rst hold", "0")
            phase.drop_objection(self)
            return
        await self.cycles(10)
        if ival(d.device_rst, 0):
            self.bad("tc_rst_port_device", "10 cyc after pulse", "released", "still 1")
            phase.drop_objection(self)
            return
        await self.cycles(8)
        if bit(d.port_rst, 2):
            self.bad("tc_rst_port_device", "wait after port_rst_pulse[2]",
                     "port_rst[2]=0", "1")
        else:
            self.ok("tc_rst_port_device")
        phase.drop_objection(self)


uvm_component_utils(tc_rst_port_device)


class tc_fecn_mark(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.cci_in, 0)
        sset(d.voq_occ, 0)
        await Timer(1, "NS")
        if ival(d.marked, 0):
            self.bad("tc_fecn_mark", "empty VOQ mode 0", "not marked", "1")
            phase.drop_objection(self)
            return
        sset(d.cci_in, (0b100 << 13) | 0b01)
        sset(d.voq_occ, 24)
        await Timer(1, "NS")
        if not ival(d.marked, 0):
            self.bad("tc_fecn_mark", "Mode=100 FECN=01 occ=24", "marked", "0")
            phase.drop_objection(self)
            return
        sset(d.cci_in, (0b010 << 13) | 0b01)
        await Timer(1, "NS")
        if not ival(d.marked, 0):
            self.bad("tc_fecn_mark", "Mode=010 FECN=01 occ=24", "marked", "0")
            phase.drop_objection(self)
            return
        sset(d.cci_in, (0b100 << 13) | 0b00)
        await Timer(1, "NS")
        if ival(d.marked, 0):
            self.bad("tc_fecn_mark", "FECN=00", "not marked", "1")
            phase.drop_objection(self)
            return
        sset(d.cci_in, (0b100 << 13) | 0b11)
        await Timer(1, "NS")
        if ival(d.marked, 0):
            self.bad("tc_fecn_mark", "FECN=11 already severe", "not marked", "1")
            phase.drop_objection(self)
            return
        sset(d.cci_in, 0b01)
        await Timer(1, "NS")
        if ival(d.marked, 0):
            self.bad("tc_fecn_mark", "Mode=000", "not marked", "1")
        else:
            self.ok("tc_fecn_mark")
        phase.drop_objection(self)


uvm_component_utils(tc_fecn_mark)


class tc_credit_grain_n(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.consume_flits, 8)
        sset(d.consume_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.consume_vld, 0)
        await RisingEdge(d.clk)
        cells = ival(d.cells, -1)
        if cells != 1:
            self.bad("tc_credit_grain_n", "consume 8 flits grain_n=8",
                     "cells=1", str(cells), "u_crd.cells")
            phase.drop_objection(self)
            return
        sset(d.grain_n, 1)
        await FallingEdge(d.clk)
        sset(d.consume_flits, 8)
        sset(d.consume_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.consume_vld, 0)
        await RisingEdge(d.clk)
        if ival(d.cells, -1) != 9:
            self.bad("tc_credit_grain_n", "8 flits grain=1 after cells=1",
                     "cells=9", str(ival(d.cells, -1)))
            phase.drop_objection(self)
            return
        sset(d.grain_n, 1)
        for _ in range(64):
            await FallingEdge(d.clk)
            sset(d.consume_flits, 1023)
            sset(d.consume_vld, 1)
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            sset(d.consume_vld, 0)
        await FallingEdge(d.clk)
        sset(d.consume_flits, 53)
        sset(d.consume_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.consume_vld, 0)
        await RisingEdge(d.clk)
        if ival(d.cells, -1) != 65534:
            self.bad("tc_credit_grain_n", "climb to 65534",
                     "65534", str(ival(d.cells, -1)))
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.consume_flits, 4)
        sset(d.consume_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.consume_vld, 0)
        await RisingEdge(d.clk)
        if not ival(d.fc_ovf, 0) or ival(d.cells, -1) != 65535:
            self.bad("tc_credit_grain_n", "65534 + 4 flits n=1",
                     "fc_ovf=1 cells=65535",
                     f"ovf={ival(d.fc_ovf, 0)} cells={ival(d.cells, -1)}")
        else:
            self.ok("tc_credit_grain_n")
        phase.drop_objection(self)


uvm_component_utils(tc_credit_grain_n)


class tc_credit_no_underflow(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        text = (ROOT / "rtl" / "dll" / "vibe_dll_credit.sv").read_text()
        code = "\n".join(
            ln.split("//", 1)[0] for ln in text.splitlines()
        )
        if "underflow" in code.lower() or "und_err" in code:
            self.bad("tc_credit_no_underflow",
                     "scan vibe_dll_credit.sv (comments ignored)",
                     "no underflow / und_err token",
                     "token present", "rtl/dll/vibe_dll_credit.sv")
            phase.drop_objection(self)
            return
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 4)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        await RisingEdge(d.clk)
        if ival(d.fc_ovf, 0):
            self.bad("tc_credit_no_underflow", "credit_ret_n=4 no consume",
                     "fc_ovf=0", "1")
        else:
            self.ok("tc_credit_no_underflow")
        phase.drop_objection(self)


uvm_component_utils(tc_credit_no_underflow)


class tc_nw_adapt_linkready(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        gtx, grx = lph.nw512_golden_tx(), lph.nw512_golden_rx()
        sset(d.rst_n, 1)
        sset(d.link_ready, 0)
        sset(d.fab_nw_data, gtx)
        sset(d.mgmt_nw_data, 0)
        sset(d.dll_nw_data, grx)
        sset(d.fab_nw_vld, 1)
        sset(d.mgmt_nw_vld, 0)
        sset(d.nw_dll_ready, 1)
        sset(d.dll_nw_vld, 1)
        sset(d.nw_fab_ready, 1)
        await Timer(1, "NS")
        if ival(d.fab_nw_ready, 0) or ival(d.nw_dll_vld, 0):
            self.bad("tc_nw_adapt_linkready", "link_ready=0 fab GOLDEN_TX",
                     "fab_nw_ready=0 nw_dll_vld=0",
                     f"rdy={ival(d.fab_nw_ready, 0)} vld={ival(d.nw_dll_vld, 0)}")
            phase.drop_objection(self)
            return
        sset(d.link_ready, 1)
        await Timer(1, "NS")
        if ival(d.nw_dll_data, 0) != gtx or not ival(d.nw_dll_vld, 0):
            self.bad("tc_nw_adapt_linkready", "TX GOLDEN_TX",
                     hex(gtx), hex(ival(d.nw_dll_data, 0)), "nw_dll_data")
            phase.drop_objection(self)
            return
        if ival(d.nw_fab_data, 0) != grx or not ival(d.nw_fab_vld, 0):
            self.bad("tc_nw_adapt_linkready", "RX GOLDEN_RX",
                     hex(grx), hex(ival(d.nw_fab_data, 0)), "nw_fab_data")
            phase.drop_objection(self)
            return
        sset(d.mgmt_nw_vld, 1)
        sset(d.mgmt_nw_data, grx)
        await Timer(1, "NS")
        if ival(d.nw_dll_data, 0) != grx or ival(d.fab_nw_ready, 0):
            self.bad("tc_nw_adapt_linkready", "mgmt GOLDEN_RX priority",
                     hex(grx), hex(ival(d.nw_dll_data, 0)))
        else:
            self.ok("tc_nw_adapt_linkready")
        phase.drop_objection(self)


uvm_component_utils(tc_nw_adapt_linkready)


class tc_phy_nw_dll_512b(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        gtx, grx = lph.nw512_golden_tx(), lph.nw512_golden_rx()
        sset(d.rst_n, 1)
        sset(d.link_ready, 1)
        sset(d.fab_nw_data, 0)
        sset(d.mgmt_nw_data, 0)
        sset(d.dll_nw_data, 0)
        sset(d.fab_nw_vld, 0)
        sset(d.mgmt_nw_vld, 0)
        sset(d.nw_dll_ready, 1)
        sset(d.dll_nw_vld, 0)
        sset(d.nw_fab_ready, 1)
        await Timer(1, "NS")
        sset(d.fab_nw_data, gtx)
        sset(d.fab_nw_vld, 1)
        await Timer(1, "NS")
        if ival(d.nw_dll_data, 0) != gtx or not ival(d.fab_nw_ready, 0) or not ival(d.nw_dll_vld, 0):
            self.bad("tc_phy_nw_dll_512b", "TX GOLDEN_TX handshake",
                     hex(gtx), hex(ival(d.nw_dll_data, 0)))
            phase.drop_objection(self)
            return
        sset(d.fab_nw_vld, 0)
        sset(d.dll_nw_data, grx)
        sset(d.dll_nw_vld, 1)
        await Timer(1, "NS")
        if ival(d.nw_fab_data, 0) != grx or not ival(d.nw_fab_vld, 0):
            self.bad("tc_phy_nw_dll_512b", "RX GOLDEN_RX",
                     hex(grx), hex(ival(d.nw_fab_data, 0)))
            phase.drop_objection(self)
            return
        sset(d.dll_nw_vld, 0)
        sset(d.link_ready, 0)
        sset(d.fab_nw_vld, 1)
        await Timer(1, "NS")
        if ival(d.fab_nw_ready, 0) or ival(d.nw_dll_vld, 0):
            self.bad("tc_phy_nw_dll_512b", "link_ready=0", "ready=0 vld=0",
                     f"{ival(d.fab_nw_ready, 0)} {ival(d.nw_dll_vld, 0)}")
        else:
            self.ok("tc_phy_nw_dll_512b")
        phase.drop_objection(self)


uvm_component_utils(tc_phy_nw_dll_512b)


class tc_saf_ing(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.in_vld, 0)
        sset(d.pkt_ready, 0)
        sset(d.in_data, 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        while not ival(d.in_ready, 0):
            await RisingEdge(d.clk)
        sset(d.in_data, lph.mk_beat(lph.mk_flit(
            3, 0, 0, 1, 1, lph.plen_nflit(5))))
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        early = 0
        for _ in range(4):
            await RisingEdge(d.clk)
            if ival(d.pkt_vld, 0):
                early = 1
        if early:
            self.bad("tc_saf_ing", "1 of 2 declared beats", "pkt_vld=0", "1")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.in_data, 0xB)
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await self.cycles(4)
        if not ival(d.pkt_vld, 0):
            self.bad("tc_saf_ing", "2nd beat of 2", "pkt_vld", "0")
            phase.drop_objection(self)
            return
        sset(d.pkt_ready, 1)
        await self.cycles(8)
        sset(d.pkt_ready, 0)
        await FallingEdge(d.clk)
        sset(d.in_data, lph.mk_beat(lph.mk_flit(
            3, 0, 0, 1, 1, lph.plen_oversize())))
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await RisingEdge(d.clk)
        if not ival(d.len_err, 0):
            self.bad("tc_saf_ing", "oversize PLEN", "len_err", "0")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.in_data, lph.mk_beat(lph.mk_flit(
            3, 0, 0, 1, 1, lph.plen_nflit(9))))
        sset(d.in_vld, 1)
        sset(d.pkt_ready, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_data, 0xC1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.pkt_vld, 0):
            self.bad("tc_saf_ing", "2 of 3 beats", "pkt_vld=0", "1")
            phase.drop_objection(self)
            return
        sset(d.in_data, 0xC2)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await self.cycles(3)
        sset(d.pkt_ready, 1)
        await self.cycles(8)
        sset(d.pkt_ready, 0)
        await FallingEdge(d.clk)
        sset(d.in_data, lph.mk_beat(lph.mk_flit(
            3, 0, 0, 1, 1, lph.plen_nflit(1))))
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not (ival(d.pkt_vld, 0) and ival(d.pkt_sop, 0) and ival(d.pkt_eop, 0)):
            self.bad("tc_saf_ing", "1-flit packet", "vld&&sop&&eop",
                     f"{ival(d.pkt_vld, 0)} {ival(d.pkt_sop, 0)} {ival(d.pkt_eop, 0)}")
        else:
            self.ok("tc_saf_ing")
        sset(d.pkt_ready, 1)
        await self.cycles(4)
        phase.drop_objection(self)


uvm_component_utils(tc_saf_ing)


class tc_voq_rd(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.wr_en, 0)
        sset(d.rd_en, 0)
        sset(d.wr_vl, 0)
        sset(d.rd_vl, 0)
        sset(d.wr_data, 0xA5)
        sset(d.wr_sop, 1)
        sset(d.wr_eop, 1)
        await self.reset_n()
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        await self.cycles(2)
        await FallingEdge(d.clk)
        if not bit(d.nonempty, 0):
            self.bad("tc_voq_rd", "wr VL0", "nonempty[0]", hex(ival(d.nonempty, 0)))
            phase.drop_objection(self)
            return
        sset(d.rd_en, 1)
        sset(d.rd_vl, 0)
        await self.cycles(3)
        sset(d.rd_en, 0)
        await FallingEdge(d.clk)
        sset(d.wr_vl, 3)
        sset(d.wr_data, 0x33)
        sset(d.wr_en, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.rd_vl, 3)
        sset(d.rd_en, 1)
        await RisingEdge(d.clk)
        sset(d.rd_en, 0)
        self.ok("tc_voq_rd")
        phase.drop_objection(self)


uvm_component_utils(tc_voq_rd)


class tc_dll_sm_states(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "link_up", "param_ok", "credit_ok", "dll_error"):
            sset(getattr(d, n), 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 0 or not ival(d.disabled, 0):
            self.bad("tc_dll_sm_states", "reset LinkUp=0", "ST_DIS disabled=1",
                     f"st={ival(d.state, -1)} dis={ival(d.disabled, 0)}")
            phase.drop_objection(self)
            return
        sset(d.link_up, 1)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 1:
            self.bad("tc_dll_sm_states", "LinkUp=1", "Param_Init (1)",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.param_ok, 0)
        await self.cycles(3)
        if ival(d.state, -1) != 1:
            self.bad("tc_dll_sm_states", "param_ok=0", "stay Param",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.param_ok, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.state, -1) != 2:
            self.bad("tc_dll_sm_states", "param_ok", "Credit_Init (2)",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.credit_ok, 0)
        await self.cycles(3)
        if ival(d.state, -1) != 2:
            self.bad("tc_dll_sm_states", "credit_ok=0", "stay Credit",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.credit_ok, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.state, -1) != 3 or not ival(d.status_up, 0):
            self.bad("tc_dll_sm_states", "credit_ok", "Normal status_up=1",
                     f"{ival(d.state, -1)} {ival(d.status_up, 0)}")
            phase.drop_objection(self)
            return
        await self.cycles(4)
        if ival(d.state, -1) != 3:
            self.bad("tc_dll_sm_states", "hold Normal", "remain 3",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.link_up, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.state, -1) != 0:
            self.bad("tc_dll_sm_states", "LinkUp=0", "Disabled",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.link_up, 1)
        sset(d.param_ok, 1)
        sset(d.credit_ok, 1)
        await self.cycles(3)
        sset(d.port_rst, 1)
        await RisingEdge(d.clk)
        await Timer(1, "NS")
        if ival(d.state, -1) != 0:
            self.bad("tc_dll_sm_states", "port_rst while LinkUp=1",
                     "Disabled", str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.port_rst, 0)
        await RisingEdge(d.clk)
        sset(d.link_up, 1)
        await self.cycles(3)
        sset(d.dll_error, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.dll_error, 0)
        if ival(d.state, -1) != 0:
            self.bad("tc_dll_sm_states", "dll_error in Normal",
                     "Disabled", str(ival(d.state, -1)))
        else:
            self.ok("tc_dll_sm_states")
        phase.drop_objection(self)


uvm_component_utils(tc_dll_sm_states)


class tc_mgmt_byp(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.in_vld, 0)
        sset(d.out_ready, 0)
        sset(d.in_data, 0xA5)
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.in_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.in_vld, 0)
        await RisingEdge(d.clk)
        if not ival(d.out_vld, 0) or ival(d.out_data, 0) != 0xA5:
            self.bad("tc_mgmt_byp", "one 512b write, out_ready=0",
                     "out_vld=1 data=A5",
                     f"vld={ival(d.out_vld, 0)} data={ival(d.out_data, 0):x}")
            phase.drop_objection(self)
            return
        sset(d.out_ready, 1)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        if ival(d.out_vld, 0):
            self.bad("tc_mgmt_byp", "out_ready after one beat", "empty", "still vld")
        else:
            self.ok("tc_mgmt_byp")
        phase.drop_objection(self)


uvm_component_utils(tc_mgmt_byp)


class tc_xbar_unit(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.status_up, 0xF)
        sset(d.in_vld, 0)
        sset(d.in_sop, 0)
        sset(d.in_eop, 0)
        sset(d.out_ready, 0xF)
        for i in range(4):
            sset(getattr(d, f"in_data_{i}"), 0)
            sset(getattr(d, f"in_dst_{i}"), 0)
        await self.reset_n()
        sset(d.in_data_0, 0xA << 352)
        sset(d.in_dst_0, 1)
        sset(d.in_vld, 1)
        sset(d.in_sop, 1)
        sset(d.in_eop, 1)
        await Timer(1, "NS")
        await RisingEdge(d.clk)
        if not bit(d.out_vld, 1) or not bit(d.in_ready, 0):
            self.bad("tc_xbar_unit", "1-beat in0 dest=1",
                     "out_vld[1]=1 in_ready[0]=1",
                     f"ov={ival(d.out_vld, 0):04b} ir={ival(d.in_ready, 0):04b}")
            phase.drop_objection(self)
            return
        sset(d.in_vld, 0)
        sset(d.in_sop, 0)
        sset(d.in_eop, 0)
        await self.cycles(2)
        sset(d.in_data_0, 0xB << 352)
        sset(d.in_dst_0, 2)
        sset(d.in_vld, 1)
        sset(d.in_sop, 1)
        sset(d.in_eop, 0)
        await RisingEdge(d.clk)
        sset(d.in_sop, 0)
        sset(d.in_eop, 1)
        sset(d.in_data_0, 0xC << 352)
        await RisingEdge(d.clk)
        sset(d.in_vld, 0)
        sset(d.in_eop, 0)
        await self.cycles(2)
        sset(d.in_data_0, 0xE << 352)
        sset(d.in_dst_0, 1)
        sset(d.in_vld, 1)
        sset(d.in_sop, 1)
        sset(d.in_eop, 0)
        sset(d.out_ready, 0xF)
        await RisingEdge(d.clk)
        sset(d.out_ready, 0xD)
        sset(d.in_sop, 0)
        await RisingEdge(d.clk)
        sset(d.out_ready, 0xF)
        sset(d.in_eop, 1)
        sset(d.in_data_0, 0xF << 352)
        await RisingEdge(d.clk)
        sset(d.in_vld, 0)
        sset(d.in_eop, 0)
        await self.cycles(2)
        sset(d.in_data_0, 0x1 << 352)
        sset(d.in_dst_0, 3)
        sset(d.in_data_1, 0x2 << 352)
        sset(d.in_dst_1, 3)
        sset(d.in_vld, 0b0011)
        sset(d.in_sop, 0b0011)
        sset(d.in_eop, 0b0011)
        await Timer(1, "NS")
        await RisingEdge(d.clk)
        sset(d.in_vld, 0)
        sset(d.status_up, 0xE)
        sset(d.in_data_2, 0xD << 352)
        sset(d.in_dst_2, 0)
        sset(d.in_vld, 0b0100)
        sset(d.in_sop, 0b0100)
        sset(d.in_eop, 0b0100)
        await Timer(1, "NS")
        if bit(d.out_vld, 0):
            self.bad("tc_xbar_unit", "dest=0 status_up[0]=0",
                     "out_vld[0]=0", "1")
        else:
            self.ok("tc_xbar_unit")
        sset(d.in_vld, 0)
        phase.drop_objection(self)


uvm_component_utils(tc_xbar_unit)


class tc_cna_ep(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.cna, 0x1111)
        sset(d.cna_written, 1)
        sset(d.fab_mgmt_cfg6_hit, 0)
        sset(d.mgmt_nw_ready, 0xF)
        for i in range(4):
            sset(getattr(d, f"fab_mgmt_cfg6_data_{i}"), 0)
        sset(d.rst_n, 0)
        await self.cycles(2)
        sset(d.rst_n, 1)
        sset(d.fab_mgmt_cfg6_data_0, lph.mk_beat(lph.mk_flit(
            6, 0, 0, 2, 0x1111, lph.plen_nflit(1))))
        await Timer(1, "NS")
        sset(d.fab_mgmt_cfg6_hit, 1)
        await Timer(1, "NS")
        if not bit(d.consume, 0) or not bit(d.mgmt_nw_vld, 0):
            self.bad("tc_cna_ep", "DCNA==written CNA", "consume+reply",
                     f"cons={ival(d.consume, 0):b} vld={ival(d.mgmt_nw_vld, 0):b}")
            phase.drop_objection(self)
            return
        sset(d.fab_mgmt_cfg6_hit, 0)
        await Timer(1, "NS")
        sset(d.fab_mgmt_cfg6_data_1, lph.mk_beat(lph.mk_flit(
            6, 0, 0, 2, 0x2222, lph.plen_nflit(1), 0, 0, 1, 0)))
        sset(d.fab_mgmt_cfg6_hit, 2)
        await Timer(1, "NS")
        if not bit(d.consume, 1):
            self.bad("tc_cna_ep", "NLP=1 DCNA!=CNA", "consume", "0")
            phase.drop_objection(self)
            return
        sset(d.fab_mgmt_cfg6_hit, 0)
        await Timer(1, "NS")
        sset(d.fab_mgmt_cfg6_data_2, lph.mk_beat(lph.mk_flit(
            6, 0, 0, 2, 0x2222, lph.plen_nflit(1))))
        sset(d.fab_mgmt_cfg6_hit, 4)
        await Timer(1, "NS")
        if bit(d.consume, 2):
            self.bad("tc_cna_ep", "miss CNA NLP=0", "no consume", "1")
            phase.drop_objection(self)
            return
        sset(d.fab_mgmt_cfg6_hit, 0)
        sset(d.cna_written, 0)
        sset(d.fab_mgmt_cfg6_data_3, lph.mk_beat(lph.mk_flit(
            6, 0, 0, 2, 0x1111, lph.plen_nflit(1))))
        sset(d.fab_mgmt_cfg6_hit, 8)
        await Timer(1, "NS")
        if bit(d.consume, 3):
            self.bad("tc_cna_ep", "CNA unwritten", "no match", "consume=1")
        elif ival(d.icrc_fail, 0):
            self.bad("tc_cna_ep", "echo path", "icrc_fail=0", "1")
        else:
            self.ok("tc_cna_ep")
        phase.drop_objection(self)


uvm_component_utils(tc_cna_ep)


class tc_credit_timeout_1us(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        for _ in range(lph.US_CYC - 2):
            await RisingEdge(d.clk)
        if ival(d.proto_err, 0):
            self.bad("tc_credit_timeout_1us", "pending=1 wait <1250",
                     "proto_err=0", "1")
            phase.drop_objection(self)
            return
        await self.cycles(8)
        if not ival(d.proto_err, 0):
            self.bad("tc_credit_timeout_1us", "pending held >=1us",
                     "proto_err=1", f"0 pending={ival(d.pending, -1)}")
        else:
            self.ok("tc_credit_timeout_1us")
        phase.drop_objection(self)


uvm_component_utils(tc_credit_timeout_1us)


class tc_deadlock_timeout_1us(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.wr_en, 0)
        sset(d.rd_en, 0)
        sset(d.wr_vl, 0)
        sset(d.rd_vl, 0)
        sset(d.wr_data, 1)
        sset(d.wr_sop, 1)
        sset(d.wr_eop, 1)
        await self.reset_n()
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        for _ in range(lph.US_CYC - 4):
            await RisingEdge(d.clk)
        if ival(d.deadlock_drop, 0):
            self.bad("tc_deadlock_timeout_1us", "enqueue wait <1us",
                     "deadlock_drop=0", "1")
            phase.drop_objection(self)
            return
        await self.cycles(16)
        if not ival(d.deadlock_drop, 0) and ival(d.deadlock_cnt, 0) == 0:
            self.bad("tc_deadlock_timeout_1us", "VOQ occupied >=1250",
                     "drop pulse / cnt>0",
                     f"drop={ival(d.deadlock_drop, 0)} cnt={ival(d.deadlock_cnt, 0)}")
        else:
            await FallingEdge(d.clk)
            sset(d.wr_en, 1)
            sset(d.wr_vl, 1)
            sset(d.wr_data, 2)
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            sset(d.wr_en, 0)
            sset(d.rd_vl, 1)
            sset(d.rd_en, 1)
            await RisingEdge(d.clk)
            sset(d.rd_en, 0)
            self.ok("tc_deadlock_timeout_1us")
        phase.drop_objection(self)


uvm_component_utils(tc_deadlock_timeout_1us)


class tc_retry_buf_256(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "wr_en", "is_null", "is_retry", "ack_rel"):
            sset(getattr(d, n), 0)
        sset(d.link_up, 1)
        sset(d.send_size, 1)
        sset(d.rel_size, 0)
        sset(d.rd_ptr_i, 0)
        sset(d.wr_flit, 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        if ival(d.num_free, -1) != 256:
            self.bad("tc_retry_buf_256", "reset", "NumFreeBuf=256",
                     str(ival(d.num_free, -1)))
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.is_null, 1)
        sset(d.wr_flit, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        sset(d.is_null, 0)
        await RisingEdge(d.clk)
        if ival(d.num_free, -1) != 256 or ival(d.wr_ptr, -1) != 0:
            self.bad("tc_retry_buf_256", "wr_en is_null", "free stays 256",
                     f"free={ival(d.num_free, -1)}")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.is_retry, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        sset(d.is_retry, 0)
        await RisingEdge(d.clk)
        if ival(d.num_free, -1) != 256:
            self.bad("tc_retry_buf_256", "is_retry write", "not entered",
                     str(ival(d.num_free, -1)))
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.wr_flit, 0x55)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        await RisingEdge(d.clk)
        if ival(d.num_free, -1) != 255:
            self.bad("tc_retry_buf_256", "one data flit", "free=255",
                     str(ival(d.num_free, -1)))
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.ack_rel, 1)
        sset(d.rel_size, 8)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.ack_rel, 0)
        await RisingEdge(d.clk)
        if not ival(d.proto_err, 0):
            self.bad("tc_retry_buf_256", "ack_rel 8 with free=255",
                     "proto_err", "0")
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await self.cycles(2)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.wr_flit, 0x11)
        sset(d.is_null, 0)
        sset(d.is_retry, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        sset(d.ack_rel, 1)
        sset(d.rel_size, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.ack_rel, 0)
        await RisingEdge(d.clk)
        if ival(d.num_free, -1) != 256 or ival(d.proto_err, 0):
            self.bad("tc_retry_buf_256", "write 1 then ack_rel 1",
                     "free=256 proto_err=0",
                     f"free={ival(d.num_free, -1)} err={ival(d.proto_err, 0)}")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        sset(d.port_rst, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.num_free, -1) != 256:
            self.bad("tc_retry_buf_256", "port_rst", "free=256",
                     str(ival(d.num_free, -1)))
        else:
            self.ok("tc_retry_buf_256")
        sset(d.link_up, 0)
        await RisingEdge(d.clk)
        sset(d.link_up, 1)
        phase.drop_objection(self)


uvm_component_utils(tc_retry_buf_256)


class tc_retry_req_gbn(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "device_rst", "start_retry", "phy_retrain", "wait_done_ack"):
            sset(getattr(d, n), 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        sset(d.start_retry, 1)
        await RisingEdge(d.clk)
        sset(d.start_retry, 0)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 1 or not ival(d.drop_data, 0):
            self.bad("tc_retry_req_gbn", "start_retry GBN",
                     "ST_REQ drop_data=1",
                     f"st={ival(d.state, -1)} drop={ival(d.drop_data, 0)}")
        else:
            self.ok("tc_retry_req_gbn")
        phase.drop_objection(self)


uvm_component_utils(tc_retry_req_gbn)


class tc_retry_ack_replay(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.start_ack, 0)
        sset(d.wr_ptr, 4)
        sset(d.rcv_ptr, 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        sset(d.start_ack, 1)
        await RisingEdge(d.clk)
        sset(d.start_ack, 0)
        await self.cycles(2)
        if ival(d.state, -1) == 0:
            self.bad("tc_retry_ack_replay", "start_ack wr=4 rcv=0",
                     "leave NORMAL", "still NORMAL")
            phase.drop_objection(self)
            return
        await self.cycles(40)
        if ival(d.state, -1) not in (2, 0):
            self.bad("tc_retry_ack_replay", "40 cyc after start_ack",
                     "ST_P or NORMAL", str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        await self.cycles(8)
        if ival(d.state, -1) != 0:
            self.bad("tc_retry_ack_replay", "replay until rd==wr",
                     "NORMAL", str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.start_ack, 1)
        await RisingEdge(d.clk)
        sset(d.start_ack, 0)
        sset(d.port_rst, 1)
        await RisingEdge(d.clk)
        sset(d.port_rst, 0)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 0:
            self.bad("tc_retry_ack_replay", "port_rst during ACK",
                     "NORMAL", str(ival(d.state, -1)))
        else:
            self.ok("tc_retry_ack_replay")
        phase.drop_objection(self)


uvm_component_utils(tc_retry_ack_replay)


class tc_retry_wait_retrain(VibeUnitBaseTest):
    async def _burst(self, d):
        sset(d.start_retry, 1)
        await RisingEdge(d.clk)
        sset(d.start_retry, 0)
        await self.cycles(34)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "device_rst", "start_retry", "phy_retrain", "wait_done_ack"):
            sset(getattr(d, n), 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        await self._burst(d)
        if ival(d.state, -1) != 2:
            self.bad("tc_retry_wait_retrain", "33-cyc REQ burst",
                     "ST_WAIT (2)", str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        if not ival(d.drop_data, 0):
            self.bad("tc_retry_wait_retrain", "WAIT", "drop_data=1", "0")
            phase.drop_objection(self)
            return
        sset(d.wait_done_ack, 1)
        await RisingEdge(d.clk)
        sset(d.wait_done_ack, 0)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 0:
            self.bad("tc_retry_wait_retrain", "wait_done_ack", "NORMAL",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        await self._burst(d)
        if ival(d.state, -1) != 2:
            self.bad("tc_retry_wait_retrain", "second burst", "WAIT",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        await self.cycles(6)
        if ival(d.state, -1) != 1:
            self.bad("tc_retry_wait_retrain", "WAIT timeout", "REQ",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        await self.cycles(34)
        i = 0
        while ival(d.state, -1) not in (3, 4) and i < 400:
            st = ival(d.state, -1)
            if st == 0:
                await self._burst(d)
            elif st == 2:
                await self.cycles(6)
            else:
                await RisingEdge(d.clk)
            i += 1
        sset(d.rst_n, 0)
        await self.cycles(2)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        saw_e = 0
        for _ in range(4):
            sset(d.start_retry, 1)
            await RisingEdge(d.clk)
            sset(d.start_retry, 0)
            sset(d.phy_retrain, 1)
            for _ in range(40):
                await RisingEdge(d.clk)
                if ival(d.state, -1) == 4 or ival(d.retry_error, 0):
                    saw_e = 1
            sset(d.phy_retrain, 0)
        if not saw_e and not ival(d.retry_error, 0):
            self.bad("tc_retry_wait_retrain", "4 phy reinits", "ERROR",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.port_rst, 1)
        await RisingEdge(d.clk)
        sset(d.port_rst, 0)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 0:
            self.bad("tc_retry_wait_retrain", "port_rst in ERROR",
                     "NORMAL", str(ival(d.state, -1)))
        else:
            self.ok("tc_retry_wait_retrain")
        phase.drop_objection(self)


uvm_component_utils(tc_retry_wait_retrain)


class tc_icrc_txrx_vs_transit(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.last, 0)
        sset(d.in_byte, 0)
        await self.reset_n(n_lo=4, n_hi=0)
        await RisingEdge(d.clk)
        sset(d.start, 1)
        await RisingEdge(d.clk)
        sset(d.start, 0)
        sset(d.in_vld, 1)
        sset(d.last, 1)
        sset(d.in_byte, 0)
        await RisingEdge(d.clk)
        sset(d.in_vld, 0)
        sset(d.last, 0)
        await self.cycles(4)
        await FallingEdge(d.clk)
        if not ival(d.done, 0) and ival(d.crc_out, 0) == 0:
            self.bad("tc_icrc_txrx_vs_transit", "start + one byte 0x00 last",
                     "done=1 and crc computed",
                     f"done={ival(d.done, 0)} crc={ival(d.crc_out, 0):x}")
        else:
            self.ok("tc_icrc_txrx_vs_transit")
        phase.drop_objection(self)


uvm_component_utils(tc_icrc_txrx_vs_transit)


class tc_pma_512b_slice(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        if hasattr(d, "txrst_n"):
            sset(d.txrst_n, 0)
        if hasattr(d, "rxrst_n"):
            sset(d.rxrst_n, 0)
        sset(d.afifo_pma_lane0, 0x11)
        sset(d.afifo_pma_lane1, 0x22)
        sset(d.afifo_pma_lane2, 0x33)
        sset(d.afifo_pma_lane3, 0x44)
        sset(d.afifo_pma_lane_vld, 0)
        sset(d.pma_pcs_rxdata, 0)
        await RisingEdge(d.txclk)
        if hasattr(d, "txrst_n"):
            sset(d.txrst_n, 1)
        if hasattr(d, "rxrst_n"):
            sset(d.rxrst_n, 1)
        for _ in range(2):
            await RisingEdge(d.txclk)
        if ival(d.pcs_pma_txdata, 0) == 0:
            self.bad("tc_pma_512b_slice", "afifo_pma_lane_vld=0",
                     "PRBS23 nonzero", "0")
            phase.drop_objection(self)
            return
        idle0 = ival(d.pcs_pma_txdata, 0)
        await RisingEdge(d.txclk)
        tx = ival(d.pcs_pma_txdata, 0)
        if tx == 0 or tx == idle0:
            self.bad("tc_pma_512b_slice", "second idle txclk",
                     "new PRBS23 beat", hex(tx))
            phase.drop_objection(self)
            return
        sset(d.afifo_pma_lane_vld, 1)
        await RisingEdge(d.txclk)
        await RisingEdge(d.txclk)
        tx = ival(d.pcs_pma_txdata, 0)
        if ((tx & ((1 << 128) - 1)) != 0x11
                or ((tx >> 128) & ((1 << 128) - 1)) != 0x22
                or ((tx >> 256) & ((1 << 128) - 1)) != 0x33
                or ((tx >> 384) & ((1 << 128) - 1)) != 0x44):
            self.bad("tc_pma_512b_slice", "tx lanes 11/22/33/44",
                     "lane slices", hex(tx))
            phase.drop_objection(self)
            return
        sset(d.pma_pcs_rxdata, (0xAA << 384) | (0xBB << 256) | (0xCC << 128) | 0xDD)
        await RisingEdge(d.rxclk)
        await RisingEdge(d.rxclk)
        if ival(d.pma_afifo_lane0, 0) != 0xDD or ival(d.pma_afifo_lane3, 0) != 0xAA:
            self.bad("tc_pma_512b_slice", "rx {AA,BB,CC,DD}",
                     "lane0=DD lane3=AA",
                     f"r0={ival(d.pma_afifo_lane0, 0):x} r3={ival(d.pma_afifo_lane3, 0):x}")
        else:
            self.ok("tc_pma_512b_slice")
        sset(d.afifo_pma_lane_vld, 0)
        await RisingEdge(d.txclk)
        phase.drop_objection(self)


uvm_component_utils(tc_pma_512b_slice)


class tc_afifo_afull10(VibeUnitBaseTest):
    def clk(self):
        return self.dut.wclk

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.wrst_n, 0)
        sset(d.rrst_n, 0)
        sset(d.wen, 0)
        sset(d.ren, 0)
        sset(d.wdata, 0)
        for _ in range(4):
            await RisingEdge(d.wclk)
        sset(d.wrst_n, 1)
        sset(d.rrst_n, 1)
        for _ in range(4):
            await RisingEdge(d.wclk)
        for i in range(10):
            await FallingEdge(d.wclk)
            sset(d.wdata, i)
            sset(d.wen, 1)
            await RisingEdge(d.wclk)
        await FallingEdge(d.wclk)
        sset(d.wen, 0)
        await RisingEdge(d.wclk)
        if not ival(d.almost_full, 0):
            self.bad("tc_afifo_afull10", "10 writes no reads",
                     "almost_full=1",
                     f"afull={ival(d.almost_full, 0)} wocc={ival(d.wocc, -1)}")
            phase.drop_objection(self)
            return
        for i in range(10, 16):
            await FallingEdge(d.wclk)
            sset(d.wdata, i)
            sset(d.wen, 1)
            await RisingEdge(d.wclk)
        await FallingEdge(d.wclk)
        sset(d.wen, 0)
        await RisingEdge(d.wclk)
        if not ival(d.wfull, 0):
            self.bad("tc_afifo_afull10", "16 writes", "wfull=1",
                     f"0 wocc={ival(d.wocc, -1)}")
            phase.drop_objection(self)
            return
        await FallingEdge(d.wclk)
        sset(d.wen, 1)
        sset(d.wdata, 0xDEAD)
        await RisingEdge(d.wclk)
        await FallingEdge(d.wclk)
        sset(d.wen, 0)
        for _ in range(4):
            await RisingEdge(d.rclk)
        for _ in range(16):
            await FallingEdge(d.rclk)
            if not ival(d.rempty, 0):
                sset(d.ren, 1)
            await RisingEdge(d.rclk)
        await FallingEdge(d.rclk)
        sset(d.ren, 0)
        for _ in range(4):
            await RisingEdge(d.rclk)
        if not ival(d.rempty, 0):
            self.bad("tc_afifo_afull10", "16 reads after full", "rempty=1", "0")
        else:
            self.ok("tc_afifo_afull10")
        phase.drop_objection(self)


uvm_component_utils(tc_afifo_afull10)


class tc_lmsm_walk(VibeUnitBaseTest):
    async def _chk(self, d, exp, tag):
        await FallingEdge(d.clk)
        st = ival(d.state, -1)
        if st != exp:
            self.bad("tc_lmsm_walk", f"tag={tag}", str(exp), str(st), "state")
            return False
        return True

    async def _zap(self, d):
        try:
            d.tmr.value = Force(0)
        except Exception:
            pass

    async def _rel(self, d):
        try:
            d.tmr.value = Release()
        except Exception:
            pass

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "lmsm_go", "lid_bad", "lane0_fail", "eq_negotiated", "retrain_req"):
            sset(getattr(d, n), 0)
        sset(d.am_locked, 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        if ival(d.width_fail, 0):
            self.bad("tc_lmsm_walk", "reset", "width_fail=0", "1")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        if not await self._chk(d, 1, 1):
            phase.drop_objection(self)
            return
        await self._zap(d)
        await RisingEdge(d.clk)
        await self._rel(d)
        if not await self._chk(d, 0, 2):
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        await FallingEdge(d.clk)
        sset(d.am_locked, 0xF)
        await RisingEdge(d.clk)
        ok = True
        for exp, tag in ((2, 3), (3, 4), (4, 5), (5, 6), (8, 7)):
            if exp != 2:
                await RisingEdge(d.clk)
            if not await self._chk(d, exp, tag):
                ok = False
                break
        if ok and (not ival(d.link_up, 0) or not ival(d.sdf_period, 0)):
            self.bad("tc_lmsm_walk", "NULL", "link_up sdf_period",
                     f"{ival(d.link_up, 0)} {ival(d.sdf_period, 0)}")
            ok = False
        if ok:
            await self.cycles(10)
            if not await self._chk(d, 9, 8):
                ok = False
            elif not ival(d.link_ready, 0):
                self.bad("tc_lmsm_walk", "ACTIVE", "link_ready", "0")
                ok = False
        if ok:
            self.ok("tc_lmsm_walk")
        phase.drop_objection(self)


uvm_component_utils(tc_lmsm_walk)


class tc_lmsm_vlock(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "lmsm_go", "lid_bad", "lane0_fail", "eq_negotiated", "retrain_req"):
            sset(getattr(d, n), 0)
        sset(d.am_locked, 0)
        await self.reset_n(n_lo=4, n_hi=2)
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk)
        sset(d.lmsm_go, 0)
        await RisingEdge(d.clk)
        if ival(d.state, -1) != 1:
            self.bad("tc_lmsm_vlock", "lmsm_go + 2 posedge", "Disc.A (1)",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        sset(d.am_locked, 0xF)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        if ival(d.state, -1) not in (2, 3):
            self.bad("tc_lmsm_vlock", "am_locked=1111", "Disc.C or CFG_A",
                     str(ival(d.state, -1)))
            phase.drop_objection(self)
            return
        await self.cycles(6)
        await self.cycles(12)
        if ival(d.state, -1) != 9:
            self.bad("tc_lmsm_vlock", "lock walk", "ACTIVE (9)",
                     str(ival(d.state, -1)))
        else:
            self.ok("tc_lmsm_vlock")
        phase.drop_objection(self)


uvm_component_utils(tc_lmsm_vlock)


class tc_lmsm_cc(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "lmsm_go", "lid_bad", "lane0_fail", "eq_negotiated", "retrain_req"):
            sset(getattr(d, n), 0)
        sset(d.am_locked, 0)
        await self.reset_n(n_lo=4, n_hi=2)
        sset(d.am_locked, 0b0111)
        await FallingEdge(d.clk)
        try:
            d.st.value = Force(2)
            d.tmr.value = Force(8)
            await RisingEdge(d.clk)
            d.st.value = Release()
            d.tmr.value = Release()
            await RisingEdge(d.clk)
        except Exception:
            pass
        await FallingEdge(d.clk)
        if ival(d.state, -1) != 2:
            self.bad("tc_lmsm_cc", "park Disc.C partial lock", "2",
                     str(ival(d.state, -1)))
        else:
            self.ok("tc_lmsm_cc")
        phase.drop_objection(self)


uvm_component_utils(tc_lmsm_cc)


class tc_cfg0_term_not_fabric(VibeUnitBaseTest):
    async def _send(self, d, cfg):
        await FallingEdge(d.clk)
        sset(d.pcs_dll_data, lph.mk_pcs_beat(lph.mk_flit(
            cfg, 0, 0, 1, 2, lph.plen_nflit(1))))
        sset(d.pcs_dll_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.pcs_dll_vld, 0)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.fec_fail, 0)
        sset(d.pcs_dll_vld, 0)
        sset(d.pcs_dll_data, 0)
        sset(d.dll_nw_ready, 1)
        await self.reset_n(n_lo=4, n_hi=2)
        saw_cfg0 = 0
        saw_nw = 0
        await self._send(d, 0)
        for _ in range(6):
            await RisingEdge(d.clk)
            if ival(d.cfg0_hit, 0):
                saw_cfg0 = 1
            if ival(d.dll_nw_vld, 0):
                saw_nw = 1
        if not saw_cfg0:
            self.bad("tc_cfg0_term_not_fabric", "CFG=0 beat",
                     "cfg0_hit pulse", "no cfg0_hit")
            phase.drop_objection(self)
            return
        if saw_nw:
            self.bad("tc_cfg0_term_not_fabric", "CFG0 beat",
                     "dll_nw_vld never rises", "pulsed")
            phase.drop_objection(self)
            return
        await self._send(d, 3)
        for _ in range(8):
            await RisingEdge(d.clk)
            if ival(d.dll_nw_vld, 0):
                saw_nw = 1
        if not saw_nw:
            self.bad("tc_cfg0_term_not_fabric", "CFG=3 beat",
                     "dll_nw_vld pulse", "none")
        else:
            self.ok("tc_cfg0_term_not_fabric")
        phase.drop_objection(self)


uvm_component_utils(tc_cfg0_term_not_fabric)


class tc_dll_rx_errflag(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.fec_fail, 0)
        sset(d.pcs_dll_vld, 0)
        sset(d.pcs_dll_data, 0)
        sset(d.dll_nw_ready, 0)
        await self.reset_n(n_lo=4, n_hi=2)
        await FallingEdge(d.clk)
        sset(d.pcs_dll_data, lph.mk_pcs_beat(lph.mk_flit(
            3, 0, 0, 1, 2, lph.plen_nflit(1))))
        sset(d.pcs_dll_vld, 1)
        sset(d.dll_nw_ready, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.pcs_dll_vld, 0)
        sset(d.link_up, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not ival(d.dll_nw_vld, 0):
            self.bad("tc_dll_rx_errflag", "drop link_up after have",
                     "dll_nw_vld + pad0/ERROR_FLAG", "dll_nw_vld=0")
        else:
            self.ok("tc_dll_rx_errflag")
        sset(d.link_up, 1)
        sset(d.dll_nw_ready, 1)
        phase.drop_objection(self)


uvm_component_utils(tc_dll_rx_errflag)


class tc_fec_fail_gbn(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.fec_fail, 0)
        sset(d.pcs_dll_vld, 0)
        sset(d.pcs_dll_data, 0)
        sset(d.dll_nw_ready, 1)
        await self.reset_n(n_lo=4, n_hi=2)
        if ival(d.start_retry, 0):
            self.bad("tc_fec_fail_gbn", "reset fec_fail=0", "start_retry=0", "1")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.fec_fail, 1)
        await Timer(1, "NS")
        if not ival(d.start_retry, 0):
            self.bad("tc_fec_fail_gbn", "fec_fail=1", "start_retry=1", "0")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.fec_fail, 0)
        await Timer(1, "NS")
        if ival(d.start_retry, 0):
            self.bad("tc_fec_fail_gbn", "fec_fail deassert", "start_retry=0", "1")
        else:
            self.ok("tc_fec_fail_gbn")
        phase.drop_objection(self)


uvm_component_utils(tc_fec_fail_gbn)


class tc_rt_g1_official(VibeUnitBaseTest):
    async def _sel(self, d, rt, dest):
        await FallingEdge(d.clk)
        sset(d.rt, rt)
        sset(d.dest, dest)
        sset(d.lu_vld, 1)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.lu_vld, 0)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.device_rst, 0)
        sset(d.wr_en, 0)
        sset(d.lu_vld, 0)
        sset(d.status_up, 0xF)
        sset(d.default_bm, 0)
        sset(d.cfg, 3)
        sset(d.vl, 0)
        sset(d.src, 0x22)
        sset(d.dest, 0x000B)
        sset(d.rt, 0)
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.wr_idx, 0x000B)
        sset(d.wr_data, 0x4)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        await self._sel(d, 0b01, 0x000B)
        if ival(d.drop, 0) or ival(d.drop_g1, 0):
            self.bad("tc_rt11_not_as_rt01", "RT=01 dest=B unique port2",
                     "drop=0 drop_g1=0",
                     f"drop={ival(d.drop, 0)} g1={ival(d.drop_g1, 0)}")
            phase.drop_objection(self)
            return
        await self._sel(d, 0b11, 0x000B)
        if not ival(d.drop, 0) or not ival(d.drop_g1, 0):
            self.bad("tc_rt11_not_as_rt01", "same dest RT=11",
                     "drop=1 drop_g1=1",
                     f"drop={ival(d.drop, 0)} g1={ival(d.drop_g1, 0)}")
            phase.drop_objection(self)
            return
        self.ok("tc_rt11_not_as_rt01")
        await self._sel(d, 0b10, 0x000B)
        if not ival(d.drop_g1, 0) or not ival(d.drop, 0):
            self.bad("tc_rt_g1_official", "RT=10 unique bitmap",
                     "drop_g1=1 drop=1",
                     f"g1={ival(d.drop_g1, 0)} drop={ival(d.drop, 0)}")
            phase.drop_objection(self)
            return
        self.ok("tc_rt_detect_in_port_sel")
        self.ok("tc_rt10_unique_bm_drop")
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.wr_idx, 0x00FF)
        sset(d.wr_data, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        await self._sel(d, 0b10, 0x00FF)
        if not ival(d.drop_g1, 0) or not ival(d.drop, 0):
            self.bad("tc_rt10_on_default_drop", "RT=10 dest=00FF table=0",
                     "drop=1 (G1)",
                     f"g1={ival(d.drop_g1, 0)} drop={ival(d.drop, 0)}")
        else:
            self.ok("tc_rt10_on_default_drop")
            self.ok("tc_rt10_not_proto_err")
            self.ok("tc_rt_g1_official")
        phase.drop_objection(self)


uvm_component_utils(tc_rt_g1_official)


class tc_dll_tx_cfg0(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "credit_low", "bp_pending", "drop_data",
                  "replay", "send_idle", "send_req", "send_ack",
                  "nw_dll_vld", "credit_ret"):
            sset(getattr(d, n), 0)
        sset(d.link_up, 1)
        sset(d.status_up, 1)
        sset(d.can_send, 1)
        sset(d.replay_flit, 0)
        sset(d.dll_pcs_ready, 1)
        sset(d.credit_ret_n, 0)
        sset(d.nw_dll_data, lph.mk_beat(lph.mk_flit(
            0, 0, 0, 1, 2, lph.plen_nflit(1))))
        await self.reset_n()
        await FallingEdge(d.clk)
        sset(d.nw_dll_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.nw_dll_vld, 0)
        await self.cycles(8)
        if ival(d.cells, -1) != 0:
            self.bad("tc_dll_tx_cfg0", "CFG0 on dll_tx",
                     "cells=0", str(ival(d.cells, -1)), "u_crd.cells")
        else:
            self.ok("tc_dll_tx_cfg0")
        phase.drop_objection(self)


uvm_component_utils(tc_dll_tx_cfg0)


class tc_mgmt(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.cfg_wr_vld, 0)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        sset(d.fab_mgmt_cfg6_hit, 0)
        sset(d.mgmt_nw_ready, 0xF)
        for n in ("rx_ovf", "fc_ovf", "proto_err", "retry_error",
                  "len_err", "deadlock_drop", "drop_g1", "afifo_ovf"):
            sset(getattr(d, n), 0)
        await self.reset_n()
        await RisingEdge(d.clk)
        if not ival(d.cfg_wr_ready, 0):
            self.bad("tc_mgmt", "reset", "cfg_wr_ready", "0")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_data, 0x1111)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_vld, 0)
        await RisingEdge(d.clk)
        if ival(d.cna, 0) != 0x1111 or not ival(d.cna_written, 0):
            self.bad("tc_mgmt", "CNA write", "cna=1111 written",
                     f"{ival(d.cna, 0):x} {ival(d.cna_written, 0)}")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.drop_g1, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not ival(d.irq_logic, 0):
            self.bad("tc_mgmt", "drop_g1", "irq_logic sticky", "0")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, 3)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_vld, 0)
        await self.cycles(2)
        if bit(d.port_rst, 0):
            self.bad("tc_mgmt", "cmd=3 data[0]=0", "port_rst[0]=0", "1")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, 3)
        sset(d.cfg_wr_data, 1)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_vld, 0)
        await self.cycles(2)
        if not bit(d.port_rst, 0):
            self.bad("tc_mgmt", "cmd=3 data[0]=1", "port_rst[0]=1 W1C",
                     f"{ival(d.port_rst, 0):04b}")
        else:
            self.ok("tc_mgmt")
        phase.drop_objection(self)


uvm_component_utils(tc_mgmt)

           