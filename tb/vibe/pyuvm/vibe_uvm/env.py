from uvm import UVMEnv, UVMConfigDb, uvm_component_utils, uvm_fatal, UVM_PASSIVE
from vibe_uvm.agents import VibeCfgAgent, VibeNwAgent, VibePmaAgent
from vibe_uvm.scoreboard import VibeAsScoreboard


class VibeFabEnv(UVMEnv):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.cfg = None
        self.ing = None
        self.egr = None
        self.sb = None

    def build_phase(self, phase):
        super().build_phase(phase)
        UVMConfigDb.set(self, "egr", "is_active", UVM_PASSIVE)
        self.cfg = VibeCfgAgent.type_id.create("cfg", self)
        self.ing = VibeNwAgent.type_id.create("ing", self)
        self.egr = VibeNwAgent.type_id.create("egr", self)
        self.sb = VibeAsScoreboard.type_id.create("sb", self)
        UVMConfigDb.set(self, "ing.mon", "is_ingress", True)
        UVMConfigDb.set(self, "egr.mon", "is_ingress", False)
        for field, key in (
            ("cfg_vif", "cfg_vif"),
            ("ing_vif", "ing_vif"),
            ("egr_vif", "egr_vif"),
            ("probe", "probe"),
        ):
            box = []
            if not UVMConfigDb.get(self, "", field, box):
                uvm_fatal("ENV", field)
            if field == "cfg_vif":
                UVMConfigDb.set(self, "cfg.*", "cfg_vif", box[0])
            elif field == "ing_vif":
                UVMConfigDb.set(self, "ing.*", "nw_vif", box[0])
            elif field == "egr_vif":
                UVMConfigDb.set(self, "egr.*", "nw_vif", box[0])
                UVMConfigDb.set(self, "sb", "probe", box[0] if field == "probe" else box[0])
        probe = []
        UVMConfigDb.get(self, "", "probe", probe)
        UVMConfigDb.set(self, "sb", "probe", probe[0])

    def connect_phase(self, phase):
        super().connect_phase(phase)
        self.ing.mon.ap.connect(self.sb.ing_imp)


uvm_component_utils(VibeFabEnv)


class VibeSwitchEnv(UVMEnv):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.cfg = None
        self.pma = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.cfg = VibeCfgAgent.type_id.create("cfg", self)
        self.pma = VibePmaAgent.type_id.create("pma", self)
        cfg = []
        if not UVMConfigDb.get(self, "", "cfg_vif", cfg):
            uvm_fatal("SENV", "cfg_vif")
        UVMConfigDb.set(self, "cfg.*", "cfg_vif", cfg[0])
        for key in ("pma_rx", "pma_tx", "pma_clk"):
            box = []
            if UVMConfigDb.get(self, "", key, box):
                UVMConfigDb.set(self, "pma.*", key, box[0])


uvm_component_utils(VibeSwitchEnv)


class VibePortEnv(UVMEnv):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.pma = None

    def build_phase(self, phase):
        super().build_phase(phase)
        self.pma = VibePmaAgent.type_id.create("pma", self)
        for key in ("pma_rx", "pma_tx", "pma_clk"):
            box = []
            if UVMConfigDb.get(self, "", key, box):
                UVMConfigDb.set(self, "pma.*", key, box[0])


uvm_component_utils(VibePortEnv)
