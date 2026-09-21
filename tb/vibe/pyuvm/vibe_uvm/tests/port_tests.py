"""Port PHY TCs — tc_port_smoke / tc_nw_pkt_to_pma_tx / tc_nw_pkt_pma_loopback."""

from uvm import UVMTest, UVMConfigDb, uvm_component_utils, uvm_fatal
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.handle import Force
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.report import tb_pass, tb_fail


class VibePortBase(UVMTest):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None

    def build_phase(self, phase):
        super().build_phase(phase)
        dut = []
        if not UVMConfigDb.get(self, "", "dut", dut):
            uvm_fatal(self.get_type_name(), "dut")
        self.dut = dut[0]

    async def bringup_link(self):
        d = self.dut
        sset(d.loopback, 1)
        sset(d.rst_n, 0)
        sset(d.port_rst, 0)
        sset(d.device_rst, 0)
        sset(d.lmsm_go, 0)
        sset(d.fab_nw_vld, 0)
        sset(d.nw_fab_ready, 1)
        sset(d.mgmt_nw_vld, 0)
        sset(d.fab_nw_data, 0)
        sset(d.mgmt_nw_data, 0)
        for _ in range(8):
            await RisingEdge(d.clk_fab)
        sset(d.rst_n, 1)
        for _ in range(8):
            await RisingEdge(d.clk_fab)
        hier(d, "u_p.u_lmsm.am_locked").value = Force(0xF)
        hier(d, "u_p.u_lmsm.lid_bad").value = Force(0)
        await FallingEdge(d.clk_fab)
        sset(d.lmsm_go, 1)
        await RisingEdge(d.clk_fab)
        sset(d.lmsm_go, 0)
        for _ in range(64):
            if ival(d.u_p.link_ready, 0) and ival(d.status_up, 0):
                break
            await RisingEdge(d.clk_fab)
        if not (ival(d.u_p.link_ready, 0) and ival(d.status_up, 0)):
            return False
        hier(d, "u_p.u_dll.u_crd.cells").value = Force(64)
        await RisingEdge(d.clk_fab)
        hier(d, "u_p.u_lmsm.st").value = Force(9)
        await RisingEdge(d.clk_fab)
        return True

    async def accept_nw(self, beat, timeout=32) -> bool:
        d = self.dut
        sset(d.fab_nw_data, beat)
        for _ in range(timeout):
            await FallingEdge(d.clk_fab)
            sset(d.fab_nw_vld, 1)
            if ival(d.fab_nw_ready, 0):
                await RisingEdge(d.clk_fab)
                sset(d.fab_nw_vld, 0)
                return True
            await RisingEdge(d.clk_fab)
        sset(d.fab_nw_vld, 0)
        return False


class tc_port_smoke(VibePortBase):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        if not await self.bringup_link():
            tb_fail("tc_port_smoke", "lmsm_go + force am_locked=1111 lid_bad=0",
                    "link_ready=1 status_up=1 (TX and RX domains up)",
                    "LMSM/DLL did not reach ACTIVE/NRM", "u_p.u_lmsm / u_p.u_dll.u_sm")
            phase.drop_objection(self)
            return
        golden = lph.nw512_golden_tx()
        accepted = await self.accept_nw(golden)
        if not accepted:
            tb_fail("tc_port_smoke", "fab_nw_vld GOLDEN_TX after LinkReady+cells=64",
                    "fab_nw_ready handshake (packet accepted)",
                    "not accepted", "u_p.u_nw.fab_nw_ready")
            phase.drop_objection(self)
            return
        dll = ival(d.u_p.nw_dll_data, 0)
        if dll != golden:
            tb_fail("tc_port_smoke", "TX NW→DLL accepted beat GOLDEN_TX",
                    f"GOLDEN {golden:x}", f"{dll:x}", "u_p.nw_dll_data")
            phase.drop_objection(self)
            return
        if lph.nw512_flit0(dll) != lph.nw512_flit0(golden):
            tb_fail("tc_port_smoke", "TX SOP LPH GOLDEN[511:352] vs DUT[511:352]",
                    hex(lph.nw512_flit0(golden)), hex(lph.nw512_flit0(dll)),
                    "u_p.nw_dll_data[511:352]")
            phase.drop_objection(self)
            return
        await self.accept_nw(lph.nw512_golden_tx_b2())
        saw_tx = 0
        saw_rx = 0
        last_rx = 0
        for _ in range(20000):
            await RisingEdge(d.clk_fab)
            if ival(d.pcs_pma_txdata, 0):
                saw_tx = 1
            if ival(d.nw_fab_vld, 0):
                saw_rx = 1
                last_rx = ival(d.nw_fab_data, 0)
                break
        if not saw_tx:
            tb_fail("tc_port_smoke", "watch pcs_pma_txdata after GOLDEN TX",
                    "pcs_pma_txdata nonzero", "stayed 0", "u_p.u_pma")
        elif not saw_rx:
            tb_fail("tc_port_smoke", "PMA loopback GOLDEN_TX",
                    "nw_fab_vld recover GOLDEN", "nw_fab_vld=0", "u_p.nw_fab_vld")
        elif last_rx != golden:
            tb_fail("tc_port_smoke", "RX after PMA loopback",
                    f"GOLDEN {golden:x}", f"{last_rx:x}", "u_p.nw_fab_data")
        else:
            tb_pass("tc_port_smoke")
        phase.drop_objection(self)


