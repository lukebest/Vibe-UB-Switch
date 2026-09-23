import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
from uvm import run_test, UVMConfigDb
from uvm.dpi.uvm_hdl import uvm_hdl
from vibe_uvm.tests import unit_leaf  # noqa: F401
from vibe_uvm.tests import unit_more  # noqa: F401
from vibe_uvm.tests import unit_pcs  # noqa: F401
from vibe_uvm.tests import unit_afifo  # noqa: F401
from vibe_uvm.tests import unit_sync2  # noqa: F401
from vibe_uvm.tests import unit_rst_sync  # noqa: F401
from vibe_uvm.tests import unit_gear_128_160  # noqa: F401


@cocotb.test()
async def test_unit(dut):
    uvm_hdl.set_dut(dut)
    UVMConfigDb.set(None, "*", "dut", dut)
    clk = getattr(dut, "clk", None) or getattr(dut, "clk_fab", None)
    if clk is not None:
        cocotb.start_soon(Clock(clk, 2, units="ns").start())
    # PMA-only (no clk): 922 MHz product period ≈ 1085 ps.
    # Chain / port (has clk): 4 ns tx/rx matching Icarus always #2.
    pma_only = clk is None
    for name in ("txclk", "rxclk"):
        if hasattr(dut, name):
            if pma_only:
                # Icarus #(1085/2) is integer 542 ps → 1084 ps period.
                cocotb.start_soon(Clock(getattr(dut, name), 1084, units="ps").start())
            else:
                cocotb.start_soon(Clock(getattr(dut, name), 4, units="ns").start())
    if hasattr(dut, "wclk"):
        cocotb.start_soon(Clock(dut.wclk, 2, units="ns").start())
    if hasattr(dut, "rclk"):
        # Icarus tc_afifo_afull10: always #2 rclk → 4 ns period.
        cocotb.start_soon(Clock(dut.rclk, 4, units="ns").start())
    await Timer(1, "NS")
    await run_test(os.environ.get("UVM_TESTNAME", "tc_vl_rr"))
