from uvm import UVMSequenceItem, uvm_object_utils
from vibe_uvm import lph


class VibeCfgItem(UVMSequenceItem):
    def __init__(self, name="cfg"):
        super().__init__(name)
        self.cmd = 0
        self.idx = 0
        self.data = 0


uvm_object_utils(VibeCfgItem)


class VibePktItem(UVMSequenceItem):
    def __init__(self, name="pkt"):
        super().__init__(name)
        self.port = 0
        self.cfg = 0
        self.rt = 0
        self.vl = 0
        self.scna = 0
        self.dcna = 0
        self.plen = lph.plen_nflit(5)
        self.cci = 0
        self.lbf = 0
        self.nlp = 0
        self.opc = 0
        self.payload_lo = 0
        self.extra_beats = 0

    def mk_flit(self) -> int:
        return lph.mk_flit(
            self.cfg, self.rt, self.vl, self.scna, self.dcna,
            self.plen, self.cci, self.lbf, self.nlp, self.opc,
        )

    def sop_beat(self) -> int:
        return lph.mk_beat(self.mk_flit(), self.payload_lo)

    def decl_beats(self) -> int:
        return lph.decl_beats(self.plen)

    def pack_beats(self):
        n = self.extra_beats if self.extra_beats > 0 else self.decl_beats()
        if n < 1:
            n = 1
        beats = []
        for b in range(n):
            beats.append(self.sop_beat() if b == 0 else (self.payload_lo & ((1 << 352) - 1)))
        return beats

    def unpack_beat(self, beat: int, port: int = 0):
        self.port = port
        self.payload_lo = beat & ((1 << 352) - 1)
        f = lph.nw512_flit0(beat)
        self.cfg = lph.lph_cfg(f)
        self.rt = lph.lph_rt(f)
        self.vl = lph.lph_vl(f)
        self.scna = lph.nth_scna(f)
        self.dcna = lph.nth_dcna(f)
        self.plen = lph.lph_plength(f)
        self.cci = lph.nth_cci(f)
        self.lbf = lph.nth_lbf(f)
        self.nlp = lph.nth_nlp(f)
        self.opc = lph.nth_opc(f)
        return self


uvm_object_utils(VibePktItem)


class VibePmaBeat(UVMSequenceItem):
    def __init__(self, name="pma"):
        super().__init__(name)
        self.port = 0
        self.rxdata = 0
        self.txdata = 0


uvm_object_utils(VibePmaBeat)