uvm_component_utils(tc_port_smoke)


class tc_nw_pkt_to_pma_tx(VibePortBase):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        if not await self.bringup_link():
            tb_fail("tc_nw_pkt_to_pma_tx", "link bring-up", "link_ready", "0", "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        golden = lph.nw512_golden_tx()
        if not await self.accept_nw(golden):
            tb_fail("tc_nw_pkt_to_pma_tx", "GOLDEN_TX after LinkReady",
                    "accepted", "not accepted", "fab_nw_ready")
            phase.drop_objection(self)
            return
        await self.accept_nw(lph.nw512_golden_tx_b2())
        saw = 0
        for _ in range(20000):
            await RisingEdge(d.txclk)
            if ival(d.pcs_pma_txdata, 0):
                saw = 1
                break
        if not saw:
            tb_fail("tc_nw_pkt_to_pma_tx", "legal NW/LPH on NW data[511:0]",
                    "pcs_pma_txdata[511:0] nonzero (lane pack)",
                    "stayed 0", "u_p.pcs_pma_txdata")
        else:
            tb_pass("tc_nw_pkt_to_pma_tx")
        phase.drop_objection(self)


uvm_component_utils(tc_nw_pkt_to_pma_tx)


class tc_nw_pkt_pma_loopback(VibePortBase):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        if not await self.bringup_link():
            tb_fail("tc_nw_pkt_pma_loopback", "link bring-up", "link_ready", "0", "u_p.u_lmsm")
            phase.drop_objection(self)
            return
        npkt = 100
        rx_n = 0
        for n in range(npkt):
            sop = lph.nw512_golden_tx_n(n)
            b2 = lph.nw512_golden_tx_b2()
            if not await self.accept_nw(sop):
                tb_fail("tc_nw_pkt_pma_loopback", f"packet {n} SOP",
                        "fab_nw_ready accept", "timeout", "u_p.u_nw")
                phase.drop_objection(self)
                return
            await self.accept_nw(b2)
            hit = False
            for _ in range(4096):
                await RisingEdge(d.clk_fab)
                if ival(d.nw_fab_vld, 0):
                    got = ival(d.nw_fab_data, 0)
                    if got != sop:
                        tb_fail("tc_nw_pkt_pma_loopback", f"packet {n} RX SOP",
                                f"{sop:x}", f"{got:x}", "u_p.nw_fab_data")
                        phase.drop_objection(self)
                        return
                    hit = True
                    rx_n += 1
                    break
            if not hit:
                tb_fail("tc_nw_pkt_pma_loopback", f"packet {n} wait RX",
                        "nw_fab_vld recover SOP", "timeout", "u_p.nw_fab_vld")
                phase.drop_objection(self)
                return
        tb_pass(f"tc_nw_pkt_pma_loopback ({rx_n}/{npkt})")
        tb_pass("tc_nw_pkt_pma_loopback")
        phase.drop_objection(self)


uvm_component_utils(tc_nw_pkt_pma_loopback)
