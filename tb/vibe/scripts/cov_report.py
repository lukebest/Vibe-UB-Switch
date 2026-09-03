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
    """Parse Verilator SystemC::Coverage-3 records.

    Lines look like:
      C '\\x01f\\x02/path/vibe_x.sv\\x01l\\x0226\\x01page\\x02v_line/vibe_x...' N
    """
    recs = []
    if not os.path.isfile(path):
        return recs
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("C "):
                continue
            m = re.match(r"C '(.*)'\s+(\d+)\s*$", line)
            if not m:
                continue
            payload, cnt = m.group(1), int(m.group(2))
            fields = {"count": cnt}
            for part in payload.split("\x01"):
                if not part or "\x02" not in part:
                    continue
                k, v = part.split("\x02", 1)
                fields[k] = v
            recs.append(fields)
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
    # Merge of per-cluster .dat files repeats the same file:line when a
    # module is elaborated in several clusters. Uniq by (file,line,page,hier)
    # and keep the max count so the total is implemented RTL, not cluster×N.
    uniq = {}
    for r in recs:
        fn = r.get("f") or r.get("filename") or r.get("file") or ""
        if not fn or not is_vibe_rtl(fn, rtl_root):
            continue
        page = (r.get("page") or "").lower()
        loc = r.get("l") or r.get("line") or "?"
        name = r.get("o") or ""
        hier = r.get("h") or r.get("hier") or ""
        # Source-line coverage of vibe_*.sv (not per-instance / per-cluster).
        kind = "tog" if ("toggle" in page or page.startswith("v_t")) else "line"
        key = (os.path.basename(fn), loc, kind, name)
        cnt = int(r.get("count") or 0)
        prev = uniq.get(key)
        if prev is None or cnt > prev["count"]:
            uniq[key] = {**r, "f": fn, "count": cnt, "page": page, "l": loc, "o": name}

    by_file = defaultdict(lambda: {"line_tot": 0, "line_hit": 0, "tog_tot": 0, "tog_hit": 0, "miss": []})

    for r in uniq.values():
        fn = r["f"]
        base = os.path.basename(fn)
        page = (r.get("page") or "").lower()
        is_tog = "toggle" in page or page.startswith("v_t")
        cnt = int(r.get("count") or 0)
        loc = r.get("l") or "?"
        name = r.get("o") or ""
        if name:
            loc = f"{loc} {name}"
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

    line_miss = []
    tog_miss = []
    for fn in files:
        for m in by_file[fn]["miss"]:
            if m.startswith("line "):
                line_miss.append(m)
            else:
                tog_miss.append(m)

    lines.append("## Uncovered LINE points")
    lines.append("")
    if not line_miss:
        lines.append("None.")
        lines.append("")
    else:
        for m in line_miss:
            lines.append(f"- `{m}`")
        lines.append("")

    lines.append("## Uncovered toggle bins (first 40; not the line gate)")
    lines.append("")
    n = 0
    for m in tog_miss:
        if n >= 40:
            break
        lines.append(f"- `{m}`")
        n += 1
    extra = len(tog_miss) - n
    if extra > 0:
        lines.append(f"- … {extra} more (see annotate/ and cov_raw.txt)")
    lines.append("")
    lines.append("Classification: see `COVERAGE_HOLES.md`.")
    lines.append("Acceptance: LINE ≥95% + waiver (do not chase 100%).")
    lines.append("Wide-bus toggle miss is unused data-bit patterns (not the LINE gate).")
    lines.append("TB holes: fill if cheap, else waiver. dll_tx :98/:144 = WAIVER/防御.")
    lines.append("TOOL: tmr_load / dec_lid / combo-pad settle. Do not patch rtl/.")
    lines.append("Suite Verilator bind OOM on VOQ — use per-module clusters.")
    lines.append("")
    classify = os.path.join(os.path.dirname(out_md), "..", "scripts", "cov_classify.md")
    # tb/vibe/results/../scripts/cov_classify.md
    classify = os.path.normpath(classify)
    if os.path.isfile(classify):
        with open(classify, "r", encoding="utf-8") as cf:
            lines.append(cf.read().rstrip())
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
