"""Top product-pin smoke — port of tc_top_smoke.sv. Do not weaken G1 irq check."""

from uvm import UVMTest, UVMConfigDb, uvm_component_utils, uvm_fatal
from cocotb.triggers import RisingEdge, FallingEdge
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset
from vibe_uvm.report import tb_pass, tb_fail


class tc_top_smoke(UVMTest):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None

    def build_phase(self, phase):
        super().build_phase(phase)
        dut = []
        if not UVMConfigDb.get(self, "", "dut", dut):
            uvm_fatal(self.get_type_name(), "dut")
        self.dut = dut[0]

    async def cfgw(self, cmd, idx, data):
        d = self.dut
        await FallingEdge(d.clk_fab)
        sset(d.cfg_wr_cmd, cmd)
        sset(d.cfg_wr_idx, idx)
        sset(d.cfg_wr_data, data)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk_fab)
        await FallingEdge(d.clk_fab)
        sset(d.cfg_wr_vld, 0)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.cfg_wr_vld, 0)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_idx, 0)
        sset(d.cfg_wr_data, 0)
        sset(d.prst, 0)
        sset(d.pdrst, 0)
        sset(d.plgo, 0)
        sset(d.p_ftv, 0)
        sset(d.p_frr, 1)
        sset(d.p_mv, 0)
        sset(d.p_fab_tx, 0)
        sset(d.p_mgmt, 0)
        for _ in range(8):
            await RisingEdge(d.clk_fab)
        sset(d.rst_n, 1)
        for _ in range(8):
            await RisingEdge(d.clk_fab)
        if not ival(d.cfg_wr_ready, 0):
            tb_fail("tc_top_smoke", "reset", "cfg_wr_ready=1", "0", "dut.cfg_wr_ready")
            phase.drop_objection(self)
            return
        if ival(d.irq_logic, 0):
            tb_fail("tc_top_smoke", "reset, idle PMA", "irq_logic=0", "1", "dut.irq_logic")
            phase.drop_objection(self)
            return
        await self.cfgw(0, 0, 1)
        if ival(d.dut.u_mgmt.cna, -1) != 1:
            tb_fail("tc_top_smoke", "cfg_wr CNA=1", "u_mgmt.cna=1",
                    "CNA not written", "dut.u_mgmt.cna")
            phase.drop_objection(self)
            return
        sset(d.u_peer.u_lmsm.am_locked, 0xF)
        sset(d.u_peer.u_lmsm.lid_bad, 0)
        sset(d.dut.g_port[0].u_port.u_lmsm.am_locked, 0xF)
        sset(d.dut.g_port[0].u_port.u_lmsm.lid_bad, 0)
        sset(d.dut.g_port[1].u_port.u_lmsm.am_locked, 0xF)
        sset(d.dut.g_port[1].u_port.u_lmsm.lid_bad, 0)
        await FallingEdge(d.clk_fab)
        sset(d.plgo, 1)
        await self.cfgw(5, 0, 0)
        await self.cfgw(5, 1, 0)
        await RisingEdge(d.clk_fab)
        sset(d.plgo, 0)
        for _ in range(64):
            if ival(d.u_peer.link_ready, 0) and ival(d.p_up, 0):
                break
            await RisingEdge(d.clk_fab)
        if not (ival(d.u_peer.link_ready, 0) and ival(d.p_up, 0)):
            tb_fail("tc_top_smoke", "peer lmsm_go + am_locked",
                    "peer link_ready && status_up", "peer did not reach ACTIVE",
                    "u_peer.u_lmsm")
            phase.drop_objection(self)
            return
        sset(d.u_peer.u_dll.u_crd.cells, 64)
        sset(d.dut.g_port[0].u_port.u_dll.u_crd.cells, 64)
        await RisingEdge(d.clk_fab)
        sset(d.u_peer.u_lmsm.st, 9)
        sset(d.dut.g_port[0].u_port.u_lmsm.st, 9)
        sset(d.dut.g_port[1].u_port.u_lmsm.st, 9)
        await RisingEdge(d.clk_fab)
        if not ival(d.dut.g_port[0].u_port.link_up, 0):
            tb_fail("tc_top_smoke", "DUT port0 lmsm_go + force ACTIVE",
                    "link_up=1 so DLL RX can deliver to fabric",
                    "link_up=0 — packet cannot be accepted",
                    "dut.g_port[0].u_port.link_up")
            phase.drop_objection(self)
            return
        beat = lph.mk_beat(lph.mk_flit(
            3, 0b10, 0, 0xA11A, 0xB22B, lph.plen_nflit(1), 0xC33C, 0x5A, 0, 0
        ))
        sset(d.p_fab_tx, beat)
        accepted = 0
        for _ in range(32):
            await FallingEdge(d.clk_fab)
            sset(d.p_ftv, 1)
            if ival(d.p_ftr, 0):
                await RisingEdge(d.clk_fab)
                accepted = 1
                sset(d.p_ftv, 0)
                break
            await RisingEdge(d.clk_fab)
        sset(d.p_ftv, 0)
        if not accepted:
            tb_fail("tc_top_smoke", "peer fab_nw RT=10 after LinkReady",
                    "peer fab_nw_ready handshake", "encoder did not accept packet",
                    "u_peer.u_nw / u_peer.u_dll.u_tx")
            phase.drop_objection(self)
            return
        saw_peer_tx = 0
        for _ in range(20000):
            await RisingEdge(d.clk_fab)
            if ival(d.ptx, 0):
                saw_peer_tx = 1
            if ival(d.irq_logic, 0):
                break
        if not saw_peer_tx:
            tb_fail("tc_top_smoke",
                    "peer accepted RT=10; watch peer pcs_pma_txdata → dut.pma_pcs_rxdata_0",
                    "peer pcs_pma_txdata nonzero (PMA encoded packet)",
                    "peer pcs_pma_txdata stayed 0", "u_peer.u_pma.pcs_pma_txdata")
        elif not ival(d.irq_logic, 0):
            tb_fail("tc_top_smoke",
                    "pma_pcs_rxdata_0 = peer pcs_pma_txdata (RT=10 LPH); wait 20000 clk_fab",
                    "irq_logic=1 (G1 at top pin)",
                    "irq_logic stayed 0",
                    "dut.irq_logic / dut.u_fab.drop_g1 / dut.u_mgmt")
        else:
            tb_pass("tc_top_smoke")
        phase.drop_objection(self)


uvm_component_utils(tc_top_smoke)
