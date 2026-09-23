"""Full-wrapper uvm-python TC for official TP-DLL-004.

Stock Icarus `tc_dll` instantiates `vibe_dll` and only smokes LinkUp=0
→ disabled plus a 1-flit poke. Leaf `tc_dll_sm_states` / credit / retry /
rx / tx do **not** score this ID.

This TC keeps the stock wrapper + disabled check, then drives a DLLDP
whose PLENGTH is >32 flits and scores the official split:

    DLLDP >32 flit 拆 ≤16×≤32

G1 TX streams the NW 512b byte stream into 20B flits and emits 4-flit
PCS groups (BCRC in the last 32b of each group). The official DLLDB
window is 32 flits (nblk/lastn in LPH). We score that a >32-flit DP is
accepted in full and partitions into ≤16 chunks of ≤32 flits — not
truncated at 32.

Not 1/3, 4/3, freeze, or signoff. Not a full-chip consecutive-green reopen.
"""

from uvm import uvm_component_utils
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.handle import Force
from vibe_uvm import lph
from vibe_uvm.hdl import ival, sset, hier
from vibe_uvm.tests.unit_base import VibeUnitBaseTest

MASK160 = (1 << 160) - 1
MASK512 = (1 << 512) - 1
MASK640 = (1 << 640) - 1
MASK352 = (1 << 352) - 1

# Primary vector: 40 flits = 2 DLLDBs (32+8). Boundary: 33 = 32+1.
SPLIT_NFLITS = (40, 33)
NAME = "tc_dll"


def _pat512(idx: int) -> int:
    """64 distinct nonzero bytes so emit flits cannot collapse to Null."""
    v = 0
    for i in range(64):
        v = (v << 8) | ((0xA0 + (idx * 17 + i)) & 0xFF)
    return v & MASK512


def _sop_beat(nflits: int, pat_idx: int = 0) -> int:
    plen = lph.plen_flits(nflits)
    flit0 = lph.mk_flit(3, 0, 0, 1, 2, plen)
    return lph.mk_beat(flit0, _pat512(pat_idx) & MASK352)


def _nw_beats(nflits: int) -> list[int]:
    nbytes = nflits * 20
    nbeats = (nbytes + 63) // 64
    beats = [_sop_beat(nflits, 0)]
    for i in range(1, nbeats):
        beats.append(_pat512(i))
    return beats


def _pcs_flits(beat: int) -> list[int]:
    b = beat & MASK640
    return [
        (b >> 480) & MASK160,
        (b >> 320) & MASK160,
        (b >> 160) & MASK160,
        b & MASK160,
    ]


def _score_chunks(nflits: int, consumed: int, n_pcs: int) -> tuple[bool, str, str]:
    """Return (ok, expected, actual) for the official split."""
    chunks = lph.dllp_chunks(nflits)
    exp_pcs = (nflits + 3) // 4
    exp = (f"nflits={nflits}>32 chunks={chunks} (n={len(chunks)}≤16, "
           f"each≤32) consume={nflits} pcs_beats={exp_pcs}")
    act = (f"nflits={nflits} chunks={chunks} consume={consumed} "
           f"pcs_beats={n_pcs}")
    if nflits <= 32:
        return False, "declared nflits>32", act
    if not chunks or len(chunks) > 16:
        return False, exp, f"{act} n_chunks={len(chunks)}"
    if any(c < 1 or c > 32 for c in chunks):
        return False, exp, f"{act} chunk out of 1..32"
    if sum(chunks) != nflits:
        return False, exp, f"{act} chunk sum={sum(chunks)}"
    if consumed != nflits:
        return False, exp, f"{act} DUT did not consume all declared flits"
    if n_pcs != exp_pcs:
        return False, exp, f"{act} emit groups != ceil(nflits/4)"
    return True, exp, act


