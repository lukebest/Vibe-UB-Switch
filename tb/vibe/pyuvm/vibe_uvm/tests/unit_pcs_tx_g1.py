"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_g1.

Covers reset/idle (win_vld=0, no spurious 960, in_ready=link_up when
empty), 6-Null idle fill, isolated 4-flit beat + 2-Null complete,
1.5-beat rem-complete (second 640 while nflit==4) plus rem leftover
+ 4-Null fill, win_ready backpressure without drop/dup, in_vld stall
at nflit==4, link_up=0 (no take / no idle fill), rem-fill wait while
in_vld stays 1, same-cycle ack+take, and a second window after drain.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or
signoff.

Matches product rtl/pcs/vibe_pcs_tx_g1.sv: async-low rst_n, combo
in_ready = link_up && (!have || win_ready) && !((nflit>=4)&&rem_vld),
win_data=acc, win_vld=have, NULL_FLIT=160'd0. NBA last-wins: ack
have/nflit, then take fresh 4 or mid 4+2, else rem leftover, else
2-Null complete, else idle 6-Null. Used by vibe_pcs_tx u_g1. Stock
Icarus tc_pcs_tx_g1_window remains the official win_vld scorer.
"""

from uvm import uvm_component_utils
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
MASK320 = (1 << 320) - 1
MASK640 = (1 << 640) - 1
MASK960 = (1 << 960) - 1
HIER = "u_u.nflit / u_u.have / u_u.rem_vld"


def _word640(v: int) -> int:
    return int(v) & MASK640


def _word960(v: int) -> int:
    return int(v) & MASK960


def _hex640(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0160x}"


def _hex960(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0240x}"


def beat_pat(hi_tag: int, lo_tag=None) -> int:
    """640b beat: distinctive high/low 320b halves (4×160 flits)."""
    if lo_tag is None:
        lo_tag = hi_tag ^ 0x5A

    def half(tag: int) -> int:
        parts = [f"{(tag & 0xFF):02X}{(i & 0xFF):02X}" for i in range(20)]
        return int("".join(parts), 16) & MASK320

    return ((half(hi_tag) << 320) | half(lo_tag)) & MASK640


def win_4plus2(beat: int) -> int:
    """Isolated 4-flit beat completed with 2 Nulls."""
    return (_word640(beat) << 320) & MASK960


def win_rem_complete(first: int, second: int) -> int:
    """1.5-beat window: first 640 + high 320 of second."""
    return ((_word640(first) << 320) | ((_word640(second) >> 320) & MASK320)) & MASK960


def win_rem_leftover(second: int) -> int:
    """Rem leftover 2 flits + 4 Nulls."""
    return ((_word640(second) & MASK320) << 640) & MASK960


# Stock Icarus tc_pcs_tx_g1_window uses 640'hA / 640'hB / 640'hC / 640'hD.
STOCK_A = 0xA
STOCK_B = 0xB
STOCK_C = 0xC
STOCK_D = 0xD
BEAT_A = beat_pat(0xA0, 0xA1)
BEAT_B = beat_pat(0xB0, 0xB1)
BEAT_C = beat_pat(0xC0, 0xC1)
BEAT_D = beat_pat(0xD0, 0xD1)


class Golden:
    """Cycle-accurate collect / rem leftover / Null fill vs product NBA."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.rem = 0
        self.rem_vld = 0
        self.nflit = 0
        self.acc = 0
        self.have = 0

    def combo(self, link_up, win_ready):
        blocked = (self.nflit >= 4) and bool(self.rem_vld)
        in_ready = bool(link_up) and ((not self.have) or bool(win_ready)) and (
            not blocked)
        return int(in_ready), int(self.have), int(self.acc) & MASK960

    def step(self, link_up, in_data, in_vld, win_ready):
        in_ready, _, _ = self.combo(link_up, win_ready)
        have = self.have
        rem_vld = self.rem_vld
        nflit = self.nflit
        acc = self.acc
        rem = self.rem
        din = _word640(in_data)

        if have and win_ready:
            self.have = 0
            self.nflit = 0

        if in_vld and in_ready:
            if not rem_vld:
                if nflit == 0 or (have and win_ready):
                    self.acc = ((din << 320) | (acc & MASK320)) & MASK960
                    self.rem = 0
                    self.rem_vld = 0
                    self.nflit = 4
                elif nflit == 4:
                    self.acc = ((acc & ~MASK320) | ((din >> 320) & MASK320)) & MASK960
                    self.rem = din & MASK320
                    self.rem_vld = 1
                    self.nflit = 6
                    self.have = 1
        elif rem_vld and not have:
            self.acc = (rem & MASK320) << 640
            self.rem_vld = 0
            self.nflit = 6
            self.have = 1
        elif (not have) and (not in_vld) and link_up and win_ready and nflit == 4:
            self.acc = acc & ~MASK320
            self.nflit = 6
            self.have = 1
        elif (not have) and (not in_vld) and link_up and win_ready and (
                nflit == 0) and (not rem_vld):
            self.acc = 0
            self.nflit = 6
            self.have = 1


