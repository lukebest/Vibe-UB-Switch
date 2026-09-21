from uvm import UVMSequence, uvm_object_utils
from vibe_uvm.items import VibeCfgItem, VibePktItem


class VibeCfgWriteSeq(UVMSequence):
    def __init__(self, name="cfg_wr"):
        super().__init__(name)
        self.cmd = 0
        self.idx = 0
        self.data = 0

    async def body(self):
        t = VibeCfgItem("t")
        await self.start_item(t)
        t.cmd = self.cmd
        t.idx = self.idx
        t.data = self.data
        await self.finish_item(t)


uvm_object_utils(VibeCfgWriteSeq)


class VibePktSeq(UVMSequence):
    def __init__(self, name="pkt"):
        super().__init__(name)
        self.tmpl = VibePktItem("tmpl")

    async def body(self):
        t = VibePktItem("t")
        t.port = self.tmpl.port
        t.cfg = self.tmpl.cfg
        t.rt = self.tmpl.rt
        t.vl = self.tmpl.vl
        t.scna = self.tmpl.scna
        t.dcna = self.tmpl.dcna
        t.plen = self.tmpl.plen
        t.cci = self.tmpl.cci
        t.lbf = self.tmpl.lbf
        t.nlp = self.tmpl.nlp
        t.opc = self.tmpl.opc
        t.payload_lo = self.tmpl.payload_lo
        t.extra_beats = self.tmpl.extra_beats
        await self.start_item(t)
        await self.finish_item(t)


uvm_object_utils(VibePktSeq)
