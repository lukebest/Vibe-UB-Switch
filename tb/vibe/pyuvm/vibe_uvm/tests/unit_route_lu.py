"""Module-level uvm-python TC for Decision-I stage-82 vibe_route_lu.

Covers reset / device_rst clearing tbl + bitmap + drop_g1; wr_en stores
wr_data at wr_idx[7:0]; lu_vld + RT=00/01 returns tbl[dest[7:0]][3:0];
lu_vld + RT=10/11 pulses drop_g1 one cycle and forces bitmap=0; without
lu_vld no drop pulse and bitmap holds; wrap-vs-DUT instance score
(cocotb instance u_u); and a pin scan with instance u_u.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/fabric/vibe_route_lu.sv: async-low rst_n, sync
device_rst OR'd into the reset clause, NBA write then lookup, drop only
on lu_vld && (rt==10 || rt==11). Product instantiator is vibe_fabric
u_rt / g_rt.u_rti; stock Icarus tc_route_lu uses u_rt; Decision-I wrap
uses instance u_u (not leftover u_rt / u_rti / u_lu).
This is not vibe_fecn_mark / vibe_vl_rr / vibe_icrc / vibe_nw_adapt /
vibe_dll / vibe_bcrc / vibe_dll_tx / vibe_dll_credit / vibe_dll_sm /
vibe_dll_rx / vibe_dll_retry_ack_sm / vibe_dll_retry_buf /
vibe_dll_retry_req_sm / vibe_port / vibe_ub_switch /
vibe_pcs_tx / vibe_pcs_rx / vibe_pcs_scramble / vibe_ebch16 /
vibe_pcs_tx_cw2beat / vibe_pcs_tx_amctl / vibe_pcs_tx_g1 /
vibe_pcs_tx_fec / vibe_rs128_120_enc / vibe_rs128_120_dec /
vibe_pcs_rx_deskew / vibe_pcs_rx_amctl_lock /
vibe_pcs_rx_unpack / vibe_pcs_tx_pack / gear / vibe_afifo /
vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module; do not ECO F1.
CHILDREN: none.
Third fabric leaf after stage-80 vibe_fecn_mark wrap and
stage-81 vibe_vl_rr wrap. Do not invent vibe_port_sel or later
fabric leaves here.
Stock Icarus tc_route_lu remains the official TP scorer
(direct vibe_route_lu top, instance u_rt). Header-only vs stock;
no Dijkstra / RT rewrite. Count/irq are fabric-side.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

DEPTH = 256
MASK8 = 0xFF
MASK4 = 0xF
MASK2 = 0x3
HIER = "u_u.bitmap / u_u.drop_g1"
WRAP = "vibe_route_lu_cocotb_top"
INST = "u_u"
# Product ports from rtl/fabric/vibe_route_lu.sv. Sequential: clk /
# async-low rst_n + sync device_rst. ovf_l (F1) is not a port.
PINS = (
    "clk", "rst_n", "device_rst",
    "wr_en", "wr_idx", "wr_data",
    "dest", "rt", "lu_vld",
    "bitmap", "drop_g1",
)
# Leftover leaf / dual-clock / F1 / sibling pins must not appear on
# the wrap top. Instance is u_u (Decision-I leaf wrappers), not
# leftover product instantiator u_rt / g_rt.u_rti or stock Icarus u_rt.
ABSENT = (
    "clk_fab",
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld",
    "u_fecn", "u_f", "u_n", "u_nw", "u_icrc", "u_bcrc", "u_b",
    "u_l", "u_dsk", "u_un", "u_fec",
    "u_crd", "u_sm", "u_rbuf", "u_dll", "u_tx", "u_rx",
    "u_ack", "u_req", "u_rack", "u_adapt",
    "u_vl", "u_rr", "u_lu", "u_rt", "u_rti", "u_ps", "u_voq",
    "u_saf", "u_xbar",
    "cci_in", "voq_occ", "cci_out", "marked",
    "nonempty", "grant", "vl_sel", "valid",
    "start", "in_vld", "in_byte", "last", "crc_out", "done",
    "lane_id", "seed_load", "en", "cw_sel", "cw", "u_cw", "u_a",
    "cw_data", "cw_vld", "cw_ready", "beat_data", "beat_vld", "beat_ready",
    "amctl_40B", "sdf_period", "fec_fail", "data_out",
    "u_g", "u_g1", "u_enc", "u_enc_a", "u_enc_b", "u_pack", "u_dec",
    "grain_n", "is_cfg0",
    "credit_ret", "credit_ret_n",
    "pending", "credit_low", "force_crd_ack",
    "bp_nw", "proto_err", "fc_ovf",
    "param_ok", "credit_ok", "dll_error",
    "in_flit", "error_flag", "crc_word",
    "in_sym", "parity", "in_ready",
    "win_data", "win_vld", "win_ready",
    "locked", "lid", "lid_bad", "is_amctl", "sdf", "edf",
    "bcrc_fail", "start_retry", "rx_ovf", "cfg0_hit",
    "link_up", "port_rst", "status_up", "disabled",
    "pcs_dll_data", "pcs_dll_vld", "dll_nw_ready",
    "pcs_dll_ready", "dll_nw_data", "dll_nw_vld",
    "start_ack", "rd_ptr", "wr_ptr", "rcv_ptr", "tail_ptr", "num_free",
    "link_ready", "fab_nw_data", "fab_nw_vld", "fab_nw_ready",
)


class Golden:
    """Cycle-accurate tbl / bitmap / drop_g1 vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.tbl = [0] * DEPTH
        self.bitmap = 0
        self.drop_g1 = 0

    def step(self, wr_en=0, wr_idx=0, wr_data=0, dest=0, rt=0, lu_vld=0,
             device_rst=0):
        if device_rst:
            self.reset()
            return
        self.drop_g1 = 0
        if wr_en:
            self.tbl[int(wr_idx) & MASK8] = int(wr_data) & 0xFFFFFFFF
        if lu_vld:
            rtv = int(rt) & MASK2
            if rtv in (0b10, 0b11):
                self.drop_g1 = 1
                self.bitmap = 0
            else:
                self.bitmap = self.tbl[int(dest) & MASK8] & MASK4


