"""Module-level uvm-python TC for Decision-I stage-79 vibe_nw_adapt.

Covers combo idle (clk / rst_n unused in the combo body),
link_ready gate on both TX readies and nw_dll_vld, mgmt inject
priority over VOQ, TX/RX 512b GOLDEN paths plus SOP LPH
[511:352], ready trees (mgmt_nw_ready / fab_nw_ready /
dll_nw_ready), wrap-vs-DUT instance score (cocotb instance u_u),
rst_n unused (toggle does not change combo outs), and a pin scan
with instance u_u.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/nw/vibe_nw_adapt.sv: combo assigns only.
mgmt_nw_ready = link_ready && nw_dll_ready;
fab_nw_ready  = link_ready && nw_dll_ready && !mgmt_nw_vld;
nw_dll_vld    = link_ready && (mgmt_nw_vld || fab_nw_vld);
nw_dll_data   = mgmt_nw_vld ? mgmt_nw_data : fab_nw_data;
RX is a wire-through (dll_nw_* ↔ nw_fab_*). Product instantiator
is vibe_port u_nw; stock Icarus tc_nw_adapt_linkready uses u_n;
Decision-I wrap uses instance u_u (not leftover u_n / u_nw).
This is not vibe_icrc / vibe_dll / vibe_bcrc / vibe_dll_tx /
vibe_dll_credit / vibe_dll_sm / vibe_dll_rx /
vibe_dll_retry_ack_sm / vibe_dll_retry_buf /
vibe_dll_retry_req_sm / vibe_port / vibe_ub_switch /
vibe_pcs_tx / vibe_pcs_rx / vibe_pcs_scramble / vibe_ebch16 /
vibe_pcs_tx_cw2beat / vibe_pcs_tx_amctl / vibe_pcs_tx_g1 /
vibe_pcs_tx_fec / vibe_rs128_120_enc / vibe_rs128_120_dec /
vibe_pcs_rx_deskew / vibe_pcs_rx_amctl_lock /
vibe_pcs_rx_unpack / vibe_pcs_tx_pack / gear / vibe_afifo /
vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module; do not ECO F1.
CHILDREN: none.
Last NW leaf after stage-78 vibe_icrc wrap (NW tip-align wave
complete; do not invent further NW leaves).
Stock Icarus tc_nw_adapt_linkready remains the official
LinkReady / mgmt-pri scorer (direct vibe_nw_adapt top, instance
u_n). Header-only vs stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.lph import nw512_flit0, nw512_golden_rx, nw512_golden_tx
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK512 = (1 << 512) - 1
MASK160 = (1 << 160) - 1
HIER = ("u_u.fab_nw_ready / u_u.mgmt_nw_ready / u_u.nw_dll_data / "
        "u_u.nw_dll_vld / u_u.dll_nw_ready / u_u.nw_fab_data / "
        "u_u.nw_fab_vld")
WRAP = "vibe_nw_adapt_cocotb_top"
INST = "u_u"
# Product ports from rtl/nw/vibe_nw_adapt.sv. ovf_l (F1) is not a port.
PINS = (
    "clk", "rst_n", "link_ready",
    "fab_nw_data", "fab_nw_vld", "fab_nw_ready",
    "mgmt_nw_data", "mgmt_nw_vld", "mgmt_nw_ready",
    "nw_dll_data", "nw_dll_vld", "nw_dll_ready",
    "dll_nw_data", "dll_nw_vld", "dll_nw_ready",
    "nw_fab_data", "nw_fab_vld", "nw_fab_ready",
)
# Leftover leaf / dual-clock / F1 / sibling pins must not appear on
# the wrap top. Instance is u_u (Decision-I leaf wrappers), not
# leftover product instantiator u_nw or stock Icarus u_n.
ABSENT = (
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld",
    "u_n", "u_nw", "u_icrc", "u_bcrc", "u_b", "u_l", "u_dsk", "u_un",
    "u_fec", "u_crd", "u_sm", "u_rbuf", "u_dll", "u_tx", "u_rx",
    "u_ack", "u_req", "u_rack", "u_adapt",
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
    "device_rst", "pcs_dll_data", "pcs_dll_vld",
    "pcs_dll_ready",
    "start_ack", "rd_ptr", "wr_ptr", "rcv_ptr", "tail_ptr", "num_free",
)

OUT_KEYS = (
    "fab_nw_ready", "mgmt_nw_ready",
    "nw_dll_data", "nw_dll_vld",
    "dll_nw_ready", "nw_fab_data", "nw_fab_vld",
)


def _mask512(v) -> int:
    return int(v) & MASK512


def _hex512(v) -> str:
    if v is None:
        return "x"
    return f"0x{_mask512(v):0128x}"


def _width(sig) -> int:
    try:
        return int(len(sig))
    except Exception:
        v = getattr(sig, "value", None)
        n = getattr(v, "n_bits", None)
        return int(n) if n is not None else -1


def sop_lph_fail(exp, act) -> bool:
    """Stock vibe_tb_nw512_sop_lph_fail: 160b [511:352] plus named fields."""
    if exp is None or act is None:
        return True
    e = nw512_flit0(_mask512(exp))
    a = nw512_flit0(_mask512(act))
    if e != a:
        return True
    if ((e >> 8) & 0xF) != ((a >> 8) & 0xF):
        return True
    if ((e >> 22) & 0x3) != ((a >> 22) & 0x3):
        return True
    if ((e >> 32) & 0xFFFF) != ((a >> 32) & 0xFFFF):
        return True
    if ((e >> 48) & 0xFFFF) != ((a >> 48) & 0xFFFF):
        return True
    return False


def combo(link_ready, fab_data, fab_vld, mgmt_data, mgmt_vld,
          nw_dll_ready, dll_data, dll_vld, nw_fab_ready):
    """Product combo assigns (rtl/nw/vibe_nw_adapt.sv)."""
    lr = 1 if link_ready else 0
    fv = 1 if fab_vld else 0
    mv = 1 if mgmt_vld else 0
    ndr = 1 if nw_dll_ready else 0
    dv = 1 if dll_vld else 0
    nfr = 1 if nw_fab_ready else 0
    fd = _mask512(fab_data)
    md = _mask512(mgmt_data)
    dd = _mask512(dll_data)
    return {
        "fab_nw_ready": int(lr and ndr and (not mv)),
        "mgmt_nw_ready": int(lr and ndr),
        "nw_dll_data": md if mv else fd,
        "nw_dll_vld": int(lr and (mv or fv)),
        "dll_nw_ready": nfr,
        "nw_fab_data": dd,
        "nw_fab_vld": dv,
    }


def _fmt(s) -> str:
    return (
        f"fab_rdy={s['fab_nw_ready']} mgmt_rdy={s['mgmt_nw_ready']} "
        f"nw_dll_vld={s['nw_dll_vld']} nw_dll={_hex512(s['nw_dll_data'])} "
        f"dll_rdy={s['dll_nw_ready']} nw_fab_vld={s['nw_fab_vld']} "
        f"nw_fab={_hex512(s['nw_fab_data'])}"
    )


class tc_vibe_nw_adapt(VibeUnitBaseTest):
    def _sample(self):
        d = self.dut
        return {
            "fab_nw_ready": ival(d.fab_nw_ready, -1),
            "mgmt_nw_ready": ival(d.mgmt_nw_ready, -1),
            "nw_dll_data": ival(d.nw_dll_data, None),
            "nw_dll_vld": ival(d.nw_dll_vld, -1),
            "dll_nw_ready": ival(d.dll_nw_ready, -1),
            "nw_fab_data": ival(d.nw_fab_data, None),
            "nw_fab_vld": ival(d.nw_fab_vld, -1),
        }

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        return {
            "fab_nw_ready": ival(u.fab_nw_ready, -1),
            "mgmt_nw_ready": ival(u.mgmt_nw_ready, -1),
            "nw_dll_data": ival(u.nw_dll_data, None),
            "nw_dll_vld": ival(u.nw_dll_vld, -1),
            "dll_nw_ready": ival(u.dll_nw_ready, -1),
            "nw_fab_data": ival(u.nw_fab_data, None),
            "nw_fab_vld": ival(u.nw_fab_vld, -1),
        }

    def _eq_out(self, a, b) -> bool:
        for k in OUT_KEYS:
            av, bv = a[k], b[k]
            if av is None or bv is None:
                if av != bv:
                    return False
                continue
            if k.endswith("_data"):
                if _mask512(av) != _mask512(bv):
                    return False
            elif int(av) != int(bv):
                return False
        return True

    def _score_inner(self, name, stim, got):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        if not self._eq_out(got, inner):
            self.bad(name, stim + f" (port vs {INST})",
                     _fmt(got), _fmt(inner), HIER)
            return False
        return True

    def _score(self, name, stim, exp, got, check_lph=None):
        if not self._eq_out(exp, got):
            self.bad(name, stim, _fmt(exp), _fmt(got), HIER)
            return False
        if check_lph is not None:
            key, golden = check_lph
            act = got[key]
            if sop_lph_fail(golden, act):
                self.bad(name, stim + f" (SOP LPH {key}[511:352])",
                         f"flit0={hex(nw512_flit0(_mask512(golden)))}",
                         f"flit0={hex(nw512_flit0(_mask512(act))) if act is not None else 'x'}",
                         f"{INST}.{key}[511:352]")
                return False
        return self._score_inner(name, stim, got)

    async def _apply(self, link_ready, fab_data, fab_vld, mgmt_data, mgmt_vld,
                     nw_dll_ready, dll_data, dll_vld, nw_fab_ready, rst_n=1):
        """Drive combo inputs and settle (#1 like stock tc_nw_adapt_linkready)."""
        d = self.dut
        sset(d.rst_n, 1 if rst_n else 0)
        sset(d.link_ready, 1 if link_ready else 0)
        sset(d.fab_nw_data, _mask512(fab_data))
        sset(d.fab_nw_vld, 1 if fab_vld else 0)
        sset(d.mgmt_nw_data, _mask512(mgmt_data))
        sset(d.mgmt_nw_vld, 1 if mgmt_vld else 0)
        sset(d.nw_dll_ready, 1 if nw_dll_ready else 0)
        sset(d.dll_nw_data, _mask512(dll_data))
        sset(d.dll_nw_vld, 1 if dll_vld else 0)
        sset(d.nw_fab_ready, 1 if nw_fab_ready else 0)
        await Timer(1, "NS")
        return self._sample()

    async def _expect(self, name, stim, link_ready, fab_data, fab_vld,
                      mgmt_data, mgmt_vld, nw_dll_ready, dll_data, dll_vld,
                      nw_fab_ready, rst_n=1, check_lph=None):
        exp = combo(link_ready, fab_data, fab_vld, mgmt_data, mgmt_vld,
                    nw_dll_ready, dll_data, dll_vld, nw_fab_ready)
        got = await self._apply(link_ready, fab_data, fab_vld, mgmt_data,
                                mgmt_vld, nw_dll_ready, dll_data, dll_vld,
                                nw_fab_ready, rst_n=rst_n)
        if not self._score(name, stim, exp, got, check_lph=check_lph):
            return None
        return got

    def _golden_selfcheck(self, name):
        gtx = nw512_golden_tx()
        grx = nw512_golden_rx()
        if gtx == 0 or grx == 0 or gtx == grx:
            self.bad(name, "golden uniqueness (GOLDEN_TX / GOLDEN_RX)",
                     "two distinct nonzero 512b vectors",
                     f"tx={_hex512(gtx)} rx={_hex512(grx)}",
                     "golden")
            return False
        if gtx > MASK512 or grx > MASK512:
            self.bad(name, "golden width",
                     "each vector fits in 512 bits",
                     f"tx_bits={(gtx.bit_length())} rx_bits={grx.bit_length()}",
                     "golden")
            return False
        if sop_lph_fail(gtx, gtx) or sop_lph_fail(grx, grx):
            self.bad(name, "golden SOP LPH self",
                     "LPH window matches itself", "fail", "golden")
            return False
        if nw512_flit0(gtx) == nw512_flit0(grx):
            self.bad(name, "golden SOP LPH distinct TX vs RX",
                     "distinct [511:352]",
                     f"tx={hex(nw512_flit0(gtx))} rx={hex(nw512_flit0(grx))}",
                     "golden")
            return False
        idle = combo(0, gtx, 1, 0, 0, 1, grx, 1, 1)
        if idle["fab_nw_ready"] or idle["mgmt_nw_ready"] or idle["nw_dll_vld"]:
            self.bad(name, "golden link_ready=0 fab GOLDEN_TX",
                     "fab_nw_ready=0 mgmt_nw_ready=0 nw_dll_vld=0",
                     _fmt(idle), "golden")
            return False
        tx = combo(1, gtx, 1, 0, 0, 1, grx, 1, 1)
        if (tx["nw_dll_data"] != gtx or not tx["nw_dll_vld"]
                or not tx["fab_nw_ready"] or tx["mgmt_nw_ready"] != 1):
            self.bad(name, "golden TX GOLDEN_TX",
                     f"nw_dll={_hex512(gtx)} vld=1 fab_rdy=1",
                     _fmt(tx), "golden")
            return False
        pri = combo(1, gtx, 1, grx, 1, 1, grx, 1, 1)
        if (pri["nw_dll_data"] != grx or pri["fab_nw_ready"]
                or not pri["mgmt_nw_ready"] or not pri["nw_dll_vld"]):
            self.bad(name, "golden mgmt GOLDEN_RX priority",
                     f"nw_dll={_hex512(grx)} fab_rdy=0",
                     _fmt(pri), "golden")
            return False
        rx = combo(0, 0, 0, 0, 0, 0, grx, 1, 1)
        if rx["nw_fab_data"] != grx or not rx["nw_fab_vld"]:
            self.bad(name, "golden RX wire-through (no link_ready)",
                     f"nw_fab={_hex512(grx)} vld=1",
                     _fmt(rx), "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_nw_adapt"
        gtx = nw512_golden_tx()
        grx = nw512_golden_rx()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        # Width is a gate (stock $bits). Overlay B 512b.
        for sig_name in ("fab_nw_data", "nw_dll_data", "nw_fab_data",
                         "mgmt_nw_data", "dll_nw_data"):
            w = _width(getattr(d, sig_name))
            if w != 512:
                self.bad(name, f"FS-0.2.7 Overlay B $bits({sig_name})",
                         "512", str(w), f"{INST}.{sig_name}")
                phase.drop_objection(self)
                return
        u = getattr(d, INST, None)
        if u is None:
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for sig_name in ("fab_nw_data", "nw_dll_data", "nw_fab_data"):
            w = _width(getattr(u, sig_name))
            if w != 512:
                self.bad(name, f"FS-0.2.7 Overlay B $bits({INST}.{sig_name})",
                         "512", str(w), f"{INST}.{sig_name}")
                phase.drop_objection(self)
                return

        # 1. Combo idle / link_ready=0 (stock first vector).
        got = await self._expect(
            name, "link_ready=0 fab GOLDEN_TX (stock)",
            0, gtx, 1, 0, 0, 1, grx, 1, 1)
        if got is None:
            phase.drop_objection(self)
            return
        if got["fab_nw_ready"] or got["nw_dll_vld"] or got["mgmt_nw_ready"]:
            self.bad(name, "link_ready=0 gates TX readies and nw_dll_vld",
                     "fab_nw_ready=0 mgmt_nw_ready=0 nw_dll_vld=0",
                     _fmt(got), f"{INST}.fab_nw_ready")
            phase.drop_objection(self)
            return

        # RX is wire-through even when link_ready=0.
        if (got["nw_fab_data"] is None
                or _mask512(got["nw_fab_data"]) != grx
                or got["nw_fab_vld"] != 1):
            self.bad(name, "RX GOLDEN_RX while link_ready=0 (wire-through)",
                     f"nw_fab={_hex512(grx)} vld=1",
                     _fmt(got), f"{INST}.nw_fab_data")
            phase.drop_objection(self)
            return
        if sop_lph_fail(grx, got["nw_fab_data"]):
            self.bad(name, "RX SOP LPH GOLDEN_RX[511:352] link_ready=0",
                     hex(nw512_flit0(grx)),
                     hex(nw512_flit0(_mask512(got["nw_fab_data"]))),
                     f"{INST}.nw_fab_data[511:352]")
            phase.drop_objection(self)
            return

        # 2. Stock Icarus: link_ready=1 fab only GOLDEN_TX + RX GOLDEN_RX.
        got = await self._expect(
            name, "TX NW→DLL link_ready=1 fab only GOLDEN_TX (stock)",
            1, gtx, 1, 0, 0, 1, grx, 1, 1,
            check_lph=("nw_dll_data", gtx))
        if got is None:
            phase.drop_objection(self)
            return
        if (_mask512(got["nw_dll_data"]) != gtx or not got["nw_dll_vld"]
                or not got["fab_nw_ready"] or not got["mgmt_nw_ready"]):
            self.bad(name, "TX GOLDEN_TX handshake",
                     f"nw_dll={_hex512(gtx)} vld=1 fab_rdy=1 mgmt_rdy=1",
                     _fmt(got), f"{INST}.nw_dll_data")
            phase.drop_objection(self)
            return
        if sop_lph_fail(grx, got["nw_fab_data"]) or not got["nw_fab_vld"]:
            self.bad(name, "RX DLL→NW GOLDEN_RX (stock)",
                     f"nw_fab={_hex512(grx)} vld=1",
                     _fmt(got), f"{INST}.nw_fab_data")
            phase.drop_objection(self)
            return

        # 3. Stock Icarus: mgmt GOLDEN_RX priority over fab GOLDEN_TX.
        got = await self._expect(
            name, "mgmt GOLDEN_RX priority over fab GOLDEN_TX (stock)",
            1, gtx, 1, grx, 1, 1, grx, 1, 1,
            check_lph=("nw_dll_data", grx))
        if got is None:
            phase.drop_objection(self)
            return
        if (_mask512(got["nw_dll_data"]) != grx or got["fab_nw_ready"]
                or not got["mgmt_nw_ready"] or not got["nw_dll_vld"]):
            self.bad(name, "mgmt priority: nw_dll=GOLDEN_RX fab_rdy=0",
                     f"nw_dll={_hex512(grx)} fab_rdy=0 mgmt_rdy=1",
                     _fmt(got), f"{INST}.nw_dll_data")
            phase.drop_objection(self)
            return

        # 4. Ready trees / both-idle / nw_dll_ready gate / RX ready.
        vectors = (
            ("both TX idle, link_ready=1 (nw_dll_vld=0, readies 1)",
             1, gtx, 0, grx, 0, 1, 0, 0, 1, None),
            ("nw_dll_ready=0 gates both TX readies (link_ready=1 fab vld)",
             1, gtx, 1, 0, 0, 0, grx, 1, 1, None),
            ("nw_dll_ready=0 + mgmt vld (mgmt_rdy=0, still muxes mgmt)",
             1, gtx, 1, grx, 1, 0, 0, 0, 1, ("nw_dll_data", grx)),
            ("mgmt only GOLDEN_RX (fab_vld=0, fab_rdy=0)",
             1, gtx, 0, grx, 1, 1, 0, 0, 1, ("nw_dll_data", grx)),
            ("RX nw_fab_ready=0 → dll_nw_ready=0 (data still wires)",
             1, 0, 0, 0, 0, 1, grx, 1, 0, ("nw_fab_data", grx)),
            ("RX idle (dll_nw_vld=0) → nw_fab_vld=0",
             1, 0, 0, 0, 0, 1, grx, 0, 1, None),
            ("link_ready=0 + mgmt vld (mgmt_rdy=0 nw_dll_vld=0)",
             0, gtx, 1, grx, 1, 1, grx, 1, 1, None),
        )
        for stim, lr, fd, fv, md, mv, ndr, dd, dv, nfr, lph in vectors:
            if await self._expect(
                    name, stim, lr, fd, fv, md, mv, ndr, dd, dv, nfr,
                    check_lph=lph) is None:
                phase.drop_objection(self)
                return

        # 5. rst_n unused in combo body: toggle must not change outs.
        live = await self._expect(
            name, "pre-rst_n-toggle park (fab GOLDEN_TX)",
            1, gtx, 1, 0, 0, 1, grx, 1, 1,
            check_lph=("nw_dll_data", gtx))
        if live is None:
            phase.drop_objection(self)
            return
        held = live
        got0 = await self._apply(1, gtx, 1, 0, 0, 1, grx, 1, 1, rst_n=0)
        if not self._eq_out(held, got0):
            self.bad(name, "rst_n=0 unused (combo outs hold)",
                     _fmt(held), _fmt(got0), f"{INST}.nw_dll_data")
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "rst_n=0 unused", got0):
            phase.drop_objection(self)
            return
        got1 = await self._apply(1, gtx, 1, 0, 0, 1, grx, 1, 1, rst_n=1)
        if not self._eq_out(held, got1):
            self.bad(name, "rst_n=1 after unused toggle (combo outs hold)",
                     _fmt(held), _fmt(got1), f"{INST}.nw_dll_data")
            phase.drop_objection(self)
            return

        # Hold a named TX vector; combo output must not drift.
        await Timer(5, "NS")
        later = self._sample()
        if not self._eq_out(held, later):
            self.bad(name, "hold GOLDEN_TX vector for 5 ns (combo, no latch)",
                     _fmt(held), _fmt(later), HIER)
            phase.drop_objection(self)
            return
        exp_hold = combo(1, gtx, 1, 0, 0, 1, grx, 1, 1)
        if not self._score(name, "hold 5 ns still matches golden",
                           exp_hold, later, check_lph=("nw_dll_data", gtx)):
            phase.drop_objection(self)
            return

        # Re-score stock sequence (combo stable).
        replay = (
            ("replay link_ready=0 fab GOLDEN_TX",
             0, gtx, 1, 0, 0, 1, grx, 1, 1, None),
            ("replay TX GOLDEN_TX",
             1, gtx, 1, 0, 0, 1, grx, 1, 1, ("nw_dll_data", gtx)),
            ("replay mgmt GOLDEN_RX priority",
             1, gtx, 1, grx, 1, 1, grx, 1, 1, ("nw_dll_data", grx)),
        )
        for stim, lr, fd, fv, md, mv, ndr, dd, dv, nfr, lph in replay:
            if await self._expect(
                    name, stim, lr, fd, fv, md, mv, ndr, dd, dv, nfr,
                    check_lph=lph) is None:
                phase.drop_objection(self)
                return

        # 6. Leaf pins match product SV (no ovf_l / leftover u_n / u_nw).
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_nw_adapt product port",
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


uvm_component_utils(tc_vibe_nw_adapt)
