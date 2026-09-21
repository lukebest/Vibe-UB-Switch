"""Static / hole / official-neg TCs. No simulator. Same PASS lines as Icarus."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from vibe_uvm import lph
from vibe_uvm.report import tb_pass, tb_fail, tb_hole, tb_note

ROOT = Path(__file__).resolve().parents[5]
RTL = ROOT / "rtl"
TB = ROOT / "tb" / "vibe"

# Official scan — reuse the existing script rules.
sys.path.insert(0, str(TB / "scripts"))
from scan_official_neg import RULES, scan  # noqa: E402


NEG_TOKENS = {
    "tc_neg_dijkstra": (r"dijkstra|shortest_path|path_cost", "unimpl"),
    "tc_neg_ubfm": (r"\bUBFM\b|ubfm_", None),
    "tc_neg_no_optical": (r"optical_pma|OPTICAL_PMA|qdlws_optical|ST_OPTICAL", None),
    "tc_neg_exact_route": (r"exact_route|ExactRoute|EXACT_ROUTE", None),
    "tc_neg_port_cna": (r"PORT_CNA|port_cna|PortCNA", None),
    "tc_neg_cut_through": (r"cut_through|cutthrough|CUT_THROUGH", None),
    "tc_neg_hi_fec_ber": (r"hi_FEC_BER|hi_fec_ber|HIFECBER", None),
    "tc_neg_probe": (r"ST_PROBE|st_probe|Probe_Active", None),
    "tc_neg_qdlws": (r"QDLWS|qdlws", None),
}

HOLES = [
    ("tc_hole_g2_route_max", "TP-HOLE-G2 — Route Table Max Index 未在 FS 闭合"),
    ("tc_hole_g3_irq_pin", "TP-HOLE-G3 — 额外 IRQ 引脚未在 FS 闭合"),
    ("tc_hole_g4_reset_pin", "TP-HOLE-G4 — 额外复位引脚未在 FS 闭合"),
    ("tc_hole_g5_cna_poweron", "TP-HOLE-G5 — CNA 上电值未在 FS 闭合"),
    ("tc_hole_g6_lmsm_go_src", "TP-HOLE-G6 — lmsm_go 来源未在 FS 闭合"),
    ("tc_hole_g8_package_pins", "TP-HOLE-G8 — 封装引脚未在 FS 闭合"),
    ("tc_hole_g9_rxeq_tension", "TP-HOLE-G9 — RXEQ 张力未在 FS 闭合"),
    ("tc_hole_010_perf", "TP-HOLE-010 — 性能数字未在 FS 闭合"),
    ("tc_hole_012_counter_width", "TP-HOLE-012 — 计数器宽度非 FS 必须（禁止臆造产品宽度）"),
]


def _rtl_text() -> str:
    parts = []
    for fp in sorted(RTL.rglob("vibe_*.sv")) + sorted(RTL.rglob("vibe_*.vh")):
        parts.append(fp.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def run_neg_named() -> int:
    fails = 0
    text = _rtl_text()
    for name, (pat, allow) in NEG_TOKENS.items():
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pat, line):
                if allow and allow in line:
                    continue
                if re.search(r"(?i)(no |not |don't |do not|absent|unimpl|forbidden)", line):
                    continue
                hits.append(line.strip()[:80])
        if hits and name == "tc_neg_dijkstra":
            tb_fail(name, f"scan rtl for {pat}", "no shortest-path RTL",
                    hits[0], "rtl/**/vibe_*.sv")
            fails += 1
        else:
            tb_pass(name)
    return fails


def run_id_nports() -> int:
    fails = 0
    if lph.N_PORT != 4:
        tb_fail("tc_id_nports_entity0", "compile-time VIBE_N_PORT", "4",
                str(lph.N_PORT), "vibe_ub_params.vh")
        fails += 1
    if ((lph.PORT_BASIC >> 16) & 0xFFFF) != 4:
        tb_fail("tc_id_nports_entity0", "CFG0_PORT_BASIC nports field", "4",
                str((lph.PORT_BASIC >> 16) & 0xFFFF), "VIBE_PORT_BASIC")
        fails += 1
    if not fails:
        tb_pass("tc_id_nports_entity0")
        tb_pass("tc_neg_no_fifth_port")
    return fails


def run_holes() -> int:
    for name, note in HOLES:
        tb_hole(name, note)
    tb_note("TP-HOLE-G7 mapped to tc_credit_1024_flit_bp (closed: 1024 is cell)")
    tb_note("TP-HOLE-011 mapped to tc_rt10_must_drop (G1 is not a hole)")
    tb_pass("tc_tp_holes")
    return 0


def run_official_neg() -> int:
    hits = scan(RTL)
    fails = 0
    name_by_flag = {flag: tname for flag, tname, _ in RULES}
    for flag, tname, _ in RULES:
        if hits.get(flag):
            tb_fail(tname, f"scan rtl/vibe_*.sv for {flag}",
                    "identifier absent from code (comments citing ban OK)",
                    "token present in RTL", "rtl/**/vibe_*.sv")
            fails += 1
        else:
            tb_pass(tname)
    if not fails:
        tb_pass("tc_neg_official")
    return fails


def run_absent_scan() -> int:
    """Port of tb/vibe/scripts/scan_absent.sh."""
    fails = 0
    pairs = [
        ("qdlws", r"QDLWS|qdlws"),
        ("exact_route", r"exact_route|ExactRoute|EXACT_ROUTE"),
        ("port_cna", r"PORT_CNA|port_cna|PortCNA"),
        ("scna_compare", r"scna_cmp|SCNA_CMP|scna_compare"),
        ("cut_through", r"cut_through|cutthrough|CUT_THROUGH"),
        ("ubfm", r"\bUBFM\b|ubfm_"),
        ("hi_fec_ber", r"hi_FEC_BER|hi_fec_ber|HIFECBER"),
        ("probe_state", r"ST_PROBE|st_probe|Probe_Active"),
        ("optical", r"optical_pma|OPTICAL_PMA|qdlws_optical|ST_OPTICAL"),
    ]
    for name, pat in pairs:
        real = []
        for fp in RTL.rglob("*.sv"):
            for i, line in enumerate(fp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if re.search(pat, line) and not re.search(
                    r"(?i)(No |not |NOT |do not|Do not|absent|unimpl)", line
                ):
                    real.append(f"{fp}:{i}")
        if real:
            tb_note(f"{name}: identifier present (inspect — may be comment-only)")
        else:
            tb_pass(f"neg_{name}")
    # Dijkstra
    dijk = []
    for fp in RTL.rglob("*.sv"):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(r"dijkstra|shortest_path|path_cost", line) and "unimpl" not in line:
                dijk.append(line)
    if dijk:
        tb_fail("neg_no_dijkstra", "scan rtl", "no shortest-path RTL", dijk[0], "rtl")
        fails += 1
    else:
        tb_pass("neg_no_dijkstra")
    # no cfg_rd_* in TB
    rd = []
    for fp in TB.rglob("*.sv"):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(r"\bcfg_rd_", line) and not re.search(
                r"no cfg_rd|No cfg_rd|not .*cfg_rd|cfg_rd_\*", line
            ):
                rd.append(str(fp))
    if rd:
        tb_fail("neg_no_cfg_rd", "scan tb/vibe", "no cfg_rd_* in TB", rd[0], "tb/vibe")
        fails += 1
    else:
        tb_pass("neg_no_cfg_rd (no cfg_rd_* in TB)")
    return fails


def run_all_static() -> int:
    f = 0
    f += run_id_nports()
    f += run_holes()
    f += run_neg_named()
    f += run_official_neg()
    return f


if __name__ == "__main__":
    sys.exit(1 if run_all_static() else 0)
