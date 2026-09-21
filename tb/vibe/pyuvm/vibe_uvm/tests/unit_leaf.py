"""Leaf-unit TCs ported from tb/vibe/tests/*.sv (same stimulus/score)."""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest


class tc_vl_rr(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.nonempty, 0)
        sset(d.grant, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        sset(d.nonempty, 0b0101)
        await RisingEdge(d.clk)
        a = ival(d.vl_sel, -1)
        sset(d.grant, 1)
        await RisingEdge(d.clk)
        sset(d.grant, 0)
        await RisingEdge(d.clk)
        b = ival(d.vl_sel, -1)
        sset(d.grant, 1)
        await RisingEdge(d.clk)
        sset(d.grant, 0)
        await RisingEdge(d.clk)
        c = ival(d.vl_sel, -1)
        if not ival(d.valid, 0):
            self.bad("tc_vl_rr", "nonempty=VL0|VL2", "valid=1", "valid=0", "u_rr.valid")
        elif a == b == c:
            self.bad("tc_vl_rr", "nonempty VL0+VL2, three grants",
                     "RR walks both VLs (not pinned)", f"vl_sel stayed {a}", "u_rr.rr")
        else:
            self.ok("tc_vl_rr")
        phase.drop_objection(self)


uvm_component_utils(tc_vl_rr)


class tc_vl_rr_0_15(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.nonempty, 0xFFFF)
        sset(d.grant, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        seen = 0
        for _ in range(16):
            if not ival(d.valid, 0):
                self.fail_n += 1
            seen |= 1 << ival(d.vl_sel, 0)
            sset(d.grant, 1)
            await RisingEdge(d.clk)
            sset(d.grant, 0)
            await RisingEdge(d.clk)
        if seen != 0xFFFF:
            self.bad("tc_vl_rr_0_15", "nonempty=FFFF, 16 grants",
                     "every VL0-15 selected once (RR)", f"seen={seen:x}", "u_rr.rr")
        else:
            sset(d.nonempty, 0)
            await Timer(1, "NS")
            if ival(d.valid, 0):
                self.bad("tc_vl_rr_0_15", "nonempty=0", "valid=0", "1", "valid")
            else:
                sset(d.nonempty, 0x8000)
                await Timer(1, "NS")
                if ival(d.vl_sel, -1) != 15:
                    self.bad("tc_vl_rr_0_15", "only VL15", "vl_sel=15",
                             str(ival(d.vl_sel, -1)), "vl_sel")
                else:
                    self.ok("tc_vl_rr_0_15")
        phase.drop_objection(self)


uvm_component_utils(tc_vl_rr_0_15)


class tc_lmsm_idle_discovery(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "lmsm_go", "lid_bad", "lane0_fail", "eq_negotiated", "retrain_req"):
            sset(getattr(d, n), 0)
        sset(d.am_locked, 0)
        sset(d.rst_n, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        st = ival(d.state, -1)
        if st != 0:
            self.bad("tc_lmsm_idle_discovery", "reset", "Idle", str(st), "state")
        else:
            sset(d.lmsm_go, 1)
            await RisingEdge(d.clk)
            sset(d.lmsm_go, 0)
            await RisingEdge(d.clk)
            st = ival(d.state, -1)
            if st != 1:
                self.bad("tc_lmsm_idle_discovery", "lmsm_go",
                         "Discovery.Active (1), not Probe", str(st), "state")
            else:
                self.ok("tc_lmsm_idle_discovery")
        phase.drop_objection(self)


uvm_component_utils(tc_lmsm_idle_discovery)


class tc_neg_absent_features(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        for n in ("port_rst", "lmsm_go", "lid_bad", "lane0_fail", "eq_negotiated", "retrain_req"):
            sset(getattr(d, n), 0)
        sset(d.am_locked, 0)
        sset(d.rst_n, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        if ival(d.state, -1) != 0:
            self.bad("tc_neg_absent_features", "reset", "ST_IDLE (no Probe state)",
                     str(ival(d.state, -1)), "u_lmsm.st")
        else:
            sset(d.lmsm_go, 1)
            await RisingEdge(d.clk)
            sset(d.lmsm_go, 0)
            await RisingEdge(d.clk)
            st = ival(d.state, -1)
            if st != 1:
                self.bad("tc_neg_absent_features", "pulse lmsm_go from Idle",
                         "Discovery.Active (5'd1) — not Probe / QDLWS / RXEQ_Optimize",
                         str(st), "u_lmsm.st")
            else:
                await self.cycles(8)
                st = ival(d.state, -1)
                if st in (12, 13, 31):
                    self.bad("tc_neg_absent_features", "after lmsm_go",
                             "remain in implemented subset (no Probe encoding)",
                             str(st), "state")
                else:
                    self.ok("tc_neg_absent_features")
        phase.drop_objection(self)


uvm_component_utils(tc_neg_absent_features)


class tc_bcrc_crc30(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.start, 0)
        sset(d.in_vld, 0)
        sset(d.last, 0)
        sset(d.error_flag, 1)
        sset(d.in_flit, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        sset(d.start, 1)
        await RisingEdge(d.clk)
        sset(d.start, 0)
        sset(d.in_vld, 1)
        sset(d.last, 1)
        sset(d.in_flit, 0xA5A5A5A5A5A5A5A5A5A5)
        await RisingEdge(d.clk)
        if not ival(d.done, 0):
            self.bad("tc_bcrc_crc30", "start + one flit last error_flag=1",
                     "done=1", f"done=0 crc={ival(d.crc_word, 0):x}", "u_b.crc")
        else:
            crc = ival(d.crc_word, 0)
            if ((crc >> 31) & 1) != 0 or ((crc >> 30) & 1) != 1:
                self.bad("tc_bcrc_crc30", "error_flag=1",
                         "bit31=0 reserved, bit30=ERROR_FLAG=1",
                         f"crc_word={crc:x}", "crc_word")
            else:
                sset(d.in_vld, 0)
                sset(d.last, 0)
                await RisingEdge(d.clk)
                sset(d.start, 1)
                await RisingEdge(d.clk)
                sset(d.start, 0)
                sset(d.in_vld, 1)
                sset(d.last, 0)
                sset(d.error_flag, 0)
                sset(d.in_flit, 1)
                await RisingEdge(d.clk)
                sset(d.last, 1)
                await RisingEdge(d.clk)
                sset(d.in_vld, 0)
                sset(d.last, 0)
                self.ok("tc_bcrc_crc30")
        phase.drop_objection(self)


uvm_component_utils(tc_bcrc_crc30)


class tc_rst_sync(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n_in, 0)
        await self.cycles(3)
        if ival(d.rst_n_out, 1):
            self.bad("tc_rst_sync", "rst_n_in=0", "rst_n_out=0 async assert",
                     str(ival(d.rst_n_out, -1)), "rst_n_out")
        else:
            sset(d.rst_n_in, 1)
            await RisingEdge(d.clk)
            if ival(d.rst_n_out, 1):
                self.bad("tc_rst_sync", "deassert, first dest clock",
                         "still 0 (2-FF)", str(ival(d.rst_n_out, -1)), "rst_n_out")
            else:
                await RisingEdge(d.clk)
                await RisingEdge(d.clk)
                if not ival(d.rst_n_out, 0):
                    self.bad("tc_rst_sync", "two dest clocks after deassert",
                             "rst_n_out=1", str(ival(d.rst_n_out, -1)), "rst_n_out")
                else:
                    self.ok("tc_rst_sync")
        phase.drop_objection(self)


uvm_component_utils(tc_rst_sync)


class tc_p0_down_drop(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.bitmap, 0)
        sset(d.status_up, 0xF)
        sset(d.default_bm, 0)
        sset(d.rt, 0)
        sset(d.drop_g1, 0)
        sset(d.sel_vld, 0)
        sset(d.cfg, 3)
        sset(d.vl, 0)
        sset(d.src, 0x0030)
        sset(d.dest, 0x00FF)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.status_up, 0xF)
        sset(d.bitmap, 0)
        sset(d.sel_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if ival(d.drop, 1) or ival(d.egr, -1) != 0:
            self.bad("tc_p0_down_drop",
                     "RT=00 bitmap=0 default_bm=0 status_up=1111 dest=00FF",
                     "drop=0 egr=0 (AS-0.1 §8 default → port 0)",
                     f"drop={ival(d.drop, -1)} egr={ival(d.egr, -1)}", "u_ps.use_bm")
            phase.drop_objection(self)
            return
        sset(d.sel_vld, 0)
        await RisingEdge(d.clk)
        cnt_before = ival(d.drop_down_cnt, 0)
        await FallingEdge(d.clk)
        sset(d.status_up, 0xE)
        sset(d.bitmap, 0)
        sset(d.sel_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not ival(d.drop, 0):
            self.bad("tc_p0_down_drop", "default all-0 → port 0; status_up[0]=0",
                     "drop=1 (no flood)", f"drop={ival(d.drop, -1)}", "u_ps.drop")
        elif ival(d.drop_down_cnt, 0) != cnt_before + 1:
            self.bad("tc_p0_down_drop", "port 0 Down after empty bitmap filter",
                     "drop_down_cnt += 1",
                     f"before={cnt_before} after={ival(d.drop_down_cnt, 0)}",
                     "u_ps.drop_down_cnt")
        else:
            self.ok("tc_p0_down_drop")
        sset(d.sel_vld, 0)
        phase.drop_objection(self)


uvm_component_utils(tc_p0_down_drop)


class tc_route_lu(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.device_rst, 0)
        sset(d.wr_en, 0)
        sset(d.lu_vld, 0)
        sset(d.wr_idx, 0)
        sset(d.wr_data, 0)
        sset(d.dest, 1)
        sset(d.rt, 0)
        await self.cycles(4)
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.lu_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.lu_vld, 0)
        if ival(d.bitmap, -1) != 0 or ival(d.drop_g1, 0):
            self.bad("tc_route_lu", "lu dest=1 empty table", "bitmap=0 drop_g1=0",
                     f"bm={ival(d.bitmap, 0):x} g1={ival(d.drop_g1, 0)}", "bitmap")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.wr_en, 1)
        sset(d.wr_idx, 1)
        sset(d.wr_data, 0xF)
        await RisingEdge(d.clk)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.wr_en, 0)
        sset(d.dest, 1)
        sset(d.rt, 0)
        sset(d.lu_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.lu_vld, 0)
        if ival(d.bitmap, 0) != 0xF:
            self.bad("tc_route_lu", "wr dest=1 data=F, lu RT=00", "bitmap=1111",
                     f"{ival(d.bitmap, 0):04b}", "bitmap")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.rt, 0b10)
        sset(d.lu_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        if not ival(d.drop_g1, 0) or ival(d.bitmap, -1) != 0:
            self.bad("tc_route_lu", "RT=10", "drop_g1=1 bitmap=0 (not alias 00)",
                     f"g1={ival(d.drop_g1, 0)} bm={ival(d.bitmap, 0):04b}", "drop_g1")
        else:
            sset(d.lu_vld, 0)
            await FallingEdge(d.clk)
            sset(d.rt, 0b11)
            sset(d.lu_vld, 1)
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            if not ival(d.drop_g1, 0):
                self.bad("tc_route_lu", "RT=11", "drop_g1", "0", "drop_g1")
            else:
                self.ok("tc_route_lu")
        phase.drop_objection(self)


uvm_component_utils(tc_route_lu)


class tc_cfg0_no_credit(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 32)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.is_cfg0, 1)
        sset(d.consume_vld, 1)
        sset(d.consume_flits, 32)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.consume_vld, 0)
        sset(d.is_cfg0, 0)
        await RisingEdge(d.clk)
        cells = ival(d.cells, 0)
        if ival(d.fc_ovf, 0) or cells != 0:
            self.bad("tc_cfg0_no_credit", "consume_vld=1 is_cfg0=1 consume_flits=32",
                     "cells stay 0 (CFG0 does not consume)",
                     f"cells={cells} fc_ovf={ival(d.fc_ovf, 0)}", "u_crd.cells")
        else:
            await FallingEdge(d.clk)
            sset(d.is_cfg0, 0)
            sset(d.consume_vld, 1)
            sset(d.consume_flits, 8)
            await RisingEdge(d.clk)
            await FallingEdge(d.clk)
            sset(d.consume_vld, 0)
            await RisingEdge(d.clk)
            if ival(d.cells, 0) == 0:
                self.bad("tc_cfg0_no_credit", "consume_vld=1 is_cfg0=0 flits=8 grain=8",
                         "cells += ceil(8/8)=1", f"cells={ival(d.cells, 0)}", "cells")
            else:
                self.ok("tc_cfg0_no_credit")
        phase.drop_objection(self)


uvm_component_utils(tc_cfg0_no_credit)


class tc_credit_1024_flit_bp(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 1023)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        await RisingEdge(d.clk)
        if ival(d.pending, -1) != 1023:
            self.bad("tc_credit_1024_flit_bp",
                     "credit_ret_n=1023 cell (already cells, no ×n / no /n)",
                     "pending==1023 cell (not 1023 flit, not ceil_div)",
                     f"pending={ival(d.pending, -1)}", "u_crd.pend")
            phase.drop_objection(self)
            return
        if ival(d.bp_nw, 0):
            self.bad("tc_credit_1024_flit_bp", "pending=1023 cell",
                     "bp_nw=0 (threshold is 1024 cell)", "bp_nw=1", "u_crd.bp_nw")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        await RisingEdge(d.clk)
        if ival(d.pending, -1) != 1024 or not ival(d.bp_nw, 0) or not ival(d.force_crd_ack, 0):
            self.bad("tc_credit_1024_flit_bp",
                     "pending reaches 1024 cell via credit_ret_n (not ×n flit)",
                     "pending=1024 cell bp_nw=1 force_crd_ack=1",
                     f"pending={ival(d.pending, -1)} bp={ival(d.bp_nw, 0)} ack={ival(d.force_crd_ack, 0)}",
                     "u_crd.pend")
        else:
            self.ok("tc_credit_1024_flit_bp")
        phase.drop_objection(self)


uvm_component_utils(tc_credit_1024_flit_bp)


class tc_credit_1024_hole(tc_credit_1024_flit_bp):
    """G7 closed as cell — same 1023→1024 score as tc_credit_1024_flit_bp."""

    async def run_phase(self, phase):
        # Reuse body but print the hole name on pass.
        phase.raise_objection(self)
        # Call parent logic by instantiating the same stimulus under this name.
        d = self.dut
        sset(d.rst_n, 0)
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.grain_n, 8)
        sset(d.consume_vld, 0)
        sset(d.consume_flits, 0)
        sset(d.is_cfg0, 0)
        sset(d.credit_ret, 0)
        sset(d.credit_ret_n, 0)
        await self.cycles(3)
        sset(d.rst_n, 1)
        await self.cycles(2)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 1023)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 1)
        sset(d.credit_ret_n, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.credit_ret, 0)
        await RisingEdge(d.clk)
        if ival(d.pending, -1) != 1024 or not ival(d.bp_nw, 0):
            self.bad("tc_credit_1024_hole", "1023 then +1 cell",
                     "pending=1024 bp_nw=1 (G7 cell)",
                     f"pending={ival(d.pending, -1)} bp={ival(d.bp_nw, 0)}", "u_crd")
        else:
            self.ok("tc_credit_1024_hole")
        phase.drop_objection(self)


