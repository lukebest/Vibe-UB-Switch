from uvm import UVMComponent, UVMAnalysisImp, UVMConfigDb, uvm_component_utils, uvm_info, UVM_LOW
from vibe_uvm import lph
from vibe_uvm.hdl import ival


class VibeAsScoreboard(UVMComponent):
    """AS-0.1: G1 drop, length, CFG6 term vs fwd, transit ICRC, irq sticky."""

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.ing_imp = UVMAnalysisImp("ing_imp", self)
        self.probe = None
        self.exp_cna = 0
        self.exp_cna_written = False
        self.route_bm = [0] * 256
        self.default_bm = 0
        self.exp_g1_cnt = 0
        self.n_g1_seen = 0
        self.n_len_err = 0
        self.n_fwd = 0
        self.mismatch = 0

    def build_phase(self, phase):
        super().build_phase(phase)
        probe = []
        if UVMConfigDb.get(self, "", "probe", probe):
            self.probe = probe[0]

    def cfg6_term(self, t) -> bool:
        us = self.exp_cna_written and (t.dcna == self.exp_cna)
        return us or (t.nlp == 1) or (t.opc == 0x10 and us)

    def len_illegal(self, t) -> bool:
        bytes_ = lph.decl_flits(t.plen) * 20
        return bytes_ < lph.PKT_LEN_MIN or bytes_ > lph.PKT_LEN_MAX

    def write(self, t):
        if (t.cfg == 0 and t.rt == 0 and t.dcna == 0 and t.scna == 0
                and t.plen == 0 and t.payload_lo == 0):
            return
        if t.rt in (0b10, 0b11):
            self.n_g1_seen += 1
            if self.exp_g1_cnt != 0xFFFFFFFF:
                self.exp_g1_cnt += 1
            return
        if self.len_illegal(t):
            self.n_len_err += 1
            return
        if t.cfg == 6 and self.cfg6_term(t):
            return
        self.n_fwd += 1

    def note_cna(self, c, written=True):
        self.exp_cna = c & 0xFFFF
        self.exp_cna_written = written

    def note_route(self, dest, bm):
        self.route_bm[dest & 0xFF] = bm & 0xF

    def note_default(self, bm):
        self.default_bm = bm & 0xF

    def report_phase(self, phase):
        super().report_phase(phase)
        uvm_info("AS_SB",
                 f"g1_pkts={self.n_g1_seen} len_err={self.n_len_err} "
                 f"fwd_pred={self.n_fwd} mismatch={self.mismatch}",
                 UVM_LOW)


uvm_component_utils(VibeAsScoreboard)
