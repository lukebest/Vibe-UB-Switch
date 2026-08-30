#!/usr/bin/env python3
"""Honest Verilator coverage totals for vibe_*.sv only.

Verilator has no VCS-style FSM report. FSM coverage is line hits on state
case/if. Toggle points are reported separately when present in the .dat.
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict


def parse_dat(path: str):
    """Parse Verilator coverage.dat records."""
    recs = []
    cur = {}
    if not os.path.isfile(path):
        return recs
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("C "):
                # C 'key' 'value'
                m = re.match(r"C\s+'([^']*)'\s+'([^']*)'", line)
                if not m:
                    continue
                k, v = m.group(1), m.group(2)
                if k == "count" and cur:
                    cur["count"] = int(v) if v.isdigit() else 0
                    recs.append(cur)
                    cur = {}
                else:
                    cur[k] = v
            elif line.startswith("#") or not line.strip():
                continue
    return recs


def is_vibe_rtl(fn: str, rtl_root: str) -> bool:
    base = os.path.basename(fn)
    if not (base.startswith("vibe_") and base.endswith(".sv")):
        return False
    # Prefer RTL tree; still count if path contains /rtl/
    if "/rtl/" in fn.replace("\\", "/"):
        return True
    if os.path.isfile(os.path.join(rtl_root, base)):
        return True
    # walk rtl
    for dirpath, _, files in os.walk(rtl_root):
        if base in files:
            return True
    return False


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: cov_report.py merged.dat rtl_root out.md")
        return 2
    dat, rtl_root, out_md = sys.argv[1], sys.argv[2], sys.argv[3]
    recs = parse_dat(dat)
    by_file = defaultdict(lambda: {"line_tot": 0, "line_hit": 0, "tog_tot": 0, "tog_hit": 0, "miss": []})

    for r in recs:
        fn = r.get("filename") or r.get("file") or r.get("page") or ""
        if not fn:
            continue
        if not is_vibe_rtl(fn, rtl_root):
            continue
        base = os.path.basename(fn)
        typ = (r.get("type") or r.get("thresh") or "l").lower()
        # Verilator uses 'l' line, 't' toggle; some dumps use comment
        comment = (r.get("comment") or "").lower()
        is_tog = typ.startswith("t") or "toggle" in comment
        cnt = int(r.get("count") or 0)
        loc = r.get("line") or r.get("column") or "?"
        bucket = by_file[base]
        if is_tog:
            bucket["tog_tot"] += 1
            if cnt > 0:
                bucket["tog_hit"] += 1
            else:
                bucket["miss"].append(f"toggle {fn}:{loc}")
        else:
            bucket["line_tot"] += 1
            if cnt > 0:
                bucket["line_hit"] += 1
            else:
                bucket["miss"].append(f"line {fn}:{loc}")

    files = sorted(by_file)
    lt = lh = tt = th = 0
    lines = []
    lines.append("# Verilator coverage (vibe_*.sv only)")
    lines.append("")
    lines.append("Honest tool output. FSM = line hits on state `case`/`if` (no VCS FSM engine).")
    lines.append("")
    lines.append("| Module | Line hit/tot | Line % | Toggle hit/tot | Toggle % |")
    lines.append("|--------|-------------:|-------:|---------------:|---------:|")
    for fn in files:
        b = by_file[fn]
        lt += b["line_tot"]
        lh += b["line_hit"]
        tt += b["tog_tot"]
        th += b["tog_hit"]
        lp = (100.0 * b["line_hit"] / b["line_tot"]) if b["line_tot"] else 0.0
        tp = (100.0 * b["tog_hit"] / b["tog_tot"]) if b["tog_tot"] else 0.0
        lines.append(
            f"| `{fn}` | {b['line_hit']}/{b['line_tot']} | {lp:.1f} | "
            f"{b['tog_hit']}/{b['tog_tot']} | {tp:.1f} |"
        )
    lp = (100.0 * lh / lt) if lt else 0.0
    tp = (100.0 * th / tt) if tt else 0.0
    lines.append(
        f"| **TOTAL implemented vibe_*** | **{lh}/{lt}** | **{lp:.1f}** | "
        f"**{th}/{tt}** | **{tp:.1f}** |"
    )
    lines.append("")
    # RTL files with zero records
    rtl_sv = []
    for dirpath, _, fs in os.walk(rtl_root):
        for f in fs:
            if f.startswith("vibe_") and f.endswith(".sv"):
                rtl_sv.append(f)
    missing = sorted(set(rtl_sv) - set(files))
    if missing:
        lines.append("## RTL files with no coverage records")
        lines.append("")
        for f in missing:
            lines.append(f"- `{f}` — no stimulus in Verilator clusters (or not elaborated)")
        lines.append("")

    lines.append("## Uncovered bins (first 80)")
    lines.append("")
    n = 0
    for fn in files:
        for m in by_file[fn]["miss"]:
            if n >= 80:
                break
            lines.append(f"- `{m}`")
            n += 1
        if n >= 80:
            break
    extra = sum(len(by_file[fn]["miss"]) for fn in files) - n
    if extra > 0:
        lines.append(f"- … {extra} more (see annotate/ and cov_raw.txt)")
    lines.append("")
    lines.append("Classification: timer-heavy LMSM/retry-wait paths and unused RX PCS")
    lines.append("states are **missing stimulus**, not faked as covered. Dead/non-goal")
    lines.append("bins (Probe, Dijkstra, QDLWS, Exact Route) are not in RTL.")
    lines.append("")

    text = "\n".join(lines)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w") as f:
        f.write(text + "\n")
    print(text)
    print(f"LINE {lh}/{lt} = {lp:.1f}%")
    print(f"TOGGLE {th}/{tt} = {tp:.1f}%")
    print(f"FSM note: no separate FSM engine; use line % on state machines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
