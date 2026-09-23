"""Module-level uvm-python TC for Decision-I leaf vibe_dll_tx.

Covers reset / !link_up clearing rem / pkt / fq_n / dll_pcs_vld;
combo nw_dll_ready backpressure (credit_low / bp_pending / drop_data
/ !can_send / replay / AMCTL / fq_occ); CFG0 consume_cfg0 (credit
skip, no credit DUT here); 1-flit EOP Null-pad to a 4-flit group +
BCRC emit; 80-byte remainder pack across two 64B beats; send_idle /
send_req / send_ack zero-beat; replay {replay_flit, 480'0}; async
rst_n mid-stream. Not a full-chip consecutive-green gate. Not 1/3,
4/3, freeze, or signoff. Not TP-DLL-004 / full vibe_dll.

Matches product rtl/dll/vibe_dll_tx.sv: async-low rst_n, 512b→20B
rem pack, emit {fq[0], fq[1], fq[2], fq[3][159:32], crc_w} with
CRC30 init all-1s (same poly as vibe_bcrc; no invert; last 32b
{2'b0, crc3}), EOP Null-pad, consume counts data flits only.
Instantiated by vibe_dll u_tx. Stock Icarus tc_dll_tx_cfg0 remains
the official TP scorer (tx + credit cells). Header-only vs stock;
no invented protocol. ovf_l (F1) is not in this module.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest
from vibe_uvm.tests.unit_bcrc import CRC_INIT, crc30_flit

MASK4 = 0xF
MASK5 = 0x1F
MASK7 = 0x7F
MASK10 = 0x3FF
MASK16 = 0xFFFF
MASK30 = (1 << 30) - 1
MASK32 = (1 << 32) - 1
MASK160 = (1 << 160) - 1
MASK352 = (1 << 352) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
MASK672 = (1 << 672) - 1
HIER = "u_u.nw_dll_ready / dll_pcs_vld / consume_* / fq_n / pkt_act"

# Distinctive 352b body so a slice/shift swap fails (stock overlay B).
PAT352 = int("A5A55A5A0123456789ABCDEFFEDCBA98765432101111222233334444555566667777888899", 16) & MASK352
PAT352B = int("5A5AA5A5FEDCBA98765432100123456789ABCDEF2222111133334444555566667777888899", 16) & MASK352
REPLAY_FLIT = 0x0123456789ABCDEF0123456789ABCDEF01234567


def pkt_bytes(flit: int) -> int:
    """Product vibe_pkt_bytes: decl_flits(PLENGTH) * 20."""
    return lph.decl_flits(lph.lph_plength(int(flit) & MASK160)) * 20


def mk_nw(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """512b NW beat: LPH in [511:352] (vibe_nw512_flit0)."""
    if payload is None:
        payload = PAT352
    return lph.mk_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK352,
    )


def pcs_beat_of(flits) -> int:
    """Product emit: {fq0, fq1, fq2, fq3[159:32], {2'b0, crc3}}."""
    fq = [int(f) & MASK160 for f in list(flits)[:4]]
    while len(fq) < 4:
        fq.append(0)
    c = CRC_INIT
    for f in fq:
        c = crc30_flit(c, f)
    crc_w = c & MASK30
    low160 = ((fq[3] >> 32) << 32) | crc_w
    return ((fq[0] << 480) | (fq[1] << 320) | (fq[2] << 160) | low160) & MASK640


def pack_stream(rem_lj, rem_b, nw_data, val_b, n_flits):
    """Product 672b rem || valid-NW window → nf0..nf3 + new_rem_lj."""
    rem_bits = (int(rem_b) & MASK5) * 8
    val_bits = (int(val_b) & MASK7) * 8
    if rem_b == 0:
        rem_c = 0
    else:
        rem_c = int(rem_lj) & MASK160 & (MASK160 << (160 - rem_bits))
    if val_b == 0:
        nw_c = 0
    else:
        nw_c = int(nw_data) & MASK512 & (MASK512 << (512 - val_bits))
    gap = 160 - rem_bits
    stream = ((rem_c << 512) | (nw_c << gap)) & MASK672
    nfs = [
        (stream >> 512) & MASK160,
        (stream >> 352) & MASK160,
        (stream >> 192) & MASK160,
        (stream >> 32) & MASK160,
    ]
    stream_sh = (stream << (int(n_flits) * 160)) & MASK672
    new_rem_lj = (stream_sh >> 512) & MASK160
    return nfs, new_rem_lj


class Golden:
    """Cycle-accurate rem / pkt / fq / emit vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.rem_lj = 0
        self.rem_b = 0
        self.pkt_act = 0
        self.pkt_left = 0
        self.fq = [0] * 8
        self.fq_n = 0
        self.dll_pcs_data = 0
        self.dll_pcs_vld = 0

    def _cur_left_val(self, nw_dll_data):
        sop_flit = lph.nw512_flit0(int(nw_dll_data) & MASK512)
        sop_bytes = pkt_bytes(sop_flit) & MASK16
        cur_left = (self.pkt_left & MASK16) if self.pkt_act else sop_bytes
        val_b = 64 if cur_left > 64 else (cur_left & MASK7)
        tot_b = (self.rem_b & MASK5) + val_b
        n_flits = tot_b // 20
        new_rem_b = tot_b % 20
        return sop_flit, cur_left, val_b, n_flits, new_rem_b

    def combo(self, link_up=1, status_up=1, credit_low=0, bp_pending=0,
              drop_data=0, can_send=1, replay=0, send_idle=0, send_req=0,
              send_ack=0, nw_dll_data=0, nw_dll_vld=0, dll_pcs_ready=1):
        emitting = (self.fq_n >= 4
                    and (bool(dll_pcs_ready) or not self.dll_pcs_vld)
                    and not send_idle and not send_req
                    and not send_ack and not replay)
        fq_occ = self.fq_n - (4 if emitting else 0)
        ready = (bool(link_up) and bool(status_up) and not credit_low
                 and not bp_pending and not drop_data and bool(can_send)
                 and not replay and not send_idle and not send_req
                 and not send_ack and fq_occ <= 4)
        sop_flit, cur_left, val_b, n_flits, new_rem_b = self._cur_left_val(
            nw_dll_data)
        nfs, new_rem_lj = pack_stream(
            self.rem_lj, self.rem_b, nw_dll_data, val_b, n_flits)
        is_null = 1 if send_idle else 0
        is_retry = 1 if (send_req or send_ack) else 0
        wr_en = 1 if (emitting and not is_null and not is_retry) else 0
        consume_cfg0 = 1 if (not self.pkt_act
                             and lph.lph_cfg(sop_flit) == 0) else 0
        consume_vld = 1 if (nw_dll_vld and ready) else 0
        return {
            "nw_dll_ready": 1 if ready else 0,
            "dll_pcs_data": self.dll_pcs_data & MASK640,
            "dll_pcs_vld": int(self.dll_pcs_vld),
            "wr_en": wr_en,
            "wr_flit": self.fq[0] & MASK160,
            "is_null": is_null,
            "is_retry": is_retry,
            "consume_flits": n_flits & MASK10,
            "consume_vld": consume_vld,
            "consume_cfg0": consume_cfg0,
            "emitting": 1 if emitting else 0,
            "n_flits": n_flits,
            "nfs": nfs,
            "new_rem_lj": new_rem_lj,
            "new_rem_b": new_rem_b,
            "cur_left": cur_left,
            "val_b": val_b,
            "pcs_beat": pcs_beat_of(self.fq[:4]),
            "fq_n": self.fq_n & MASK4,
            "pkt_act": int(self.pkt_act),
            "rem_b": self.rem_b & MASK5,
        }

    def step(self, link_up=1, status_up=1, credit_low=0, bp_pending=0,
             drop_data=0, can_send=1, replay=0, replay_flit=0,
             send_idle=0, send_req=0, send_ack=0,
             nw_dll_data=0, nw_dll_vld=0, dll_pcs_ready=1):
        if not link_up:
            self.rem_lj = 0
            self.rem_b = 0
            self.pkt_act = 0
            self.pkt_left = 0
            self.fq_n = 0
            self.dll_pcs_vld = 0
            return self.combo(
                link_up, status_up, credit_low, bp_pending, drop_data,
                can_send, replay, send_idle, send_req, send_ack,
                nw_dll_data, nw_dll_vld, dll_pcs_ready)

        c = self.combo(
            link_up, status_up, credit_low, bp_pending, drop_data,
            can_send, replay, send_idle, send_req, send_ack,
            nw_dll_data, nw_dll_vld, dll_pcs_ready)
        fq_nxt = self.fq[:]
        fq_n_nxt = self.fq_n
        if c["emitting"]:
            fq_nxt = self.fq[4:] + [0, 0, 0, 0]
            fq_n_nxt = self.fq_n - 4
        if c["consume_vld"]:
            for i in range(c["n_flits"]):
                fq_nxt[fq_n_nxt + i] = c["nfs"][i] & MASK160
            fq_n_nxt = fq_n_nxt + c["n_flits"]
            if c["cur_left"] <= c["val_b"]:
                while fq_n_nxt & 3:
                    fq_nxt[fq_n_nxt] = 0
                    fq_n_nxt += 1
        self.fq = [int(x) & MASK160 for x in fq_nxt]
        self.fq_n = fq_n_nxt & MASK4

        slot_free = bool(dll_pcs_ready) or not self.dll_pcs_vld
        if send_idle or send_req or send_ack:
            if slot_free:
                self.dll_pcs_data = 0
                self.dll_pcs_vld = 1
        elif replay:
            if slot_free:
                self.dll_pcs_data = (int(replay_flit) & MASK160) << 480
                self.dll_pcs_vld = 1
        elif c["emitting"]:
            self.dll_pcs_data = c["pcs_beat"] & MASK640
            self.dll_pcs_vld = 1
        elif self.dll_pcs_vld and dll_pcs_ready:
            self.dll_pcs_vld = 0

        if c["consume_vld"]:
            if c["cur_left"] <= c["val_b"]:
                self.pkt_act = 0
                self.pkt_left = 0
                self.rem_b = 0
                self.rem_lj = 0
            else:
                self.pkt_act = 1
                self.pkt_left = (c["cur_left"] - c["val_b"]) & MASK16
                self.rem_b = c["new_rem_b"] & MASK5
                self.rem_lj = c["new_rem_lj"] & MASK160
        return self.combo(
            link_up, status_up, credit_low, bp_pending, drop_data,
            can_send, replay, send_idle, send_req, send_ack,
            nw_dll_data, nw_dll_vld, dll_pcs_ready)


class tc_vibe_dll_tx(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=1, **kw):
        d = self.dut
        stim = {
            "link_up": 1 if link_up else 0,
            "status_up": 1,
            "credit_low": 0,
            "bp_pending": 0,
            "drop_data": 0,
            "can_send": 1,
            "replay": 0,
            "replay_flit": 0,
            "send_idle": 0,
            "send_req": 0,
            "send_ack": 0,
            "nw_dll_data": 0,
            "nw_dll_vld": 0,
            "dll_pcs_ready": 1,
        }
        stim.update(kw)
        sset(d.link_up, stim["link_up"])
        sset(d.status_up, stim["status_up"])
        sset(d.credit_low, stim["credit_low"])
        sset(d.bp_pending, stim["bp_pending"])
        sset(d.drop_data, stim["drop_data"])
        sset(d.can_send, stim["can_send"])
        sset(d.replay, stim["replay"])
        sset(d.replay_flit, int(stim["replay_flit"]) & MASK160)
        sset(d.send_idle, stim["send_idle"])
        sset(d.send_req, stim["send_req"])
        sset(d.send_ack, stim["send_ack"])
        sset(d.nw_dll_data, int(stim["nw_dll_data"]) & MASK512)
        sset(d.nw_dll_vld, stim["nw_dll_vld"])
        sset(d.dll_pcs_ready, stim["dll_pcs_ready"])
        self._stim = stim

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

    def _inner(self, path, default=None):
        try:
            return ival(hier(self.dut, path), default)
        except Exception:
            return default

    def _sample(self):
        d = self.dut
        return {
            "nw_dll_ready": ival(d.nw_dll_ready, -1),
            "dll_pcs_data": ival(d.dll_pcs_data, None),
            "dll_pcs_vld": ival(d.dll_pcs_vld, -1),
            "wr_en": ival(d.wr_en, -1),
            "wr_flit": ival(d.wr_flit, None),
            "is_null": ival(d.is_null, -1),
            "is_retry": ival(d.is_retry, -1),
            "consume_flits": ival(d.consume_flits, -1),
            "consume_vld": ival(d.consume_vld, -1),
            "consume_cfg0": ival(d.consume_cfg0, -1),
            "fq_n": self._inner("u_u.fq_n", None),
            "pkt_act": self._inner("u_u.pkt_act", None),
            "rem_b": self._inner("u_u.rem_b", None),
        }

    def _fmt(self, s):
        data = s["dll_pcs_data"]
        flit = s["wr_flit"]
        dh = "x" if data is None or (isinstance(data, int) and data < 0) else hex(data)
        fh = "x" if flit is None or (isinstance(flit, int) and flit < 0) else hex(flit)
        return (
            f"rdy={s['nw_dll_ready']} pcs_vld={s['dll_pcs_vld']} "
            f"wr_en={s['wr_en']} null={s['is_null']} retry={s['is_retry']} "
            f"cvld={s['consume_vld']} cfl={s['consume_flits']} "
            f"cfg0={s['consume_cfg0']} fq_n={s['fq_n']} "
            f"pkt_act={s['pkt_act']} rem_b={s['rem_b']} "
            f"pcs={dh} wr={fh}"
        )

    def _exp_combo(self):
        st = self._stim
        return self.g.combo(
            st["link_up"], st["status_up"], st["credit_low"],
            st["bp_pending"], st["drop_data"], st["can_send"],
            st["replay"], st["send_idle"], st["send_req"], st["send_ack"],
            st["nw_dll_data"], st["nw_dll_vld"], st["dll_pcs_ready"])

    @staticmethod
    def _wide_ok(got, exp, mask):
        if got is None or (isinstance(got, int) and got < 0):
            return True
        return (int(got) & mask) == (int(exp) & mask)

    def _score_combo(self, name, stim, got, exp, score_wide=True):
        keys = ("nw_dll_ready", "dll_pcs_vld", "wr_en", "is_null",
                "is_retry", "consume_flits", "consume_vld", "consume_cfg0")
        for k in keys:
            gv, ev = got[k], exp[k]
            if gv is None or (isinstance(gv, int) and gv < 0):
                self.bad(name, stim + f" ({k} unresolved)",
                         f"{k}={ev}", self._fmt(got), HIER)
                return False
            if (int(gv) & (MASK10 if k == "consume_flits" else 1)) != ev:
                self.bad(name, stim + f" ({k})",
                         f"{k}={ev}", self._fmt(got), HIER)
                return False
        if score_wide:
            if not self._wide_ok(got["dll_pcs_data"], exp["dll_pcs_data"],
                                 MASK640):
                self.bad(name, stim + " (dll_pcs_data)",
                         hex(exp["dll_pcs_data"]), self._fmt(got),
                         "u_u.dll_pcs_data")
                return False
            if not self._wide_ok(got["wr_flit"], exp["wr_flit"], MASK160):
                self.bad(name, stim + " (wr_flit)",
                         hex(exp["wr_flit"]), self._fmt(got), "u_u.wr_flit")
                return False
        return True

    def _score_state(self, name, stim, got):
        checks = (
            ("fq_n", got["fq_n"], self.g.fq_n, MASK4),
            ("pkt_act", got["pkt_act"], self.g.pkt_act, 1),
            ("rem_b", got["rem_b"], self.g.rem_b, MASK5),
        )
        for key, gv, ev, mask in checks:
            if gv is None:
                continue
            if (int(gv) & mask) != (int(ev) & mask):
                self.bad(name, stim + f" (u_u.{key})",
                         f"{key}={ev}", f"u_u.{key}={gv}", f"u_u.{key}")
                return False
        return True

    async def _drive(self, **kw):
        await self._idle(**kw)
        await Timer(100, "PS")

    async def _cycle(self, **kw):
        await self._drive(**kw)
        pre = self._sample()
        st = self._stim
        pre_exp = self.g.combo(
            st["link_up"], st["status_up"], st["credit_low"],
            st["bp_pending"], st["drop_data"], st["can_send"],
            st["replay"], st["send_idle"], st["send_req"], st["send_ack"],
            st["nw_dll_data"], st["nw_dll_vld"], st["dll_pcs_ready"])
        self.g.step(
            st["link_up"], st["status_up"], st["credit_low"],
            st["bp_pending"], st["drop_data"], st["can_send"],
            st["replay"], st["replay_flit"],
            st["send_idle"], st["send_req"], st["send_ack"],
            st["nw_dll_data"], st["nw_dll_vld"], st["dll_pcs_ready"])
        await self._to_fall()
        post = self._sample()
        return pre, post, pre_exp

    async def _expect(self, name, stim, score_wide=True, **kw):
        pre, post, pre_exp = await self._cycle(**kw)
        if not self._score_combo(name, stim + " (pre-NBA combo)",
                                 pre, pre_exp, score_wide=score_wide):
            return None
        if not self._score_combo(name, stim + " (post-NBA combo)",
                                 post, self._exp_combo(),
                                 score_wide=score_wide):
            return None
        if not self._score_state(name, stim, post):
            return None
        return pre, post

    def _golden_selfcheck(self, name):
        gchk = Golden()
        idle = gchk.combo()
        if (idle["dll_pcs_vld"] or idle["wr_en"] or idle["consume_vld"]
                or not idle["nw_dll_ready"] or idle["fq_n"]):
            self.bad(name, "golden reset idle",
                     "rdy=1 pcs_vld=0 wr_en=0 cvld=0 fq_n=0",
                     f"rdy={idle['nw_dll_ready']} vld={idle['dll_pcs_vld']}",
                     "golden")
            return False
        # data=0 → LPH cfg=0 → consume_cfg0 combo 1 (product, not a pulse).
        if idle["consume_cfg0"] != 1 or idle["consume_flits"] != 1:
            self.bad(name, "golden idle data=0 is CFG0 LPH",
                     "consume_cfg0=1 consume_flits=1",
                     f"cfg0={idle['consume_cfg0']} cfl={idle['consume_flits']}",
                     "golden")
            return False
        b1 = mk_nw(3, 0, 1)
        if pkt_bytes(lph.nw512_flit0(b1)) != 20:
            self.bad(name, "golden vibe_pkt_bytes 1-flit",
                     "20", str(pkt_bytes(lph.nw512_flit0(b1))), "golden")
            return False
        fire = gchk.combo(nw_dll_data=b1, nw_dll_vld=1)
        if fire["consume_vld"] != 1 or fire["consume_flits"] != 1:
            self.bad(name, "golden 1-flit accept combo",
                     "consume_vld=1 consume_flits=1",
                     f"cvld={fire['consume_vld']} cfl={fire['consume_flits']}",
                     "golden")
            return False
        if fire["consume_cfg0"] != 0 or fire["emitting"]:
            self.bad(name, "golden 1-flit not CFG0 / not yet emit",
                     "cfg0=0 emitting=0",
                     f"cfg0={fire['consume_cfg0']} em={fire['emitting']}",
                     "golden")
            return False
        gchk.step(nw_dll_data=b1, nw_dll_vld=1)
        if gchk.fq_n != 4 or gchk.pkt_act or gchk.fq[1] or gchk.fq[2] or gchk.fq[3]:
            self.bad(name, "golden 1-flit EOP Null-pad",
                     "fq_n=4 fq[1..3]=0 pkt_act=0",
                     f"fq_n={gchk.fq_n} fq1={gchk.fq[1]:x} act={gchk.pkt_act}",
                     "golden")
            return False
        if (gchk.fq[0] & MASK160) != (lph.nw512_flit0(b1) & MASK160):
            self.bad(name, "golden 1-flit nf0 is LPH",
                     hex(lph.nw512_flit0(b1)), hex(gchk.fq[0]), "golden")
            return False
        post = gchk.combo()
        if post["emitting"] != 1 or post["wr_en"] != 1:
            self.bad(name, "golden emit after pad",
                     "emitting=1 wr_en=1",
                     f"em={post['emitting']} wr={post['wr_en']}", "golden")
            return False
        gchk.step()
        exp = pcs_beat_of([lph.nw512_flit0(b1), 0, 0, 0])
        if (gchk.dll_pcs_data & MASK640) != exp or not gchk.dll_pcs_vld:
            self.bad(name, "golden 1-flit + BCRC emit",
                     hex(exp), hex(gchk.dll_pcs_data), "golden")
            return False
        gchk.reset()
        b4 = mk_nw(3, 0, 4)
        if pkt_bytes(lph.nw512_flit0(b4)) != 80:
            self.bad(name, "golden vibe_pkt_bytes 4-flit",
                     "80", str(pkt_bytes(lph.nw512_flit0(b4))), "golden")
            return False
        gchk.step(nw_dll_data=b4, nw_dll_vld=1)
        if gchk.fq_n != 3 or not gchk.pkt_act or gchk.pkt_left != 16 or gchk.rem_b != 4:
            self.bad(name, "golden 80B first beat rem",
                     "fq_n=3 pkt_act=1 left=16 rem_b=4",
                     f"fq_n={gchk.fq_n} act={gchk.pkt_act} "
                     f"left={gchk.pkt_left} rem={gchk.rem_b}",
                     "golden")
            return False
        gchk.step(nw_dll_data=mk_nw(3, 0, 4, PAT352B), nw_dll_vld=1)
        if gchk.fq_n != 4 or gchk.pkt_act or gchk.rem_b:
            self.bad(name, "golden 80B second beat EOP",
                     "fq_n=4 pkt_act=0 rem_b=0",
                     f"fq_n={gchk.fq_n} act={gchk.pkt_act} rem={gchk.rem_b}",
                     "golden")
            return False
        gchk.reset()
        for pin, key in (("credit_low", "credit_low"),
                         ("bp_pending", "bp_pending"),
                         ("drop_data", "drop_data")):
            blocked = gchk.combo(**{key: 1})
            if blocked["nw_dll_ready"]:
                self.bad(name, f"golden {pin} backpressure",
                         "nw_dll_ready=0",
                         f"rdy={blocked['nw_dll_ready']}", "golden")
                return False
        idle_am = gchk.combo(send_idle=1)
        if not idle_am["is_null"] or idle_am["nw_dll_ready"]:
            self.bad(name, "golden send_idle",
                     "is_null=1 rdy=0",
                     f"null={idle_am['is_null']} rdy={idle_am['nw_dll_ready']}",
                     "golden")
            return False
        gchk.step(send_idle=1)
        if gchk.dll_pcs_data != 0 or not gchk.dll_pcs_vld:
            self.bad(name, "golden send_idle zero beat",
                     "pcs=0 vld=1",
                     f"pcs={gchk.dll_pcs_data:x} vld={gchk.dll_pcs_vld}",
                     "golden")
            return False
        gchk.reset()
        gchk.step(replay=1, replay_flit=REPLAY_FLIT)
        exp_r = (REPLAY_FLIT & MASK160) << 480
        if (gchk.dll_pcs_data & MASK640) != exp_r or not gchk.dll_pcs_vld:
            self.bad(name, "golden replay {flit,480'0}",
                     hex(exp_r), hex(gchk.dll_pcs_data), "golden")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_tx"
        self.g = Golden()

        if not self._golden_selfcheck(name):
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: ready (up/can_send), no emit / consume pulse.
        got = self._sample()
        exp = self.g.combo()
        if not self._score_combo(name, "reset then release, idle", got, exp):
            phase.drop_objection(self)
            return
        if not self._score_state(name, "reset then release, idle", got):
            phase.drop_objection(self)
            return
        if (got["nw_dll_ready"] != 1 or got["dll_pcs_vld"]
                or got["wr_en"] or got["consume_vld"]):
            self.bad(name, "reset idle ports",
                     "rdy=1 pcs_vld=0 wr_en=0 cvld=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return

        # 2. Combo backpressure pins.
        for pin in ("credit_low", "bp_pending", "drop_data"):
            pair = await self._expect(name, f"{pin}=1 backpressure", **{pin: 1})
            if pair is None:
                phase.drop_objection(self)
                return
            if pair[0]["nw_dll_ready"] != 0:
                self.bad(name, f"{pin}=1",
                         "nw_dll_ready=0", self._fmt(pair[0]), HIER)
                phase.drop_objection(self)
                return
        pair = await self._expect(name, "can_send=0 backpressure", can_send=0)
        if pair is None or pair[0]["nw_dll_ready"] != 0:
            if pair is not None:
                self.bad(name, "can_send=0",
                         "nw_dll_ready=0", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "status_up=0 backpressure", status_up=0)
        if pair is None or pair[0]["nw_dll_ready"] != 0:
            if pair is not None:
                self.bad(name, "status_up=0",
                         "nw_dll_ready=0", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return

        # 3. CFG0 SOP: consume_cfg0 + consume_vld; 1-flit EOP pads + emits.
        c0 = mk_nw(0, 0, 1)
        pair = await self._expect(name, "CFG0 1-flit accept",
                                  nw_dll_data=c0, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["consume_cfg0"] != 1 or pre["consume_vld"] != 1:
            self.bad(name, "CFG0 consume (credit skip)",
                     "consume_cfg0=1 consume_vld=1",
                     self._fmt(pre), "u_u.consume_cfg0")
            phase.drop_objection(self)
            return
        if post["fq_n"] not in (None, 4) and post["fq_n"] != 4:
            self.bad(name, "CFG0 EOP Null-pad fq_n",
                     "fq_n=4", self._fmt(post), "u_u.fq_n")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "CFG0 emit 4-flit + BCRC")
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["wr_en"] != 1 or post["dll_pcs_vld"] != 1:
            self.bad(name, "CFG0 emit",
                     "pre wr_en=1 post pcs_vld=1",
                     f"pre {self._fmt(pre)} post {self._fmt(post)}", HIER)
            phase.drop_objection(self)
            return
        exp_c0 = pcs_beat_of([lph.nw512_flit0(c0), 0, 0, 0])
        if not self._wide_ok(post["dll_pcs_data"], exp_c0, MASK640):
            self.bad(name, "CFG0 pcs beat + BCRC",
                     hex(exp_c0), self._fmt(post), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "deassert pcs_vld after CFG0 emit")
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[1]["dll_pcs_vld"] != 0:
            self.bad(name, "pcs_vld drops when ready",
                     "dll_pcs_vld=0", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return

        # 4. CFG3 1-flit: LPH + 3 Nulls + BCRC; consume_cfg0=0.
        b1 = mk_nw(3, 0, 1)
        pair = await self._expect(name, "CFG3 1-flit accept",
                                  nw_dll_data=b1, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["consume_cfg0"] != 0 or pre["consume_vld"] != 1:
            self.bad(name, "CFG3 consume (not CFG0)",
                     "consume_cfg0=0 consume_vld=1",
                     self._fmt(pre), "u_u.consume_cfg0")
            phase.drop_objection(self)
            return
        if pre["consume_flits"] != 1:
            self.bad(name, "CFG3 1-flit consume_flits",
                     "consume_flits=1", self._fmt(pre), "u_u.consume_flits")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "CFG3 1-flit emit")
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["wr_en"] != 1 or post["dll_pcs_vld"] != 1:
            self.bad(name, "CFG3 emit",
                     "pre wr_en=1 post pcs_vld=1",
                     f"pre {self._fmt(pre)} post {self._fmt(post)}", HIER)
            phase.drop_objection(self)
            return
        exp_b1 = pcs_beat_of([lph.nw512_flit0(b1), 0, 0, 0])
        if not self._wide_ok(post["dll_pcs_data"], exp_b1, MASK640):
            self.bad(name, "CFG3 1-flit pcs beat + BCRC",
                     hex(exp_b1), self._fmt(post), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return
        if not self._wide_ok(pre["wr_flit"], lph.nw512_flit0(b1), MASK160):
            self.bad(name, "wr_flit is fq[0] LPH",
                     hex(lph.nw512_flit0(b1)), self._fmt(pre), "u_u.wr_flit")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "idle after CFG3 emit")
        if pair is None:
            phase.drop_objection(self)
            return

        # 5. 80-byte (4-flit) remainder: 64B → 3 flits + rem 4B; 16B EOP.
        b4 = mk_nw(3, 0, 4)
        b4b = mk_nw(3, 0, 4, PAT352B)
        pair = await self._expect(name, "80B first 64B beat",
                                  nw_dll_data=b4, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["consume_vld"] != 1 or pre["consume_flits"] != 3:
            self.bad(name, "80B beat0 consume 3 data flits",
                     "consume_vld=1 consume_flits=3",
                     self._fmt(pre), "u_u.consume_flits")
            phase.drop_objection(self)
            return
        if post["pkt_act"] not in (None, 1) and post["pkt_act"] != 1:
            self.bad(name, "80B beat0 pkt_act",
                     "pkt_act=1", self._fmt(post), "u_u.pkt_act")
            phase.drop_objection(self)
            return
        if post["fq_n"] not in (None, 3) and post["fq_n"] != 3:
            self.bad(name, "80B beat0 fq_n",
                     "fq_n=3", self._fmt(post), "u_u.fq_n")
            phase.drop_objection(self)
            return
        if post["dll_pcs_vld"]:
            self.bad(name, "80B beat0 must not emit yet",
                     "dll_pcs_vld=0", self._fmt(post), HIER)
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "80B second beat completes EOP",
                                  nw_dll_data=b4b, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        pre, post = pair
        if pre["consume_vld"] != 1 or pre["consume_flits"] != 1:
            self.bad(name, "80B beat1 consume 1 rem flit",
                     "consume_vld=1 consume_flits=1",
                     self._fmt(pre), "u_u.consume_flits")
            phase.drop_objection(self)
            return
        if post["pkt_act"] not in (None, 0) and post["pkt_act"] != 0:
            self.bad(name, "80B EOP clears pkt_act",
                     "pkt_act=0", self._fmt(post), "u_u.pkt_act")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "80B emit 4 data flits + BCRC")
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[0]["wr_en"] != 1 or pair[1]["dll_pcs_vld"] != 1:
            self.bad(name, "80B emit",
                     "pre wr_en=1 post pcs_vld=1",
                     f"pre {self._fmt(pair[0])} post {self._fmt(pair[1])}",
                     HIER)
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "idle after 80B emit")
        if pair is None:
            phase.drop_objection(self)
            return

        # 6. send_idle / send_req / send_ack: AMCTL zero beat; ready=0.
        pair = await self._expect(name, "send_idle is_null + zero beat",
                                  send_idle=1)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[0]["is_null"] != 1 or pair[0]["nw_dll_ready"] != 0:
            self.bad(name, "send_idle combo",
                     "is_null=1 rdy=0", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return
        if pair[1]["dll_pcs_vld"] != 1:
            self.bad(name, "send_idle emit vld",
                     "dll_pcs_vld=1", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return
        if not self._wide_ok(pair[1]["dll_pcs_data"], 0, MASK640):
            self.bad(name, "send_idle zero 640b",
                     "0", self._fmt(pair[1]), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "send_req is_retry + zero beat",
                                  send_req=1)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[0]["is_retry"] != 1 or pair[0]["is_null"] != 0:
            self.bad(name, "send_req combo",
                     "is_retry=1 is_null=0", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return
        if not self._wide_ok(pair[1]["dll_pcs_data"], 0, MASK640):
            self.bad(name, "send_req zero 640b",
                     "0", self._fmt(pair[1]), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "send_ack is_retry + zero beat",
                                  send_ack=1)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[0]["is_retry"] != 1:
            self.bad(name, "send_ack combo",
                     "is_retry=1", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return

        # 7. replay: {replay_flit, 480'0}; ready=0; wr_en=0.
        pair = await self._expect(
            name, "replay emit {flit,480'0}",
            replay=1, replay_flit=REPLAY_FLIT)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[0]["nw_dll_ready"] != 0 or pair[0]["wr_en"] != 0:
            self.bad(name, "replay blocks NW / no wr_en",
                     "rdy=0 wr_en=0", self._fmt(pair[0]), HIER)
            phase.drop_objection(self)
            return
        exp_r = (REPLAY_FLIT & MASK160) << 480
        if pair[1]["dll_pcs_vld"] != 1:
            self.bad(name, "replay pcs_vld",
                     "dll_pcs_vld=1", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return
        if not self._wide_ok(pair[1]["dll_pcs_data"], exp_r, MASK640):
            self.bad(name, "replay {flit,480'0}",
                     hex(exp_r), self._fmt(pair[1]), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return

        # 8. !link_up clears rem / pkt / fq_n / dll_pcs_vld (data may hold).
        pair = await self._expect(name, "CFG3 accept before !link_up",
                                  nw_dll_data=b1, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[1]["fq_n"] not in (None, 4) and pair[1]["fq_n"] != 4:
            self.bad(name, "pre-!link_up fq_n",
                     "fq_n=4", self._fmt(pair[1]), "u_u.fq_n")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "!link_up clears fq_n / pcs_vld",
                                  link_up=0)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[1]["dll_pcs_vld"] != 0:
            self.bad(name, "!link_up dll_pcs_vld",
                     "dll_pcs_vld=0", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return
        if pair[1]["fq_n"] not in (None, 0) and pair[1]["fq_n"] != 0:
            self.bad(name, "!link_up fq_n",
                     "fq_n=0", self._fmt(pair[1]), "u_u.fq_n")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "re-up after !link_up", link_up=1)
        if pair is None:
            phase.drop_objection(self)
            return

        # 9. Async rst_n mid-stream (no posedge) clears registered state.
        pair = await self._expect(name, "accept before async rst",
                                  nw_dll_data=b1, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score_combo(name, "async rst_n=0 mid-fq (100ps, no posedge)",
                                 got, self.g.combo()):
            phase.drop_objection(self)
            return
        if not self._score_state(name, "async rst_n=0 mid-fq", got):
            phase.drop_objection(self)
            return
        if got["dll_pcs_vld"] != 0 or got["wr_en"] != 0:
            self.bad(name, "async rst_n mid-stream",
                     "pcs_vld=0 wr_en=0", self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score_combo(name, "after async re-reset release, idle",
                                 got, self.g.combo()):
            phase.drop_objection(self)
            return

        # 10. dll_pcs_ready=0 holds a data beat (no silent drop).
        pair = await self._expect(name, "1-flit accept before pcs stall",
                                  nw_dll_data=b1, nw_dll_vld=1)
        if pair is None:
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "emit with pcs_ready=0 (hold slot)",
                                  dll_pcs_ready=0)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[1]["dll_pcs_vld"] != 1:
            self.bad(name, "held pcs_vld while ready=0",
                     "dll_pcs_vld=1", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return
        held = pair[1]["dll_pcs_data"]
        pair = await self._expect(name, "still held (pcs_ready=0)",
                                  dll_pcs_ready=0)
        if pair is None:
            phase.drop_objection(self)
            return
        if pair[1]["dll_pcs_vld"] != 1:
            self.bad(name, "pcs_vld stays while ready=0",
                     "dll_pcs_vld=1", self._fmt(pair[1]), HIER)
            phase.drop_objection(self)
            return
        if (held is not None and held >= 0
                and pair[1]["dll_pcs_data"] is not None
                and pair[1]["dll_pcs_data"] >= 0
                and (int(pair[1]["dll_pcs_data"]) & MASK640)
                != (int(held) & MASK640)):
            self.bad(name, "held pcs data must not change",
                     hex(held), self._fmt(pair[1]), "u_u.dll_pcs_data")
            phase.drop_objection(self)
            return
        pair = await self._expect(name, "pcs_ready=1 releases held beat")
        if pair is None:
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_tx)
