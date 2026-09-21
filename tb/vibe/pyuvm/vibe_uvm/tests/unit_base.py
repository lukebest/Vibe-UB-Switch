from uvm import UVMTest, UVMConfigDb, uvm_component_utils, uvm_fatal
from cocotb.triggers import RisingEdge, FallingEdge
from vibe_uvm.hdl import ival, sset
from vibe_uvm.report import tb_pass, tb_fail


class VibeUnitBaseTest(UVMTest):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.dut = None
        self.fail_n = 0

    def build_phase(self, phase):
        super().build_phase(phase)
        dut = []
        if not UVMConfigDb.get(self, "", "dut", dut):
            uvm_fatal(self.get_type_name(), "dut")
        self.dut = dut[0]

    def clk(self):
        d = self.dut
        return getattr(d, "clk", getattr(d, "clk_fab", None))

    async def cycles(self, n):
        c = self.clk()
        for _ in range(n):
            await RisingEdge(c)

    async def reset_n(self, sig="rst_n", n_lo=3, n_hi=2):
        sset(getattr(self.dut, sig), 0)
        await self.cycles(n_lo)
        sset(getattr(self.dut, sig), 1)
        await self.cycles(n_hi)

    def ok(self, name):
        tb_pass(name)

    def bad(self, name, stim, exp, act, hier="dut"):
        self.fail_n += 1
        tb_fail(name, stim, exp, act, hier)

    def finish_ok(self, name):
        if not self.fail_n:
            self.ok(name)


uvm_component_utils(VibeUnitBaseTest)
