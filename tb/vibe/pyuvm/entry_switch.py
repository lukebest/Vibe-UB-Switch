import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from uvm import run_test, UVMConfigDb
from uvm.dpi.uvm_hdl import uvm_hdl
from vibe_uvm.tests import switch_tests  # noqa: F401


@cocotb.test()
async def test_switch(dut):
    uvm_hdl.set_dut(dut)
    UVMConfigDb.set(None, "*", "dut", dut)
    cocotb.start_soon(Clock(dut.clk_fab, 2, units="ns").start())
    for name in ("txclk_0", "txclk_1", "txclk_2", "txclk_3"):
        cocotb.start_soon(Clock(getattr(dut, name), 4, units="ns").start())
    await Timer(1, "NS")
    await run_test(os.environ.get("UVM_TESTNAME", "tc_top_smoke"))
