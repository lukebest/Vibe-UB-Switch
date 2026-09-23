"""Module-level uvm-python TC for Decision-I leaf vibe_dll_rx.

Covers reset / port_rst / !link_up clears; CFG0 terminate (no fabric);
PCS→NW packing / LPH / EOP leftover drop; FEC fail → start_retry;
rx_ovf on buffer full (wrapper RXBUF=32); ready/valid handshake.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff. Not TP-DLL-004 / full vibe_dll.

Matches product rtl/dll/vibe_dll_rx.sv: async-low rst_n, LPH at
pcs_dll_data[639:480], CFG0 (cfg==0) does not pack, occupancy
wptr-rptr >= RXBUF sets rx_ovf, 640b hold then OR-pack into by_lj,
emit 512b when declared bytes are ready, EOP drops intra-group
leftover, !link_up leftover → pad0/ERROR_FLAG, start_retry =
fec_fail || bcrc_fail, start_ack tied 0. Instantiated by vibe_dll
u_rx. Stock Icarus tc_cfg0_term_not_fabric / tc_dll_rx_errflag /
tc_fec_fail_gbn remain the official TP scorers. Header-only vs
stock; no invented protocol.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# Wrapper RXBUF=32 (stock unit TCs). Product default is 1024.
RXBUF = 32
MASK8 = 0xFF
MASK11 = 0x7FF
MASK16 = 0xFFFF
MASK160 = (1 << 160) - 1
MASK480 = (1 << 480) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
MASK1280 = (1 << 1280) - 1
HIER = "u_u.have / u_u.by_n / u_u.pkt_act / u_u.wptr"

# Distinctive 480b payload so a slice/shift swap fails (stock overlay B).
PAT480 = int("A5" * 60, 16) & MASK480


def pkt_bytes(flit: int) -> int:
    """Product vibe_pkt_bytes: decl_flits(PLENGTH) * 20."""
    return lph.decl_flits(lph.lph_plength(int(flit) & MASK160)) * 20


def pcs_lph(beat: int) -> int:
    return (int(beat) >> 480) & MASK160


def mk_pcs(cfg=3, vl=0, nflit=1, payload=None) -> int:
    """Stock vibe_tb_mk_pcs_beat / vibe_tb_mk_flit (lph helpers)."""
    if payload is None:
        payload = PAT480
    return lph.mk_pcs_beat(
        lph.mk_flit(cfg, 0, vl, 1, 2, lph.plen_nflit(nflit)),
        int(payload) & MASK480,
    )


def abort_word(by_lj: int) -> int:
    """Product !link_up leftover: {by_lj[1279:800], 1'b0, 1'b1, 30'd0}."""
    hi = (int(by_lj) >> 800) & MASK480
    return ((hi << 32) | (1 << 30)) & MASK512


def emit_word(by_lj: int, emit_n: int) -> int:
    """Product: by_lj[1279:768] & ({512{1}} << (512 - emit_n*8))."""
    top = (int(by_lj) >> 768) & MASK512
    keep = (int(emit_n) & MASK8) * 8
    if keep <= 0:
        return 0
    if keep >= 512:
        return top
    mask = (MASK512 << (512 - keep)) & MASK512
    return top & mask


def pack_or(by_lj: int, hold: int, by_n: int) -> int:
    """Product: by_lj | ({hold, 640'b0} >> (by_n * 8))."""
    shifted = ((int(hold) & MASK640) << 640) >> ((int(by_n) & MASK8) * 8)
    return (int(by_lj) | shifted) & MASK1280


class Golden:
    """Cycle-accurate vs product NBA (port_rst / !link_up win)."""

    def __init__(self, rxbuf=RXBUF):
        self.rxbuf = int(rxbuf) & MASK11
        self.reset()

    def reset(self):
        self.have = 0
        self.hold = 0
        self.nw_data = 0
        self.nw_vld = 0
        self.cfg0_hit = 0
        self.cfg0_data = 0
        self.bcrc_fail = 0
        self.rx_ovf = 0
        self.by_lj = 0
        self.by_n = 0
        self.pkt_act = 0
        self.pkt_left = 0
        self.wptr = [0] * 16
        self.rptr = [0] * 16

    def is_cfg0(self, pcs_data):
        return lph.lph_cfg(pcs_lph(pcs_data)) == 0

    def ready(self, link_up, pcs_data):
        if not link_up:
            return 1
        idle = (not self.have) and (self.by_n == 0) and (not self.pkt_act)
        return int(self.is_cfg0(pcs_data) or idle)

    def start_retry(self, fec_fail):
        return int(bool(fec_fail) or bool(self.bcrc_fail))

    def _hdr_bytes(self):
        return pkt_bytes((self.by_lj >> 1120) & MASK160) & MASK16

    def _need_hdr(self):
        return (not self.pkt_act) and (self.by_n >= 20)

    def _left_now(self):
        return self._hdr_bytes() if self._need_hdr() else (self.pkt_left & MASK16)

    def _emit_n(self):
        have_pkt = self.pkt_act or self._need_hdr()
        left = self._left_now()
        if have_pkt and left >= 64 and self.by_n >= 64:
            return 64
        if have_pkt and 0 < left <= 64 and self.by_n >= (left & MASK8):
            return left & MASK8
        return 0

    def _can_emit(self, nw_ready):
        en = self._emit_n()
        return en != 0 and ((not self.nw_vld) or bool(nw_ready))

    def combo(self, link_up=1, fec_fail=0, pcs_data=0):
        return (
            self.ready(link_up, pcs_data),
            self.nw_data & MASK512,
            int(self.nw_vld),
            int(self.cfg0_hit),
            self.cfg0_data & MASK640,
            int(self.bcrc_fail),
            self.start_retry(fec_fail),
            int(self.rx_ovf),
            0,
            int(self.have),
            int(self.by_n) & MASK8,
            int(self.pkt_act),
        )

    def step(self, port_rst=0, link_up=1, fec_fail=0,
             pcs_data=0, pcs_vld=0, nw_ready=1):
        if port_rst or not link_up:
            abort = (not link_up) and (self.have or self.by_n != 0)
            self.have = 0
            self.nw_vld = 0
            self.cfg0_hit = 0
            self.pkt_act = 0
            if abort:
                self.nw_data = abort_word(self.by_lj)
                self.nw_vld = 1
            self.by_lj = 0
            self.by_n = 0
            self.pkt_left = 0
            return

        ready = self.ready(link_up, pcs_data)
        is_cfg0 = self.is_cfg0(pcs_data)
        vl = lph.lph_vl(pcs_lph(pcs_data)) & 0xF
        need_hdr = self._need_hdr()
        left_now = self._left_now()
        emit_n = self._emit_n()
        can_emit = self._can_emit(nw_ready)
        have_old = self.have
        by_n_old = self.by_n
        hold_old = self.hold
        by_lj_old = self.by_lj

        self.cfg0_hit = 0
        self.bcrc_fail = 0
        if self.nw_vld and nw_ready:
            self.nw_vld = 0

        if pcs_vld and ready:
            if is_cfg0:
                self.cfg0_hit = 1
                self.cfg0_data = int(pcs_data) & MASK640
            elif ((self.wptr[vl] - self.rptr[vl]) & MASK11) >= self.rxbuf:
                self.rx_ovf = 1
            else:
                self.hold = int(pcs_data) & MASK640
                self.have = 1
                self.wptr[vl] = (self.wptr[vl] + 4) & MASK11

        if have_old and (by_n_old <= 80):
            self.by_lj = pack_or(by_lj_old, hold_old, by_n_old)
            self.by_n = (by_n_old + 80) & MASK8
            self.have = 0
        elif can_emit:
            self.nw_data = emit_word(by_lj_old, emit_n)
            self.nw_vld = 1
            if left_now <= emit_n:
                self.pkt_act = 0
                self.pkt_left = 0
                self.by_lj = 0
                self.by_n = 0
            else:
                self.by_lj = (by_lj_old << (emit_n * 8)) & MASK1280
                self.by_n = (by_n_old - emit_n) & MASK8
                self.pkt_act = 1
                self.pkt_left = (left_now - emit_n) & MASK16
        elif need_hdr:
            self.pkt_act = 1
            self.pkt_left = left_now & MASK16

        if fec_fail:
            self.bcrc_fail = 0


class tc_vibe_dll_rx(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=1, nw_ready=1):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.fec_fail, 0)
        sset(d.pcs_dll_data, 0)
        sset(d.pcs_dll_vld, 0)
        sset(d.dll_nw_ready, 1 if nw_ready else 0)

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

    def _inner(self, path, default=-1):
        try:
            return ival(hier(self.dut, path), default)
        except Exception:
            return default

    def _sample(self):
        d = self.dut
        return (
            ival(d.pcs_dll_ready, -1),
            ival(d.dll_nw_data, -1) & MASK512,
            ival(d.dll_nw_vld, -1),
            ival(d.cfg0_hit, -1),
            ival(d.cfg0_data, -1) & MASK640,
            ival(d.bcrc_fail, -1),
            ival(d.start_retry, -1),
            ival(d.rx_ovf, -1),
            ival(d.start_ack, -1),
            self._inner("u_u.have", -1),
            self._inner("u_u.by_n", -1),
            self._inner("u_u.pkt_act", -1),
        )

    def _fmt(self, s):
        ready, nw, vld, hit, c0, bf, retry, ovf, ack, have, by_n, pact = s
        return (
            f"rdy={ready} nw_vld={vld} cfg0={hit} bcrc={bf} retry={retry} "
            f"ovf={ovf} ack={ack} have={have} by_n={by_n} pkt_act={pact} "
            f"nw=0x{nw:x} c0=0x{c0:x}"
        )

    async def _cycle(self, port_rst=0, link_up=1, fec_fail=0,
                     pcs_data=0, pcs_vld=0, nw_ready=1):
        """Drive on this falling edge; sample NBA-stable outs on the next fall."""
        d = self.dut
        sset(d.port_rst, 1 if port_rst else 0)
        sset(d.link_up, 1 if link_up else 0)
        sset(d.fec_fail, 1 if fec_fail else 0)
        sset(d.pcs_dll_data, int(pcs_data) & MASK640)
        sset(d.pcs_dll_vld, 1 if pcs_vld else 0)
        sset(d.dll_nw_ready, 1 if nw_ready else 0)
        self.g.step(
            port_rst=port_rst, link_up=link_up, fec_fail=fec_fail,
            pcs_data=pcs_data, pcs_vld=pcs_vld, nw_ready=nw_ready,
        )
        await self._to_fall()
        return self._sample()

    def _score(self, name, stim, got, link_up=1, fec_fail=0, pcs_data=0):
        exp = self.g.combo(link_up=link_up, fec_fail=fec_fail, pcs_data=pcs_data)
        if got != exp:
            self.bad(name, stim, self._fmt(exp), self._fmt(got), HIER)
            return False
        if got[8] != 0:
            self.bad(name, stim + " (start_ack tied 0)",
                     "start_ack=0", self._fmt(got), "u_u.start_ack")
            return False
        return True

    async def _expect(self, name, stim, **kw):
        got = await self._cycle(**kw)
        if not self._score(name, stim, got,
                           link_up=kw.get("link_up", 1),
                           fec_fail=kw.get("fec_fail", 0),
                           pcs_data=kw.get("pcs_data", 0)):
            return None
        return got

    async def _drain_eop(self, name, tag, nflit, vl=0, payload=None,
                         nw_ready=1):
        """Accept one CFG3 beat and walk until EOP leftover drop (or 12 cyc)."""
        beat = mk_pcs(3, vl, nflit, payload)
        got = await self._expect(
            name, f"{tag} accept CFG3 {nflit}-flit",
            pcs_data=beat, pcs_vld=1, nw_ready=nw_ready)
        if got is None:
            return None
        for i in range(12):
            got = await self._expect(
                name, f"{tag} walk[{i}]",
                nw_ready=nw_ready)
            if got is None:
                return None
            if got[9] == 0 and got[10] == 0 and got[11] == 0:
                return got
        self.bad(name, f"{tag} EOP leftover drop",
                 "have=0 by_n=0 pkt_act=0", self._fmt(got), HIER)
        return None

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_dll_rx"
        self.g = Golden()

        b1 = mk_pcs(3, 0, 1)
        b5 = mk_pcs(3, 0, 5)
        c0 = mk_pcs(0, 0, 1)
        if pkt_bytes(pcs_lph(b1)) != 20 or pkt_bytes(pcs_lph(b5)) != 100:
            self.bad(name, "golden vibe_pkt_bytes (1 vs 5 flit)",
                     "20 and 100",
                     f"{pkt_bytes(pcs_lph(b1))} {pkt_bytes(pcs_lph(b5))}",
                     "golden")
            phase.drop_objection(self)
            return
        if lph.lph_cfg(pcs_lph(c0)) != 0 or lph.lph_cfg(pcs_lph(b1)) == 0:
            self.bad(name, "golden CFG0 vs CFG3 LPH",
                     "cfg0=0 cfg3!=0",
                     f"{lph.lph_cfg(pcs_lph(c0))} {lph.lph_cfg(pcs_lph(b1))}",
                     "golden")
            phase.drop_objection(self)
            return
        if abort_word(0) != (1 << 30):
            self.bad(name, "golden ERROR_FLAG abort (empty by_lj)",
                     f"bit30 set ({1 << 30:#x})",
                     f"{abort_word(0):#x}",
                     "golden")
            phase.drop_objection(self)
            return
        idle_g = Golden()
        if idle_g.ready(1, b1) != 1 or idle_g.ready(1, c0) != 1:
            self.bad(name, "golden idle ready",
                     "ready=1 for CFG3 and CFG0",
                     f"{idle_g.ready(1, b1)} {idle_g.ready(1, c0)}",
                     "golden")
            phase.drop_objection(self)
            return
        idle_g.have = 1
        if idle_g.ready(1, b1) != 0 or idle_g.ready(1, c0) != 1:
            self.bad(name, "golden CFG0 ready while have=1",
                     "CFG3 ready=0; CFG0 ready=1",
                     f"{idle_g.ready(1, b1)} {idle_g.ready(1, c0)}",
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, ready, no vld / cfg0 / retry / ovf / ack.
        got = self._sample()
        if not self._score(name, "reset then release, pcs_vld=0", got):
            phase.drop_objection(self)
            return
        if (got[0] != 1 or got[2] or got[3] or got[6] or got[7] or got[8]
                or got[9] or got[10] or got[11]):
            self.bad(name, "reset idle ports",
                     "rdy=1 nw_vld=0 cfg0=0 retry=0 ovf=0 ack=0 have=0 by_n=0",
                     self._fmt(got), HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            got = await self._expect(
                name, f"idle cycle {i} after reset (pcs_vld=0 junk data)",
                pcs_data=b1, pcs_vld=0)
            if got is None:
                phase.drop_objection(self)
                return

        # Async rst_n mid-packet (no posedge) clears registered state.
        got = await self._expect(name, "accept CFG3 1-flit before async rst",
                                 pcs_data=b1, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[9] != 1:
            self.bad(name, "have after accept (before async rst)",
                     "have=1", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if not self._score(name, "async rst_n=0 mid-have (100ps, no posedge)",
                           got):
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[2] != 0 or got[7] != 0:
            self.bad(name, "async rst_n mid-have",
                     "have=0 nw_vld=0 rx_ovf=0", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        got = self._sample()
        if not self._score(name, "after async re-reset release, idle", got):
            phase.drop_objection(self)
            return

        # 2. CFG0 terminate: hit + capture, never dll_nw_vld (stock).
        got = await self._expect(name, "CFG=0 beat (terminate in DLL)",
                                 pcs_data=c0, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != 1 or got[4] != (c0 & MASK640) or got[2] != 0:
            self.bad(name, "CFG0 terminate",
                     "cfg0_hit=1 cfg0_data=beat dll_nw_vld=0",
                     self._fmt(got), "u_u.cfg0_hit")
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[0] != 1:
            self.bad(name, "CFG0 does not set have / ready stays 1",
                     "have=0 rdy=1", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "cycle after CFG0 (hit pulsed)",
                                 pcs_data=c0, pcs_vld=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != 0 or got[2] != 0:
            self.bad(name, "CFG0 hit is a pulse; still no fabric",
                     "cfg0_hit=0 dll_nw_vld=0", self._fmt(got), "u_u.cfg0_hit")
            phase.drop_objection(self)
            return

        # 3. CFG3 1-flit: accept → pack → emit LPH + EOP leftover drop.
        got = await self._expect(name, "accept CFG3 1-flit (have=1)",
                                 pcs_data=b1, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[9] != 1 or got[0] != 0:
            self.bad(name, "PCS accept sets have, ready drops",
                     "have=1 rdy=0", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "pack 640b into by_lj (have→0 by_n=80)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[10] != 80:
            self.bad(name, "pack cycle",
                     "have=0 by_n=80", self._fmt(got), "u_u.by_n")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "emit 20B NW + EOP leftover drop")
        if got is None:
            phase.drop_objection(self)
            return
        exp_nw = emit_word(pack_or(0, b1, 0), 20)
        if got[2] != 1 or got[1] != exp_nw:
            self.bad(name, "1-flit NW beat (LPH + masked leftover)",
                     f"dll_nw_vld=1 nw=0x{exp_nw:x}",
                     self._fmt(got), "u_u.dll_nw_data")
            phase.drop_objection(self)
            return
        if (got[1] >> 352) & MASK160 != pcs_lph(b1):
            self.bad(name, "LPH is first 160b of NW beat",
                     f"nw[511:352]=0x{pcs_lph(b1):x}",
                     f"0x{(got[1] >> 352) & MASK160:x}",
                     "u_u.dll_nw_data")
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[10] != 0 or got[11] != 0:
            self.bad(name, "EOP leftover drop (Null pad + BCRC tail)",
                     "have=0 by_n=0 pkt_act=0", self._fmt(got), "u_u.by_n")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "handshake consume NW (ready=1)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 0 or got[0] != 1:
            self.bad(name, "after EOP, ready returns and vld drops",
                     "rdy=1 nw_vld=0", self._fmt(got), "u_u.dll_nw_vld")
            phase.drop_objection(self)
            return

        # 4. ready/valid: dll_nw_ready=0 sticks vld; second accept after EOP.
        got = await self._expect(name, "accept 1-flit with nw_ready=0",
                                 pcs_data=b1, pcs_vld=1, nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "pack with nw_ready=0", nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "emit with nw_ready=0 (vld sticks)",
                                 nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 1:
            self.bad(name, "emit while !dll_nw_ready",
                     "dll_nw_vld=1", self._fmt(got), "u_u.dll_nw_vld")
            phase.drop_objection(self)
            return
        held_nw = got[1]
        for i in range(3):
            got = await self._expect(
                name, f"stall NW handshake [{i}]", nw_ready=0)
            if got is None:
                phase.drop_objection(self)
                return
            if got[2] != 1 or got[1] != held_nw:
                self.bad(name, f"vld holds while !dll_nw_ready [{i}]",
                         f"nw_vld=1 nw=0x{held_nw:x}",
                         self._fmt(got), "u_u.dll_nw_vld")
                phase.drop_objection(self)
                return
        got = await self._expect(name, "release dll_nw_ready after stall",
                                 nw_ready=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 0:
            self.bad(name, "handshake consume after stall",
                     "dll_nw_vld=0", self._fmt(got), "u_u.dll_nw_vld")
            phase.drop_objection(self)
            return

        # 4-flit: emit 64B then 16B leftover (stock leftover / EOP).
        got = await self._drain_eop(name, "4-flit", 4)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "idle after 4-flit EOP")
        if got is None:
            phase.drop_objection(self)
            return

        # 5-flit on one 640b beat: emit 64, leftover 16 < remaining 36.
        b5 = mk_pcs(3, 0, 5)
        got = await self._expect(name, "accept CFG3 5-flit (leftover path)",
                                 pcs_data=b5, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "pack 5-flit")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "emit 64B of 100B declared")
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 1 or got[11] != 1:
            self.bad(name, "5-flit first emit",
                     "nw_vld=1 pkt_act=1", self._fmt(got), "u_u.pkt_act")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "5-flit leftover (by_n < left, no emit)")
        if got is None:
            phase.drop_objection(self)
            return
        if got[10] == 0 or got[11] != 1 or got[0] != 0:
            self.bad(name, "5-flit leftover sticks pkt_act (stock :118 else)",
                     "by_n!=0 pkt_act=1 rdy=0", self._fmt(got), "u_u.pkt_act")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "port_rst clears leftover / pkt_act",
                                 port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[10] != 0 or got[11] != 0 or got[3] != 0:
            self.bad(name, "port_rst clear (have / by_n / pkt / cfg0)",
                     "have=0 by_n=0 pkt_act=0 cfg0=0",
                     self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "after port_rst, idle ready")
        if got is None:
            phase.drop_objection(self)
            return

        # 5. FEC fail → start_retry combo (stock tc_fec_fail_gbn).
        await self._idle()
        sset(d.fec_fail, 1)
        await Timer(1, "NS")
        if ival(d.start_retry, 0) != 1 or ival(d.start_ack, 1) != 0:
            self.bad(name, "fec_fail=1 (combo, no posedge)",
                     "start_retry=1 start_ack=0",
                     f"retry={ival(d.start_retry, -1)} ack={ival(d.start_ack, -1)}",
                     "u_u.start_retry")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "fec_fail held through posedge",
                                 fec_fail=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[6] != 1 or got[5] != 0:
            self.bad(name, "start_retry = fec_fail || bcrc_fail",
                     "retry=1 bcrc_fail=0", self._fmt(got), "u_u.start_retry")
            phase.drop_objection(self)
            return
        sset(d.fec_fail, 0)
        await Timer(1, "NS")
        if ival(d.start_retry, 1) != 0:
            self.bad(name, "fec_fail deassert (combo)",
                     "start_retry=0", f"{ival(d.start_retry, -1)}",
                     "u_u.start_retry")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "fec_fail=0 after deassert")
        if got is None:
            phase.drop_objection(self)
            return

        # 6. !link_up while have → pad0 / ERROR_FLAG (stock tc_dll_rx_errflag).
        got = await self._expect(name, "accept CFG3 so have=1 before !link_up",
                                 pcs_data=b1, pcs_vld=1, nw_ready=0)
        if got is None or got[9] != 1:
            if got is not None:
                self.bad(name, "have before !link_up",
                         "have=1", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        got = await self._expect(
            name, "drop link_up on fall after have (stock errflag)",
            link_up=0, nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 1 or (got[1] & (1 << 30)) == 0:
            self.bad(name, "!link_up && have → dll_nw_vld + ERROR_FLAG",
                     "nw_vld=1 bit30=1", self._fmt(got), "u_u.dll_nw_data")
            phase.drop_objection(self)
            return
        if got[9] != 0 or got[10] != 0:
            self.bad(name, "!link_up clears have / by_n",
                     "have=0 by_n=0", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "link_up=1 after errflag (port_rst)",
                                 port_rst=1, link_up=1, nw_ready=1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "idle after errflag port_rst")
        if got is None:
            phase.drop_objection(self)
            return

        # port_rst with leftover does not emit ERROR_FLAG (only !link_up).
        got = await self._expect(name, "accept before port_rst (no abort)",
                                 pcs_data=b1, pcs_vld=1, nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "port_rst while have (no ERROR_FLAG)",
                                 port_rst=1, nw_ready=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 0 or got[9] != 0:
            self.bad(name, "port_rst clears without abort beat",
                     "nw_vld=0 have=0", self._fmt(got), "u_u.dll_nw_vld")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "idle after port_rst no-abort")
        if got is None:
            phase.drop_objection(self)
            return

        # 7. VL from LPH: one vl=1 accept increments wptr[1] only.
        b_vl1 = mk_pcs(3, 1, 1)
        got = await self._drain_eop(name, "vl=1", 1, vl=1)
        if got is None:
            phase.drop_objection(self)
            return
        w1 = self._inner("u_u.wptr[1]", None)
        w0 = self._inner("u_u.wptr[0]", None)
        if w1 is not None and w1 != 4:
            self.bad(name, "wptr[vl=1] += 4",
                     "wptr[1]=4", f"wptr[1]={w1} wptr[0]={w0}",
                     "u_u.wptr")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "consume NW after vl=1")
        if got is None:
            phase.drop_objection(self)
            return

        # 8. rx_ovf: RXBUF=32, +4 wptr/accept, rptr never pops (stock).
        for k in range(8):
            got = await self._drain_eop(name, f"ovf-fill[{k}]", 1)
            if got is None:
                phase.drop_objection(self)
                return
            got = await self._expect(name, f"consume after ovf-fill[{k}]")
            if got is None:
                phase.drop_objection(self)
                return
        w0 = self._inner("u_u.wptr[0]", None)
        if w0 is not None and w0 < 32:
            self.bad(name, "wptr[0] after 8 accepts",
                     "wptr[0]>=32", f"{w0}", "u_u.wptr")
            phase.drop_objection(self)
            return
        got = await self._expect(name, "9th CFG3 accept → rx_ovf (RXBUF=32)",
                                 pcs_data=b1, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[7] != 1:
            self.bad(name, "wptr-rptr >= RXBUF",
                     "rx_ovf=1", self._fmt(got), "u_u.rx_ovf")
            phase.drop_objection(self)
            return
        if got[9] != 0:
            self.bad(name, "ovf beat is dropped (no have)",
                     "have=0", self._fmt(got), "u_u.have")
            phase.drop_objection(self)
            return
        # CFG0 still terminates after ovf (does not use occupancy).
        got = await self._expect(name, "CFG0 after ovf still hits",
                                 pcs_data=c0, pcs_vld=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[3] != 1 or got[7] != 1:
            self.bad(name, "CFG0 after ovf",
                     "cfg0_hit=1 rx_ovf stays 1",
                     self._fmt(got), "u_u.cfg0_hit")
            phase.drop_objection(self)
            return
        # port_rst does not clear rx_ovf / wptr (stock).
        got = await self._expect(name, "port_rst after ovf (flag sticky)",
                                 port_rst=1)
        if got is None:
            phase.drop_objection(self)
            return
        if got[7] != 1:
            self.bad(name, "port_rst after ovf",
                     "rx_ovf stays 1", self._fmt(got), "u_u.rx_ovf")
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await self._idle()
        await Timer(100, "PS")
        self.g.reset()
        got = self._sample()
        if got[7] != 0:
            self.bad(name, "async rst_n clears rx_ovf",
                     "rx_ovf=0", self._fmt(got), "u_u.rx_ovf")
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)

        # 9. Second packet after first EOP (no leftover prefix).
        got = await self._drain_eop(name, "second-pkt-a", 1)
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._expect(name, "consume after second-pkt-a")
        if got is None:
            phase.drop_objection(self)
            return
        got = await self._drain_eop(name, "second-pkt-b", 1)
        if got is None:
            phase.drop_objection(self)
            return
        if (got[1] >> 352) & MASK160 != pcs_lph(b1):
            self.bad(name, "second SOP LPH (no leftover prefix)",
                     f"nw[511:352]=0x{pcs_lph(b1):x}",
                     f"0x{(got[1] >> 352) & MASK160:x}",
                     "u_u.dll_nw_data")
            phase.drop_objection(self)
            return

        # !link_up from idle: no abort beat.
        got = await self._expect(name, "link_up=0 from idle (no leftover)",
                                 link_up=0)
        if got is None:
            phase.drop_objection(self)
            return
        if got[2] != 0 or got[9] != 0:
            self.bad(name, "!link_up idle (no ERROR_FLAG)",
                     "nw_vld=0 have=0", self._fmt(got), "u_u.dll_nw_vld")
            phase.drop_objection(self)
            return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_dll_rx)
