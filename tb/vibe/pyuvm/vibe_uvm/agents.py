from uvm import (
    UVMAgent, UVMDriver, UVMMonitor, UVMSequencer, UVMAnalysisPort,
    UVMConfigDb, uvm_component_utils, uvm_fatal, UVM_ACTIVE,
)
from cocotb.triggers import RisingEdge, FallingEdge
from vibe_uvm.items import VibeCfgItem, VibePktItem, VibePmaBeat
from vibe_uvm.hdl import ival, sset


class VibeCfgDriver(UVMDriver):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.vif = None

    def build_phase(self, phase):
        super().build_phase(phase)
        vif = []
        if not UVMConfigDb.get(self, "", "cfg_vif", vif):
            uvm_fatal("CFGDRV", "no cfg_vif")
        self.vif = vif[0]

    async def run_phase(self, phase):
        self.vif.idle()
        while True:
            itemq = []
            await self.seq_item_port.get_next_item(itemq)
            t = itemq[0]
            await FallingEdge(self.vif.clk)
            sset(self.vif.cmd, t.cmd)
            sset(self.vif.idx, t.idx)
            sset(self.vif.data, t.data)
            sset(self.vif.vld, 1)
            await RisingEdge(self.vif.clk)
            while not ival(self.vif.ready, 0):
                await RisingEdge(self.vif.clk)
            await FallingEdge(self.vif.clk)
            sset(self.vif.vld, 0)
            for _ in range(3):
                await RisingEdge(self.vif.clk)
            self.seq_item_port.item_done()


uvm_component_utils(VibeCfgDriver)


class VibeCfgMonitor(UVMMonitor):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.vif = None
        self.ap = UVMAnalysisPort("ap", self)

    def build_phase(self, phase):
        super().build_phase(phase)
        vif = []
        if not UVMConfigDb.get(self, "", "cfg_vif", vif):
            uvm_fatal("CFGMON", "no cfg_vif")
        self.vif = vif[0]

    async def run_phase(self, phase):
        while True:
            await RisingEdge(self.vif.clk)
            if ival(self.vif.rst_n, 0) and ival(self.vif.vld, 0) and ival(self.vif.ready, 0):
                t = VibeCfgItem("cfg")
                t.cmd = ival(self.vif.cmd, 0)
                t.idx = ival(self.vif.idx, 0)
                t.data = ival(self.vif.data, 0)
                self.ap.write(t)


uvm_component_utils(VibeCfgMonitor)


class VibeCfgSequencer(UVMSequencer):
    def __init__(self, name, parent):
        super().__init__(name, parent)


uvm_component_utils(VibeCfgSequencer)


class VibeCfgAgent(UVMAgent):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.drv = None
        self.mon = None
        self.sqr = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.mon = VibeCfgMonitor.type_id.create("mon", self)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv = VibeCfgDriver.type_id.create("drv", self)
            self.sqr = VibeCfgSequencer.type_id.create("sqr", self)

    def connect_phase(self, phase):
        super().connect_phase(phase)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv.seq_item_port.connect(self.sqr.seq_item_export)


uvm_component_utils(VibeCfgAgent)


class VibeNwDriver(UVMDriver):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.vif = None

    def build_phase(self, phase):
        super().build_phase(phase)
        vif = []
        if not UVMConfigDb.get(self, "", "nw_vif", vif):
            uvm_fatal("NWDRV", "no nw_vif")
        self.vif = vif[0]

    async def drive_item(self, t):
        beats = t.pack_beats()
        p = t.port
        for beat in beats:
            await FallingEdge(self.vif.clk)
            while not self.vif.get_ready(p):
                await RisingEdge(self.vif.clk)
            self.vif.set_data(p, beat)
            self.vif.set_vld(p, 1)
            await RisingEdge(self.vif.clk)
        await FallingEdge(self.vif.clk)
        self.vif.set_vld(p, 0)

    async def run_phase(self, phase):
        self.vif.idle_master()
        while True:
            itemq = []
            await self.seq_item_port.get_next_item(itemq)
            await self.drive_item(itemq[0])
            self.seq_item_port.item_done()


