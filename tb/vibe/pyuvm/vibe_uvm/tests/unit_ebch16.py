"""Module-level uvm-python TC for Decision-I leaf vibe_ebch16.

Covers combo idle / no sequential hold (DUT has no clk / rst_n —
no async clear to pulse), Table 3-5 encode LUT vs product SV golden,
default sel 31, unique invert (decode), complementary pairs at
Hamming 16, min Hamming distance 8, mid-run cw_sel walk without
hold, and a pin scan with instance u_u. Not a full-chip
consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_ebch16.sv and stock tc_ebch16_lut
sel 0..30 Table 3-5 / default 16'hFFFF semantics. Combo leaf: cw_sel[4:0]
→ cw[15:0]. Instantiated by vibe_pcs_tx_amctl u3/u8/u9/u10/u21/u22/u28
and vibe_pcs_rx_amctl_lock the same named LUT cells. This is not
vibe_pcs_scramble / vibe_pcs_tx / vibe_pcs_rx / gear / vibe_afifo /
vibe_sync2 / vibe_rst_sync.
ovf_l (F1) is not in this module.
CHILDREN: none (leaf cell; no FSM child).
"""

from uvm import uvm_component_utils
from cocotb.triggers import Timer
from vibe_uvm.hdl import ival, sset
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

# Table 3-5 eBCH (16, 5) plus default (sel 31). Same as stock tc_ebch16_lut.
EBCH16 = (
    0x0000, 0x0A6F, 0x14DD, 0x1EB2, 0x23D6, 0x29B9, 0x370B, 0x3D64,
    0x47AC, 0x4DC3, 0x5371, 0x591E, 0x647A, 0x6E15, 0x70A7, 0x7AC8,
    0x8537, 0x8F58, 0x91EA, 0x9B85, 0xA6E1, 0xAC8E, 0xB23C, 0xB853,
    0xC29B, 0xC8F4, 0xD646, 0xDC29, 0xE14D, 0xEB22, 0xF590, 0xFFFF,
)

# AMCTL-used Table 3-5 indices (BODY/END/lane/cmd subset).
AMCTL_SELS = (3, 8, 9, 10, 21, 22, 28)

HIER = "u_u.cw / u_u.cw_sel"
WRAP = "vibe_ebch16_cocotb_top"
PINS = ("cw_sel", "cw")
ABSENT = (
    "clk", "rst_n", "ovf_l", "in_ready", "out_ready", "almost_full",
    "wclk", "rclk", "wen", "ren", "wfull", "rempty", "wocc",
    "rst_n_in", "rst_n_out", "d", "q", "phase", "hold_vld",
    "rbits", "cfg_wr_vld", "dll_pcs_vld", "u_ebch",
    "in_vld", "out_vld", "lane_id", "seed_load", "en",
)


def _hex16(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:04X}"


def _hamming(a: int, b: int) -> int:
    return bin((a ^ b) & 0xFFFF).count("1")


