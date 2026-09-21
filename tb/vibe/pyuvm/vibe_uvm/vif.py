"""DUT-handle vif wrappers. No SV virtual interface — cocotb handles HDL."""

from vibe_uvm.hdl import ival, sset, bit


class CfgVif:
    def __init__(self, dut):
        self.dut = dut
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        self.vld = dut.cfg_wr_vld
        self.ready = dut.cfg_wr_ready
        self.cmd = dut.cfg_wr_cmd
        self.idx = dut.cfg_wr_idx
        self.data = dut.cfg_wr_data
        self.irq_logic = dut.irq_logic

    def idle(self):
        sset(self.vld, 0)
        sset(self.cmd, 0)
        sset(self.idx, 0)
        sset(self.data, 0)


class Nw4Vif:
    def __init__(self, dut, data_prefix, vld_name, ready_name):
        self.dut = dut
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        self._data = [getattr(dut, f"{data_prefix}_{i}") for i in range(4)]
        self._vld = getattr(dut, vld_name)
        self._ready = getattr(dut, ready_name)

    def data(self, p):
        return self._data[p]

    def set_data(self, p, val):
        sset(self._data[p], val)

    def get_data(self, p):
        return ival(self._data[p], 0)

    def set_vld(self, p, val):
        cur = ival(self._vld, 0) or 0
        if val:
            cur |= (1 << p)
        else:
            cur &= ~(1 << p)
        sset(self._vld, cur)

    def get_vld(self, p):
        return bit(self._vld, p)

    def get_ready(self, p):
        return bit(self._ready, p)

    def set_ready_all(self, val=0xF):
        sset(self._ready, val & 0xF)

    def idle_master(self):
        sset(self._vld, 0)
        for p in range(4):
            sset(self._data[p], 0)

    def idle_slave_ready(self):
        self.set_ready_all(0xF)


class PselVif:
    def __init__(self, dut):
        self.dut = dut
        self.clk = dut.clk
        self.rst_n = dut.psel_rst_n
        self.device_rst = dut.psel_device_rst
        self.wr_en = dut.psel_wr_en
        self.sel_vld = dut.psel_sel_vld
        self.drop_g1 = dut.psel_drop_g1
        self.drop = dut.psel_drop
        self.bitmap = dut.psel_bitmap
        self.status_up = dut.psel_status_up
        self.default_bm = dut.psel_default_bm
        self.cfg = dut.psel_cfg
        self.vl = dut.psel_vl
        self.rt = dut.psel_rt
        self.egr = dut.psel_egr
        self.wr_idx = dut.psel_wr_idx
        self.src = dut.psel_src
        self.dest = dut.psel_dest
        self.wr_data = dut.psel_wr_data
        self.drop_down = dut.psel_drop_down


class CnaVif:
    def __init__(self, dut):
        self.dut = dut
        self.cna = dut.c6_cna
        self.cna_written = dut.c6_written
        self.hit = dut.c6_hit
        self.cons = dut.c6_cons
        self.rvld = dut.c6_rvld
        self.rready = dut.c6_rready
        self.data = [getattr(dut, f"c6_data_{i}") for i in range(4)]


class ProbeVif:
    def __init__(self, dut):
        self.dut = dut
        self.drop_g1 = dut.drop_g1
        self.irq_logic = dut.irq_logic
        self.rt_shortest_unimpl = dut.rt_shortest_unimpl
        self.drop_down_cnt = dut.drop_down_cnt
        self.len_err = dut.len_err
        self.deadlock_drop = dut.deadlock_drop
        self.fab_mgmt_cfg6_hit = dut.fab_mgmt_cfg6_hit
        self.x_in_v = dut.x_in_v
        self.saf_v = dut.saf_v
        self.g1_comb = dut.g1_comb
        self.g1_evt = dut.g1_evt
        self.cna = dut.cna
        self.cna_written = dut.cna_written
        self.port_rst = dut.port_rst
        self.device_rst = dut.device_rst
        self.status_up = dut.status_up
        self.default_bm = dut.default_bm
        self.guid0 = dut.guid0
        self.class_code = dut.class_code
        self.port_basic = dut.port_basic
        self.port_cap = dut.port_cap
        self.port_rst_rw1c = dut.port_rst_rw1c
        self.saf_d = [getattr(dut, f"saf_d_{i}") for i in range(4)]
        self.preload_req = dut.preload_req
        self.preload_val = dut.preload_val
        self.preload_done = dut.preload_done
        self.saw_drop_g1 = 0
        self.saw_len_err = 0
        self.saw_egr = 0
        self.saw_xin = 0
        self.egr_cnt = [0, 0, 0, 0]
        self.egr_last = [0, 0, 0, 0]
        self.last_rt_egr = [0, 0, 0, 0]

    def clr_mon(self):
        self.saw_drop_g1 = 0
        self.saw_len_err = 0
        self.saw_egr = 0
        self.saw_xin = 0
        self.egr_cnt = [0, 0, 0, 0]
        self.egr_last = [0, 0, 0, 0]
        self.last_rt_egr = [0, 0, 0, 0]