class tc_vibe_route_lu(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.device_rst, 0)
        sset(d.wr_en, 0)
        sset(d.wr_idx, 0)
        sset(d.wr_data, 0)
        sset(d.dest, 0)
        sset(d.rt, 0)
        sset(d.lu_vld, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        self.g.reset()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def _drive(self, wr_en=0, wr_idx=0, wr_data=0, dest=0, rt=0,
                     lu_vld=0, device_rst=0):
        d = self.dut
        sset(d.device_rst, 1 if device_rst else 0)
        sset(d.wr_en, 1 if wr_en else 0)
        sset(d.wr_idx, int(wr_idx) & 0xFFFF)
        sset(d.wr_data, int(wr_data) & 0xFFFFFFFF)
        sset(d.dest, int(dest) & 0xFFFF)
        sset(d.rt, int(rt) & MASK2)
        sset(d.lu_vld, 1 if lu_vld else 0)
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return ival(d.bitmap, -1), ival(d.drop_g1, -1)

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        return ival(u.bitmap, -1), ival(u.drop_g1, -1)

    def _score_inner(self, name, stim, got):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        ibm, ig1 = inner
        bm, g1 = got
        if ig1 != g1:
            self.bad(name, stim + f" (port vs {INST})",
                     f"drop_g1={g1} bitmap={bm}",
                     f"{INST} drop_g1={ig1} bitmap={ibm}",
                     HIER)
            return False
        if bm is None or ibm is None:
            if bm != ibm:
                self.bad(name, stim + f" ({INST} vs wrap)",
                         f"bitmap={bm}", f"{INST}.bitmap={ibm}",
                         f"{INST}.bitmap")
                return False
            return True
        if (int(ibm) & MASK4) != (int(bm) & MASK4):
            self.bad(name, stim + f" ({INST} vs wrap)",
                     f"bitmap={bm}", f"{INST}.bitmap={ibm}",
                     f"{INST}.bitmap")
            return False
        return True

    def _fmt(self, s):
        bm, g1 = s
        return f"bitmap={bm} drop_g1={g1}"

    def _score(self, name, stim, got):
        exp = (self.g.bitmap & MASK4, self.g.drop_g1)
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        if not self._score_inner(name, stim, got):
            return False
        return True

    async def _cycle(self, wr_en=0, wr_idx=0, wr_data=0, dest=0, rt=0,
                     lu_vld=0, device_rst=0):
        await self._drive(wr_en, wr_idx, wr_data, dest, rt, lu_vld,
                          device_rst)
        self.g.step(wr_en, wr_idx, wr_data, dest, rt, lu_vld, device_rst)
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, wr_en=0, wr_idx=0, wr_data=0,
                      dest=0, rt=0, lu_vld=0, device_rst=0):
        got = await self._cycle(wr_en, wr_idx, wr_data, dest, rt, lu_vld,
                                device_rst)
        if not self._score(name, stim, got):
            return None
        return got

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_route_lu"
        self.g = Golden()

        gchk = Golden()
        gchk.step(wr_en=1, wr_idx=1, wr_data=0xF)
        gchk.step(dest=1, rt=0, lu_vld=1)
        if gchk.bitmap != 0xF or gchk.drop_g1:
            self.bad(name, "golden RT=00 lookup",
                     "bitmap=15 drop_g1=0",
                     f"bitmap={gchk.bitmap} drop_g1={gchk.drop_g1}", "golden")
            phase.drop_objection(self)
            return
        gchk.step(dest=1, rt=0b10, lu_vld=1)
        if gchk.bitmap != 0 or gchk.drop_g1 != 1:
            self.bad(name, "golden RT=10 drop",
                     "bitmap=0 drop_g1=1",
                     f"bitmap={gchk.bitmap} drop_g1={gchk.drop_g1}", "golden")
            phase.drop_objection(self)
            return
        gchk.step(lu_vld=0, rt=0b10)
        if gchk.drop_g1 or gchk.bitmap != 0:
            self.bad(name, "golden !lu_vld holds bitmap, no drop",
                     "bitmap=0 drop_g1=0",
                     f"bitmap={gchk.bitmap} drop_g1={gchk.drop_g1}", "golden")
            phase.drop_objection(self)
            return
        gchk.reset()
        if any(gchk.tbl) or gchk.bitmap or gchk.drop_g1:
            self.bad(name, "golden reset",
                     "tbl/bitmap/drop_g1=0",
                     f"bitmap={gchk.bitmap}", "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: outputs 0; empty-table lookup → bitmap 0.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "reset idle ports",
                     "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "lu dest=1 empty table", dest=1, rt=0, lu_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "empty table lookup",
                     "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. Write several entries; RT=00/01 return low 4 bits at dest[7:0].
        writes = (
            (1, 0x0000000F),
            (2, 0xABCDE5A3),
            (7, 0x0000000A),
            (0xFF, 0x0FFFFFFC),
            (0x0203, 0x00000006),
        )
        for idx, data in writes:
            if await self._expect(
                    name, f"wr tbl[{idx & MASK8}]=0x{data:08x}",
                    wr_en=1, wr_idx=idx, wr_data=data) is None:
                phase.drop_objection(self)
                return

        lookups = (
            ("RT=00 dest=1 data=F", 1, 0b00, 0xF),
            ("RT=01 dest=2 data=A3 → nibble 3", 2, 0b01, 0x3),
            ("RT=00 dest=7 data=A", 7, 0b00, 0xA),
            ("RT=01 dest=FF data=C", 0xFF, 0b01, 0xC),
            ("dest[15:8] ignored (0x1103 → tbl[3]=6)",
             0x1103, 0b00, 0x6),
        )
        for stim, dest, rt, exp_bm in lookups:
            got = await self._expect(
                name, stim, dest=dest, rt=rt, lu_vld=1)
            if got is None:
                phase.drop_objection(self)
                return
            if got != (exp_bm, 0):
                self.bad(name, stim,
                         f"bitmap={exp_bm} drop_g1=0", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        held = got
        if await self._expect(
                name, "hold bitmap without lu_vld after RT=00",
                dest=0x0101, rt=0b00, lu_vld=0) is None:
            phase.drop_objection(self)
            return
        if self._sample() != held:
            self.bad(name, "!lu_vld must hold prior bitmap",
                     self._fmt(held), self._fmt(self._sample()), HIER)
            phase.drop_objection(self)
            return

        # 3. RT=10 / RT=11 with lu_vld → 1-cycle drop_g1, bitmap=0.
        got = await self._expect(
            name, "RT=10 lu_vld drop (not alias 00)",
            dest=1, rt=0b10, lu_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 1):
            self.bad(name, "RT=10",
                     "bitmap=0 drop_g1=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "drop_g1 is a 1-cycle pulse (next cycle !lu_vld)",
            dest=1, rt=0b10, lu_vld=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "RT=10 pulse must fall without lu_vld",
                     "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=11 lu_vld drop",
            dest=7, rt=0b11, lu_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 1):
            self.bad(name, "RT=11",
                     "bitmap=0 drop_g1=1", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "RT=11 pulse falls on the next cycle",
            dest=7, rt=0b11, lu_vld=0)
        if got is None or got != (0, 0):
            if got is not None:
                self.bad(name, "RT=11 pulse width",
                         "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Table was not cleared by drop: RT=00 dest=2 still returns nibble 3.
        got = await self._expect(
            name, "after drop, RT=00 dest=2 still tbl nibble",
            dest=2, rt=0b00, lu_vld=1)
        if got is None or got != (0x3, 0):
            if got is not None:
                self.bad(name, "drop must not wipe tbl",
                         "bitmap=3 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 4. Without lu_vld: RT=10/11 must not pulse drop or rewrite bitmap.
        held_bm = 0x3
        for i, rt in enumerate((0b10, 0b11)):
            got = await self._expect(
                name, f"!lu_vld RT={rt:02b} must not drop [{i}]",
                dest=2, rt=rt, lu_vld=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got != (held_bm, 0):
                self.bad(name, f"spurious drop/update without lu_vld RT={rt:02b}",
                         f"bitmap={held_bm} drop_g1=0", self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        # Write a new value while !lu_vld: bitmap holds prior lookup.
        if await self._expect(
                name, "wr dest=2 data=9 without lu_vld (bitmap holds)",
                wr_en=1, wr_idx=2, wr_data=0x9, dest=2, rt=0, lu_vld=0) is None:
            phase.drop_objection(self)
            return
        if self.g.bitmap != held_bm:
            self.bad(name, "write-only must not update bitmap",
                     f"bitmap={held_bm}", f"bitmap={self.g.bitmap}", HIER)
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "lu dest=2 after silent write → nibble 9",
            dest=2, rt=0b01, lu_vld=1)
        if got is None or got != (0x9, 0):
            if got is not None:
                self.bad(name, "lookup after silent write",
                         "bitmap=9 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 5. device_rst (sync) clears outputs and table.
        sset(d.device_rst, 1)
        await Timer(100, "PS")
        mid = self._sample()
        if mid != (0x9, 0):
            self.bad(name, "device_rst before posedge (sync, 100ps)",
                     "bitmap holds 9 (no async clear)",
                     self._fmt(mid), HIER)
            phase.drop_objection(self)
            return
        self.g.step(device_rst=1)
        await self._to_fall()
        sset(d.device_rst, 0)
        got = self._sample()
        if not self._score(name, "device_rst posedge clears outs", got):
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "device_rst clears bitmap/drop_g1",
                     "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "device_rst then lu dest=1 (table all-0)",
            dest=1, rt=0, lu_vld=1)
        if got is None or got != (0, 0):
            if got is not None:
                self.bad(name, "lookup after device_rst",
                         "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # Re-program dest=1 and confirm table is writable again.
        if await self._expect(
                name, "re-wr dest=1 data=F after device_rst",
                wr_en=1, wr_idx=1, wr_data=0xF) is None:
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "lu dest=1 after re-write",
            dest=1, rt=0, lu_vld=1)
        if got is None or got != (0xF, 0):
            if got is not None:
                self.bad(name, "lookup after re-write",
                         "bitmap=15 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 6. Async rst_n mid-stream clears outs (no posedge).
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "async rst_n mid-stream",
                     "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)
        got = await self._expect(
            name, "after async rst, empty lu dest=1",
            dest=1, rt=0, lu_vld=1)
        if got is None or got != (0, 0):
            if got is not None:
                self.bad(name, "post-async-rst empty table",
                         "bitmap=0 drop_g1=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 7. Leaf pins match product SV (clk / rst_n / device_rst /
        # wr_en / wr_idx / wr_data / dest / rt / lu_vld / bitmap /
        # drop_g1; no ovf_l / leftover u_rt).
        # Instance u_u (not leftover u_rt / u_rti / u_lu / u_rr).
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_route_lu product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return
        u = getattr(d, INST)
        for need in PINS:
            if not hasattr(u, need):
                self.bad(name, f"leaf instance pin scan ({INST}.{need})",
                         f"{INST}.{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_route_lu)