uvm_component_utils(VibeNwDriver)


class VibeNwMonitor(UVMMonitor):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.vif = None
        self.ap = UVMAnalysisPort("ap", self)
        self.is_ingress = True

    def build_phase(self, phase):
        super().build_phase(phase)
        vif = []
        if not UVMConfigDb.get(self, "", "nw_vif", vif):
            uvm_fatal("NWMON", "no nw_vif")
        self.vif = vif[0]
        flag = []
        if UVMConfigDb.get(self, "", "is_ingress", flag):
            self.is_ingress = bool(flag[0])

    async def run_phase(self, phase):
        while True:
            await RisingEdge(self.vif.clk)
            if not ival(self.vif.rst_n, 0):
                continue
            for p in range(4):
                if self.vif.get_vld(p) and self.vif.get_ready(p):
                    t = VibePktItem("beat")
                    t.unpack_beat(self.vif.get_data(p), p)
                    self.ap.write(t)


uvm_component_utils(VibeNwMonitor)


class VibeNwSequencer(UVMSequencer):
    def __init__(self, name, parent):
        super().__init__(name, parent)


uvm_component_utils(VibeNwSequencer)


class VibeNwAgent(UVMAgent):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.drv = None
        self.mon = None
        self.sqr = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.mon = VibeNwMonitor.type_id.create("mon", self)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv = VibeNwDriver.type_id.create("drv", self)
            self.sqr = VibeNwSequencer.type_id.create("sqr", self)

    def connect_phase(self, phase):
        super().connect_phase(phase)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv.seq_item_port.connect(self.sqr.seq_item_export)


uvm_component_utils(VibeNwAgent)


class VibePmaDriver(UVMDriver):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.rx = None

    def build_phase(self, phase):
        super().build_phase(phase)
        rx = []
        if not UVMConfigDb.get(self, "", "pma_rx", rx):
            uvm_fatal("PMADRV", "no pma_rx")
        self.rx = rx[0]

    async def run_phase(self, phase):
        while True:
            itemq = []
            await self.seq_item_port.get_next_item(itemq)
            t = itemq[0]
            sset(self.rx[t.port], t.rxdata)
            self.seq_item_port.item_done()


uvm_component_utils(VibePmaDriver)


class VibePmaMonitor(UVMMonitor):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.tx = None
        self.clk = None
        self.ap = UVMAnalysisPort("ap", self)

    def build_phase(self, phase):
        super().build_phase(phase)
        tx = []
        clk = []
        if not UVMConfigDb.get(self, "", "pma_tx", tx):
            uvm_fatal("PMAMON", "no pma_tx")
        if not UVMConfigDb.get(self, "", "pma_clk", clk):
            uvm_fatal("PMAMON", "no pma_clk")
        self.tx = tx[0]
        self.clk = clk[0]

    async def run_phase(self, phase):
        while True:
            await RisingEdge(self.clk)
            for p, sig in enumerate(self.tx):
                val = ival(sig, 0)
                if val:
                    t = VibePmaBeat("tx")
                    t.port = p
                    t.txdata = val
                    self.ap.write(t)


uvm_component_utils(VibePmaMonitor)


class VibePmaSequencer(UVMSequencer):
    def __init__(self, name, parent):
        super().__init__(name, parent)


uvm_component_utils(VibePmaSequencer)


class VibePmaAgent(UVMAgent):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.drv = None
        self.mon = None
        self.sqr = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.mon = VibePmaMonitor.type_id.create("mon", self)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv = VibePmaDriver.type_id.create("drv", self)
            self.sqr = VibePmaSequencer.type_id.create("sqr", self)

    def connect_phase(self, phase):
        super().connect_phase(phase)
        if self.get_is_active() == UVM_ACTIVE:
            self.drv.seq_item_port.connect(self.sqr.seq_item_export)


uvm_component_utils(VibePmaAgent)
