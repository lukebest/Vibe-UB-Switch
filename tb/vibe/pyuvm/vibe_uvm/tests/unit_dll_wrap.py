"""Wrap-level uvm-python TC for Decision-I stage-77 vibe_dll.

Covers submodule wiring (seven children + wrap-local proto/fc combo);
async rst_n / LinkUp=0 → Disabled; hardcoded param_ok/credit_ok walk
Disabled → Param → Credit → Normal; credit_low blocks NW until cells
are granted; 1-flit CFG3 TX smoke; CFG0 RX terminate (no fabric);
CFG3 1-flit RX smoke; fec_fail → start_retry → drop_data; port_rst /
!link_up force Disabled; wrap-vs-DUT instance score (cocotb instance
u_dll, shared with stock tc_dll); mid-run async rst_n through dest
posedge then a fresh stimulus walk (no leftover mid-protocol residue);
leaf pin scan on that instance. Not a full-chip consecutive-green
gate. Not 1/3, 4/3, freeze, or signoff. Not TP-DLL-004 (`tc_dll` /
`make dll` still scores the official >32-flit split).

Matches product rtl/dll/vibe_dll.sv: hierarchy wrap of vibe_dll_sm
u_sm, vibe_dll_credit u_crd, vibe_dll_retry_buf u_rbuf,
vibe_dll_retry_req_sm u_req, vibe_dll_retry_ack_sm u_ack,
vibe_dll_tx u_tx, vibe_dll_rx u_rx; proto_err = crd_proto | buf_proto;
fc_ovf = crd_ovf; param_ok/credit_ok tied 1'b1.
This is not vibe_bcrc / vibe_dll_credit / vibe_dll_sm / vibe_dll_rx /
vibe_dll_retry_ack_sm / vibe_dll_retry_buf / vibe_dll_retry_req_sm /
vibe_dll_tx / vibe_icrc / vibe_pcs_tx / vibe_pcs_rx /
vibe_pcs_scramble / vibe_ebch16 / vibe_pcs_tx_cw2beat /
vibe_pcs_tx_amctl / vibe_pcs_tx_g1 / vibe_pcs_tx_fec /
vibe_rs128_120_enc / vibe_rs128_120_dec / vibe_pcs_rx_deskew /
vibe_pcs_rx_amctl_lock / vibe_pcs_rx_unpack / vibe_pcs_tx_pack /
gear / vibe_afifo / vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module; do not ECO F1.
CHILDREN: u_sm / u_crd / u_rbuf / u_req / u_ack / u_tx / u_rx
(as instantiated). First DLL structural wrap after those eight
child leaves (bcrc / credit / dll_sm / dll_rx / retry_ack_sm /
retry_buf / retry_req_sm / dll_tx).
Stock Icarus tc_dll and pyuvm tc_dll remain the official
TP-DLL-004 scorers. Header-only vs stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.handle import Force
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

ST_DIS = 0
ST_PARM = 1
ST_CRD = 2
ST_NRM = 3
ST_NAME = {0: "Disabled", 1: "Param", 2: "Credit", 3: "Normal"}
REQ_N = 0
REQ_Q = 1
MASK160 = (1 << 160) - 1
MASK352 = (1 << 352) - 1
MASK480 = (1 << 480) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
CHILDREN = ("u_sm", "u_crd", "u_rbuf", "u_req", "u_ack", "u_tx", "u_rx")
HIER = "u_dll.u_sm / u_dll.u_tx / u_dll.u_rx"
WRAP = "vibe_dll_cocotb_top"
INST = "u_dll"
# Product ports from rtl/dll/vibe_dll.sv. ovf_l (F1) is not a port.
PINS = (
    "clk", "rst_n", "port_rst", "device_rst",
    "link_up", "fec_fail",
    "nw_dll_data", "nw_dll_vld", "nw_dll_ready",
    "dll_nw_data", "dll_nw_vld", "dll_nw_ready",
    "dll_pcs_data", "dll_pcs_vld", "dll_pcs_ready",
    "pcs_dll_data", "pcs_dll_vld", "pcs_dll_ready",
    "status_up", "disabled", "retrain_req", "retry_error",
    "proto_err", "fc_ovf", "rx_ovf", "cfg0_hit", "cfg0_data",
)
# Leftover leaf / dual-clock / F1 / sibling pins must not appear on
# the wrap top. Instance is u_dll (shared with stock tc_dll), not u_u.
ABSENT = (
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld",
    "u_u", "u_crd", "u_bcrc", "u_b", "u_l", "u_dsk", "u_un", "u_fec",
    "u_sm", "u_rbuf", "u_tx", "u_rx",
    "u_ack", "u_req", "u_rack",
    "lane_id", "seed_load", "en", "cw_sel", "cw", "u_cw", "u_a",
    "cw_data", "cw_vld", "cw_ready", "beat_data", "beat_vld", "beat_ready",
    "amctl_40B", "sdf_period", "data_out",
    "u_g", "u_g1", "u_enc", "u_enc_a", "u_enc_b", "u_pack", "u_dec",
    "grain_n", "is_cfg0",
    "credit_ret", "credit_ret_n",
    "pending", "credit_low", "force_crd_ack",
    "bp_nw",
    "param_ok", "credit_ok", "dll_error",
    "start", "in_vld", "in_flit", "last", "error_flag", "crc_word", "done",
    "in_sym", "parity", "in_ready",
    "win_data", "win_vld", "win_ready",
    "locked", "lid", "lid_bad", "is_amctl", "sdf", "edf",
    "bcrc_fail",
    "start_ack", "start_retry", "rd_ptr",
    "wr_ptr", "rcv_ptr", "tail_ptr", "num_free",
    "consume_flits", "consume_vld", "consume_cfg0",
    "wr_en", "wr_flit", "is_null", "is_retry",
    "replay", "replay_flit", "send_idle", "send_req", "send_ack",
    "can_send", "drop_data", "bp_pending",
)
PAT352 = int(
    "A5A55A5A0123456789ABCDEFFEDCBA98765432101111222233334444555566667777888899",
    16,
) & MASK352
PAT480 = int("A5" * 60, 16) & MASK480


def mk_nw(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """512b NW beat: LPH in [511:352] (vibe_nw512_flit0)."""
    if payload is None:
        payload = PAT352
    return lph.mk_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK352,
    )


def mk_pcs(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """640b PCS beat: LPH in [639:480]."""
    if payload is None:
        payload = PAT480
    return lph.mk_pcs_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK480,
    )


def pcs_lph(beat: int) -> int:
    return (int(beat) >> 480) & MASK160


class tc_vibe_dll(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=0):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.device_rst, 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.fec_fail, 0)
        sset(d.nw_dll_vld, 0)
        sset(d.nw_dll_data, 0)
        sset(d.dll_nw_ready, 1)
        sset(d.dll_pcs_ready, 1)
        sset(d.pcs_dll_vld, 0)
        sset(d.pcs_dll_data, 0)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle(link_up=0)
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    def _inner(self, path, default=None):
        try:
            return ival(hier(self.dut, path), default)
        except Exception:
            return default

    def _exists(self, path) -> bool:
        try:
            hier(self.dut, path)
            return True
        except Exception:
            return False

    def _sm(self):
        st = self._inner("u_dll.sm_st", None)
        if st is None:
            st = self._inner("u_dll.u_sm.st", None)
        if st is None:
            st = self._inner("u_dll.u_sm.state", None)
        return st

    def _fmt(self):
        d = self.dut
        st = self._sm()
        name = ST_NAME.get(st, f"?{st}")
        return (
            f"st={st} ({name}) up={ival(d.status_up, -1)} "
            f"dis={ival(d.disabled, -1)} rdy={ival(d.nw_dll_ready, -1)} "
            f"pcs_vld={ival(d.dll_pcs_vld, -1)} "
            f"nw_vld={ival(d.dll_nw_vld, -1)} "
            f"cfg0={ival(d.cfg0_hit, -1)} "
            f"clow={self._inner('u_dll.credit_low', -1)} "
            f"drop={self._inner('u_dll.drop_data', -1)}"
        )

    def _score_combo(self, name):
        crd = self._inner("u_dll.crd_proto", None)
        buf = self._inner("u_dll.buf_proto", None)
        pe = ival(self.dut.proto_err, None)
        if crd is not None and buf is not None and pe is not None:
            if int(pe) != (int(crd) | int(buf)):
                self.bad(name, "wrap proto_err = crd_proto | buf_proto",
                         f"proto_err={int(crd) | int(buf)}",
                         f"proto_err={pe} crd={crd} buf={buf}",
                         "u_dll.proto_err")
                return False
        ovf = ival(self.dut.fc_ovf, None)
        crd_ovf = self._inner("u_dll.crd_ovf", None)
        if ovf is not None and crd_ovf is not None and int(ovf) != int(crd_ovf):
            self.bad(name, "wrap fc_ovf = crd_ovf",
                     f"fc_ovf={crd_ovf}", f"fc_ovf={ovf}", "u_dll.fc_ovf")
            return False
        return True

    def _score_children(self, name):
        missing = [inst for inst in CHILDREN
                   if not self._exists(f"u_dll.{inst}")]
        if missing:
            self.bad(name, "AS-0.1 §12 children present",
                     "u_sm u_crd u_rbuf u_req u_ack u_tx u_rx",
                     f"missing={missing}", "u_dll")
            return False
        return True

    def _sample(self):
        d = self.dut
        return {
            "status_up": ival(d.status_up, -1),
            "disabled": ival(d.disabled, -1),
            "nw_dll_ready": ival(d.nw_dll_ready, -1),
            "dll_nw_data": ival(d.dll_nw_data, None),
            "dll_nw_vld": ival(d.dll_nw_vld, -1),
            "dll_pcs_data": ival(d.dll_pcs_data, None),
            "dll_pcs_vld": ival(d.dll_pcs_vld, -1),
            "pcs_dll_ready": ival(d.pcs_dll_ready, -1),
            "retrain_req": ival(d.retrain_req, -1),
            "retry_error": ival(d.retry_error, -1),
            "proto_err": ival(d.proto_err, -1),
            "fc_ovf": ival(d.fc_ovf, -1),
            "rx_ovf": ival(d.rx_ovf, -1),
            "cfg0_hit": ival(d.cfg0_hit, -1),
            "cfg0_data": ival(d.cfg0_data, None),
        }

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        return {
            "status_up": ival(u.status_up, -1),
            "disabled": ival(u.disabled, -1),
            "nw_dll_ready": ival(u.nw_dll_ready, -1),
            "dll_nw_data": ival(u.dll_nw_data, None),
            "dll_nw_vld": ival(u.dll_nw_vld, -1),
            "dll_pcs_data": ival(u.dll_pcs_data, None),
            "dll_pcs_vld": ival(u.dll_pcs_vld, -1),
            "pcs_dll_ready": ival(u.pcs_dll_ready, -1),
            "retrain_req": ival(u.retrain_req, -1),
            "retry_error": ival(u.retry_error, -1),
            "proto_err": ival(u.proto_err, -1),
            "fc_ovf": ival(u.fc_ovf, -1),
            "rx_ovf": ival(u.rx_ovf, -1),
            "cfg0_hit": ival(u.cfg0_hit, -1),
            "cfg0_data": ival(u.cfg0_data, None),
        }

    def _score_inner(self, name, stim, got=None, inner=None):
        # Compare wrap vs u_dll from the same sample instant. Do not
        # re-read after a later posedge (pre-NBA would then see post).
        if got is None:
            got = self._sample()
        if inner is None:
            inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        bits = (
            "status_up", "disabled", "nw_dll_ready",
            "dll_nw_vld", "dll_pcs_vld", "pcs_dll_ready",
            "retrain_req", "retry_error", "proto_err",
            "fc_ovf", "rx_ovf", "cfg0_hit",
        )
        for k in bits:
            gv, iv = got[k], inner[k]
            if gv is None or (isinstance(gv, int) and gv < 0):
                self.bad(name, stim + f" ({k} unresolved)",
                         f"{k} present on wrap", self._fmt(), WRAP)
                return False
            if iv is None or (isinstance(iv, int) and iv < 0):
                self.bad(name, stim + f" ({INST}.{k} unresolved)",
                         f"{INST}.{k} present", self._fmt(), WRAP)
                return False
            if int(gv) != int(iv):
                self.bad(name, stim + f" (port vs {INST}.{k})",
                         f"{k}={gv}", f"{INST}.{k}={iv}", WRAP)
                return False
        for k, mask in (("dll_nw_data", MASK512), ("dll_pcs_data", MASK640),
                        ("cfg0_data", MASK640)):
            gv, iv = got[k], inner[k]
            if gv is None or (isinstance(gv, int) and gv < 0):
                continue
            if iv is None or (isinstance(iv, int) and iv < 0):
                continue
            if (int(gv) & mask) != (int(iv) & mask):
                self.bad(name, stim + f" (port vs {INST}.{k})",
                         hex(int(gv) & mask), hex(int(iv) & mask), WRAP)
                return False
        return True

    async def _grant_credit(self, cells=1024):
        """TB-only Force. Stock vibe_dll starts cells=0 → credit_low=1."""
        hier(self.dut, "u_dll.u_crd.cells").value = Force(cells)
        hier(self.dut, "u_dll.u_crd.pend").value = Force(0)
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll"

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        if not self._score_children(name):
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "reset then release (wrap vs u_dll)"):
            phase.drop_objection(self)
            return

        # 1. After reset: LinkUp=0 → Disabled (stock tc_dll).
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "reset then release, link_up=0",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        st = self._sm()
        if st not in (None, ST_DIS) and st != ST_DIS:
            self.bad(name, "reset sm_st",
                     "sm_st=0 (Disabled)", self._fmt(), "u_dll.sm_st")
            phase.drop_objection(self)
            return
        for pin, exp in (("dll_pcs_vld", 0), ("dll_nw_vld", 0),
                         ("cfg0_hit", 0), ("retrain_req", 0),
                         ("retry_error", 0), ("proto_err", 0),
                         ("fc_ovf", 0), ("rx_ovf", 0)):
            got = ival(getattr(d, pin), None)
            if got is None or (isinstance(got, int) and got < 0):
                continue
            if int(got) != exp:
                self.bad(name, f"reset idle {pin}",
                         f"{pin}={exp}", self._fmt(), f"u_dll.{pin}")
                phase.drop_objection(self)
                return

        # 2. link_up=1 + tied param_ok/credit_ok: DIS→PARM→CRD→NRM.
        sset(d.link_up, 1)
        walk = []
        for i in range(3):
            await self._to_fall()
            walk.append(self._sm())
            if not self._score_combo(name):
                phase.drop_objection(self)
                return
        exp_walk = [ST_PARM, ST_CRD, ST_NRM]
        if any(s is not None for s in walk) and walk != exp_walk:
            # Allow unresolved inner st, but flags must match Normal.
            if walk != exp_walk:
                resolved = [s for s in walk if s is not None]
                if resolved and resolved != exp_walk[:len(resolved)]:
                    self.bad(name, "link_up walk DIS→PARM→CRD→NRM",
                             f"walk={exp_walk}", f"walk={walk}",
                             "u_dll.sm_st")
                    phase.drop_objection(self)
                    return
        if ival(d.status_up, 0) != 1 or ival(d.disabled, 1) != 0:
            self.bad(name, "LinkUp=1, param_ok/credit_ok hardcoded",
                     "status_up=1 disabled=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "link_up walk (wrap vs u_dll)"):
            phase.drop_objection(self)
            return

        # 3. cells=0 → credit_low → nw_dll_ready=0 (TX wired to u_crd).
        clow = self._inner("u_dll.credit_low", None)
        if clow not in (None, 1) and clow != 1:
            self.bad(name, "stock cells=0 after reset/up",
                     "credit_low=1", self._fmt(), "u_dll.u_crd.credit_low")
            phase.drop_objection(self)
            return
        if ival(d.nw_dll_ready, 1) != 0:
            self.bad(name, "credit_low blocks NW (u_crd → u_tx)",
                     "nw_dll_ready=0", self._fmt(), "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return

        # 4. Grant cells (TB-only Force, same as port/top / tc_dll).
        await self._grant_credit(1024)
        if ival(d.nw_dll_ready, 0) != 1:
            self.bad(name, "after credit grant",
                     "nw_dll_ready=1", self._fmt(), "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return

        # 5. TX smoke: 1-flit CFG3 → consume + 4-flit Null-pad emit.
        b1 = mk_nw(3, 0, 1)
        sent = 0
        pcs = []
        for _ in range(16):
            await FallingEdge(d.clk)
            if sent == 0:
                sset(d.nw_dll_data, b1)
                sset(d.nw_dll_vld, ival(d.nw_dll_ready, 0))
            else:
                sset(d.nw_dll_vld, 0)
            if ival(d.dll_pcs_vld, 0) and ival(d.dll_pcs_ready, 0):
                pcs.append(ival(d.dll_pcs_data, 0) or 0)
            await RisingEdge(d.clk)
            if sent == 0 and ival(d.nw_dll_vld, 0) and ival(d.nw_dll_ready, 0):
                sent = 1
            if sent and pcs:
                break
        sset(d.nw_dll_vld, 0)
        if not sent:
            self.bad(name, "TX 1-flit CFG3 accept",
                     "nw_dll_ready handshake", self._fmt(),
                     "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return
        if not pcs:
            self.bad(name, "TX 1-flit after status_up + credit",
                     "dll_pcs_vld beat", "none", "u_dll.u_tx.dll_pcs_vld")
            phase.drop_objection(self)
            return
        f0 = (pcs[0] >> 480) & MASK160
        if lph.lph_cfg(f0) != 3:
            self.bad(name, "TX first PCS flit CFG",
                     "CFG=3", f"CFG={lph.lph_cfg(f0)} beat=0x{pcs[0]:x}",
                     "u_dll.u_tx.dll_pcs_data")
            phase.drop_objection(self)
            return
        await FallingEdge(d.clk)

        # 6. RX CFG0 terminate: hit + capture, never dll_nw_vld.
        c0 = mk_pcs(0, 0, 1)
        sset(d.pcs_dll_data, c0)
        sset(d.pcs_dll_vld, 1)
        await self._to_fall()
        if ival(d.cfg0_hit, 0) != 1:
            self.bad(name, "RX CFG0 terminate (u_rx)",
                     "cfg0_hit=1 dll_nw_vld=0", self._fmt(),
                     "u_dll.u_rx.cfg0_hit")
            phase.drop_objection(self)
            return
        if ival(d.dll_nw_vld, 1) != 0:
            self.bad(name, "CFG0 does not enter fabric",
                     "dll_nw_vld=0", self._fmt(), "u_dll.u_rx.dll_nw_vld")
            phase.drop_objection(self)
            return
        got_c0 = ival(d.cfg0_data, None)
        if (got_c0 is not None and got_c0 >= 0
                and (int(got_c0) & MASK640) != (c0 & MASK640)):
            self.bad(name, "CFG0 capture",
                     hex(c0 & MASK640), hex(int(got_c0) & MASK640),
                     "u_dll.u_rx.cfg0_data")
            phase.drop_objection(self)
            return
        sset(d.pcs_dll_vld, 0)
        await self._to_fall()
        if ival(d.cfg0_hit, 1) != 0:
            self.bad(name, "CFG0 hit is a pulse",
                     "cfg0_hit=0", self._fmt(), "u_dll.u_rx.cfg0_hit")
            phase.drop_objection(self)
            return

        # 7. RX CFG3 1-flit: accept → pack → emit LPH on dll_nw_*.
        r1 = mk_pcs(3, 0, 1)
        sset(d.pcs_dll_data, r1)
        sset(d.pcs_dll_vld, 1)
        await self._to_fall()
        sset(d.pcs_dll_vld, 0)
        nw = None
        for _ in range(8):
            if ival(d.dll_nw_vld, 0):
                nw = ival(d.dll_nw_data, 0) or 0
                break
            await self._to_fall()
        if nw is None:
            self.bad(name, "RX CFG3 1-flit emit",
                     "dll_nw_vld=1", self._fmt(), "u_dll.u_rx.dll_nw_vld")
            phase.drop_objection(self)
            return
        got_cfg = lph.lph_cfg((nw >> 352) & MASK160)
        if got_cfg != 3:
            self.bad(name, "RX NW LPH CFG",
                     "CFG=3", f"CFG={got_cfg} nw=0x{nw:x}",
                     "u_dll.u_rx.dll_nw_data")
            phase.drop_objection(self)
            return
        if ((nw >> 352) & MASK160) != pcs_lph(r1):
            self.bad(name, "RX LPH is first 160b of NW beat",
                     hex(pcs_lph(r1)), hex((nw >> 352) & MASK160),
                     "u_dll.u_rx.dll_nw_data")
            phase.drop_objection(self)
            return
        await self._to_fall()

        # 8. fec_fail wires u_rx.start_retry → u_req → drop_data.
        sset(d.fec_fail, 1)
        await Timer(100, "PS")
        sr = self._inner("u_dll.start_retry", None)
        if sr is None:
            sr = self._inner("u_dll.u_rx.start_retry", None)
        if sr not in (None, 1) and sr != 1:
            self.bad(name, "fec_fail → start_retry combo",
                     "start_retry=1", self._fmt(), "u_dll.u_rx.start_retry")
            phase.drop_objection(self)
            return
        await self._to_fall()
        sset(d.fec_fail, 0)
        drop = self._inner("u_dll.drop_data", None)
        req_st = self._inner("u_dll.req_st", None)
        if req_st is None:
            req_st = self._inner("u_dll.u_req.state", None)
        if drop not in (None, 1) and drop != 1:
            self.bad(name, "start_retry → REQ|WAIT drop_data",
                     "drop_data=1", self._fmt(), "u_dll.u_req.drop_data")
            phase.drop_objection(self)
            return
        if req_st not in (None, REQ_Q) and req_st != REQ_Q:
            self.bad(name, "u_req entered REQ",
                     "req_st=1 (REQ)", f"req_st={req_st}", "u_dll.req_st")
            phase.drop_objection(self)
            return
        if ival(d.nw_dll_ready, 1) != 0:
            self.bad(name, "drop_data blocks NW (u_req → u_tx)",
                     "nw_dll_ready=0", self._fmt(), "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return

        # 9. !link_up forces Disabled (wrap u_sm).
        sset(d.link_up, 0)
        sset(d.fec_fail, 0)
        await self._to_fall()
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "!link_up force Disabled",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return

        # 10. Re-up walk + port_rst force Disabled.
        sset(d.link_up, 1)
        for _ in range(3):
            await self._to_fall()
        if ival(d.status_up, 0) != 1 or ival(d.disabled, 1) != 0:
            self.bad(name, "re-up after !link_up",
                     "status_up=1 disabled=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        sset(d.port_rst, 1)
        await self._to_fall()
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "port_rst force Disabled",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        sset(d.port_rst, 0)
        await self._to_fall()

        # 11. Mid-run async rst_n through dest posedge. Park leftover
        # REQ / drop_data after fec_fail, then pulse rst_n.
        sset(d.port_rst, 0)
        sset(d.link_up, 1)
        sset(d.fec_fail, 0)
        for _ in range(3):
            await self._to_fall()
        if ival(d.status_up, 0) != 1 or ival(d.disabled, 1) != 0:
            self.bad(name, "re-up before mid-run rst park",
                     "status_up=1 disabled=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        await self._grant_credit(1024)
        sset(d.fec_fail, 1)
        await Timer(100, "PS")
        await self._to_fall()
        sset(d.fec_fail, 0)
        drop = self._inner("u_dll.drop_data", None)
        req_st = self._inner("u_dll.req_st", None)
        if req_st is None:
            req_st = self._inner("u_dll.u_req.state", None)
        if drop not in (None, 1) and drop != 1:
            self.bad(name, "pre-async-rst park (live leftover)",
                     "drop_data=1", self._fmt(), "u_dll.u_req.drop_data")
            phase.drop_objection(self)
            return
        if req_st not in (None, REQ_Q) and req_st != REQ_Q:
            self.bad(name, "pre-async-rst park (live leftover REQ)",
                     "req_st=1 (REQ)", f"req_st={req_st}", "u_dll.req_st")
            phase.drop_objection(self)
            return
        if ival(d.nw_dll_ready, 1) != 0:
            self.bad(name, "pre-async-rst park (drop_data blocks NW)",
                     "nw_dll_ready=0", self._fmt(), "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "pre-async-rst park (wrap vs u_dll)"):
            phase.drop_objection(self)
            return
        await self._idle(link_up=0)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "mid-run rst_n=0 (100ps, no posedge)",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        if ival(d.dll_pcs_vld, 1) != 0 or ival(d.dll_nw_vld, 1) != 0:
            self.bad(name, "mid-run rst_n=0 clears datapath valids",
                     "dll_pcs_vld=0 dll_nw_vld=0", self._fmt(), "u_dll")
            phase.drop_objection(self)
            return
        drop = self._inner("u_dll.drop_data", None)
        req_st = self._inner("u_dll.req_st", None)
        if req_st is None:
            req_st = self._inner("u_dll.u_req.state", None)
        if drop not in (None, 0) and drop != 0:
            self.bad(name, "mid-run rst_n=0 clears drop_data",
                     "drop_data=0", f"drop_data={drop}", "u_dll.u_req.drop_data")
            phase.drop_objection(self)
            return
        if req_st not in (None, REQ_N) and req_st != REQ_N:
            self.bad(name, "mid-run rst_n=0 clears req_st",
                     "req_st=0 (NORMAL)", f"req_st={req_st}", "u_dll.req_st")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "mid-run rst_n=0 (wrap vs u_dll)"):
            phase.drop_objection(self)
            return
        await self._to_fall()
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "rst_n held 0 through dest posedge",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        if ival(d.dll_pcs_vld, 1) != 0 or ival(d.dll_nw_vld, 1) != 0:
            self.bad(name, "rst_n through dest posedge clears valids",
                     "dll_pcs_vld=0 dll_nw_vld=0", self._fmt(), "u_dll")
            phase.drop_objection(self)
            return
        drop = self._inner("u_dll.drop_data", None)
        req_st = self._inner("u_dll.req_st", None)
        if req_st is None:
            req_st = self._inner("u_dll.u_req.state", None)
        if drop not in (None, 0) and drop != 0:
            self.bad(name, "rst_n through dest posedge clears drop_data",
                     "drop_data=0", f"drop_data={drop}", "u_dll.u_req.drop_data")
            phase.drop_objection(self)
            return
        if req_st not in (None, REQ_N) and req_st != REQ_N:
            self.bad(name, "rst_n through dest posedge clears req_st",
                     "req_st=0 (NORMAL)", f"req_st={req_st}", "u_dll.req_st")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "rst_n through dest posedge (wrap vs u_dll)"):
            phase.drop_objection(self)
            return
        await self._idle(link_up=0)
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.disabled, 0) != 1 or ival(d.status_up, 1) != 0:
            self.bad(name, "after async re-release, link_up=0",
                     "disabled=1 status_up=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        drop = self._inner("u_dll.drop_data", None)
        req_st = self._inner("u_dll.req_st", None)
        if req_st is None:
            req_st = self._inner("u_dll.u_req.state", None)
        if drop not in (None, 0) and drop != 0:
            self.bad(name, "after async re-release, no leftover drop_data",
                     "drop_data=0", f"drop_data={drop}", "u_dll.u_req.drop_data")
            phase.drop_objection(self)
            return
        if req_st not in (None, REQ_N) and req_st != REQ_N:
            self.bad(name, "after async re-release, no leftover REQ",
                     "req_st=0 (NORMAL)", f"req_st={req_st}", "u_dll.req_st")
            phase.drop_objection(self)
            return
        if not self._score_combo(name):
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "after async re-release (wrap vs u_dll)"):
            phase.drop_objection(self)
            return

        # Fresh walk after mid-run rst: leftover REQ / drop_data gone.
        sset(d.link_up, 1)
        for _ in range(3):
            await self._to_fall()
        if ival(d.status_up, 0) != 1 or ival(d.disabled, 1) != 0:
            self.bad(name, "fresh walk after mid-run rst",
                     "status_up=1 disabled=0", self._fmt(), "u_dll.u_sm")
            phase.drop_objection(self)
            return
        await self._grant_credit(1024)
        if ival(d.nw_dll_ready, 0) != 1:
            self.bad(name, "fresh walk after mid-run rst (no leftover drop)",
                     "nw_dll_ready=1", self._fmt(), "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return
        b1 = mk_nw(3, 0, 1)
        sent = 0
        pcs = []
        for _ in range(16):
            await FallingEdge(d.clk)
            if sent == 0:
                sset(d.nw_dll_data, b1)
                sset(d.nw_dll_vld, ival(d.nw_dll_ready, 0))
            else:
                sset(d.nw_dll_vld, 0)
            if ival(d.dll_pcs_vld, 0) and ival(d.dll_pcs_ready, 0):
                pcs.append(ival(d.dll_pcs_data, 0) or 0)
            await RisingEdge(d.clk)
            if sent == 0 and ival(d.nw_dll_vld, 0) and ival(d.nw_dll_ready, 0):
                sent = 1
            if sent and pcs:
                break
        sset(d.nw_dll_vld, 0)
        if not sent:
            self.bad(name, "fresh TX after mid-run rst (no leftover residue)",
                     "nw_dll_ready handshake", self._fmt(),
                     "u_dll.u_tx.nw_dll_ready")
            phase.drop_objection(self)
            return
        if not pcs:
            self.bad(name, "fresh TX emit after mid-run rst",
                     "dll_pcs_vld beat", "none", "u_dll.u_tx.dll_pcs_vld")
            phase.drop_objection(self)
            return
        f0 = (pcs[0] >> 480) & MASK160
        if lph.lph_cfg(f0) != 3:
            self.bad(name, "fresh TX CFG after mid-run rst",
                     "CFG=3", f"CFG={lph.lph_cfg(f0)} beat=0x{pcs[0]:x}",
                     "u_dll.u_tx.dll_pcs_data")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "fresh walk after mid-run rst"):
            phase.drop_objection(self)
            return

        # 12. Leaf pins match product SV (no ovf_l / dual-clock / leftover
        # u_u). Instance u_dll (shared with stock tc_dll).
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_dll product port",
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


uvm_component_utils(tc_vibe_dll)
