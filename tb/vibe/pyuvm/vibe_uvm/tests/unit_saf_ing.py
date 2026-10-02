"""Module-level uvm-python TC for Decision-I stage-85 vibe_saf_ing.

Covers reset clearing pointers / assemble state / len_err (combo
in_ready=1, pkt_vld=0); store-and-forward hold until declared
beats are assembled (not cut-through); wr then drain data/sop/eop
and pkt_bytes; 1-beat sop&&eop; oversize PLEN pulses len_err and
rewinds wptr; max-legal 4300 B SOP does not error; async rst_n
mid-stream; wrap-vs-DUT instance score (cocotb instance u_u); and
a pin scan with instance u_u.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/fabric/vibe_saf_ing.sv: async-low rst_n, combo
in_ready / pkt_*, DEPTH=128, header temps vibe_lph_plength /
vibe_decl_flits / vibe_nw512_decl_beats, Packet Length Error when
(dflits*20) not in 16–4300. Product instantiator is vibe_fabric
g_saf.u_saf; stock Icarus tc_saf_ing uses u_s; Decision-I wrap
uses instance u_u (not leftover u_saf / u_s).
This is not vibe_fecn_mark / vibe_vl_rr / vibe_route_lu /
vibe_port_sel / vibe_voq_egr / vibe_icrc / vibe_nw_adapt /
vibe_dll / vibe_bcrc / vibe_dll_tx / vibe_dll_credit /
vibe_dll_sm / vibe_dll_rx / vibe_dll_retry_ack_sm /
vibe_dll_retry_buf / vibe_dll_retry_req_sm / vibe_port /
vibe_ub_switch / vibe_pcs_tx / vibe_pcs_rx / vibe_pcs_scramble /
vibe_ebch16 / vibe_pcs_tx_cw2beat / vibe_pcs_tx_amctl /
vibe_pcs_tx_g1 / vibe_pcs_tx_fec / vibe_rs128_120_enc /
vibe_rs128_120_dec / vibe_pcs_rx_deskew / vibe_pcs_rx_amctl_lock /
vibe_pcs_rx_unpack / vibe_pcs_tx_pack / gear / vibe_afifo /
vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module; do not ECO F1.
CHILDREN: none.
Sixth fabric leaf after stage-80 vibe_fecn_mark wrap, stage-81
vibe_vl_rr wrap, stage-82 vibe_route_lu wrap, stage-83
vibe_port_sel wrap, and stage-84 vibe_voq_egr wrap. Do not invent
vibe_xbar or later fabric leaves here.
Stock Icarus tc_saf_ing remains the official TP scorer
(direct vibe_saf_ing top, instance u_s). Header-only vs stock;
no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

DEPTH = 128
MASK7 = 0x7F
MASK16 = 0xFFFF
MASK512 = (1 << 512) - 1
PKT_LEN_MIN = 16
PKT_LEN_MAX = 4300
HIER = "u_u.in_ready / u_u.pkt_* / u_u.len_err"
WRAP = "vibe_saf_ing_cocotb_top"
INST = "u_u"
# Product ports from rtl/fabric/vibe_saf_ing.sv. Sequential: clk /
# async-low rst_n. ovf_l (F1) is not a port.
PINS = (
    "clk", "rst_n",
    "in_data", "in_vld", "in_ready",
    "pkt_data", "pkt_vld", "pkt_ready",
    "pkt_sop", "pkt_eop", "pkt_bytes", "len_err",
)
# Leftover leaf / dual-clock / F1 / sibling pins must not appear on
# the wrap top. Instance is u_u (Decision-I leaf wrappers), not
# leftover product instantiator g_saf.u_saf or stock Icarus u_s.
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
    "u_vl", "u_rr", "u_lu", "u_rt", "u_rti", "u_ps", "u_psi",
    "u_voq", "u_v", "u_saf", "u_s", "u_xbar",
    "cci_in", "voq_occ", "cci_out", "marked",
    "grant", "vl_sel", "valid",
    "device_rst", "wr_idx", "lu_vld",
    "egr", "drop", "drop_down_cnt",
    "bitmap", "drop_g1", "status_up", "default_bm",
    "rt", "sel_vld", "cfg", "src", "dest", "vl",
    "wr_vl", "wr_en", "wr_data", "wr_sop", "wr_eop", "wr_ready",
    "rd_vl", "rd_en", "rd_data", "rd_sop", "rd_eop",
    "nonempty", "occ_vl0", "deadlock_drop", "deadlock_cnt",
    "start", "in_byte", "last", "crc_out", "done",
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
    "in_sym", "parity",
    "win_data", "win_vld", "win_ready",
    "locked", "lid", "lid_bad", "is_amctl", "sdf", "edf",
    "bcrc_fail", "start_retry", "rx_ovf", "cfg0_hit",
    "link_up", "port_rst", "disabled",
    "pcs_dll_data", "pcs_dll_vld", "dll_nw_ready",
    "pcs_dll_ready", "dll_nw_data", "dll_nw_vld",
    "start_ack", "rd_ptr", "wr_ptr", "rcv_ptr", "tail_ptr", "num_free",
    "link_ready", "fab_nw_data", "fab_nw_vld", "fab_nw_ready",
)


def header_fields(beat):
    """Stock vibe_ub_fn.vh: plen / dflits / bytes / decl_beats."""
    flit0 = lph.nw512_flit0(int(beat) & MASK512)
    plen = lph.lph_plength(flit0)
    dflits = lph.decl_flits(plen)
    bytes_ = dflits * 20
    decl = lph.decl_beats(plen)
    return plen, dflits, bytes_, decl


def sop_beat(nflit, payload_lo=0):
    """Official LPH SOP beat: cfg=3, RT=00, scna=1, dcna=1."""
    return lph.mk_beat(
        lph.mk_flit(3, 0, 0, 1, 1, lph.plen_nflit(nflit)),
        int(payload_lo) & ((1 << 352) - 1),
    )


def oversize_beat(payload_lo=0):
    return lph.mk_beat(
        lph.mk_flit(3, 0, 0, 1, 1, lph.plen_oversize()),
        int(payload_lo) & ((1 << 352) - 1),
    )


def max_legal_beat(payload_lo=0):
    return lph.mk_beat(
        lph.mk_flit(3, 0, 0, 1, 1, lph.plen_4300()),
        int(payload_lo) & ((1 << 352) - 1),
    )


def body_beat(tag):
    """Distinct mid/EOP body: tag in [31:0] and [511:496]."""
    tag = int(tag) & 0xFFFFFFFF
    return tag | ((tag & 0xFFFF) << 496)


class Golden:
    """Cycle-accurate pointers / mem / assemble vs product NBA."""

    def __init__(self):
        self.mem = [0] * DEPTH
        self.reset()

    def reset(self):
        # Product reset does not wipe mem.
        self.wptr = 0
        self.rptr = 0
        self.beat_cnt = 0
        self.decl_beats = 0
        self.bytes = 0
        self.assembling = 0
        self.done = 0
        self.len_err = 0

    def in_ready(self):
        return int(((self.wptr + 1) & MASK7) != self.rptr)

    def pkt_vld(self):
        return int(bool(self.done) and (self.rptr != self.wptr))

    def pkt_data(self):
        return self.mem[self.rptr & MASK7] & MASK512

    def pkt_sop(self):
        return int(self.pkt_vld() and (self.rptr == 0 or self.beat_cnt == 0))

    def pkt_eop(self):
        return int(self.pkt_vld() and (((self.rptr + 1) & MASK7) == self.wptr))

    def step(self, in_data=0, in_vld=0, pkt_ready=0):
        in_data = int(in_data) & MASK512
        in_ready = self.in_ready()
        pkt_vld = self.pkt_vld()
        pkt_eop = self.pkt_eop()
        self.len_err = 0
        if in_vld and in_ready:
            self.mem[self.wptr & MASK7] = in_data
            self.wptr = (self.wptr + 1) & MASK7
            if not self.assembling:
                _plen, _dflits, bytes_, decl = header_fields(in_data)
                self.assembling = 1
                self.decl_beats = decl & MASK7
                self.bytes = bytes_ & MASK16
                self.beat_cnt = 1
                if bytes_ < PKT_LEN_MIN or bytes_ > PKT_LEN_MAX:
                    self.len_err = 1
                    self.assembling = 0
                    self.wptr = self.rptr
                elif decl == 1:
                    self.assembling = 0
                    self.done = 1
            else:
                self.beat_cnt = (self.beat_cnt + 1) & MASK7
                if self.beat_cnt >= self.decl_beats:
                    self.assembling = 0
                    self.done = 1
        if pkt_vld and pkt_ready:
            self.rptr = (self.rptr + 1) & MASK7
            if pkt_eop:
                self.done = 0
                self.wptr = 0
                self.rptr = 0


class tc_vibe_saf_ing(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.in_data, 0)
        sset(d.in_vld, 0)
        sset(d.pkt_ready, 0)

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

    async def _drive(self, in_data=0, in_vld=0, pkt_ready=0):
        d = self.dut
        sset(d.in_data, int(in_data) & MASK512)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.pkt_ready, 1 if pkt_ready else 0)
        await Timer(100, "PS")

    def _sample(self):
        d = self.dut
        return (
            ival(d.in_ready, -1),
            ival(d.pkt_vld, -1),
            ival(d.pkt_sop, -1),
            ival(d.pkt_eop, -1),
            ival(d.pkt_data, -1),
            ival(d.pkt_bytes, -1),
            ival(d.len_err, -1),
        )

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        return (
            ival(u.in_ready, -1),
            ival(u.pkt_vld, -1),
            ival(u.pkt_sop, -1),
            ival(u.pkt_eop, -1),
            ival(u.pkt_data, -1),
            ival(u.pkt_bytes, -1),
            ival(u.len_err, -1),
        )

    def _score_inner(self, name, stim, got):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        irdy, ivld, isop, ieop, idata, iby, ierr = inner
        rdy, vld, sop, eop, data, by, err = got
        if ierr != err:
            self.bad(name, stim + f" (port vs {INST})",
                     f"len_err={err} pkt={vld}/{sop}/{eop}",
                     f"{INST} len_err={ierr} pkt={ivld}/{isop}/{ieop}",
                     HIER)
            return False
        pairs = (
            ("in_ready", rdy, irdy, 1),
            ("pkt_vld", vld, ivld, 1),
            ("pkt_sop", sop, isop, 1),
            ("pkt_eop", eop, ieop, 1),
            ("pkt_data", data, idata, MASK512),
            ("pkt_bytes", by, iby, MASK16),
            ("len_err", err, ierr, 1),
        )
        for pname, outer, inner_v, mask in pairs:
            if outer is None or inner_v is None:
                if outer != inner_v:
                    self.bad(name, stim + f" ({INST} vs wrap)",
                             f"{pname}={outer}",
                             f"{INST}.{pname}={inner_v}",
                             f"{INST}.{pname}")
                    return False
            elif (int(inner_v) & mask) != (int(outer) & mask):
                self.bad(name, stim + f" ({INST} vs wrap)",
                         f"{pname}={outer}",
                         f"{INST}.{pname}={inner_v}",
                         f"{INST}.{pname}")
                return False
        return True

    def _fmt(self, s):
        rdy, vld, sop, eop, data, by, err = s
        return (f"in_ready={rdy} pkt={vld}/{sop}/{eop} "
                f"data={data} bytes={by} len_err={err}")

    def _peek_state(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        keys = ("wptr", "rptr", "beat_cnt", "decl_beats",
                "bytes", "assembling", "done", "len_err")
        out = {}
        try:
            for k in keys:
                out[k] = ival(getattr(u, k), None)
        except Exception:
            return None
        return out

    def _score(self, name, stim, got, score_data=True):
        exp = (
            self.g.in_ready(),
            self.g.pkt_vld(),
            self.g.pkt_sop(),
            self.g.pkt_eop(),
            self.g.pkt_data() if self.g.pkt_vld() else None,
            self.g.bytes & MASK16,
            self.g.len_err,
        )
        rdy, vld, sop, eop, data, by, err = got
        if (rdy != exp[0] or vld != exp[1] or sop != exp[2]
                or eop != exp[3] or (by & MASK16) != exp[5] or err != exp[6]):
            self.bad(name, stim,
                     (f"in_ready={exp[0]} pkt={exp[1]}/{exp[2]}/{exp[3]} "
                      f"bytes={exp[5]} len_err={exp[6]}"),
                     self._fmt(got), HIER)
            return False
        if score_data and exp[1] and exp[4] is not None:
            if (data & MASK512) != (exp[4] & MASK512):
                self.bad(name, stim + " (pkt_data)",
                         f"pkt_data={exp[4]}",
                         self._fmt(got), f"{INST}.pkt_data")
                return False
        if not self._score_inner(name, stim, got):
            return False
        st = self._peek_state()
        if st is not None:
            checks = (
                ("wptr", self.g.wptr, MASK7),
                ("rptr", self.g.rptr, MASK7),
                ("beat_cnt", self.g.beat_cnt, MASK7),
                ("decl_beats", self.g.decl_beats, MASK7),
                ("bytes", self.g.bytes, MASK16),
                ("assembling", self.g.assembling, 1),
                ("done", self.g.done, 1),
                ("len_err", self.g.len_err, 1),
            )
            for key, exp_v, mask in checks:
                got_v = st.get(key)
                if got_v is None:
                    continue
                if (got_v & mask) != (exp_v & mask):
                    self.bad(name, stim + f" ({INST}.{key})",
                             f"{key}={exp_v}",
                             f"{INST}.{key}={got_v}", f"{INST}.{key}")
                    return False
        return True

    async def _cycle(self, in_data=0, in_vld=0, pkt_ready=0):
        await self._drive(in_data, in_vld, pkt_ready)
        self.g.step(in_data, in_vld, pkt_ready)
        await self._to_fall()
        return self._sample()

    async def _expect(self, name, stim, in_data=0, in_vld=0, pkt_ready=0,
                      score_data=True):
        got = await self._cycle(in_data, in_vld, pkt_ready)
        if not self._score(name, stim, got, score_data=score_data):
            return None
        return got

    def _golden_selfcheck(self, name):
        gchk = Golden()
        if (gchk.in_ready() != 1 or gchk.pkt_vld() or gchk.len_err
                or gchk.pkt_sop() or gchk.pkt_eop()):
            self.bad(name, "golden reset idle",
                     "in_ready=1 pkt=0/0/0 len_err=0",
                     (f"rdy={gchk.in_ready()} vld={gchk.pkt_vld()} "
                      f"err={gchk.len_err}"),
                     "golden")
            return False
        b0 = sop_beat(5, 0xA5)
        gchk.step(in_data=b0, in_vld=1)
        if gchk.pkt_vld() or gchk.len_err or gchk.assembling != 1:
            self.bad(name, "golden 1 of 2 declared beats",
                     "pkt_vld=0 assembling=1",
                     f"vld={gchk.pkt_vld()} asm={gchk.assembling}",
                     "golden")
            return False
        b1 = body_beat(0xB)
        gchk.step(in_data=b1, in_vld=1)
        if (not gchk.pkt_vld() or gchk.pkt_sop() != 1 or gchk.pkt_eop() != 0
                or gchk.pkt_data() != b0 or gchk.bytes != 100):
            self.bad(name, "golden 2nd beat of 2",
                     f"vld/sop/eop=1/1/0 data={b0} bytes=100",
                     (f"pkt={gchk.pkt_vld()}/{gchk.pkt_sop()}/{gchk.pkt_eop()} "
                      f"data={gchk.pkt_data()} bytes={gchk.bytes}"),
                     "golden")
            return False
        gchk.step(pkt_ready=1)
        if (not gchk.pkt_vld() or gchk.pkt_sop() or gchk.pkt_eop() != 1
                or gchk.pkt_data() != b1):
            self.bad(name, "golden drain first beat",
                     f"vld/sop/eop=1/0/1 data={b1}",
                     (f"pkt={gchk.pkt_vld()}/{gchk.pkt_sop()}/{gchk.pkt_eop()} "
                      f"data={gchk.pkt_data()}"),
                     "golden")
            return False
        gchk.step(pkt_ready=1)
        if gchk.pkt_vld() or gchk.done or gchk.wptr or gchk.rptr:
            self.bad(name, "golden EOP drain clears",
                     "pkt_vld=0 done=0 wptr=0 rptr=0",
                     f"vld={gchk.pkt_vld()} done={gchk.done}",
                     "golden")
            return False
        gchk.reset()
        one = sop_beat(1, 0x11)
        gchk.step(in_data=one, in_vld=1)
        if not (gchk.pkt_vld() and gchk.pkt_sop() and gchk.pkt_eop()):
            self.bad(name, "golden 1-flit sop&&eop",
                     "vld&&sop&&eop",
                     f"{gchk.pkt_vld()} {gchk.pkt_sop()} {gchk.pkt_eop()}",
                     "golden")
            return False
        if gchk.bytes != 20:
            self.bad(name, "golden 1-flit bytes",
                     "pkt_bytes=20", f"bytes={gchk.bytes}", "golden")
            return False
        gchk.reset()
        bad = oversize_beat(0xEE)
        gchk.step(in_data=bad, in_vld=1)
        if not gchk.len_err or gchk.pkt_vld() or gchk.wptr != gchk.rptr:
            self.bad(name, "golden oversize PLEN",
                     "len_err=1 pkt_vld=0 wptr==rptr",
                     f"err={gchk.len_err} vld={gchk.pkt_vld()}",
                     "golden")
            return False
        gchk.reset()
        mx = max_legal_beat(0x43)
        gchk.step(in_data=mx, in_vld=1)
        if gchk.len_err or gchk.pkt_vld() or gchk.assembling != 1:
            self.bad(name, "golden max-legal 4300 SOP",
                     "len_err=0 pkt_vld=0 assembling=1",
                     f"err={gchk.len_err} asm={gchk.assembling}",
                     "golden")
            return False
        _, _, mx_bytes, mx_decl = header_fields(mx)
        if mx_bytes != 4300 or mx_decl != 68:
            self.bad(name, "golden plen_4300 decode",
                     "bytes=4300 decl_beats=68",
                     f"bytes={mx_bytes} decl={mx_decl}",
                     "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_saf_ing"
        self.g = Golden()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: combo empty, assemble/len_err cleared.
        got = self._sample()
        if not self._score(name, "reset then release, idle", got,
                           score_data=False):
            phase.drop_objection(self)
            return
        if (got[0] != 1 or got[1] != 0 or got[2] != 0 or got[3] != 0
                or got[6] != 0):
            self.bad(name, "reset idle ports",
                     "in_ready=1 pkt=0/0/0 len_err=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. 5 flits → 2 declared beats; first beat must not present.
        b0 = sop_beat(5, 0xA5A5)
        got = await self._expect(
            name, "1 of 2 declared beats (SAF hold)",
            in_data=b0, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 0 or got[6] != 0:
            self.bad(name, "1 of 2 declared beats",
                     "pkt_vld=0 len_err=0 (SAF, not cut-through)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "idle hold after first beat still assembling",
            in_data=0, in_vld=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 0:
            self.bad(name, "hold after 1 of 2",
                     "pkt_vld=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        b1 = body_beat(0xB)
        got = await self._expect(
            name, "2nd beat of 2 presents SOP",
            in_data=b1, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] != 1 or got[2] != 1 or got[3] != 0
                or (got[4] & MASK512) != b0 or got[5] != 100):
            self.bad(name, "2nd beat of 2",
                     f"pkt=1/1/0 data={b0} bytes=100",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "idle hold after assemble (head stays)",
            in_data=0, in_vld=0, pkt_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] != 1 or (got[4] & MASK512) != b0 or got[2] != 1):
            self.bad(name, "head must hold without pkt_ready",
                     f"pkt=1/1/0 data={b0}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "drain first beat of 2",
            pkt_ready=1)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] != 1 or got[2] != 0 or got[3] != 1
                or (got[4] & MASK512) != b1):
            self.bad(name, "second beat becomes head",
                     f"pkt=1/0/1 data={b1}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "drain EOP of 2-beat packet",
            pkt_ready=1, score_data=False)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 0 or got[6] != 0:
            self.bad(name, "EOP drain empties",
                     "pkt_vld=0 len_err=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 3. Oversize PLEN → 1-cycle len_err, drop, rewind.
        bad = oversize_beat(0xEE)
        got = await self._expect(
            name, "oversize PLEN",
            in_data=bad, in_vld=1, score_data=False)
        if got is None:
            phase.drop_objection(self)
            return
        if got[6] != 1 or got[1] != 0:
            self.bad(name, "oversize PLEN",
                     "len_err=1 pkt_vld=0", self._fmt(got),
                     f"{INST}.len_err")
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "len_err is a 1-cycle pulse",
            in_data=0, in_vld=0, score_data=False)
        if got is None:
            phase.drop_objection(self)
            return
        if got[6] != 0 or got[1] != 0:
            self.bad(name, "len_err pulse ends",
                     "len_err=0 pkt_vld=0", self._fmt(got),
                     f"{INST}.len_err")
            phase.drop_objection(self)
            return

        # 4. 9 flits → 3 declared beats; mid-assemble still hidden.
        c0 = sop_beat(9, 0xC0)
        got = await self._expect(
            name, "1 of 3 declared beats",
            in_data=c0, in_vld=1)
        if got is None or got[1] != 0:
            if got is not None:
                self.bad(name, "1 of 3",
                         "pkt_vld=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        c1 = body_beat(0xC1)
        got = await self._expect(
            name, "2 of 3 declared beats",
            in_data=c1, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[1] != 0:
            self.bad(name, "2 of 3 declared beats",
                     "pkt_vld=0 (still assembling)",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        c2 = body_beat(0xC2)
        got = await self._expect(
            name, "3rd beat of 3 presents SOP",
            in_data=c2, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] != 1 or got[2] != 1 or got[3] != 0
                or (got[4] & MASK512) != c0 or got[5] != 180):
            self.bad(name, "3rd beat of 3",
                     f"pkt=1/1/0 data={c0} bytes=180",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        for stim, exp_sop, exp_eop, exp_data in (
            ("drain beat 0 of 3", 0, 0, c1),
            ("drain beat 1 of 3", 0, 1, c2),
        ):
            got = await self._expect(name, stim, pkt_ready=1)
            if got is None:
                phase.drop_objection(self)
                return
            if (got[2] != exp_sop or got[3] != exp_eop
                    or (got[4] & MASK512) != exp_data):
                self.bad(name, stim,
                         f"sop/eop={exp_sop}/{exp_eop} data={exp_data}",
                         self._fmt(got), HIER)
                phase.drop_objection(self)
                return

        got = await self._expect(
            name, "drain EOP of 3-beat packet",
            pkt_ready=1, score_data=False)
        if got is None or got[1] != 0:
            if got is not None:
                self.bad(name, "3-beat EOP drain empties",
                         "pkt_vld=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 5. 1-flit / 1-beat: complete on SOP so sop&&eop coincide.
        one = sop_beat(1, 0x11)
        got = await self._expect(
            name, "1-flit packet",
            in_data=one, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if not (got[1] and got[2] and got[3]):
            self.bad(name, "1-flit packet",
                     "vld&&sop&&eop",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        if (got[4] & MASK512) != one or got[5] != 20:
            self.bad(name, "1-flit data/bytes",
                     f"data={one} bytes=20",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        got = await self._expect(
            name, "drain 1-flit EOP",
            pkt_ready=1, score_data=False)
        if got is None or got[1] != 0:
            if got is not None:
                self.bad(name, "1-flit drain empties",
                         "pkt_vld=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 6. Max-legal 4300 B SOP: no len_err, still assembling.
        mx = max_legal_beat(0x43)
        got = await self._expect(
            name, "max-legal 4300 SOP",
            in_data=mx, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[6] != 0 or got[1] != 0 or got[5] != 4300:
            self.bad(name, "max-legal 4300 SOP",
                     "len_err=0 pkt_vld=0 bytes=4300",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 7. Async rst_n mid-stream (assembling 4300) — no posedge.
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-stream (100ps, no posedge)",
                           got, score_data=False):
            phase.drop_objection(self)
            return
        if (got[0] != 1 or got[1] != 0 or got[6] != 0):
            self.bad(name, "async rst_n mid-stream",
                     "in_ready=1 pkt_vld=0 len_err=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        await self._idle()
        await self._release_reset()
        await FallingEdge(d.clk)

        # After async rst, a 1-beat packet must complete again.
        one2 = sop_beat(1, 0x22)
        got = await self._expect(
            name, "1-flit after async rst",
            in_data=one2, in_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if not (got[1] and got[2] and got[3] and (got[4] & MASK512) == one2):
            self.bad(name, "1-flit after async rst",
                     f"vld&&sop&&eop data={one2}",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 8. Leaf pins match product SV (clk / rst_n / in_* / pkt_* /
        # len_err; no ovf_l / leftover u_saf). Instance u_u (not
        # leftover u_saf / u_s / u_voq / u_v).
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_saf_ing product port",
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


uvm_component_utils(tc_vibe_saf_ing)