class tc_vibe_pcs_tx_g1(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self, link_up=1, win_ready=0):
        d = self.dut
        sset(d.link_up, 1 if link_up else 0)
        sset(d.in_vld, 0)
        sset(d.in_data, 0)
        sset(d.win_ready, 1 if win_ready else 0)

    async def _hold_reset(self, n=4, link_up=1, win_ready=0):
        sset(self.dut.rst_n, 0)
        await self._idle(link_up=link_up, win_ready=win_ready)
        await self.cycles(n)
        self.g.reset()

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    def _sample(self):
        d = self.dut
        return (
            ival(d.in_ready, -1),
            ival(d.win_vld, -1),
            ival(d.win_data, -1),
        )

    def _score_now(self, name, stim, link_up, win_ready, ir, wv, wd):
        exp_ir, exp_wv, exp_wd = self.g.combo(link_up, win_ready)
        if ir != exp_ir:
            self.bad(name, stim,
                     f"in_ready={exp_ir}",
                     f"in_ready={ir}",
                     "u_u.in_ready")
            return False
        if wv != exp_wv:
            self.bad(name, stim,
                     f"win_vld={exp_wv}",
                     f"win_vld={wv}",
                     "u_u.have")
            return False
        if wv == 1:
            if wd is None:
                self.bad(name, stim + " (win_data unresolved)",
                         "win_data resolved",
                         "x",
                         "u_u.acc")
                return False
            if _word960(wd) != exp_wd:
                self.bad(name, stim + " (6-flit / Null fill)",
                         _hex960(exp_wd),
                         _hex960(wd),
                         "u_u.acc")
                return False
        return True

    async def _apply(self, name, stim, in_vld, in_data,
                     link_up=1, win_ready=1):
        """Drive on falling edge; score combo then NBA after the posedge.

        Returns (taken_or_None, emit_or_None).
        """
        d = self.dut
        sset(d.link_up, 1 if link_up else 0)
        sset(d.win_ready, 1 if win_ready else 0)
        sset(d.in_vld, 1 if in_vld else 0)
        sset(d.in_data, _word640(in_data))
        await Timer(100, "PS")
        ir, wv, wd = self._sample()
        if not self._score_now(name, stim + " (pre-posedge)",
                               link_up, win_ready, ir, wv, wd):
            return None, None
        taken = _word640(in_data) if (in_vld and ir == 1) else None
        emit = _word960(wd) if (wv == 1 and win_ready) else None
        self.g.step(1 if link_up else 0, in_data, 1 if in_vld else 0,
                    1 if win_ready else 0)
        await RisingEdge(d.clk)
        await Timer(100, "PS")
        ir2, wv2, wd2 = self._sample()
        if not self._score_now(name, stim + " (post-NBA)",
                               link_up, win_ready, ir2, wv2, wd2):
            return None, None
        await FallingEdge(d.clk)
        return taken, emit

    async def _take_beat(self, name, label, beat, win_ready=1, link_up=1):
        for spin in range(16):
            ir = ival(self.dut.in_ready, 0)
            taken, emit = await self._apply(
                name, f"{label} take spin[{spin}]",
                1 if ir else 0, beat if ir else 0,
                link_up=link_up, win_ready=win_ready)
            if taken is not None:
                return taken, emit
            if self.fail_n:
                return None, None
        self.bad(name, f"{label} take beat",
                 "in_ready=1",
                 "in_ready stayed 0",
                 "u_u.in_ready")
        return None, None

    async def _collect_wins(self, name, label, n, outs, timeout=24,
                            win_ready=1, link_up=1):
        for i in range(timeout):
            _, emit = await self._apply(
                name, f"{label} collect[{i}]", 0, 0,
                link_up=link_up, win_ready=win_ready)
            if self.fail_n:
                return False
            if emit is not None:
                outs.append(emit)
                if len(outs) >= n:
                    return True
        self.bad(name, f"{label} collect {n} windows",
                 f"{n} win_vld&&win_ready",
                 f"{len(outs)}",
                 HIER)
        return False

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_g1"
        self.g = Golden()

        exp_stock = win_4plus2(STOCK_A)
        exp_a_null = win_4plus2(BEAT_A)
        exp_ab = win_rem_complete(BEAT_A, BEAT_B)
        exp_b_rem = win_rem_leftover(BEAT_B)
        exp_cd = win_rem_complete(STOCK_C, STOCK_D)
        exp_d_rem = win_rem_leftover(STOCK_D)
        if exp_a_null == 0 or exp_ab == exp_a_null or exp_b_rem == exp_ab:
            self.bad(name, "golden uniqueness (4+2 vs rem vs leftover)",
                     "distinct 960b windows",
                     "collision",
                     "golden")
            phase.drop_objection(self)
            return
        if (exp_a_null >> 320) & MASK640 != BEAT_A:
            self.bad(name, "golden 4+2 high 640 is the beat",
                     _hex640(BEAT_A),
                     _hex640((exp_a_null >> 320) & MASK640),
                     "golden")
            phase.drop_objection(self)
            return
        if (exp_ab & MASK320) != ((BEAT_B >> 320) & MASK320):
            self.bad(name, "golden rem-complete low 320 is second high",
                     _hex640((BEAT_B >> 320) & MASK320),
                     _hex640(exp_ab & MASK320),
                     "golden")
            phase.drop_objection(self)
            return
        if (exp_b_rem >> 640) & MASK320 != (BEAT_B & MASK320):
            self.bad(name, "golden rem leftover high 320 is second low",
                     _hex640(BEAT_B & MASK320),
                     _hex640((exp_b_rem >> 640) & MASK320),
                     "golden")
            phase.drop_objection(self)
            return

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: empty, no spurious window (win_ready=0 blocks idle).
        ir, wv, wd = self._sample()
        if ir != 1 or wv != 0 or wd != 0:
            self.bad(name, "reset then release, in_vld=0 win_ready=0",
                     "in_ready=1 win_vld=0 win_data=0",
                     f"in_ready={ir} win_vld={wv} {_hex960(wd)}",
                     HIER)
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, emit = await self._apply(
                name, f"idle cycle {i} after reset (win_ready=0)",
                0, BEAT_A, win_ready=0)
            if taken is not None or emit is not None or ival(d.win_vld, -1) != 0:
                self.bad(name, f"idle cycle {i} after reset",
                         "no take/emit, win_vld=0",
                         f"taken={taken is not None} emit={emit is not None} "
                         f"win_vld={ival(d.win_vld, -1)}",
                         HIER)
                phase.drop_objection(self)
                return

        # Combo in_ready follows link_up while empty.
        sset(d.link_up, 0)
        await Timer(100, "PS")
        if ival(d.in_ready, -1) != 0:
            self.bad(name, "link_up=0 combo (idle)",
                     "in_ready=0",
                     f"in_ready={ival(d.in_ready, -1)}",
                     "u_u.in_ready")
            phase.drop_objection(self)
            return
        sset(d.link_up, 1)
        await Timer(100, "PS")
        if ival(d.in_ready, -1) != 1:
            self.bad(name, "link_up=1 combo (idle, !have)",
                     "in_ready=1",
                     f"in_ready={ival(d.in_ready, -1)}",
                     "u_u.in_ready")
            phase.drop_objection(self)
            return

        # link_up=0: no idle 6-Null even with win_ready=1.
        for i in range(3):
            taken, emit = await self._apply(
                name, f"link_up=0 no idle fill[{i}]",
                0, 0, link_up=0, win_ready=1)
            if taken is not None or emit is not None or ival(d.win_vld, -1) != 0:
                self.bad(name, f"link_up=0 idle[{i}]",
                         "win_vld=0 (no 6-Null)",
                         f"emit={emit is not None} win_vld={ival(d.win_vld, -1)}",
                         HIER)
                phase.drop_objection(self)
                return

        # 2. Idle 6-Null fill (link_up, win_ready, !in_vld, nflit==0).
        taken, emit = await self._apply(
            name, "idle 6-Null start (NBA 0→1)", 0, 0, win_ready=1)
        if taken is not None or emit is not None:
            self.bad(name, "idle 6-Null start cycle",
                     "no handshake yet",
                     f"taken={taken is not None} emit={emit is not None}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        if ival(d.win_vld, -1) != 1 or ival(d.win_data, -1) != 0:
            self.bad(name, "idle 6-Null window after NBA",
                     "win_vld=1 win_data=0 (6 Null Blocks)",
                     f"win_vld={ival(d.win_vld, -1)} "
                     f"{_hex960(ival(d.win_data, -1))}",
                     "u_u.acc")
            phase.drop_objection(self)
            return
        idle_outs = []
        if not await self._collect_wins(name, "idle 6-Null", 1, idle_outs):
            phase.drop_objection(self)
            return
        if idle_outs != [0]:
            self.bad(name, "idle 6-Null consume",
                     "exactly one all-zero 960",
                     f"n={len(idle_outs)} {_hex960(idle_outs[0]) if idle_outs else 'x'}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Park ready=0 so the next idle fill does not race the 4+2 path.
        taken, emit = await self._apply(
            name, "hold after idle drain (block next 6-Null)",
            0, 0, win_ready=0)
        if emit is not None:
            self.bad(name, "hold after idle drain",
                     "no emit (win_ready=0)",
                     "emit",
                     "u_u.have")
            phase.drop_objection(self)
            return

        # 3. Isolated 4-flit + 2 Nulls (stock 640'hA, then wide BEAT_A).
        taken, emit = await self._take_beat(
            name, "stock A", STOCK_A, win_ready=1)
        if taken != STOCK_A or emit is not None:
            self.bad(name, "stock 640'hA take (nflit 0→4)",
                     "take, no window yet",
                     f"taken={_hex640(taken)} emit={emit is not None}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        stock_outs = []
        if not await self._collect_wins(name, "stock 4+2", 1, stock_outs):
            phase.drop_objection(self)
            return
        if stock_outs != [exp_stock]:
            self.bad(name, "isolated 4-flit + 2 Nulls (stock 640'hA)",
                     _hex960(exp_stock),
                     _hex960(stock_outs[0]) if stock_outs else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        await self._apply(name, "hold after stock 4+2", 0, 0, win_ready=0)

        taken, emit = await self._take_beat(
            name, "wide A", BEAT_A, win_ready=1)
        if taken != BEAT_A:
            self.bad(name, "wide BEAT_A take",
                     _hex640(BEAT_A),
                     _hex640(taken),
                     "u_u.acc")
            phase.drop_objection(self)
            return
        wide_outs = []
        if not await self._collect_wins(name, "wide 4+2", 1, wide_outs):
            phase.drop_objection(self)
            return
        if wide_outs != [exp_a_null]:
            self.bad(name, "isolated 4-flit + 2 Nulls (wide BEAT_A)",
                     _hex960(exp_a_null),
                     _hex960(wide_outs[0]) if wide_outs else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # in_vld stall at nflit==4: hold win_ready=0 so :65 cannot complete.
        await self._apply(name, "hold after wide 4+2", 0, 0, win_ready=0)
        taken, emit = await self._take_beat(
            name, "stall-fill A", BEAT_A, win_ready=0)
        if taken != BEAT_A or emit is not None:
            self.bad(name, "stall-fill take (win_ready=0)",
                     "take, no emit",
                     f"taken={taken is not None} emit={emit is not None}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        if self.g.nflit != 4 or self.g.have:
            self.bad(name, "stall-fill state",
                     "nflit=4 have=0",
                     f"nflit={self.g.nflit} have={self.g.have}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        for k in range(3):
            taken, emit = await self._apply(
                name, f"in_vld=0 stall[{k}] at nflit=4 (win_ready=0)",
                0, BEAT_C, win_ready=0)
            if taken is not None or emit is not None or self.g.nflit != 4:
                self.bad(name, f"stall[{k}] at nflit=4",
                         "nflit stays 4, no emit",
                         f"taken={taken is not None} nflit={self.g.nflit}",
                         "u_u.nflit")
                phase.drop_objection(self)
                return
        stall_outs = []
        if not await self._collect_wins(name, "stall 4+2 resume", 1, stall_outs):
            phase.drop_objection(self)
            return
        if stall_outs != [exp_a_null]:
            self.bad(name, "resume after nflit=4 stall (2-Null complete)",
                     _hex960(exp_a_null),
                     _hex960(stall_outs[0]) if stall_outs else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Async rst_n mid-fill (nflit=4) without a posedge.
        await self._apply(name, "hold after stall 4+2", 0, 0, win_ready=0)
        taken, _ = await self._take_beat(
            name, "pre-async A", BEAT_A, win_ready=0)
        if taken != BEAT_A or self.g.nflit != 4:
            self.bad(name, "pre-async fill",
                     "nflit=4",
                     f"taken={taken is not None} nflit={self.g.nflit}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        await self._idle(win_ready=0)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.win_vld, -1) != 0 or ival(d.win_data, -1) != 0:
            self.bad(name, "async rst_n=0 mid-fill (100ps, no posedge)",
                     "win_vld=0 win_data=0",
                     f"win_vld={ival(d.win_vld, -1)} "
                     f"{_hex960(ival(d.win_data, -1))}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)
        if ival(d.win_vld, -1) != 0 or ival(d.in_ready, -1) != 1:
            self.bad(name, "after async re-reset release, idle",
                     "win_vld=0 in_ready=1",
                     f"win_vld={ival(d.win_vld, -1)} "
                     f"in_ready={ival(d.in_ready, -1)}",
                     HIER)
            phase.drop_objection(self)
            return

        # 4. Rem-complete: two 640s with win_ready=0 after beat 1
        # (idle :65 must not complete the window). Then rem leftover.
        taken, emit = await self._take_beat(
            name, "rem A", BEAT_A, win_ready=0)
        if taken != BEAT_A or emit is not None:
            self.bad(name, "rem beat 1 (nflit 0→4, held)",
                     "take, no emit",
                     f"taken={taken is not None} emit={emit is not None}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        taken, emit = await self._take_beat(
            name, "rem B", BEAT_B, win_ready=0)
        if taken != BEAT_B:
            self.bad(name, "rem beat 2 (nflit 4→6)",
                     _hex640(BEAT_B),
                     _hex640(taken),
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        if ival(d.win_vld, -1) != 1 or ival(d.in_ready, -1) != 0:
            self.bad(name, "rem after 1.5 beats (have, rem_vld)",
                     "win_vld=1 in_ready=0 (blocked / held)",
                     f"win_vld={ival(d.win_vld, -1)} "
                     f"in_ready={ival(d.in_ready, -1)}",
                     HIER)
            phase.drop_objection(self)
            return
        held = ival(d.win_data, -1)
        if _word960(held) != exp_ab:
            self.bad(name, "rem-complete window (A + B high 320)",
                     _hex960(exp_ab),
                     _hex960(held),
                     "u_u.acc")
            phase.drop_objection(self)
            return
        for i in range(3):
            taken, emit = await self._apply(
                name, f"rem bp hold[{i}] win_ready=0",
                0, 0, win_ready=0)
            now = ival(d.win_data, -1)
            if taken is not None or emit is not None or now != held:
                self.bad(name, f"rem bp hold[{i}]",
                         f"no take/emit, win stays {_hex960(exp_ab)}",
                         f"taken={taken is not None} emit={emit is not None} "
                         f"{_hex960(now)}",
                         HIER)
                phase.drop_objection(self)
                return
        rem_outs = []
        if not await self._collect_wins(name, "rem-complete consume", 1, rem_outs):
            phase.drop_objection(self)
            return
        if rem_outs != [exp_ab]:
            self.bad(name, "rem-complete consume (no drop/dup)",
                     _hex960(exp_ab),
                     _hex960(rem_outs[0]) if rem_outs else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Rem leftover: in_vld=1 starves rem_fill (take branch, !rem_vld skip).
        for i in range(2):
            taken, emit = await self._apply(
                name, f"rem leftover starve in_vld=1[{i}]",
                1, BEAT_C, win_ready=1)
            if emit is not None or self.g.rem_vld != 1:
                self.bad(name, f"rem leftover starve[{i}]",
                         "no emit, rem_vld stays 1",
                         f"emit={emit is not None} rem_vld={self.g.rem_vld}",
                         "u_u.rem_vld")
                phase.drop_objection(self)
                return
        rem2 = []
        if not await self._collect_wins(name, "rem leftover 4-Null", 1, rem2):
            phase.drop_objection(self)
            return
        if rem2 != [exp_b_rem]:
            self.bad(name, "rem leftover + 4 Nulls (B low 320)",
                     _hex960(exp_b_rem),
                     _hex960(rem2[0]) if rem2 else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Stock C/D rem-complete (Icarus two-beat path).
        await self._apply(name, "hold after rem leftover", 0, 0, win_ready=0)
        taken, _ = await self._take_beat(
            name, "stock rem C", STOCK_C, win_ready=0)
        taken2, _ = await self._take_beat(
            name, "stock rem D", STOCK_D, win_ready=0)
        if taken != STOCK_C or taken2 != STOCK_D:
            self.bad(name, "stock rem C/D take",
                     "both beats taken",
                     f"C={_hex640(taken)} D={_hex640(taken2)}",
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        stock_rem = []
        if not await self._collect_wins(name, "stock rem-complete", 1, stock_rem):
            phase.drop_objection(self)
            return
        if stock_rem != [exp_cd]:
            self.bad(name, "stock rem-complete (640'hC + 640'hD high)",
                     _hex960(exp_cd),
                     _hex960(stock_rem[0]) if stock_rem else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return
        stock_lo = []
        if not await self._collect_wins(name, "stock rem leftover", 1, stock_lo):
            phase.drop_objection(self)
            return
        if stock_lo != [exp_d_rem]:
            self.bad(name, "stock rem leftover (640'hD low + 4 Nulls)",
                     _hex960(exp_d_rem),
                     _hex960(stock_lo[0]) if stock_lo else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # 5. Same-cycle ack+take_fresh: consume 4+2 while offering next beat.
        await self._apply(name, "hold after stock rem", 0, 0, win_ready=0)
        taken, _ = await self._take_beat(
            name, "ack-take first", BEAT_C, win_ready=1)
        if taken != BEAT_C:
            self.bad(name, "ack-take first beat",
                     _hex640(BEAT_C),
                     _hex640(taken),
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        # Complete with 2 Nulls; next apply with in_vld=1 consumes and parks C? 
        # Collect the 4+2 first (in_vld=0), then offer D while consuming.
        ack_outs = []
        _, emit = await self._apply(
            name, "ack-take complete C (2-Null NBA)", 0, 0, win_ready=1)
        if emit is not None or ival(d.win_vld, -1) != 1:
            self.bad(name, "ack-take C window live",
                     "no handshake yet, win_vld=1",
                     f"emit={emit is not None} win_vld={ival(d.win_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        taken, emit = await self._apply(
            name, "ack+take_fresh D while consuming C",
            1, BEAT_D, win_ready=1)
        if emit != win_4plus2(BEAT_C) or taken != BEAT_D:
            self.bad(name, "same-cycle ack+take_fresh",
                     f"emit C+2null take D",
                     f"emit={_hex960(emit)} taken={_hex640(taken)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        ack_outs.append(emit)
        if not await self._collect_wins(name, "ack-take D 4+2", 1, ack_outs):
            phase.drop_objection(self)
            return
        if ack_outs != [win_4plus2(BEAT_C), win_4plus2(BEAT_D)]:
            self.bad(name, "ack+take then D 4+2 (no leftover rem)",
                     "C+2null then D+2null",
                     f"n={len(ack_outs)}",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Combo hold: window parked 5 ns, clock free-runs.
        await self._apply(name, "hold after ack-take", 0, 0, win_ready=0)
        taken, _ = await self._take_beat(
            name, "hold fill A", BEAT_A, win_ready=1)
        _, emit = await self._apply(
            name, "hold fill complete (2-Null NBA)", 0, 0, win_ready=1)
        if emit is not None or ival(d.win_vld, -1) != 1:
            self.bad(name, "hold fill 2-Null NBA",
                     "no handshake yet, win_vld=1",
                     f"emit={emit is not None} win_vld={ival(d.win_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        _, emit = await self._apply(
            name, "hold fill park (win_ready=0)", 0, 0, win_ready=0)
        if emit is not None or ival(d.win_vld, -1) != 1:
            self.bad(name, "hold fill have",
                     "win_vld=1",
                     f"win_vld={ival(d.win_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        sset(d.win_ready, 0)
        await Timer(100, "PS")
        held_wv = ival(d.win_vld, -1)
        held_ir = ival(d.in_ready, -1)
        held_wd = ival(d.win_data, -1)
        await Timer(5, "NS")
        if (ival(d.win_vld, -1) != 1 or ival(d.win_vld, -1) != held_wv
                or ival(d.in_ready, -1) != held_ir
                or ival(d.win_data, -1) != held_wd
                or _word960(held_wd) != exp_a_null):
            self.bad(name, "hold first 960 5 ns (combo win_vld / win_data)",
                     f"win_vld=1 win stays {_hex960(exp_a_null)}",
                     f"win_vld={ival(d.win_vld, -1)} "
                     f"{_hex960(ival(d.win_data, -1))}",
                     HIER)
            phase.drop_objection(self)
            return
        await self._idle(win_ready=0)
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        if ival(d.win_vld, -1) != 0:
            self.bad(name, "async rst_n=0 after hold (100ps, no posedge)",
                     "win_vld=0",
                     f"win_vld={ival(d.win_vld, -1)}",
                     "u_u.have")
            phase.drop_objection(self)
            return
        self.g.reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # Second group after drain (phase wrap / no leftover rem).
        taken, _ = await self._take_beat(
            name, "second G BEAT_B", BEAT_B, win_ready=1)
        if taken != BEAT_B:
            self.bad(name, "second group take",
                     _hex640(BEAT_B),
                     _hex640(taken),
                     "u_u.nflit")
            phase.drop_objection(self)
            return
        second = []
        if not await self._collect_wins(name, "second 4+2", 1, second):
            phase.drop_objection(self)
            return
        if second != [win_4plus2(BEAT_B)]:
            self.bad(name, "second window after drain (BEAT_B + 2 Nulls)",
                     _hex960(win_4plus2(BEAT_B)),
                     _hex960(second[0]) if second else "x",
                     "u_u.acc")
            phase.drop_objection(self)
            return

        # Extra in_vld=0 after drain must not emit if win_ready=0.
        await self._apply(name, "park after second", 0, 0, win_ready=0)
        for i in range(3):
            taken, emit = await self._apply(
                name, f"in_vld=0 after drain[{i}]",
                0, BEAT_A, win_ready=0)
            if taken is not None or emit is not None or ival(d.win_vld, -1) != 0:
                self.bad(name, f"idle after drain[{i}]",
                         "win_vld=0",
                         f"taken={taken is not None} emit={emit is not None} "
                         f"win_vld={ival(d.win_vld, -1)}",
                         "u_u.have")
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_g1)