class tc_dll(VibeUnitBaseTest):
    """TP-DLL-004: DLLDP >32 flit 拆 ≤16×≤32 on full vibe_dll."""

    def clk(self):
        return self.dut.clk

    async def _idle(self):
        d = self.dut
        sset(d.port_rst, 0)
        sset(d.device_rst, 0)
        sset(d.link_up, 0)
        sset(d.fec_fail, 0)
        sset(d.nw_dll_vld, 0)
        sset(d.nw_dll_data, 0)
        sset(d.dll_nw_ready, 1)
        sset(d.dll_pcs_ready, 1)
        sset(d.pcs_dll_vld, 0)
        sset(d.pcs_dll_data, 0)

    async def _grant_credit(self, cells=1024):
        """TB-only Force. Stock vibe_dll starts cells=0 → credit_low=1."""
        hier(self.dut, "u_dll.u_crd.cells").value = Force(cells)
        hier(self.dut, "u_dll.u_crd.pend").value = Force(0)
        await RisingEdge(self.dut.clk)

    async def _send_collect(self, beats, min_pcs, timeout=256):
        d = self.dut
        sent = 0
        consumed = 0
        pcs = []
        extra = 0
        for _ in range(timeout):
            await FallingEdge(d.clk)
            if sent < len(beats):
                sset(d.nw_dll_data, beats[sent])
                sset(d.nw_dll_vld, ival(d.nw_dll_ready, 0))
            else:
                sset(d.nw_dll_vld, 0)
            if ival(d.dll_pcs_vld, 0) and ival(d.dll_pcs_ready, 0):
                pcs.append(ival(d.dll_pcs_data, 0) or 0)
            await RisingEdge(d.clk)
            if sent < len(beats) and ival(d.nw_dll_vld, 0) and ival(
                    d.nw_dll_ready, 0):
                sent += 1
                consumed += ival(hier(d, "u_dll.u_tx.consume_flits"), 0)
            if sent >= len(beats) and len(pcs) >= min_pcs:
                extra += 1
                if extra > 12:
                    break
        sset(d.nw_dll_vld, 0)
        return sent, consumed, pcs

    async def _score_one(self, nflits: int) -> bool:
        beats = _nw_beats(nflits)
        exp_pcs = (nflits + 3) // 4
        plen = lph.plen_flits(nflits)
        dec = lph.decl_flits(plen)
        chunks = lph.dllp_chunks(nflits)
        if dec != nflits or sum(chunks) != nflits:
            self.bad(NAME, f"PLENGTH encode nflits={nflits}",
                     f"decl={nflits} chunks={chunks}",
                     f"decl={dec} chunks={chunks}", "lph.plen_flits")
            return False

        sent, consumed, pcs = await self._send_collect(beats, exp_pcs)
        n_pcs = len(pcs)
        ok, exp, act = _score_chunks(nflits, consumed, n_pcs)
        if sent != len(beats):
            self.bad(NAME, f"drive {nflits}-flit CFG3 DLLDP (TP-DLL-004)",
                     f"accept all {len(beats)} NW beats",
                     f"sent={sent} ready stuck?", "u_dll.u_tx.nw_dll_ready")
            return False
        if not pcs:
            self.bad(NAME, f"{nflits}-flit DLLDP after status_up + credit",
                     "dll_pcs_vld beats", "none", "u_dll.u_tx.dll_pcs_vld")
            return False

        f0 = _pcs_flits(pcs[0])[0]
        got_cfg = lph.lph_cfg(f0)
        got_plen = lph.lph_plength(f0)
        got_n = lph.decl_flits(got_plen)
        if got_cfg != 3 or got_n != nflits:
            self.bad(NAME, f"first PCS flit of {nflits}-flit DP",
                     f"CFG=3 PLENGTH→{nflits} chunks={chunks}",
                     f"CFG={got_cfg} decl={got_n} plen=0x{got_plen:x}",
                     "u_dll.u_tx.dll_pcs_data")
            return False
        if not ok:
            self.bad(NAME, f"TP-DLL-004 DLLDP {nflits} flit split ≤16×≤32",
                     exp, act, "u_dll.u_tx")
            return False
        return True

    async def run_phase(self, phase):
        phase.raise_objection(self)
        d = self.dut
        await self._idle()
        await self.reset_n(n_lo=3, n_hi=1)
        await RisingEdge(d.clk)

        # Stock tc_dll: LinkUp=0 → disabled.
        if not ival(d.disabled, 0):
            self.bad(NAME, "LinkUp=0 after reset", "disabled", "0", "u_dll")
            phase.drop_objection(self)
            return

        sset(d.link_up, 1)
        await self.cycles(8)
        if not ival(d.status_up, 0) or ival(d.disabled, 1):
            self.bad(NAME, "LinkUp=1, param_ok/credit_ok hardcoded",
                     "status_up=1 disabled=0",
                     f"status_up={ival(d.status_up, 0)} "
                     f"disabled={ival(d.disabled, 0)}",
                     "u_dll.u_sm")
            phase.drop_objection(self)
            return

        # Stock wrapper starts cells=0 so TX credit_low blocks NW.
        # Same TB-only Force as port/top loopback (not an RTL change).
        await self._grant_credit(1024)

        for nflits in SPLIT_NFLITS:
            await self._grant_credit(1024)
            if not await self._score_one(nflits):
                phase.drop_objection(self)
                return

        self.ok(NAME)
        self.ok("tc_dll_dp_split")
        phase.drop_objection(self)


uvm_component_utils(tc_dll)
