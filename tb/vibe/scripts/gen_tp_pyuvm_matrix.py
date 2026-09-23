#!/usr/bin/env python3
"""TP-0.3 ↔ pyuvm (Python) correspondence audit.

Writes tb/vibe/results/TP_PYUVM_MATRIX.md.

Rules (verification / 验证):
- Official ID set is TP-0.3 (159). Do not invent TP-FEC-* or TP-CFG-008..012.
- Stock SV / tb/vibe/tests/tc_*.sv / SV UVM alone does NOT count as HAS.
- Decision-I leaf TCs (tc_vibe_afifo, tc_vibe_sync2, tc_vibe_rst_sync)
  cover only that leaf. They do not mark full-chip official TPs as HAS.
- This file is a docs/results audit. It is not 1/3, 4/3, freeze, or signoff.

Usage:
  python3 tb/vibe/scripts/gen_tp_pyuvm_matrix.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PYUVM = ROOT / "tb" / "vibe" / "pyuvm"
RESULTS = ROOT / "tb" / "vibe" / "results"
def _tip_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"

sys.path.insert(0, str(HERE))
from official_tp03 import R  # noqa: E402
from scan_official_neg import RULES  # noqa: E402

# Decision-I module-level leaves — never used as full-chip TP cover.
LEAF_ONLY = {
    "tc_vibe_afifo": "tb/vibe/pyuvm/vibe_uvm/tests/unit_afifo.py",
    "tc_vibe_sync2": "tb/vibe/pyuvm/vibe_uvm/tests/unit_sync2.py",
    "tc_vibe_rst_sync": "tb/vibe/pyuvm/vibe_uvm/tests/unit_rst_sync.py",
}

# Matrix TC name is not a standalone Python class; scored inside another TC.
ALIASES = {
    "tc_rt11_not_as_rt01": (
        "tc_rt_g1_official",
        "tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py",
        "unit-sim",
        "PASS line inside tc_rt_g1_official (not a standalone class)",
    ),
}

TEST_FILES = [
    ("fab-suite", "tb/vibe/pyuvm/vibe_uvm/tests/fab_tests.py"),
    ("unit-sim", "tb/vibe/pyuvm/vibe_uvm/tests/unit_leaf.py"),
    ("unit-sim", "tb/vibe/pyuvm/vibe_uvm/tests/unit_more.py"),
    ("unit-sim", "tb/vibe/pyuvm/vibe_uvm/tests/unit_pcs.py"),
    ("port-sim", "tb/vibe/pyuvm/vibe_uvm/tests/port_tests.py"),
    ("switch-sim", "tb/vibe/pyuvm/vibe_uvm/tests/switch_tests.py"),
    ("leaf-only", "tb/vibe/pyuvm/vibe_uvm/tests/unit_afifo.py"),
    ("leaf-only", "tb/vibe/pyuvm/vibe_uvm/tests/unit_sync2.py"),
    ("leaf-only", "tb/vibe/pyuvm/vibe_uvm/tests/unit_rst_sync.py"),
    ("unit-sim", "tb/vibe/pyuvm/vibe_uvm/tests/unit_dll.py"),
]

CLASS_RE = re.compile(r"^class (tc_[A-Za-z0-9_]+)\b", re.M)
NAME_ASSIGN_RE = re.compile(r"^(tc_[A-Za-z0-9_]+) = _one\(", re.M)
OK_RE = re.compile(r'self\.ok\("(tc_[A-Za-z0-9_]+)"\)')
PASS_RE = re.compile(r'tb_pass\("(tc_[A-Za-z0-9_]+)"\)')
HOLE_RE = re.compile(r'\("(tc_hole_[A-Za-z0-9_]+)"')


def _discover_python() -> tuple[dict[str, tuple[str, str]], set[str]]:
    """name -> (relpath, scope). Second return is PASS-line aliases (not classes)."""
    found: dict[str, tuple[str, str]] = {}
    aliases: set[str] = set()
    for scope, rel in TEST_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for name in CLASS_RE.findall(text) + NAME_ASSIGN_RE.findall(text):
            found.setdefault(name, (rel, scope))
        if scope == "unit-sim":
            for name in OK_RE.findall(text):
                if name not in found:
                    found[name] = (rel, scope)
                    aliases.add(name)
    static = PYUVM / "vibe_uvm" / "tests" / "static_tests.py"
    st = static.read_text(encoding="utf-8")
    rel = "tb/vibe/pyuvm/vibe_uvm/tests/static_tests.py"
    for name in PASS_RE.findall(st) + HOLE_RE.findall(st):
        found.setdefault(name, (rel, "static"))
    # NEG_TOKENS keys are passed to tb_pass(name) — not string literals.
    for name in re.findall(r'"(tc_neg_[A-Za-z0-9_]+)"\s*:', st):
        found.setdefault(name, (rel, "static-neg"))
    for _flag, tname, _pat in RULES:
        found.setdefault(tname, (rel, "static-neg"))
    found.setdefault("tc_neg_official", (rel, "static-neg"))
    found.setdefault("tc_tp_holes", (rel, "static-hole"))
    return found, aliases


def _catalog_names() -> set[str]:
    names: set[str] = set()
    for rel in (
        "tb/vibe/pyuvm/catalog.py",
        "tb/vibe/pyuvm/catalog_more.py",
        "tb/vibe/pyuvm/catalog_pcs.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        names.update(re.findall(r'"(tc_[A-Za-z0-9_]+)"', text))
    return names


def classify(tid: str, planned: str, sv_tc: str, py: dict[str, tuple[str, str]],
             pass_aliases: set[str]):
    """Return (status, tc, path, scope, note)."""
    # Never credit Decision-I leaves onto official full-chip IDs.
    def ok(name: str, extra: str = "") -> tuple | None:
        path, scope = py[name]
        if name in LEAF_ONLY or scope == "leaf-only":
            return None
        if name in pass_aliases and name in ALIASES:
            an, ap, ascope, anote = ALIASES[name]
            note = anote if not extra else f"{anote}; {extra}"
            return ("HAS", an, ap, ascope, note)
        if name in pass_aliases:
            extra2 = extra + ("; " if extra else "") + "PASS line (not a standalone class)"
            return ("HAS", name, path, scope, extra2)
        return ("HAS", name, path, scope, extra)

    if sv_tc in py and sv_tc not in LEAF_ONLY and py[sv_tc][1] != "leaf-only":
        rec = ok(sv_tc)
        if rec:
            if tid == "TP-DLL-004":
                extra = ("full vibe_dll; scores >32-flit split ≤16×≤32 "
                         "(not leaf SM/credit/retry/rx/tx)")
                return (rec[0], rec[1], rec[2], rec[3], extra)
            return rec
    if sv_tc in ALIASES:
        name, path, scope, note = ALIASES[sv_tc]
        return ("HAS", name, path, scope, note)
    if planned in py and planned not in LEAF_ONLY and py[planned][1] != "leaf-only":
        rec = ok(planned, "via official planned_name (matrix SV name absent in pyuvm)")
        if rec:
            return rec

    return (
        "GAP",
        "—",
        "—",
        "gap",
        f"no Python TC corresponding to matrix `{sv_tc}` / planned `{planned}` "
        f"(stock SV `{sv_tc}` alone does not count)",
    )


def main() -> int:
    assert len(R) == 159, len(R)
    ids = [r[0] for r in R]
    assert len(ids) == len(set(ids))
    py, pass_aliases = _discover_python()
    catalog = _catalog_names()

    rows = []
    for tid, planned, rule, sv_tc, _sv_path, sv_verd in R:
        status, tc, path, scope, note = classify(
            tid, planned, sv_tc, py, pass_aliases)
        rows.append((tid, rule, status, tc, path, scope, note, sv_tc, sv_verd))

    n = len(rows)
    m = sum(1 for r in rows if r[2] == "HAS")
    g = sum(1 for r in rows if r[2] == "GAP")
    assert n == m + g == 159

    # Catalogued sim TCs that are not Decision-I leaves and not in official map.
    mapped_tcs = {r[3] for r in rows if r[2] == "HAS"}
    extra_sim = sorted(
        name
        for name in catalog
        if name not in LEAF_ONLY
        and name not in mapped_tcs
        and name != "tc_suite_all"
    )

    lines = [
        "# TP-0.3 ↔ pyuvm (Python) coverage matrix",
        "",
        "Docs/results audit only. **Python column is authoritative.**",
        "Stock SV / `tb/vibe/tests/tc_*.sv` / SV UVM (`tb/vibe/uvm/pkg/*.svh`) "
        "alone does **not** count as HAS.",
        "",
        "This document is **not** 1/3, **not** 4/3, **not** freeze, **not** signoff.",
        "",
        "## Sources",
        "",
        f"- Official IDs (159): [`docs/Vibe-UB-Switch-testpoints.md`](../../../docs/Vibe-UB-Switch-testpoints.md) / [`TP-0.3.md`](TP-0.3.md)",
        "- Existing SV/UVM-biased matrix (re-checked, not copied): [`TP_TC_MATRIX.md`](TP_TC_MATRIX.md)",
        "- Python gate: `tb/vibe/pyuvm/` (`catalog*.py`, `entry_*.py`, `vibe_uvm/tests/*.py`)",
        "- Regenerator: `tb/vibe/scripts/gen_tp_pyuvm_matrix.py`",
        f"- Checkout tip audited: `{_tip_sha()}` (`origin/main`)",
        "",
        "## Method",
        "",
        "1. Enumerate the locked TP-0.3 ID set (FS-0.2.7 / AS-0.1.2).",
        "2. Discover actual Python TCs: `class tc_*` / fab `_one()` factories / "
        "`static_tests.py` PASS/HOLE names / `scan_official_neg.RULES`.",
        "3. HAS = a pyuvm TC exists that corresponds to the official rule "
        "(same identifier as `TP_TC_MATRIX.md`, or an in-file PASS alias).",
        "4. GAP = no such Python TC. Icarus/SV-UVM presence is noted only as the miss.",
        "5. Decision-I leaf TCs (`tc_vibe_afifo`, `tc_vibe_sync2`, `tc_vibe_rst_sync`) "
        "cover **only that leaf**. They are listed in the appendix and are "
        "**not** used to mark full-chip official TPs as HAS.",
        "",
        "## Totals",
        "",
        f"| | count |",
        f"|---|------:|",
        f"| Official testpoints (TP-0.3) | **{n}** |",
        f"| HAS Python TC | **{m}** |",
        f"| GAP (no corresponding Python TC) | **{g}** |",
        "",
        f"N={n} / M={m} / G={g}. Do not read this as a gate fraction, freeze, or signoff.",
        "",
        "## GAP list",
        "",
    ]

    gaps = [r for r in rows if r[2] == "GAP"]
    if not gaps:
        lines.append("None.")
        lines.append("")
    else:
        lines += [
            "| ID | rule | gap |",
            "|----|------|-----|",
        ]
        for tid, rule, _st, _tc, _path, _sc, note, sv_tc, _sv in gaps:
            lines.append(f"| {tid} | {rule} | {note} |")
        lines.append("")

    by_scope: dict[str, int] = {}
    for r in rows:
        if r[2] == "HAS":
            by_scope[r[5]] = by_scope.get(r[5], 0) + 1
    lines += [
        "## HAS by Python scope (not a gate)",
        "",
        "| scope | HAS count |",
        "|-------|----------:|",
    ]
    for k in sorted(by_scope):
        lines.append(f"| {k} | {by_scope[k]} |")
    lines += [
        "",
        "Scope is where the Python TC lives. A unit-sim or static-neg TC can still "
        "be the project's designated scorer for a chip-level rule (same convention "
        "as `TP_TC_MATRIX.md`). Leaf-only Decision-I TCs are excluded from HAS.",
        "",
        "## Full matrix",
        "",
        "| TP | rule (short) | pyuvm | TC name | file | scope | note |",
        "|----|--------------|-------|---------|------|-------|------|",
    ]
    for tid, rule, status, tc, path, scope, note, sv_tc, _sv in rows:
        tc_cell = f"`{tc}`" if tc != "—" else "—"
        path_cell = f"`{path}`" if path != "—" else "—"
        note_cell = note if note else ""
        if status == "HAS" and sv_tc != tc:
            extra = f"matrix SV name `{sv_tc}`"
            note_cell = f"{note_cell}; {extra}" if note_cell else extra
        lines.append(
            f"| {tid} | {rule} | **{status}** | {tc_cell} | {path_cell} | {scope} | {note_cell} |"
        )

    lines += [
        "",
        "## Appendix — Decision-I leaf Python TCs (not full-chip cover)",
        "",
        "These exist under `tb/vibe/pyuvm` and score **only** their leaf DUT. "
        "They must not be used to close official full-chip TPs "
        "(TP-CDC-001 / TP-CDC-002 / TP-IF-* / etc.).",
        "",
        "| TC | file | leaf |",
        "|----|------|------|",
        "| `tc_vibe_afifo` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_afifo.py` | `vibe_afifo` |",
        "| `tc_vibe_sync2` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_sync2.py` | `vibe_sync2` |",
        "| `tc_vibe_rst_sync` | `tb/vibe/pyuvm/vibe_uvm/tests/unit_rst_sync.py` | `vibe_rst_sync` |",
        "",
        "Official TP-CDC-001 is scored (if HAS) by `tc_afifo_afull10`, not `tc_vibe_afifo`.",
        "Official TP-CDC-002 is scored (if HAS) by `tc_rst_sync`, not `tc_vibe_rst_sync`.",
        "There is no official TP whose designated scorer is `tc_vibe_sync2`.",
        "",
        "## Appendix — catalogued Python TCs not used as a TP scorer",
        "",
        "Present in `catalog*.py` / tests but not the designated scorer for any "
        "official TP-0.3 ID (helpers, extra PCS/DLL leaves, suite umbrella). "
        "Not a defect by itself.",
        "",
    ]
    if extra_sim:
        lines += ["| TC |", "|----|"]
        for name in extra_sim:
            lines.append(f"| `{name}` |")
        lines.append("")
    else:
        lines.append("None.")
        lines.append("")

    lines += [
        "## Appendix — still Icarus/SV-only (not Python-sim)",
        "",
        "From `tb/vibe/pyuvm/README.md` (re-checked against `vibe_uvm/tests/`):",
        "",
        "| name | Python? | note |",
        "|------|---------|------|",
        "| `tc_dll` | **yes** | full-stack wrapper; **TP-DLL-004** >32-flit split ≤16×≤32 |",
        "| `tc_pcs_rx` (full stack) | **no** | no official TP maps only to this name; leaf PCS RX units exist |",
        "| `tc_pcs_tx` (full stack) | **no** | no official TP maps only to this name; leaf PCS TX units exist |",
        "",
        "---",
        "",
        "Handoff: 验证 → 芯片开发PM. Audit only. Leave open. Do not merge as a gate.",
        "",
    ]

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "TP_PYUVM_MATRIX.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}  N={n} HAS={m} GAP={g}")
    for r in gaps:
        print(f"  GAP {r[0]}  {r[6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
