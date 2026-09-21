import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from uvm import UVMTest, UVMConfigDb, uvm_component_utils, uvm_fatal
from vibe_uvm import lph
from vibe_uvm.env import VibeFabEnv
from vibe_uvm.hdl import ival, sset, bit
from vibe_uvm.report import tb_pass, tb_fail, tb_note
from vibe_uvm.vif import CfgVif, Nw4Vif, PselVif, CnaVif, ProbeVif


class VibeFabBaseTest(UVMTest):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.env = None
        self.dut = None
        self.cfg_vif = None
        self.ing = None
        self.egr = None
        self.psel = None
        self.cna = None
        self.probe = None
        self.clk = None
        self.rst_n = None
        self.pass_count = 0
        self.fail_count = 0
        self._mon_started = False

    def build_phase(self, phase):
        super().build_phase(phase)
        dut = []
        if not UVMConfigDb.get(self, "", "dut", dut):
            uvm_fatal(self.get_type_name(), "dut")
        self.dut = dut[0]
        self.clk = self.dut.clk
        self.rst_n = self.dut.rst_n
        self.cfg_vif = CfgVif(self.dut)
        self.ing = Nw4Vif(self.dut, "nw_fab_data", "nw_fab_vld", "nw_fab_ready")
        self.egr = Nw4Vif(self.dut, "fab_nw_data", "fab_nw_vld", "fab_nw_ready")
        self.psel = PselVif(self.dut)
        self.cna = CnaVif(self.dut)
        self.probe = ProbeVif(self.dut)
        UVMConfigDb.set(None, "*", "cfg_vif", self.cfg_vif)
        UVMConfigDb.set(None, "*", "ing_vif", self.ing)
        UVMConfigDb.set(None, "*", "egr_vif", self.egr)
        UVMConfigDb.set(None, "*", "probe", self.probe)
        self.env = VibeFabEnv.type_id.create("env", self)

    async def tb_cycles(self, n):
        for _ in range(n):
            await RisingEdge(self.clk)

    async def _probe_mon(self):
        while True:
            await RisingEdge(self.clk)
            if not ival(self.rst_n, 0):
                continue
            if ival(self.probe.drop_g1, 0):
                self.probe.saw_drop_g1 = 1
            self.probe.saw_len_err |= ival(self.probe.len_err, 0) or 0
            self.probe.saw_xin |= ival(self.probe.x_in_v, 0) or 0
            for p in range(4):
                if self.egr.get_vld(p) and self.egr.get_ready(p):
                    self.probe.saw_egr |= (1 << p)
                    self.probe.egr_cnt[p] += 1
                    beat = self.egr.get_data(p)
                    self.probe.egr_last[p] = beat
                    self.probe.last_rt_egr[p] = lph.lph_rt(lph.nw512_flit0(beat))

    async def tb_reset(self):
        if not self._mon_started:
            cocotb.start_soon(self._probe_mon())
            self._mon_started = True
        sset(self.rst_n, 0)
        self.cfg_vif.idle()
        self.ing.idle_master()
        self.egr.idle_slave_ready()
        sset(self.dut.status_up, 0xF)
        sset(self.cna.cna, 0)
        sset(self.cna.cna_written, 0)
        sset(self.cna.hit, 0)
        sset(self.cna.rready, 0xF)
        for p in range(4):
            sset(self.cna.data[p], 0)
        sset(self.dut.preload_req, 0)
        await self.tb_cycles(4)
        sset(self.rst_n, 1)
        await self.tb_cycles(4)
        self.probe.clr_mon()

    async def tb_cfg(self, cmd, idx, data):
        await FallingEdge(self.clk)
        sset(self.cfg_vif.cmd, cmd)
        sset(self.cfg_vif.idx, idx)
        sset(self.cfg_vif.data, data)
        sset(self.cfg_vif.vld, 1)
        await RisingEdge(self.clk)
        while not ival(self.cfg_vif.ready, 0):
            await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        sset(self.cfg_vif.vld, 0)
        await self.tb_cycles(3)
        if cmd == lph.CMD_CNA:
            self.env.sb.note_cna(data & 0xFFFF, True)
        if cmd == lph.CMD_ROUTE:
            self.env.sb.note_route(idx, data & 0xF)
        if cmd == lph.CMD_DEFAULT:
            self.env.sb.note_default(data & 0xF)
        if cmd == lph.CMD_DEVRST:
            self.env.sb.note_cna(0, False)

    async def tb_wr_route(self, dest, bm):
        await self.tb_cfg(lph.CMD_ROUTE, dest, bm & 0xF)

    async def tb_inject(self, port, beat0, extra_beats):
        n = extra_beats if extra_beats >= 1 else 1
        for b in range(n):
            await FallingEdge(self.clk)
            while not self.ing.get_ready(port):
                await RisingEdge(self.clk)
            beat = beat0 if b == 0 else (beat0 & ((1 << 352) - 1))
            self.ing.set_data(port, beat)
            self.ing.set_vld(port, 1)
            await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        self.ing.set_vld(port, 0)

    async def tb_inject_hdr(self, port, cfg, rt, vl, scna, dcna, plen, nlp=0, opc=0):
        fl = lph.mk_flit(cfg, rt, vl, scna, dcna, plen, 0, 0, nlp, opc)
        await self.tb_inject(port, lph.mk_beat(fl), lph.decl_beats(plen))

    def tb_hold_egr(self, hold):
        self.egr.set_ready_all(0 if hold else 0xF)

    async def tb_wait_egr(self, timeout):
        t = 0
        while t < timeout and not ival(self.dut.fab_nw_vld, 0):
            await RisingEdge(self.clk)
            t += 1

    async def tb_expect_no_egr(self, timeout):
        await self.tb_cycles(timeout)

    async def tb_preload_cnt(self, val):
        sset(self.dut.preload_val, val)
        sset(self.dut.preload_req, 1)
        await RisingEdge(self.clk)
        # Verilator: deposit the fabric counter (no force).
        try:
            sset(self.dut.u_fab.rt_shortest_unimpl, val)
        except Exception:
            pass
        while not ival(self.dut.preload_done, 0):
            await RisingEdge(self.clk)
        sset(self.dut.preload_req, 0)
        await RisingEdge(self.clk)

    def ok(self, name):
        self.pass_count += 1
        tb_pass(name)

    def bad(self, name, stim, exp, act, hier):
        self.fail_count += 1
        tb_fail(name, stim, exp, act, hier)

    async def expect_drop_only(self, name, cnt_before):
        self.tb_hold_egr(False)
        await self.tb_expect_no_egr(20)
        cnt = ival(self.probe.rt_shortest_unimpl, 0)
        if self.probe.saw_egr:
            self.bad(name,
                     "inject RT=1x 2-beat pkt dest=1 vl=0",
                     "no egress beat; packet dropped (not shortest-path / not RT=00)",
                     "saw_egr != 0 (forwarded)",
                     "u_fab.x_in_v / fab_nw_vld / saw_egr")
        elif cnt_before != 0xFFFFFFFF and cnt != (cnt_before + 1):
            self.bad(name,
                     "inject RT=1x packet",
                     "drop AND rt_shortest_unimpl += 1 (AS-0.1 G1)",
                     f"cnt before={cnt_before:x} after={cnt:x}",
                     "u_fab.rt_shortest_unimpl / g1_evt")
        else:
            self.ok(name)

    async def psel_reset(self):
        sset(self.psel.rst_n, 0)
        sset(self.psel.device_rst, 0)
        sset(self.psel.status_up, 0xF)
        sset(self.psel.default_bm, 0)
        sset(self.psel.rt, 0)
        sset(self.psel.sel_vld, 0)
        sset(self.psel.cfg, 3)
        sset(self.psel.vl, 0)
        sset(self.psel.src, 0)
        sset(self.psel.dest, 0)
        sset(self.psel.wr_en, 0)
        sset(self.psel.wr_idx, 0)
        sset(self.psel.wr_data, 0)
        await self.tb_cycles(3)
        sset(self.psel.rst_n, 1)
        await self.tb_cycles(2)

    async def psel_wr_route(self, dest, bm):
        await FallingEdge(self.clk)
        sset(self.psel.wr_en, 1)
        sset(self.psel.wr_idx, dest)
        sset(self.psel.wr_data, bm & 0xF)
        await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        sset(self.psel.wr_en, 0)
        await self.tb_cycles(1)

    async def psel_select(self, rt, vl, src, dest):
        await FallingEdge(self.clk)
        sset(self.psel.rt, rt)
        sset(self.psel.vl, vl)
        sset(self.psel.src, src)
        sset(self.psel.dest, dest)
        sset(self.psel.sel_vld, 1)
        await RisingEdge(self.clk)
        await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        sset(self.psel.sel_vld, 0)
        await RisingEdge(self.clk)

    def report_phase(self, phase):
        super().report_phase(phase)
        print(f"SUITE pass={self.pass_count} fail={self.fail_count}", flush=True)
        print("SUITE_RESULT PASS" if self.fail_count == 0 else "SUITE_RESULT FAIL", flush=True)


uvm_component_utils(VibeFabBaseTest)
