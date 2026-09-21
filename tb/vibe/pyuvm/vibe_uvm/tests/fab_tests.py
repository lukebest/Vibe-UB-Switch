"""Fabric suite TCs — port of tb/vibe/uvm/pkg/vibe_fab_tests.svh / vibe_suite.sv."""

from uvm import uvm_component_utils
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, bit
from vibe_uvm.report import tb_note
from vibe_uvm.tests.fab_base import VibeFabBaseTest
from cocotb.triggers import RisingEdge, FallingEdge


class VibeFabBodies(VibeFabBaseTest):
    """Shared suite bodies. Individual tests and tc_suite_all call these."""

    async def do_rt00_per_flow_rr_fwd(self):
        print("=== tc_rt00_per_flow_rr_fwd ===", flush=True)
        await self.psel_reset()
        await self.psel_wr_route(0x0001, 0xF)
        await self.psel_select(0b00, 0, 0xA000, 0x0001)
        p0a = -1 if ival(self.psel.drop, 1) else ival(self.psel.egr, -1)
        await self.psel_select(0b00, 0, 0xA000, 0x0001)
        p0b = -1 if ival(self.psel.drop, 1) else ival(self.psel.egr, -1)
        await self.psel_select(0b00, 7, 0xA000, 0x0001)
        p1a = -1 if ival(self.psel.drop, 1) else ival(self.psel.egr, -1)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        await self.tb_inject_hdr(0, 3, 0b00, 0, 0xA000, 0x0001, lph.plen_nflit(5))
        await self.tb_cycles(12)
        if p0a < 0 or p0b < 0 or p1a < 0:
            self.bad("tc_rt00_per_flow_rr_fwd", "port_sel+route_lu RT=00 dest=1 bitmap=1111",
                     "drop=0 (forward on bitmap)", "drop=1", "psel.drop")
        elif p0a != p0b:
            self.bad("tc_rt00_per_flow_rr_fwd", "same flow {CFG,src,dest,VL} twice",
                     "sticky same egr", "egr changed", "psel.sticky")
        elif (not (self.probe.saw_xin & 1)) or bit(self.probe.g1_comb, 0):
            self.bad("tc_rt00_per_flow_rr_fwd", "fabric inject RT=00",
                     "x_in_v[0]=1 and not G1", "x_in_v/g1 mismatch", "u_fab.x_in_v")
        else:
            self.ok("tc_rt00_per_flow_rr_fwd")

    async def do_rt01_per_packet_rr_fwd(self):
        print("=== tc_rt01_per_packet_rr_fwd ===", flush=True)
        await self.psel_reset()
        await self.psel_wr_route(0x0002, 0xF)
        seqb = []
        for _ in range(4):
            await self.psel_select(0b01, 1, 0xB000, 0x0002)
            seqb.append(-1 if ival(self.psel.drop, 1) else ival(self.psel.egr, -1))
        if any(s < 0 for s in seqb):
            self.bad("tc_rt01_per_packet_rr_fwd", "4x port_sel RT=01 dest=2 bitmap=1111",
                     "each select drop=0", "a select dropped", "psel.drop")
        elif seqb[0] == seqb[1] == seqb[2] == seqb[3]:
            self.bad("tc_rt01_per_packet_rr_fwd", "4x RT=01 bitmap=1111",
                     "per-packet RR walks ports", "all 4 egr identical", "psel.rr")
        else:
            self.ok("tc_rt01_per_packet_rr_fwd")

    async def do_rt10_must_drop(self):
        print("=== tc_rt10_must_drop (TP-RT-003) ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0003, 0xE)
        self.probe.clr_mon()
        c0 = ival(self.probe.rt_shortest_unimpl, 0)
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0xC000, 0x0003, lph.plen_nflit(5))
        await self.expect_drop_only("tc_rt10_must_drop", c0)

    async def do_rt11_must_drop(self):
        print("=== tc_rt11_must_drop (TP-RT-004) ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0004, 0x7)
        self.probe.clr_mon()
        c0 = ival(self.probe.rt_shortest_unimpl, 0)
        await self.tb_inject_hdr(0, 3, 0b11, 2, 0xC001, 0x0004, lph.plen_nflit(5))
        await self.expect_drop_only("tc_rt11_must_drop", c0)

    async def do_rt_shortest_unimpl_count(self):
        print("=== tc_rt_shortest_unimpl_count ===", flush=True)
        await self.tb_reset()
        c0 = ival(self.probe.rt_shortest_unimpl, 0)
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0x1, 0x5, lph.plen_nflit(5))
        await self.tb_cycles(16)
        c1 = ival(self.probe.rt_shortest_unimpl, 0)
        await self.tb_inject_hdr(1, 3, 0b11, 0, 0x1, 0x6, lph.plen_nflit(5))
        await self.tb_cycles(16)
        c2 = ival(self.probe.rt_shortest_unimpl, 0)
        if c0 != 0:
            self.bad("tc_rt_shortest_unimpl_count", "reset then two G1 packets",
                     "counter starts 0", "nonzero after reset", "rt_shortest_unimpl")
        elif c1 != 1 or c2 != 2:
            self.bad("tc_rt_shortest_unimpl_count", "RT=10 then RT=11",
                     "rt_shortest_unimpl == 1 then 2", f"c1={c1} c2={c2}",
                     "rt_shortest_unimpl")
        else:
            self.ok("tc_rt_shortest_unimpl_count")

    async def do_rt_shortest_irq_logic(self):
        print("=== tc_rt_shortest_irq_logic ===", flush=True)
        await self.tb_reset()
        if ival(self.probe.irq_logic, 0):
            self.bad("tc_rt_shortest_irq_logic", "reset", "irq_logic=0", "already 1", "u_irq.sticky")
            return
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0x1, 0x7, lph.plen_nflit(5))
        await self.tb_cycles(16)
        if not ival(self.probe.irq_logic, 0):
            self.bad("tc_rt_shortest_irq_logic", "one RT=10 packet",
                     "irq_logic=1", "stayed 0", "drop_g1 -> u_irq")
        else:
            self.ok("tc_rt_shortest_irq_logic")

    async def do_rt_irq_logic_sticky(self):
        print("=== tc_rt_irq_logic_sticky ===", flush=True)
        await self.tb_reset()
        await self.tb_inject_hdr(0, 3, 0b11, 0, 0x1, 0x8, lph.plen_nflit(5))
        await self.tb_cycles(12)
        await self.tb_cycles(20)
        if not ival(self.probe.irq_logic, 0):
            self.bad("tc_rt_irq_logic_sticky", "RT=11 then wait 20 cycles",
                     "irq_logic remains 1", "cleared by itself", "u_irq.sticky")
            return
        await self.tb_cfg(lph.CMD_NOPCLR, 0, 0)
        await self.tb_cycles(4)
        if ival(self.probe.irq_logic, 0):
            self.bad("tc_rt_irq_logic_sticky", "static cfg_wr_cmd=7 after sticky irq",
                     "irq_logic=0 (AS-0.1 s10 clear on static write)", "still 1", "irq_clr")
            return
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0x1, 0x9, lph.plen_nflit(5))
        await self.tb_cycles(12)
        await self.tb_cfg(lph.CMD_DEVRST, 0, 0)
        await self.tb_cycles(12)
        if ival(self.probe.irq_logic, 0):
            self.bad("tc_rt_irq_logic_sticky", "second G1 then device reset",
                     "irq_logic=0", "still 1", "device_rst / u_irq")
        else:
            self.ok("tc_rt_irq_logic_sticky")

    async def do_rt_no_rewrite(self):
        print("=== tc_rt_no_rewrite ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x000A, 0x2)
        self.probe.clr_mon()
        self.tb_hold_egr(True)
        await self.tb_inject_hdr(0, 3, 0b00, 0, 0x1, 0x000A, lph.plen_nflit(5))
        await self.tb_cycles(8)
        self.tb_hold_egr(False)
        await self.tb_wait_egr(40)
        bad = 0
        if self.probe.saw_egr:
            if all(self.probe.last_rt_egr[p] != 0 for p in range(4)):
                bad = 1
        await self.tb_reset()
        await self.tb_wr_route(0x000A, 0x2)
        self.probe.clr_mon()
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0x1, 0x000A, lph.plen_nflit(5))
        await self.tb_cycles(16)
        if self.probe.saw_egr:
            for p in range(4):
                if (self.probe.saw_egr & (1 << p)) and self.probe.last_rt_egr[p] != 0b10:
                    bad = 2
        if bad == 1:
            self.bad("tc_rt_no_rewrite", "RT=00 forwarded packet", "egress LPH.RT still 00",
                     "RT field rewritten", "fab_nw_data flit[23:22]")
        elif bad == 2:
            self.bad("tc_rt_no_rewrite", "RT=10 leaked", "must not rewrite RT to 00/01",
                     "forwarded beat has rewritten RT", "saf_d / egr")
        else:
            self.ok("tc_rt_no_rewrite")

    async def do_rt10_not_as_rt00(self):
        print("=== tc_rt10_not_as_rt00 ===", flush=True)
        await self.psel_reset()
        await self.psel_wr_route(0x000B, 0x4)
        await self.psel_select(0b00, 3, 0x22, 0x000B)
        d00 = ival(self.psel.drop, 1)
        e00 = ival(self.psel.egr, -1)
        await self.psel_select(0b10, 3, 0x22, 0x000B)
        d10 = ival(self.psel.drop, 0)
        await self.tb_reset()
        await self.tb_wr_route(0x000B, 0x4)
        await self.tb_inject_hdr(0, 3, 0b10, 3, 0x22, 0x000B, lph.plen_nflit(5))
        await self.tb_cycles(16)
        if d00 or e00 != 2:
            self.bad("tc_rt10_not_as_rt00", "control RT=00 dest=B bitmap=port2",
                     "drop=0 egr=2", "RT=00 did not take bitmap port 2", "psel.egr")
        elif not d10:
            self.bad("tc_rt10_not_as_rt00", "same dest RT=10",
                     "port_sel.drop=1", "drop=0 — treated as implemented RT", "drop_g1")
        elif bit(self.probe.x_in_v, 0) or self.probe.saw_egr:
            self.bad("tc_rt10_not_as_rt00", "fabric RT=10 same dest",
                     "x_in_v=0 and no egress", "presented to xbar or forwarded", "x_in_v")
        else:
            self.ok("tc_rt10_not_as_rt00")

    async def do_rt_counter_32b_sat(self):
        print("=== tc_rt_counter_32b_sat ===", flush=True)
        await self.tb_reset()
        await self.tb_preload_cnt(0xFFFFFFFE)
        await self.tb_cycles(2)
        cnt = ival(self.probe.rt_shortest_unimpl, 0)
        if cnt != 0xFFFFFFFE:
            self.bad("tc_rt_counter_32b_sat", "preload FFFFFFFE",
                     "counter reads FFFFFFFE", "preload did not stick", "rt_shortest_unimpl")
            return
        await self.tb_inject_hdr(0, 3, 0b10, 0, 0x1, 0xC, lph.plen_nflit(5))
        await self.tb_cycles(16)
        if ival(self.probe.rt_shortest_unimpl, 0) != 0xFFFFFFFF:
            self.bad("tc_rt_counter_32b_sat", "preload FFFFFFFE + one RT=10",
                     "FFFFFFFF (sat, no wrap)", "not FFFFFFFF", "rt_shortest_unimpl")
            return
        await self.tb_inject_hdr(0, 3, 0b11, 0, 0x1, 0xD, lph.plen_nflit(5))
        await self.tb_cycles(16)
        if ival(self.probe.rt_shortest_unimpl, 0) != 0xFFFFFFFF:
            self.bad("tc_rt_counter_32b_sat", "second G1 at FFFFFFFF",
                     "stay FFFFFFFF (no wrap to 0)", "wrapped or changed", "rt_shortest_unimpl")
        else:
            self.ok("tc_rt_counter_32b_sat")

    async def do_cfg_identity_guid_class(self):
        print("=== tc_cfg_identity_guid_class ===", flush=True)
        await self.tb_reset()
        await self.tb_cfg(lph.CMD_CNA, 0, 0xAB)
        if ival(self.probe.guid0, 0) != lph.GUID_TYPE:
            self.bad("tc_cfg_identity_guid_class", "probe guid0", "GUID Type 0x3",
                     "guid0 mismatch", "u_cfg.guid0")
        elif ival(self.probe.class_code, 0) != lph.CLASS_CODE:
            self.bad("tc_cfg_identity_guid_class", "probe class_code", "Class 0x0300",
                     "class_code mismatch", "u_cfg.class_code")
        elif (ival(self.probe.port_basic, 0) != lph.PORT_BASIC
              or ival(self.probe.port_cap, 0) != lph.PORT_CAP):
            self.bad("tc_cfg_identity_guid_class", "PORT_BASIC / CAP",
                     "4p, x4, Mode-2", "constant mismatch", "u_cfg.port_basic")
        elif ival(self.probe.cna, 0) != 0x00AB or not ival(self.probe.cna_written, 0):
            self.bad("tc_cfg_identity_guid_class", "cfg_wr_cmd=0 data=00AB",
                     "cna=00AB and cna_written=1", "CNA static write did not land", "u_cfg.cna")
        else:
            self.ok("tc_cfg_identity_guid_class")

    async def do_default_rt_all0_port0(self):
        print("=== tc_default_rt_all0_port0 ===", flush=True)
        await self.psel_reset()
        await self.psel_select(0b00, 0, 0x30, 0x00FF)
        if ival(self.psel.drop, 1) or ival(self.psel.egr, -1) != 0:
            self.bad("tc_default_rt_all0_port0", "RT=00 dest=00FF table all-0 default_bm=0",
                     "drop=0 egr=0", "wrong egr or drop", "psel.use_bm")
        else:
            self.ok("tc_default_rt_all0_port0")

    async def do_pkt_len_err_drop(self):
        print("=== tc_pkt_len_err_drop ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        self.probe.clr_mon()
        fl = lph.mk_flit(3, 0b00, 0, 0x1, 0x0001, lph.plen_oversize(), 0, 0, 0, 0)
        await self.tb_inject(0, lph.mk_beat(fl), 1)
        await self.tb_cycles(12)
        if not (self.probe.saw_len_err & 1):
            self.bad("tc_pkt_len_err_drop", "declared 224 flits (4480 B)",
                     "len_err[0] pulse; drop; irq_logic", "len_err not seen", "u_saf.len_err")
        elif self.probe.saw_egr:
            self.bad("tc_pkt_len_err_drop", "oversize declared length",
                     "drop (no egress)", "packet forwarded", "fab_nw_vld")
        elif not ival(self.probe.irq_logic, 0):
            self.bad("tc_pkt_len_err_drop", "len_err observed",
                     "irq_logic sticky 1 (AS-0.1 s15)", "irq_logic=0", "u_irq")
        else:
            tb_note("tc_pkt_len_err_drop: <16 B not reachable (decl_flits clamp to 1 = 20 B)")
            self.ok("tc_pkt_len_err_drop")

    async def do_cfg6_term_vs_fwd(self):
        print("=== tc_cfg6_term_vs_fwd ===", flush=True)
        await self.tb_reset()
        sset(self.cna.cna, 0x1111)
        sset(self.cna.cna_written, 1)
        sset(self.cna.hit, 0)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x1111, lph.plen_nflit(5))))
        await RisingEdge(self.clk)
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        term_us = bit(self.cna.cons, 0) and bit(self.cna.rvld, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x2222, lph.plen_nflit(5), nlp=1)))
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        term_nlp = bit(self.cna.cons, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x1111, lph.plen_nflit(5), opc=0x10)))
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        term_opc = bit(self.cna.cons, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x2222, lph.plen_nflit(5), opc=0x10)))
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        fwd_opc_nous = not bit(self.cna.cons, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x2222, lph.plen_nflit(5))))
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        fwd_miss = not bit(self.cna.cons, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        sset(self.cna.cna_written, 0)
        sset(self.cna.cna, 0x1111)
        sset(self.cna.data[0], lph.mk_beat(lph.mk_flit(6, 0, 0, 0x2, 0x1111, lph.plen_nflit(5))))
        sset(self.cna.hit, 1)
        await RisingEdge(self.clk)
        unw = not bit(self.cna.cons, 0)
        sset(self.cna.hit, 0)
        await RisingEdge(self.clk)
        await self.tb_reset()
        await self.tb_cfg(lph.CMD_CNA, 0, 0x1111)
        await self.tb_inject_hdr(0, 6, 0, 0, 0x2, 0x1111, lph.plen_nflit(5))
        await self.tb_cycles(16)
        await self.tb_inject_hdr(0, 6, 0, 0, 0x2, 0x2222, lph.plen_nflit(5))
        await self.tb_cycles(32)
        if not term_us:
            self.bad("tc_cfg6_term_vs_fwd", "cna_ep CFG6 DCNA==written CNA",
                     "consume=1", "no consume", "u_c6.term")
        elif not term_nlp:
            self.bad("tc_cfg6_term_vs_fwd", "CFG6 NLP=1 DCNA!=CNA",
                     "consume=1 (enumerate terminate)", "consume=0", "u_c6.nlp")
        elif not term_opc:
            self.bad("tc_cfg6_term_vs_fwd", "CFG6 opcode 0x10 DCNA==CNA",
                     "consume=1", "consume=0", "u_c6.opc")
        elif not fwd_opc_nous:
            self.bad("tc_cfg6_term_vs_fwd", "CFG6 opcode 0x10 DCNA!=CNA",
                     "consume=0 (forward)", "consume=1", "u_c6.term")
        elif not fwd_miss:
            self.bad("tc_cfg6_term_vs_fwd", "CFG6 DCNA!=CNA NLP=0 opc=0",
                     "consume=0", "consume=1", "u_c6.term")
        elif not unw:
            self.bad("tc_cfg6_term_vs_fwd", "CNA not written, DCNA==power-on CNA",
                     "consume=0", "consume=1", "cna_written")
        else:
            self.ok("tc_cfg6_term_vs_fwd")

    async def do_saf_full_pkt(self):
        print("=== tc_saf_full_pkt ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0x1)
        self.probe.clr_mon()
        self.tb_hold_egr(False)
        await FallingEdge(self.clk)
        while not self.ing.get_ready(0):
            await RisingEdge(self.clk)
        self.ing.set_data(0, lph.mk_beat(lph.mk_flit(3, 0, 0, 0x1, 0x0001, lph.plen_nflit(5))))
        self.ing.set_vld(0, 1)
        await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        self.ing.set_vld(0, 0)
        await self.tb_cycles(8)
        early = ival(self.probe.saf_v, 0)
        await FallingEdge(self.clk)
        self.ing.set_data(0, 0)
        self.ing.set_vld(0, 1)
        await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        self.ing.set_vld(0, 0)
        await self.tb_cycles(8)
        if early:
            self.bad("tc_saf_full_pkt", "1 of 2 declared beats only",
                     "saf_v=0 (store-and-forward; no xbar yet)",
                     "saf_v rose before EOP", "u_saf.done")
        elif not ival(self.probe.saf_v, 0) and not self.probe.saw_egr:
            await self.tb_wait_egr(30)
            if not self.probe.saw_egr and not ival(self.probe.saf_v, 0):
                self.bad("tc_saf_full_pkt", "second beat completed declared length",
                         "packet presented (saf_v or egress)", "never presented", "saf_v")
            else:
                self.ok("tc_saf_full_pkt")
        else:
            self.ok("tc_saf_full_pkt")

    async def do_icrc_transit_no_recompute(self):
        print("=== tc_icrc_transit_no_recompute ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0003, 0x8)
        in_f = lph.mk_flit(3, 0, 4, 0xAA, 0x0003, lph.plen_nflit(5), 0xA5A5, 0x5A, 0, 0)
        self.probe.clr_mon()
        self.tb_hold_egr(True)
        await self.tb_inject(0, lph.mk_beat(in_f), 2)
        await self.tb_cycles(8)
        self.tb_hold_egr(False)
        await self.tb_wait_egr(40)
        saf_f = lph.nw512_flit0(ival(self.probe.saf_d[0], 0))
        if lph.nth_cci(saf_f) != lph.nth_cci(in_f) or lph.nth_lbf(saf_f) != lph.nth_lbf(in_f):
            self.bad("tc_icrc_transit_no_recompute", "transit CFG3 sitting in SAF",
                     "CCI/LBF unchanged (fabric has no vibe_icrc)",
                     "SAF header CCI/LBF changed", "saf_d")
        else:
            self.ok("tc_icrc_transit_no_recompute")

    async def do_cfg_fwd(self, cfg, name):
        print(f"=== {name} ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        self.probe.clr_mon()
        await self.tb_inject_hdr(0, cfg, 0, 0, 0x0001, 0x0001, lph.plen_nflit(5))
        await self.tb_cycles(14)
        if bit(self.probe.fab_mgmt_cfg6_hit, 0):
            self.bad(name, "inject CFG to dest=1 bitmap=1111",
                     "fab_mgmt_cfg6_hit=0", "fab_mgmt_cfg6_hit=1", "fab_mgmt_cfg6_hit")
        elif (not bit(self.probe.x_in_v, 0) and not bit(self.probe.g1_comb, 0)
              and not self.probe.saw_egr):
            self.bad(name, "inject non-term CFG RT=00",
                     "x_in_v=1 (forward / xbar)", "not presented to xbar", "x_in_v")
        else:
            self.ok(name)

    async def do_cfg_reserved_fwd(self):
        print("=== tc_cfg_reserved_fwd ===", flush=True)
        nfail = 0
        for cfg in (1, 2, 8, 10, 15):
            await self.tb_reset()
            await self.tb_wr_route(0x0001, 0xF)
            self.probe.clr_mon()
            await self.tb_inject_hdr(0, cfg, 0, 0, 0x0001, 0x0001, lph.plen_nflit(5))
            await self.tb_cycles(14)
            if bit(self.probe.fab_mgmt_cfg6_hit, 0) or (
                not bit(self.probe.x_in_v, 0) and not bit(self.probe.g1_comb, 0)
                and not self.probe.saw_egr
            ):
                nfail += 1
        if nfail:
            self.bad("tc_cfg_reserved_fwd", "CFG 1,2,8,10,15 RT=00 dest=1",
                     "each x_in_v=1 and fab_mgmt_cfg6_hit=0",
                     "one or more reserved CFGs not forwarded", "x_in_v")
        else:
            self.ok("tc_cfg_reserved_fwd")

    async def do_cfg_fwd_class(self):
        print("=== tc_cfg_fwd_class ===", flush=True)
        nfail = 0
        for cfg in (3, 4, 5, 7, 9, 1, 2, 8, 10, 15):
            await self.tb_reset()
            await self.tb_wr_route(0x0001, 0xF)
            self.probe.clr_mon()
            await self.tb_inject_hdr(0, cfg, 0, 0, 0x0001, 0x0001, lph.plen_nflit(5))
            await self.tb_cycles(14)
            if bit(self.probe.fab_mgmt_cfg6_hit, 0) or (
                not bit(self.probe.x_in_v, 0) and not bit(self.probe.g1_comb, 0)
                and not self.probe.saw_egr
            ):
                nfail += 1
        if nfail:
            self.bad("tc_cfg_fwd_class", "CFG 3/4/5/7/9 + reserved",
                     "each forwarded and fab_mgmt_cfg6_hit=0",
                     "one or more CFGs terminated or dropped", "x_in_v")
        else:
            self.ok("tc_cfg_fwd_class")

    async def do_port_rst_via_cfg(self):
        print("=== tc_port_rst_via_cfg ===", flush=True)
        await self.tb_reset()
        await self.tb_cfg(lph.CMD_PORTRST, 2, lph.PORTRST_NOP)
        if bit(self.probe.port_rst, 2) or bit(self.probe.port_rst_rw1c, 2):
            self.bad("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=0",
                     "port_rst[2]=0", "port_rst or rw1c bit 2 set", "port_rst")
            return
        await self.tb_cfg(lph.CMD_PORTRST, 2, lph.PORTRST_W1C)
        if not bit(self.probe.port_rst, 2):
            self.bad("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=1",
                     "port_rst[2]=1", "port_rst[2]=0", "port_rst")
        elif bit(self.probe.port_rst, 0) or bit(self.probe.port_rst, 1) or bit(self.probe.port_rst, 3):
            self.bad("tc_port_rst_via_cfg", "port reset index 2 data[0]=1",
                     "only bit 2", "other bits set", "port_rst")
        elif not bit(self.probe.port_rst_rw1c, 2):
            self.bad("tc_port_rst_via_cfg", "cfg_wr_cmd=4'h3 idx=2 data[0]=1",
                     "port_rst_rw1c[2]=1", "rw1c[2]=0", "port_rst_rw1c")
        else:
            self.ok("tc_port_rst_via_cfg")

    async def do_device_rst_via_cfg(self):
        print("=== tc_device_rst_via_cfg ===", flush=True)
        await self.tb_reset()
        await self.tb_cfg(lph.CMD_CNA, 0, 0xAA)
        await self.tb_cfg(lph.CMD_DEVRST, 0, 0)
        if not ival(self.probe.device_rst, 0):
            self.bad("tc_device_rst_via_cfg", "cfg_wr_cmd=4 device reset",
                     "device_rst hold=1", "device_rst=0", "u_rst.device_rst")
            return
        await self.tb_cycles(12)
        if ival(self.probe.cna_written, 0):
            self.bad("tc_device_rst_via_cfg", "device reset after CNA write",
                     "CNA unwritten", "cna_written still 1", "u_cfg.cna_written")
        else:
            self.ok("tc_device_rst_via_cfg")

    async def do_pkt_len_legal_16_4300(self):
        print("=== tc_pkt_len_legal_16_4300 ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        self.probe.clr_mon()
        await self.tb_inject_hdr(0, 3, 0, 0, 0x1, 0x0001, lph.plen_min_try())
        await self.tb_cycles(16)
        bad20 = self.probe.saw_len_err & 1
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        self.probe.clr_mon()
        await self.tb_inject_hdr(0, 3, 0, 0, 0x1, 0x0001, lph.plen_4300())
        await self.tb_cycles(80)
        bad4300 = self.probe.saw_len_err & 1
        if bad20:
            self.bad("tc_pkt_len_legal_16_4300", "1-flit / 20 B",
                     "len_err=0 (inside 16..4300)", "len_err pulsed", "len_err")
        elif bad4300:
            self.bad("tc_pkt_len_legal_16_4300", "declared 215 flits = 4300 B",
                     "len_err=0", "len_err pulsed", "len_err")
        else:
            tb_note("tc_pkt_len_legal_16_4300: 16 B not reachable (1-flit clamp=20 B)")
            self.ok("tc_pkt_len_legal_16_4300")

    async def do_cfg9_no_icrc(self):
        print("=== tc_cfg9_no_icrc ===", flush=True)
        await self.tb_reset()
        await self.tb_wr_route(0x0001, 0xF)
        self.probe.clr_mon()
        in_f = lph.mk_flit(9, 0, 0, 0x0002, 0x0001, lph.plen_nflit(5), 0xA5A5, 0x5A, 0, 0)
        await self.tb_inject(0, lph.mk_beat(in_f), 2)
        saw_x = 0
        saf_f = 0
        for _ in range(16):
            await RisingEdge(self.clk)
            if bit(self.probe.x_in_v, 0):
                saw_x = 1
                saf_f = lph.nw512_flit0(ival(self.probe.saf_d[0], 0))
        if saf_f == 0:
            saf_f = lph.nw512_flit0(ival(self.probe.saf_d[0], 0))
        if bit(self.probe.fab_mgmt_cfg6_hit, 0):
            self.bad("tc_cfg9_no_icrc", "CFG9 RT=00 dest=1 (not terminate class)",
                     "fab_mgmt_cfg6_hit=0 (CFG9 has no ICRC; forward)",
                     "fab_mgmt_cfg6_hit=1", "u_fab.fab_mgmt_cfg6_hit")
        elif lph.nth_cci(saf_f) != lph.nth_cci(in_f) or lph.nth_lbf(saf_f) != lph.nth_lbf(in_f):
            self.bad("tc_cfg9_no_icrc", "CFG9 sitting in SAF (AS-0.1 §13 no ICRC)",
                     "CCI/LBF unchanged (fabric has no vibe_icrc)",
                     "SAF CCI/LBF rewritten", "u_fab.saf_d")
        elif not saw_x and not bit(self.probe.g1_comb, 0):
            self.bad("tc_cfg9_no_icrc", "CFG9 RT=00 dest=1 bitmap=1111",
                     "x_in_v=1 (forward; no ICRC terminate)",
                     "not presented to xbar", "u_fab.x_in_v")
        else:
            self.ok("tc_cfg9_no_icrc")

    async def run_all_suite(self):
        await self.do_rt00_per_flow_rr_fwd()
        await self.do_rt01_per_packet_rr_fwd()
        await self.do_rt10_must_drop()
        await self.do_rt11_must_drop()
        await self.do_rt_shortest_unimpl_count()
        await self.do_rt_shortest_irq_logic()
        await self.do_rt_irq_logic_sticky()
        await self.do_rt_no_rewrite()
        await self.do_rt10_not_as_rt00()
        await self.do_rt_counter_32b_sat()
        await self.do_cfg_identity_guid_class()
        await self.do_default_rt_all0_port0()
        await self.do_pkt_len_err_drop()
        await self.do_cfg6_term_vs_fwd()
        await self.do_saf_full_pkt()
        await self.do_icrc_transit_no_recompute()
        await self.do_cfg_fwd(3, "tc_cfg3_fwd")
        await self.do_cfg_fwd(4, "tc_cfg4_fwd")
        await self.do_cfg_fwd(5, "tc_cfg5_fwd")
        await self.do_cfg_fwd(7, "tc_cfg7_fwd")
        await self.do_cfg_fwd(9, "tc_cfg9_fwd")
        await self.do_cfg_fwd(0, "tc_cfg0_fabric_no_special")
        await self.do_cfg_reserved_fwd()
        await self.do_cfg_fwd_class()
        await self.do_port_rst_via_cfg()
        await self.do_device_rst_via_cfg()
        await self.do_pkt_len_legal_16_4300()
        await self.do_cfg9_no_icrc()


def _one(name, coro_name, *args):
    class _T(VibeFabBodies):
        async def run_phase(self, phase):
            phase.raise_objection(self)
            await getattr(self, coro_name)(*args)
            phase.drop_objection(self)

    _T.__name__ = name
    _T.__qualname__ = name
    uvm_component_utils(_T)
    return _T


tc_rt00_per_flow_rr_fwd = _one("tc_rt00_per_flow_rr_fwd", "do_rt00_per_flow_rr_fwd")
tc_rt01_per_packet_rr_fwd = _one("tc_rt01_per_packet_rr_fwd", "do_rt01_per_packet_rr_fwd")
tc_rt10_must_drop = _one("tc_rt10_must_drop", "do_rt10_must_drop")
tc_rt11_must_drop = _one("tc_rt11_must_drop", "do_rt11_must_drop")
tc_rt_shortest_unimpl_count = _one("tc_rt_shortest_unimpl_count", "do_rt_shortest_unimpl_count")
tc_rt_shortest_irq_logic = _one("tc_rt_shortest_irq_logic", "do_rt_shortest_irq_logic")
tc_rt_irq_logic_sticky = _one("tc_rt_irq_logic_sticky", "do_rt_irq_logic_sticky")
tc_rt_no_rewrite = _one("tc_rt_no_rewrite", "do_rt_no_rewrite")
tc_rt10_not_as_rt00 = _one("tc_rt10_not_as_rt00", "do_rt10_not_as_rt00")
tc_rt_counter_32b_sat = _one("tc_rt_counter_32b_sat", "do_rt_counter_32b_sat")
tc_cfg_identity_guid_class = _one("tc_cfg_identity_guid_class", "do_cfg_identity_guid_class")
tc_default_rt_all0_port0 = _one("tc_default_rt_all0_port0", "do_default_rt_all0_port0")
tc_pkt_len_err_drop = _one("tc_pkt_len_err_drop", "do_pkt_len_err_drop")
tc_cfg6_term_vs_fwd = _one("tc_cfg6_term_vs_fwd", "do_cfg6_term_vs_fwd")
tc_saf_full_pkt = _one("tc_saf_full_pkt", "do_saf_full_pkt")
tc_icrc_transit_no_recompute = _one("tc_icrc_transit_no_recompute", "do_icrc_transit_no_recompute")
tc_cfg3_fwd = _one("tc_cfg3_fwd", "do_cfg_fwd", 3, "tc_cfg3_fwd")
tc_cfg4_fwd = _one("tc_cfg4_fwd", "do_cfg_fwd", 4, "tc_cfg4_fwd")
tc_cfg5_fwd = _one("tc_cfg5_fwd", "do_cfg_fwd", 5, "tc_cfg5_fwd")
tc_cfg7_fwd = _one("tc_cfg7_fwd", "do_cfg_fwd", 7, "tc_cfg7_fwd")
tc_cfg9_fwd = _one("tc_cfg9_fwd", "do_cfg_fwd", 9, "tc_cfg9_fwd")
tc_cfg0_fabric_no_special = _one("tc_cfg0_fabric_no_special", "do_cfg_fwd", 0, "tc_cfg0_fabric_no_special")
tc_cfg_reserved_fwd = _one("tc_cfg_reserved_fwd", "do_cfg_reserved_fwd")
tc_cfg_fwd_class = _one("tc_cfg_fwd_class", "do_cfg_fwd_class")
tc_port_rst_via_cfg = _one("tc_port_rst_via_cfg", "do_port_rst_via_cfg")
tc_device_rst_via_cfg = _one("tc_device_rst_via_cfg", "do_device_rst_via_cfg")
tc_pkt_len_legal_16_4300 = _one("tc_pkt_len_legal_16_4300", "do_pkt_len_legal_16_4300")
tc_cfg9_no_icrc = _one("tc_cfg9_no_icrc", "do_cfg9_no_icrc")


class tc_suite_all(VibeFabBodies):
    async def run_phase(self, phase):
        phase.raise_objection(self)
        print("VIBE_SUITE run_all (uvm-python)", flush=True)
        await self.run_all_suite()
        phase.drop_objection(self)


uvm_component_utils(tc_suite_all)