uvm_component_utils(tc_credit_1024_hole)


async def _cfg_space_reset(test):
    d = test.dut
    sset(d.rst_n, 0)
    sset(d.device_rst, 0)
    sset(d.cfg_wr_vld, 0)
    sset(d.cfg_wr_cmd, 0)
    sset(d.cfg_wr_idx, 0)
    sset(d.cfg_wr_data, 0)
    sset(d.port_rst_hold, 0)
    await test.cycles(3)
    sset(d.rst_n, 1)
    await test.cycles(2)


class tc_identity_cfg_space(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        await _cfg_space_reset(self)
        if (ival(d.guid0, 0) & 0xFF) != 0x03 or (ival(d.class_code, 0) & 0xFFFF) != 0x0300:
            self.bad("tc_identity_cfg_space", "reset (constants; AS has no cfg_wr read map)",
                     "GUID Type 0x3, Class 0x0300",
                     f"guid0={ival(d.guid0, 0):x} class={ival(d.class_code, 0):x}",
                     "u_cfg.guid0")
            phase.drop_objection(self)
            return
        if ival(d.port_basic, 0) != lph.PORT_BASIC or ival(d.port_cap, 0) != lph.PORT_CAP:
            self.bad("tc_identity_cfg_space", "reset", "PORT_BASIC/CAP constants",
                     f"basic={ival(d.port_basic, 0):x} cap={ival(d.port_cap, 0):x}",
                     "u_cfg")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_data, 0xBEEF)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_vld, 0)
        await self.cycles(2)
        if ival(d.cna, 0) != 0xBEEF or not ival(d.cna_written, 0):
            self.bad("tc_identity_cfg_space", "cfg_wr_cmd=0 data=BEEF",
                     "cna=BEEF cna_written=1",
                     f"cna={ival(d.cna, 0):x} written={ival(d.cna_written, 0)}", "cna")
        else:
            self.ok("tc_identity_cfg_space")
        phase.drop_objection(self)


uvm_component_utils(tc_identity_cfg_space)


class tc_cna_16bit(VibeUnitBaseTest):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        await _cfg_space_reset(self)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_cmd, 0)
        sset(d.cfg_wr_data, 0x00ABCDEF)
        sset(d.cfg_wr_vld, 1)
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        sset(d.cfg_wr_vld, 0)
        await self.cycles(2)
        if ival(d.cna, 0) != 0xCDEF:
            self.bad("tc_cna_16bit", "cfg_wr_cmd=0 data=00ABCDEF",
                     "cna=16'hCDEF (low 16 only; not 24-bit)",
                     f"cna={ival(d.cna, 0):x}", "u_cfg.cna")
        else:
            self.ok("tc_cna_16bit")
        phase.drop_objection(self)


uvm_component_utils(tc_cna_16bit)
