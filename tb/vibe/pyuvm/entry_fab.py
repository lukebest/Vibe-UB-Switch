import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from uvm import run_test, UVMConfigDb
from uvm.dpi.uvm_hdl import uvm_hdl
from vibe_uvm.tests import fab_tests  # noqa: F401


@cocotb.test()
async def test_fab(dut):
    uvm_hdl.set_dut(dut)
    UVMConfigDb.set(None, "*", "dut", dut)
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())
    await Timer(1, "NS")
    name = os.environ.get("UVM_TESTNAME", "tc_suite_all")
    await run_test(name)
