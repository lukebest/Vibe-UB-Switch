"""Module-level uvm-python TC for Decision-I leaf vibe_pcs_tx_cw2beat.

Covers reset/idle clean (no spurious beat_vld, cw_ready=1, beat_data=0),
async rst_n clear of registered halves, 1024→exactly 2×512 high-then-low
vs golden split, hold-full backpressure without drop/dup, cw_vld while
not ready does not overwrite parked halves, consume-last+cw_vld does
not accept (cw_ready and beat_vld are exclusive), second codeword
after drain, mid-run async rst_n through dest posedge, and a pin
scan with instance u_u. Not a full-chip consecutive-green gate.
Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_pcs_tx_cw2beat.sv and stock tc_pcs_cw2beat
count semantics, plus hi/lo data scoring. Combo: cw_ready =
!have_hi && !have_lo; beat_vld = have_hi || have_lo; beat_data =
have_hi ? hi : lo. Accept parks cw_data[1023:512] / [511:0]; consume
clears have_hi first, then have_lo. Accept and consume never overlap
in stock (ready and valid are complements). Instantiated by
vibe_pcs_tx u_cw. This is not vibe_pcs_tx / vibe_pcs_rx /
vibe_pcs_scramble / vibe_ebch16 / gear / vibe_afifo / vibe_sync2 /
vibe_rst_sync.
ovf_l (F1) is not in this module.
CHILDREN: none (leaf cell; no FSM child).
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK512 = (1 << 512) - 1
MASK1024 = (1 << 1024) - 1

# Distinct 512b halves so a hi/lo swap cannot pass by accident.
# Stock Icarus tc_pcs_cw2beat uses {512'hA, 512'hB}.
STOCK_HI = 0xA
STOCK_LO = 0xB
HI1 = int("C0DE" * 32, 16)
LO1 = int("BEEF" * 32, 16)
HI2 = int("A5A5" * 32, 16)
LO2 = int("5A5A" * 32, 16)

HIER = "u_u.have_hi / u_u.have_lo / u_u.beat_vld / u_u.cw_ready"
WRAP = "vibe_pcs_tx_cw2beat_cocotb_top"
PINS = (
    "clk", "rst_n", "cw_data", "cw_vld", "cw_ready",
    "beat_data", "beat_vld", "beat_ready",
)
ABSENT = (
    "ovf_l", "in_ready", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld", "u_cw",
    "lane_id", "seed_load", "en", "cw_sel",
)


def _word512(v: int) -> int:
    return v & MASK512


def pack_cw(hi: int, lo: int) -> int:
    """1024b codeword: {hi[511:0], lo[511:0]}."""
    return ((_word512(hi) << 512) | _word512(lo)) & MASK1024


def split_cw(cw: int):
    """Golden 1024→2×512: high beat first, then low."""
    w = cw & MASK1024
    return (w >> 512) & MASK512, w & MASK512


def _hex512(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:0128x}"


class tc_vibe_pcs_tx_cw2beat(VibeUnitBaseTest):
    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.cw_vld, 0)
        sset(d.cw_data, 0)
        sset(d.beat_ready, 1)

    async def _hold_reset(self, n=4):
        sset(self.dut.rst_n, 0)
        await self._idle()
        await self.cycles(n)

    async def _release_reset(self, n=2):
        sset(self.dut.rst_n, 1)
        await self.cycles(n)

    async def _to_fall(self):
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    def _sample(self):
        d = self.dut
        return (
            ival(d.beat_vld, -1),
            ival(d.beat_data, -1),
            ival(d.cw_ready, -1),
        )

    def _inner_sample(self):
        u = getattr(self.dut, "u_u", None)
        if u is None:
            return None
        return (
            ival(u.beat_vld, -1),
            ival(u.beat_data, -1),
            ival(u.cw_ready, -1),
        )

    def _combo_ok(self, bv, cr):
        """cw_ready and beat_vld are stock complements (never both 1 / 0)."""
        return bv in (0, 1) and cr in (0, 1) and (bv ^ cr) == 1

    def _score_inner(self, name, stim, bv, bd, cr):
        inner = self._inner_sample()
        if inner is None:
            self.bad(name, stim + " (u_u)",
                     "u_u present", "missing", WRAP)
            return False
        ibv, ibd, icr = inner
        if (ibv, ibd, icr) != (bv, bd, cr):
            self.bad(name, stim + " (port vs u_u)",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     f"u_u beat_vld={ibv} cw_ready={icr} "
                     f"beat_data={_hex512(ibd)}",
                     HIER)
            return False
        return True

    def _score_combo(self, name, stim, bv, bd, cr):
        if not self._combo_ok(bv, cr):
            self.bad(name, stim + " (cw_ready XOR beat_vld)",
                     "complements (never both 1 / both 0)",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     HIER)
            return False
        return self._score_inner(name, stim, bv, bd, cr)

    async def _advance(self, cw_vld, cw_data, beat_ready):
        """On falling edge: drive, take if beat_vld&&beat_ready, land on next fall.

        Returns (taken_or_None, accepted, post_beat_vld, post_beat_data, post_cw_ready).
        """
        d = self.dut
        sset(d.beat_ready, 1 if beat_ready else 0)
        sset(d.cw_data, cw_data & MASK1024)
        sset(d.cw_vld, 1 if cw_vld else 0)
        # Combo cw_ready / beat_vld / beat_data need a delta after sset.
        await Timer(100, "PS")
        cr = ival(d.cw_ready, 0)
        bv = ival(d.beat_vld, 0)
        bd = ival(d.beat_data, 0)
        taken = bd if (bv == 1 and beat_ready) else None
        accepted = bool(cw_vld) and bool(cr)
        await self._to_fall()
        post_bv, post_bd, post_cr = self._sample()
        return taken, accepted, post_bv, post_bd, post_cr

    async def _drain(self, outs, n=6):
        for _ in range(n):
            taken, _, bv, _, _ = await self._advance(0, 0, 1)
            if taken is not None:
                outs.append(taken)
            if bv == 0:
                break

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_pcs_tx_cw2beat"
        hier = HIER

        await self._hold_reset()
        await self._release_reset()
        await FallingEdge(d.clk)

        # 1. After reset: idle, cw_ready, no spurious beat_vld, beat_data held 0.
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "reset then release, cw_vld=0 beat_ready=1",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "reset then release, idle", bv, bd, cr):
            phase.drop_objection(self)
            return
        for i in range(4):
            taken, accepted, bv, bd, cr = await self._advance(0, pack_cw(0x55, 0xAA), 1)
            if taken is not None or accepted or bv != 0 or cr != 1 or bd != 0:
                self.bad(name, f"idle cycle {i} after reset (cw_vld=0)",
                         "no beat handshake, beat_vld=0 cw_ready=1 beat_data=0",
                         f"taken={_hex512(taken)} accepted={accepted} "
                         f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                         hier)
                phase.drop_objection(self)
                return
            if not self._score_combo(name, f"idle cycle {i} after reset",
                                     bv, bd, cr):
                phase.drop_objection(self)
                return

        # Async rst_n mid-cycle clears registered halves (100ps, no posedge).
        taken, accepted, _, _, _ = await self._advance(1, pack_cw(HI1, LO1), 0)
        if not accepted or taken is not None:
            self.bad(name, "park cw before early async rst",
                     "accept, no take",
                     f"taken={_hex512(taken)} accepted={accepted}",
                     hier)
            phase.drop_objection(self)
            return
        await self._idle()
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "async rst_n=0 mid-cycle (100ps, no posedge)",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "async rst_n=0 mid-cycle", bv, bd, cr):
            phase.drop_objection(self)
            return
        await self._release_reset()
        await FallingEdge(d.clk)
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "after async re-reset release, idle",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return

        # 2. One 1024b cw, beat_ready=1 → exactly hi then lo (stock {A,B}).
        stock = pack_cw(STOCK_HI, STOCK_LO)
        exp_hi, exp_lo = split_cw(stock)
        outs = []
        taken, accepted, bv, bd, cr = await self._advance(1, stock, 1)
        if taken is not None or not accepted:
            self.bad(name, "stock {512'hA,512'hB} accept",
                     "accept, no beat yet (empty → park both halves)",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_u.cw_ready")
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "stock accept post-edge", bv, bd, cr):
            phase.drop_objection(self)
            return
        if bv != 1 or cr != 0 or bd != exp_hi:
            self.bad(name, "stock accept parks hi on combo mux",
                     f"beat_vld=1 cw_ready=0 beat_data={_hex512(exp_hi)}",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        await self._drain(outs)
        if outs != [exp_hi, exp_lo]:
            self.bad(name, "one 1024b cw, beat_ready=1 (stock A/B)",
                     f"exactly 2×512: hi={_hex512(exp_hi)} lo={_hex512(exp_lo)}",
                     f"n={len(outs)} " + " ".join(_hex512(x) for x in outs),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # Distinctive wide halves (not just the stock nibble pair).
        cw1 = pack_cw(HI1, LO1)
        exp1 = list(split_cw(cw1))
        outs1 = []
        taken, accepted, bv, _, cr = await self._advance(1, cw1, 1)
        if taken is not None or not accepted:
            self.bad(name, "wide cw1 accept",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_u.cw_ready")
            phase.drop_objection(self)
            return
        await self._drain(outs1)
        if outs1 != exp1:
            self.bad(name, "one 1024b cw, beat_ready=1 (wide C0DE/BEEF)",
                     f"exactly 2×512: hi={_hex512(exp1[0])} lo={_hex512(exp1[1])}",
                     f"n={len(outs1)} " + " ".join(_hex512(x) for x in outs1),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # 3. Backpressure: stall when beat_ready=0 after accept; no drop/dup.
        cw_bp = pack_cw(HI1, LO1)
        exp_bp = list(split_cw(cw_bp))
        taken, accepted, bv, bd, cr = await self._advance(1, cw_bp, 0)
        if taken is not None or not accepted:
            self.bad(name, "bp accept with beat_ready=0",
                     "accept, no take (empty at sample)",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} beat_data={_hex512(bd)} cw_ready={cr}",
                     "u_u.cw_ready")
            phase.drop_objection(self)
            return
        # Both halves parked. beat_ready=0 must hold hi, cw_ready=0.
        # A different cw_vld beat must not overwrite the parked halves.
        for i in range(3):
            taken, accepted, bv, bd, cr = await self._advance(1, pack_cw(HI2, LO2), 0)
            if (taken is not None or accepted or bv != 1
                    or bd != exp_bp[0] or cr != 0):
                self.bad(name, f"bp stall[{i}] beat_ready=0 both halves parked",
                         f"no take/accept, beat_vld=1 beat_data={_hex512(exp_bp[0])} "
                         "cw_ready=0",
                         f"taken={_hex512(taken)} accepted={accepted} "
                         f"beat_vld={bv} beat_data={_hex512(bd)} cw_ready={cr}",
                         "u_u.cw_ready")
                phase.drop_objection(self)
                return
            if not self._score_combo(name, f"bp stall[{i}]", bv, bd, cr):
                phase.drop_objection(self)
                return
        # Resume: take hi (no new input). Combo mux must then show lo.
        taken, accepted, bv, bd, cr = await self._advance(0, 0, 1)
        if taken != exp_bp[0] or accepted:
            self.bad(name, "bp resume take hi",
                     f"take {_hex512(exp_bp[0])}, no new accept",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} beat_data={_hex512(bd)}",
                     "u_u.beat_data")
            phase.drop_objection(self)
            return
        if bv != 1 or cr != 0 or bd != exp_bp[1]:
            self.bad(name, "after take hi, combo mux shows lo",
                     f"beat_vld=1 cw_ready=0 beat_data={_hex512(exp_bp[1])}",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "after take hi, mux=lo", bv, bd, cr):
            phase.drop_objection(self)
            return
        outs_bp = [taken]
        await self._drain(outs_bp)
        if outs_bp != exp_bp:
            self.bad(name, "bp resume after stall, same 1024b",
                     "no drop/dup: " + " ".join(_hex512(x) for x in exp_bp),
                     f"n={len(outs_bp)} " + " ".join(_hex512(x) for x in outs_bp),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # 4. Second codeword after drain (phase wrap / no leftover halves).
        cw2 = pack_cw(HI2, LO2)
        exp2 = list(split_cw(cw2))
        outs2 = []
        taken, accepted, bv, _, cr = await self._advance(1, cw2, 1)
        if taken is not None or not accepted:
            self.bad(name, "second cw accept after drain",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     "u_u.cw_ready")
            phase.drop_objection(self)
            return
        await self._drain(outs2)
        if outs2 != exp2:
            self.bad(name, "second 1024b cw after drain (A5A5/5A5A)",
                     f"exactly 2×512: hi={_hex512(exp2[0])} lo={_hex512(exp2[1])}",
                     f"n={len(outs2)} " + " ".join(_hex512(x) for x in outs2),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # 5. Consume last lo + cw_vld: exclusive ready/vld, no same-cycle accept.
        # NBA last-wins cannot fire both arms (cw_ready && beat_vld is 0).
        taken, accepted, bv, bd, cr = await self._advance(1, cw1, 1)
        if taken is not None or not accepted:
            self.bad(name, "exclusive setup accept",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted}",
                     hier)
            phase.drop_objection(self)
            return
        taken, accepted, bv, bd, cr = await self._advance(1, pack_cw(HI2, LO2), 1)
        if taken != exp1[0] or accepted:
            self.bad(name, "take hi while cw_vld (not ready)",
                     f"take {_hex512(exp1[0])}, no accept",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     hier)
            phase.drop_objection(self)
            return
        taken, accepted, bv, bd, cr = await self._advance(1, pack_cw(HI2, LO2), 1)
        if taken != exp1[1] or accepted:
            self.bad(name, "consume last lo + cw_vld (exclusive)",
                     f"take {_hex512(exp1[1])}, no accept (cw_ready was 0)",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     hier)
            phase.drop_objection(self)
            return
        if bv != 0 or cr != 1:
            self.bad(name, "after last lo, empty (ready, no leftover)",
                     "beat_vld=0 cw_ready=1",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "after last lo + rejected cw_vld",
                                 bv, bd, cr):
            phase.drop_objection(self)
            return
        # Next cycle is empty: the pending cw_vld can now accept HI2/LO2.
        taken, accepted, bv, bd, cr = await self._advance(1, pack_cw(HI2, LO2), 1)
        if taken is not None or not accepted:
            self.bad(name, "accept after exclusive last-lo reject",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     hier)
            phase.drop_objection(self)
            return
        outs_ex = []
        await self._drain(outs_ex)
        if outs_ex != exp2:
            self.bad(name, "after exclusive reject, next cw is HI2/LO2",
                     f"exactly 2×512: hi={_hex512(exp2[0])} lo={_hex512(exp2[1])}",
                     f"n={len(outs_ex)} " + " ".join(_hex512(x) for x in outs_ex),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # 6. Mid-run async rst_n clears registered halves. Park first so
        # beat_vld=1 / beat_data!=0, then pulse rst_n through dest posedge.
        taken, accepted, _, _, _ = await self._advance(1, cw1, 0)
        if not accepted or taken is not None:
            self.bad(name, "park cw before async re-reset",
                     "accept, no take",
                     f"taken={_hex512(taken)} accepted={accepted}",
                     "u_u.cw_ready")
            phase.drop_objection(self)
            return
        await self._idle()
        bv, bd, cr = self._sample()
        if bv != 1 or cr != 0 or bd != exp1[0]:
            self.bad(name, "pre-async-rst park (beat_ready=1, no consume yet)",
                     f"beat_vld=1 cw_ready=0 beat_data={_hex512(exp1[0])}",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     hier)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 0)
        await Timer(100, "PS")
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "mid-run rst_n=0 (100ps, no posedge)",
                     "beat_vld=0 cw_ready=1 beat_data=0 (async clear)",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "mid-run rst_n=0", bv, bd, cr):
            phase.drop_objection(self)
            return
        await self._to_fall()
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "rst_n held 0 through dest posedge",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     HIER)
            phase.drop_objection(self)
            return
        sset(d.rst_n, 1)
        await self._idle()
        await self.cycles(2)
        await FallingEdge(d.clk)
        bv, bd, cr = self._sample()
        if bv != 0 or cr != 1 or bd != 0:
            self.bad(name, "after async re-release, idle",
                     "beat_vld=0 cw_ready=1 beat_data=0",
                     f"beat_vld={bv} cw_ready={cr} beat_data={_hex512(bd)}",
                     HIER)
            phase.drop_objection(self)
            return
        if not self._score_combo(name, "after async re-release, idle",
                                 bv, bd, cr):
            phase.drop_objection(self)
            return
        # After mid-run rst the parked halves are gone; a new cw must accept.
        taken, accepted, bv, bd, cr = await self._advance(1, stock, 1)
        if taken is not None or not accepted:
            self.bad(name, "accept after mid-run rst (no leftover halves)",
                     "accept, no beat yet",
                     f"taken={_hex512(taken)} accepted={accepted} "
                     f"beat_vld={bv} cw_ready={cr}",
                     hier)
            phase.drop_objection(self)
            return
        outs_rst = []
        await self._drain(outs_rst)
        if outs_rst != [exp_hi, exp_lo]:
            self.bad(name, "after mid-run rst, stock A/B",
                     f"exactly 2×512: hi={_hex512(exp_hi)} lo={_hex512(exp_lo)}",
                     f"n={len(outs_rst)} " + " ".join(_hex512(x) for x in outs_rst),
                     "u_u.beat_data")
            phase.drop_objection(self)
            return

        # 7. Leaf pins match product SV (no ovf_l / dual-clock).
        # Instance u_u (not leftover u_cw).
        if not hasattr(d, "u_u"):
            self.bad(name, "leaf instance scan (u_u)",
                     "u_u present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_pcs_tx_cw2beat product port",
                         f"{absent} present", WRAP)
                phase.drop_objection(self)
                return
        for need in PINS:
            if not hasattr(d, need):
                self.bad(name, f"leaf pin scan ({need})",
                         f"{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return
        u = d.u_u
        for need in PINS:
            if not hasattr(u, need):
                self.bad(name, f"leaf instance pin scan (u_u.{need})",
                         f"u_u.{need} present", "missing", WRAP)
                phase.drop_objection(self)
                return

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_pcs_tx_cw2beat)
