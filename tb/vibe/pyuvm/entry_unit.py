import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from uvm import run_test, UVMConfigDb
from uvm.dpi.uvm_hdl import uvm_hdl
from vibe_uvm.tests import unit_leaf  # noqa: F401


@cocotb.test()
async def test_unit(dut):
    uvm_hdl.set_dut(dut)
    UVMConfigDb.set(None, "*", "dut", dut)
    clk = getattr(dut, "clk", None) or getattr(dut, "clk_fab", None)
    if clk is not None:
        cocotb.start_soon(Clock(clk, 2, units="ns").start())
    if hasattr(dut, "txclk"):
        cocotb.start_soon(Clock(dut.txclk, 4, units="ns").start())
    await Timer(1, "NS")
    await run_test(os.environ.get("UVM_TESTNAME", "tc_vl_rr"))