class tc_vibe_ebch16(VibeUnitBaseTest):
    def _inner_cw(self):
        u = getattr(self.dut, "u_u", None)
        if u is None:
            return None
        return ival(u.cw, -1)

    def _score_inner(self, name, stim, top_cw):
        inner = self._inner_cw()
        if inner != top_cw:
            self.bad(name, stim + " (port vs u_u.cw)",
                     f"cw={_hex16(top_cw)}",
                     f"u_u.cw={_hex16(inner)}", HIER)
            return False
        return True

    async def _apply(self, sel):
        """Drive cw_sel and settle the combo LUT (#1 like stock)."""
        sset(self.dut.cw_sel, sel & 0x1F)
        await Timer(1, "NS")
        return ival(self.dut.cw, -1)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        name = "tc_vibe_ebch16"
        hier = HIER

        # 1. Combo idle / no sequential state (DUT has no rst_n / clk).
        # sel=0 is the all-zero Table 3-5 word; walking away and back
        # must not hold the previous cw. This is the reset-like check:
        # there is no async clear pin to pulse.
        cw0 = await self._apply(0)
        if cw0 != 0x0000:
            self.bad(name, "cw_sel=0 (combo idle / reset-like)",
                     "cw=0x0000", f"cw={_hex16(cw0)}", HIER)
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "cw_sel=0 (combo idle)", cw0):
            phase.drop_objection(self)
            return
        cw_def = await self._apply(31)
        if cw_def != 0xFFFF:
            self.bad(name, "cw_sel=31 after idle (default)",
                     "cw=0xFFFF", f"cw={_hex16(cw_def)}", HIER)
            phase.drop_objection(self)
            return
        cw_back = await self._apply(0)
        if cw_back != 0x0000:
            self.bad(name, "cw_sel=0 after default (no sequential hold)",
                     "cw=0x0000 (combo, not latched)",
                     f"cw={_hex16(cw_back)}", HIER)
            phase.drop_objection(self)
            return

        # 2. Encode: full 32-entry LUT vs Table 3-5 + default (product SV).
        got = []
        for sel, exp in enumerate(EBCH16):
            act = await self._apply(sel)
            got.append(act)
            if act != exp:
                self.bad(name, f"encode cw_sel={sel}",
                         f"cw={_hex16(exp)}", f"cw={_hex16(act)}", HIER)
                phase.drop_objection(self)
                return
            if not self._score_inner(name, f"encode cw_sel={sel}", act):
                phase.drop_objection(self)
                return

        # Re-score a second pass (combo stable; same sel → same cw).
        for sel, exp in enumerate(EBCH16):
            act = await self._apply(sel)
            if act != exp:
                self.bad(name, f"re-encode cw_sel={sel} (stability)",
                         f"cw={_hex16(exp)}", f"cw={_hex16(act)}", HIER)
                phase.drop_objection(self)
                return

        # AMCTL-used subset (named encode, same LUT).
        for sel in AMCTL_SELS:
            act = await self._apply(sel)
            if act != EBCH16[sel]:
                self.bad(name, f"AMCTL encode cw_sel={sel}",
                         f"cw={_hex16(EBCH16[sel])}",
                         f"cw={_hex16(act)}", HIER)
                phase.drop_objection(self)
                return

        # 3. Decode: Table 3-5 words are unique; inverse maps back to sel.
        table = got[:31]
        if len(set(table)) != 31:
            self.bad(name, "encode sel 0..30 uniqueness",
                     "31 distinct codewords",
                     f"{len(set(table))} distinct", HIER)
            phase.drop_objection(self)
            return
        if 0xFFFF in table:
            self.bad(name, "default 0xFFFF not in Table 3-5",
                     "sel 0..30 exclude 0xFFFF",
                     "0xFFFF present in 0..30", HIER)
            phase.drop_objection(self)
            return
        inv = {cw: sel for sel, cw in enumerate(table)}
        for sel, cw in enumerate(table):
            dec = inv.get(cw)
            if dec != sel:
                self.bad(name, f"decode cw={_hex16(cw)}",
                         f"cw_sel={sel}", f"cw_sel={dec}", HIER)
                phase.drop_objection(self)
                return
        if got[31] != 0xFFFF:
            self.bad(name, "decode default cw=0xFFFF",
                     "maps from cw_sel=31 only",
                     f"cw={_hex16(got[31])}", HIER)
            phase.drop_objection(self)
            return

        # 4. Min Hamming distance 8 among Table 3-5 (sel 0..30).
        # Complementary pairs in the set are distance 16; never below 8.
        for i in range(31):
            for j in range(i + 1, 31):
                dist = _hamming(table[i], table[j])
                if dist < 8:
                    self.bad(name,
                             f"Hamming(cw_sel={i}, cw_sel={j})",
                             "distance >= 8",
                             f"distance={dist} "
                             f"({_hex16(table[i])} vs {_hex16(table[j])})",
                             HIER)
                    phase.drop_objection(self)
                    return

        # Complementary pairs: sel i XOR sel (31-i) == 0xFFFF (i=1..15);
        # sel 0 complement is the default (sel 31), not a Table 3-5 word.
        if (table[0] ^ 0xFFFF) != EBCH16[31]:
            self.bad(name, "sel 0 complement is default",
                     f"cw={_hex16(EBCH16[31])}",
                     f"cw={_hex16(table[0] ^ 0xFFFF)}", hier)
            phase.drop_objection(self)
            return
        for i in range(1, 16):
            pair = 31 - i
            xor = (table[i] ^ table[pair]) & 0xFFFF
            if xor != 0xFFFF or _hamming(table[i], table[pair]) != 16:
                self.bad(name, f"complementary pair cw_sel={i}/{pair}",
                         "XOR=0xFFFF Hamming=16",
                         f"XOR={_hex16(xor)} "
                         f"Hamming={_hamming(table[i], table[pair])}",
                         hier)
                phase.drop_objection(self)
                return

        # Hold a named Table 3-5 sel; combo output must not drift.
        held = await self._apply(30)
        if held != EBCH16[30]:
            self.bad(name, "cw_sel=30 before hold",
                     f"cw={_hex16(EBCH16[30])}",
                     f"cw={_hex16(held)}", HIER)
            phase.drop_objection(self)
            return
        await Timer(5, "NS")
        later = ival(self.dut.cw, -1)
        if later != held or later != EBCH16[30]:
            self.bad(name, "hold cw_sel=30 for 5 ns (no clock)",
                     f"cw stays {_hex16(EBCH16[30])}",
                     f"cw={_hex16(later)}", HIER)
            phase.drop_objection(self)
            return

        # 5. Mid-run cw_sel walk (combo; no rst_n to pulse). Park a
        # nonzero AMCTL word, then walk idle / default without hold.
        parked = await self._apply(28)
        if parked != EBCH16[28] or parked == 0:
            self.bad(name, "pre-mid-run park (AMCTL cw_sel=28)",
                     f"cw={_hex16(EBCH16[28])} (nonzero)",
                     f"cw={_hex16(parked)}", HIER)
            phase.drop_objection(self)
            return
        mid0 = await self._apply(0)
        if mid0 != 0x0000:
            self.bad(name, "mid-run cw_sel=0 after AMCTL park",
                     "cw=0x0000 (combo clear, no sequential hold)",
                     f"cw={_hex16(mid0)}", HIER)
            phase.drop_objection(self)
            return
        mid_def = await self._apply(31)
        if mid_def != 0xFFFF:
            self.bad(name, "mid-run cw_sel=31 after idle",
                     "cw=0xFFFF", f"cw={_hex16(mid_def)}", HIER)
            phase.drop_objection(self)
            return
        mid_am = await self._apply(28)
        if mid_am != EBCH16[28]:
            self.bad(name, "mid-run cw_sel=28 after default",
                     f"cw={_hex16(EBCH16[28])} (combo, not latched)",
                     f"cw={_hex16(mid_am)}", HIER)
            phase.drop_objection(self)
            return
        if not self._score_inner(name, "mid-run cw_sel=28", mid_am):
            phase.drop_objection(self)
            return

        # 6. Leaf pins match product SV (no clk / rst_n / ovf_l).
        # Instance u_u (not leftover u_ebch).
        if not hasattr(d, "u_u"):
            self.bad(name, "leaf instance scan (u_u)",
                     "u_u present", "missing", WRAP)
            phase.drop_objection(self)
            return
        for absent in ABSENT:
            if hasattr(d, absent):
                self.bad(name, f"leaf pin scan ({absent})",
                         "not a vibe_ebch16 product port",
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


uvm_component_utils(tc_vibe_ebch16)
