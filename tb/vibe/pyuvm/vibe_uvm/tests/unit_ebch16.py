"""Module-level uvm-python TC for Decision-I leaf vibe_ebch16.

Covers combo idle (no rst_n / no sequential hold), Table 3-5 encode LUT,
default sel 31, unique invert (decode), and min Hamming distance 8.
Not a full-chip consecutive-green gate. Not 1/3, 4/3, freeze, or signoff.

Matches product rtl/pcs/vibe_ebch16.sv and stock tc_ebch16_lut
sel 0..30 Table 3-5 / default 16'hFFFF semantics. Combo leaf: cw_sel[4:0]
→ cw[15:0]. Used by vibe_pcs_tx_amctl / vibe_pcs_rx_amctl_lock.
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

HIER = "u_ebch.cw"


def _hex16(v) -> str:
    if v is None:
        return "x"
    return f"0x{v:04X}"


def _hamming(a: int, b: int) -> int:
    return bin((a ^ b) & 0xFFFF).count("1")


class tc_vibe_ebch16(VibeUnitBaseTest):
    async def _apply(self, sel):
        """Drive cw_sel and settle the combo LUT (#1 like stock)."""
        sset(self.dut.cw_sel, sel & 0x1F)
        await Timer(1, "NS")
        return ival(self.dut.cw, -1)

    async def run_phase(self, phase):
        phase.raise_objection(self)
        name = "tc_vibe_ebch16"

        # 1. Combo idle / no sequential state (DUT has no rst_n).
        # sel=0 is the all-zero Table 3-5 word; walking away and back
        # must not hold the previous cw.
        cw0 = await self._apply(0)
        if cw0 != 0x0000:
            self.bad(name, "cw_sel=0 (combo idle / reset-like)",
                     "cw=0x0000", f"cw={_hex16(cw0)}", HIER)
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

        # 2. Encode: full 32-entry LUT vs Table 3-5 + default.
        got = []
        for sel, exp in enumerate(EBCH16):
            act = await self._apply(sel)
            got.append(act)
            if act != exp:
                self.bad(name, f"encode cw_sel={sel}",
                         f"cw={_hex16(exp)}", f"cw={_hex16(act)}", HIER)
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
                d = _hamming(table[i], table[j])
                if d < 8:
                    self.bad(name,
                             f"Hamming(cw_sel={i}, cw_sel={j})",
                             "distance >= 8",
                             f"distance={d} "
                             f"({_hex16(table[i])} vs {_hex16(table[j])})",
                             HIER)
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

        self.ok(name)
        phase.drop_objection(self)


uvm_component_utils(tc_vibe_ebch16)
