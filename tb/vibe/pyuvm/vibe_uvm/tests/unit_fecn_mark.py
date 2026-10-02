"""Module-level uvm-python TC for Decision-I stage-80 vibe_fecn_mark.

Covers combo idle (no clk / no rst_n / no ready / no sequential
hold), stock tc_fecn_mark Mode 100/010 + VOQ watermark, FECN 00
unmarkable / 11 already-severe / non-markable modes, congestion
vs packet FECN worse, golden rewrite of FECN and LoC vs
pass-through, wrap-vs-DUT instance score (cocotb instance u_u),
and a pin scan with instance u_u.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/fabric/vibe_fecn_mark.sv: combo
mode=cci_in[15:13], fecn=cci_in[1:0], cong=(voq_occ>=FECN_WM[5:0])
with FECN_WM default 24, markable_mode=(mode==3'b100)||(mode==3'b010),
local_lvl=cong?2'b11:2'b10, worse=cong&&(fecn!=2'b00)&&(local_lvl>fecn),
marked=markable_mode&&worse. When marked,
cci_out={mode,3'b000,LoC=0,cci_in[8:2],local_lvl}; else cci_out=cci_in.
Not CAQM. Product instantiator is vibe_fabric u_fecn; stock Icarus
tc_fecn_mark uses u_f; Decision-I wrap uses instance u_u (not
leftover u_fecn / u_f).
This is not vibe_icrc / vibe_nw_adapt / vibe_dll / vibe_bcrc /
vibe_dll_tx / vibe_dll_credit / vibe_dll_sm / vibe_dll_rx /
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
First fabric leaf after NW tip-align wave complete (stage-79
vibe_nw_adapt wrap). Do not invent vibe_vl_rr or later fabric
leaves here.
Stock Icarus tc_fecn_mark remains the official TP scorer
(direct vibe_fecn_mark top, instance u_f). Header-only vs stock;
no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

FECN_WM = 24
MASK16 = 0xFFFF
MASK6 = 0x3F
MASK3 = 0x7
MASK2 = 0x3
MID_KEEP = 0x1FC  # cci_in[8:2]

MODE_FECN = 0b100
MODE_FECN_RTT = 0b010
FECN_UNMARKABLE = 0b00
FECN_LIGHT = 0b01
FECN_NONE = 0b10
FECN_SEVERE = 0b11
LVL_NONE = 0b10
LVL_SEVERE = 0b11

HIER = "u_u.cci_out / u_u.marked"
WRAP = "vibe_fecn_mark_cocotb_top"
INST = "u_u"
# Product ports from rtl/fabric/vibe_fecn_mark.sv. Combo: no clk /
# rst_n / ready. ovf_l (F1) is not a port.
PINS = (
    "cci_in", "voq_occ",
    "cci_out", "marked",
)
# Leftover leaf / dual-clock / F1 / sibling pins must not appear on
# the wrap top. Instance is u_u (Decision-I leaf wrappers), not
# leftover product instantiator u_fecn or stock Icarus u_f.
ABSENT = (
    "clk", "rst_n", "clk_fab",
    "ovf_l", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld",
    "u_fecn", "u_f", "u_n", "u_nw", "u_icrc", "u_bcrc", "u_b",
    "u_l", "u_dsk", "u_un", "u_fec",
    "u_crd", "u_sm", "u_rbuf", "u_dll", "u_tx", "u_rx",
    "u_ack", "u_req", "u_rack", "u_adapt",
    "u_vl", "u_rr", "u_lu", "u_ps", "u_voq", "u_saf", "u_xbar",
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
    "device_rst", "pcs_dll_data", "pcs_dll_vld", "dll_nw_ready",
    "pcs_dll_ready", "dll_nw_data", "dll_nw_vld",
    "start_ack", "rd_ptr", "wr_ptr", "rcv_ptr", "tail_ptr", "num_free",
    "link_ready", "fab_nw_data", "fab_nw_vld", "fab_nw_ready",
)
FECN_NAME = {0: "unmarkable", 1: "light", 2: "none", 3: "severe"}


def pack_cci(mode: int, mid: int = 0, fecn: int = 0) -> int:
    """mode[15:13] | mid[12:2] | fecn[1:0]. mid is the 11-bit [12:2] field."""
    return (((int(mode) & MASK3) << 13)
            | ((int(mid) & 0x7FF) << 2)
            | (int(fecn) & MASK2))


def decode(cci_in: int, voq_occ: int, fecn_wm: int = FECN_WM):
    """Product combo: marked + rewrite or pass-through."""
    cci_in = int(cci_in) & MASK16
    voq_occ = int(voq_occ) & MASK6
    mode = (cci_in >> 13) & MASK3
    fecn = cci_in & MASK2
    cong = int(voq_occ >= (int(fecn_wm) & MASK6))
    markable_mode = int(mode == MODE_FECN or mode == MODE_FECN_RTT)
    local_lvl = LVL_SEVERE if cong else LVL_NONE
    worse = int(bool(cong) and fecn != FECN_UNMARKABLE and local_lvl > fecn)
    marked = int(bool(markable_mode) and bool(worse))
    if marked:
        cci_out = (mode << 13) | (cci_in & MID_KEEP) | local_lvl
    else:
        cci_out = cci_in
    return cci_out, marked, mode, fecn, cong, markable_mode, local_lvl, worse


def _hex16(v) -> str:
    if v is None:
        return "x"
    return f"0x{int(v) & MASK16:04x}"


def _fmt(cci_out, marked) -> str:
    if cci_out is None or marked is None:
        return f"cci_out={_hex16(cci_out)} marked={marked}"
    cci_out = int(cci_out) & MASK16
    mode = (cci_out >> 13) & MASK3
    loc = (cci_out >> 9) & 1
    fecn = cci_out & MASK2
    return (
        f"cci_out={_hex16(cci_out)} marked={int(marked)} "
        f"mode={mode:03b} LoC={loc} "
        f"FECN={fecn:02b}({FECN_NAME.get(fecn, '?')})"
    )


class tc_vibe_fecn_mark(VibeUnitBaseTest):
    async def _apply(self, cci_in, voq_occ):
        """Drive combo inputs and settle (#1 like stock tc_fecn_mark)."""
        sset(self.dut.cci_in, int(cci_in) & MASK16)
        sset(self.dut.voq_occ, int(voq_occ) & MASK6)
        await Timer(1, "NS")
        return self._sample()

    def _sample(self):
        d = self.dut
        return ival(d.cci_out, -1), ival(d.marked, -1)

    def _inner_sample(self):
        u = getattr(self.dut, INST, None)
        if u is None:
            return None
        return ival(u.cci_out, -1), ival(u.marked, -1)

    def _score_inner(self, name, stim, got_out, got_m):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + f" ({INST})",
                     f"{INST} present", "missing", WRAP)
            return False
        iout, im = inner
        if im != got_m:
            self.bad(name, stim + f" (port vs {INST})",
                     f"marked={got_m} cci_out={_hex16(got_out)}",
                     f"{INST} marked={im} cci_out={_hex16(iout)}",
                     HIER)
            return False
        if got_out is None or iout is None:
            if got_out != iout:
                self.bad(name, stim + f" ({INST} vs wrap)",
                         _hex16(got_out), _hex16(iout),
                         f"{INST}.cci_out")
                return False
            return True
        if (int(iout) & MASK16) != (int(got_out) & MASK16):
            self.bad(name, stim + f" ({INST} vs wrap)",
                     _hex16(got_out), _hex16(iout),
                     f"{INST}.cci_out")
            return False
        return True

    def _score(self, name, stim, cci_in, voq_occ, got):
        exp_out, exp_m, mode, fecn, cong, markable, local_lvl, worse = decode(
            cci_in, voq_occ)
        got_out, got_m = got
        if got_out != exp_out or got_m != exp_m:
            self.bad(name, stim,
                     _fmt(exp_out, exp_m),
                     _fmt(got_out, got_m),
                     HIER)
            return False
        if got_m not in (0, 1):
            self.bad(name, stim + " (marked 0/1)",
                     "marked=0 or 1", _fmt(got_out, got_m), "u_u.marked")
            return False
        if got_m:
            if ((got_out >> 13) & MASK3) != mode:
                self.bad(name, stim + " (mode preserved)",
                         f"mode={mode:03b}", _fmt(got_out, got_m),
                         "u_u.cci_out[15:13]")
                return False
            if ((got_out >> 10) & MASK3) != 0:
                self.bad(name, stim + " (rewrite [12:10]=000)",
                         "cci_out[12:10]=000", _fmt(got_out, got_m),
                         "u_u.cci_out")
                return False
            if ((got_out >> 9) & 1) != 0:
                self.bad(name, stim + " (LoC=0 when marked)",
                         "LoC=0", _fmt(got_out, got_m), "u_u.cci_out[9]")
                return False
            if (got_out & MID_KEEP) != (int(cci_in) & MID_KEEP):
                self.bad(name, stim + " (cci_in[8:2] preserved)",
                         f"cci_out[8:2]={((int(cci_in) & MID_KEEP) >> 2):02x}",
                         _fmt(got_out, got_m), "u_u.cci_out[8:2]")
                return False
            if (got_out & MASK2) != local_lvl:
                self.bad(name, stim + " (FECN=local_lvl)",
                         f"FECN={local_lvl:02b}",
                         _fmt(got_out, got_m), "u_u.cci_out[1:0]")
                return False
        else:
            if got_out != (int(cci_in) & MASK16):
                self.bad(name, stim + " (pass-through)",
                         _hex16(cci_in), _fmt(got_out, got_m), "u_u.cci_out")
                return False
        if not self._score_inner(name, stim, got_out, got_m):
            return False
        u = getattr(self.dut, INST, None)
        if u is None:
            return True
        try:
            inner_cong = ival(u.cong, None)
            inner_worse = ival(u.worse, None)
            inner_mode = ival(u.mode, None)
            inner_fecn = ival(u.fecn, None)
            inner_mm = ival(u.markable_mode, None)
            inner_lvl = ival(u.local_lvl, None)
        except Exception:
            inner_cong = inner_worse = inner_mode = inner_fecn = None
            inner_mm = inner_lvl = None
        if inner_cong is not None and inner_cong != cong:
            self.bad(name, stim + f" ({INST}.cong)",
                     f"cong={cong}", f"{INST}.cong={inner_cong}",
                     f"{INST}.cong")
            return False
        if inner_worse is not None and inner_worse != worse:
            self.bad(name, stim + f" ({INST}.worse)",
                     f"worse={worse}", f"{INST}.worse={inner_worse}",
                     f"{INST}.worse")
            return False
        if inner_mode is not None and (inner_mode & MASK3) != mode:
            self.bad(name, stim + f" ({INST}.mode)",
                     f"mode={mode:03b}", f"{INST}.mode={inner_mode}",
                     f"{INST}.mode")
            return False
        if inner_fecn is not None and (inner_fecn & MASK2) != fecn:
            self.bad(name, stim + f" ({INST}.fecn)",
                     f"fecn={fecn:02b}", f"{INST}.fecn={inner_fecn}",
                     f"{INST}.fecn")
            return False
        if inner_mm is not None and inner_mm != markable:
            self.bad(name, stim + f" ({INST}.markable_mode)",
                     f"markable_mode={markable}",
                     f"{INST}.markable_mode={inner_mm}",
                     f"{INST}.markable_mode")
            return False
        if inner_lvl is not None and (inner_lvl & MASK2) != local_lvl:
            self.bad(name, stim + f" ({INST}.local_lvl)",
                     f"local_lvl={local_lvl:02b}",
                     f"{INST}.local_lvl={inner_lvl}",
                     f"{INST}.local_lvl")
            return False
        return True

    async def _expect(self, name, stim, cci_in, voq_occ):
        got = await self._apply(cci_in, voq_occ)
        if not self._score(name, stim, cci_in, voq_occ, got):
            return None
        return got

    async def run_phase(self, phase):
        phase.raise_objection(self)
        name = "tc_vibe_fecn_mark"

        g_idle = decode(0, 0)
        if g_idle[1] != 0 or g_idle[0] != 0:
            self.bad(name, "golden idle empty VOQ mode 0",
                     "cci_out=0 marked=0",
                     _fmt(g_idle[0], g_idle[1]), "golden")
            phase.drop_objection(self)
            return
        g_m100 = decode(pack_cci(MODE_FECN, 0, FECN_LIGHT), 24)
        if g_m100[1] != 1 or (g_m100[0] & MASK2) != LVL_SEVERE:
            self.bad(name, "golden Mode=100 FECN=01 occ=24",
                     "marked=1 FECN=11",
                     _fmt(g_m100[0], g_m100[1]), "golden")
            phase.drop_objection(self)
            return
        g_m010 = decode(pack_cci(MODE_FECN_RTT, 0, FECN_LIGHT), 24)
        if g_m010[1] != 1:
            self.bad(name, "golden Mode=010 FECN=01 occ=24",
                     "marked=1", _fmt(g_m010[0], g_m010[1]), "golden")
            phase.drop_objection(self)
            return
        g_u00 = decode(pack_cci(MODE_FECN, 0, FECN_UNMARKABLE), 24)
        if g_u00[1] != 0:
            self.bad(name, "golden FECN=00 unmarkable",
                     "marked=0", _fmt(g_u00[0], g_u00[1]), "golden")
            phase.drop_objection(self)
            return
        g_sev = decode(pack_cci(MODE_FECN, 0, FECN_SEVERE), 24)
        if g_sev[1] != 0:
            self.bad(name, "golden FECN=11 already severe",
                     "marked=0 (not worse)",
                     _fmt(g_sev[0], g_sev[1]), "golden")
            phase.drop_objection(self)
            return
        g_m000 = decode(pack_cci(0, 0, FECN_LIGHT), 24)
        if g_m000[1] != 0:
            self.bad(name, "golden Mode=000 (not CAQM)",
                     "marked=0", _fmt(g_m000[0], g_m000[1]), "golden")
            phase.drop_objection(self)
            return
        g_wm = decode(pack_cci(MODE_FECN, 0, FECN_LIGHT), 23)
        if g_wm[1] != 0:
            self.bad(name, "golden occ=23 below FECN_WM",
                     "marked=0", _fmt(g_wm[0], g_wm[1]), "golden")
            phase.drop_objection(self)
            return
        g_none = decode(pack_cci(MODE_FECN, 0, FECN_NONE), 24)
        if g_none[1] != 1 or (g_none[0] & MASK2) != LVL_SEVERE:
            self.bad(name, "golden FECN=10 none + cong → worse",
                     "marked=1 FECN=11",
                     _fmt(g_none[0], g_none[1]), "golden")
            phase.drop_objection(self)
            return

        # 1. Combo idle / empty VOQ mode 0 (stock).
        got = await self._expect(name, "empty VOQ mode 0 (stock)", 0, 0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "idle ports",
                     "cci_out=0 marked=0", _fmt(*got), HIER)
            phase.drop_objection(self)
            return

        # Walk away and back: combo, no sequential hold.
        mid_walk = pack_cci(MODE_FECN, 0x155, FECN_LIGHT)
        got = await self._expect(
            name, "Mode=100 FECN=01 occ=24 mid-walk (no hold)",
            mid_walk, 24)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "back to empty VOQ mode 0 (no sequential hold)", 0, 0)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (0, 0):
            self.bad(name, "combo idle after mark vector",
                     "cci_out=0 marked=0 (not latched)",
                     _fmt(*got), HIER)
            phase.drop_objection(self)
            return

        # 2. Stock Icarus tc_fecn_mark vectors (plus cci_out golden).
        stock = (
            ("Mode=100 FECN=01 occ=24 (stock)",
             pack_cci(MODE_FECN, 0, FECN_LIGHT), 24),
            ("Mode=010 FECN=01 occ=24 (stock)",
             pack_cci(MODE_FECN_RTT, 0, FECN_LIGHT), 24),
            ("FECN=00 unmarkable (stock)",
             pack_cci(MODE_FECN, 0, FECN_UNMARKABLE), 24),
            ("FECN=11 already severe (stock)",
             pack_cci(MODE_FECN, 0, FECN_SEVERE), 24),
            ("Mode=000 (stock; not CAQM)",
             pack_cci(0, 0, FECN_LIGHT), 24),
        )
        for stim, cci, occ in stock:
            if await self._expect(name, stim, cci, occ) is None:
                phase.drop_objection(self)
                return

        # 3. Watermark / FECN level / remaining modes (DUT header only).
        extra = (
            ("occ=23 Mode=100 FECN=01 (below FECN_WM)",
             pack_cci(MODE_FECN, 0, FECN_LIGHT), 23),
            ("occ=24 Mode=100 FECN=10 none (local worse)",
             pack_cci(MODE_FECN, 0, FECN_NONE), 24),
            ("occ=25 Mode=100 FECN=01 (above FECN_WM)",
             pack_cci(MODE_FECN, 0, FECN_LIGHT), 25),
            ("occ=0 Mode=100 FECN=01 (empty VOQ)",
             pack_cci(MODE_FECN, 0, FECN_LIGHT), 0),
            ("occ=63 Mode=100 FECN=01 (max VOQ)",
             pack_cci(MODE_FECN, 0, FECN_LIGHT), 63),
            ("occ=24 Mode=010 FECN=10 none",
             pack_cci(MODE_FECN_RTT, 0, FECN_NONE), 24),
            ("occ=23 Mode=010 FECN=01 (below WM)",
             pack_cci(MODE_FECN_RTT, 0, FECN_LIGHT), 23),
            ("occ=24 Mode=010 FECN=00 unmarkable",
             pack_cci(MODE_FECN_RTT, 0, FECN_UNMARKABLE), 24),
            ("occ=24 Mode=010 FECN=11 already severe",
             pack_cci(MODE_FECN_RTT, 0, FECN_SEVERE), 24),
            ("!cong FECN=10 Mode=100 (not worse)",
             pack_cci(MODE_FECN, 0, FECN_NONE), 0),
        )
        for stim, cci, occ in extra:
            if await self._expect(name, stim, cci, occ) is None:
                phase.drop_objection(self)
                return

        for mode in (0b000, 0b001, 0b011, 0b101, 0b110, 0b111):
            cci = pack_cci(mode, 0, FECN_LIGHT)
            stim = f"Mode={mode:03b} FECN=01 occ=24 (not markable; not CAQM)"
            if await self._expect(name, stim, cci, 24) is None:
                phase.drop_objection(self)
                return

        # 4. Rewrite vs pass-through of mid bits / LoC (DUT concat).
        mid_set = pack_cci(MODE_FECN, 0x7FF, FECN_LIGHT)  # [12:2] all 1
        got = await self._expect(
            name, "marked rewrite: LoC/[12:10] cleared, [8:2] kept",
            mid_set, 24)
        if got is None:
            phase.drop_objection(self)
            return
        exp_mid = (MODE_FECN << 13) | (mid_set & MID_KEEP) | LVL_SEVERE
        if got != (exp_mid, 1):
            self.bad(name, "marked mid-bit rewrite",
                     _fmt(exp_mid, 1), _fmt(*got), HIER)
            phase.drop_objection(self)
            return

        passthru = pack_cci(MODE_FECN, 0x7FF, FECN_SEVERE)
        got = await self._expect(
            name, "not marked: mid bits / LoC / FECN pass-through",
            passthru, 24)
        if got is None:
            phase.drop_objection(self)
            return
        if got != (passthru, 0):
            self.bad(name, "pass-through keeps LoC and [12:2]",
                     _fmt(passthru, 0), _fmt(*got), HIER)
            phase.drop_objection(self)
            return

        rtt_ts = pack_cci(MODE_FECN_RTT, 0x2A5, FECN_LIGHT)
        if await self._expect(
                name, "Mode=010 marked: [8:2] (timestamp bits) preserved",
                rtt_ts, 24) is None:
            phase.drop_objection(self)
            return

        # Re-score a second pass (combo stable; same stim → same outs).
        replay = stock + extra + (
            ("replay mid-set marked", mid_set, 24),
            ("replay mid-set pass-through", passthru, 24),
        )
        for stim, cci, occ in replay:
            if await self._expect(name, f"re-score {stim}", cci, occ) is None:
                phase.drop_objection(self)
                return

        # Hold a named marked vector; combo output must not drift.
        held_cci = pack_cci(MODE_FECN, 0x055, FECN_LIGHT)
        got = await self._expect(
            name, "hold Mode=100 FECN=01 occ=24 before settle",
            held_cci, 24)
        if got is None:
            phase.drop_objection(self)
            return
        held = got
        await Timer(5, "NS")
        later = self._sample()
        if later != held:
            self.bad(name, "hold marked vector for 5 ns (no clock)",
                     _fmt(*held), _fmt(*later), HIER)
            phase.drop_objection(self)
            return
        if not self._score(name, "hold 5 ns still matches golden",
                           held_cci, 24, later):
            phase.drop_objection(self)
            return

        # 5. Leaf pins match product SV (no clk / rst_n / ovf_l /
        # leftover u_fecn). Instance u_u (not leftover u_fecn / u_f).
        d = self.dut
        if not hasattr(d, INST):
            self.bad(name, f"leaf instance scan ({INST})",
                     f"{INST} present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_fecn_mark product port",
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


uvm_component_utils(tc_vibe_fecn_mark)
